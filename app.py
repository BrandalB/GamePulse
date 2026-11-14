"""GamePulse — Steam market intelligence dashboard."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from gamepulse.analytics import filter_games, genre_summary, overview, quality_metrics, year_summary
from gamepulse.db import create_schema, engine_from_env, read_games, read_genres, read_runs
from gamepulse.entities import display_credits
from gamepulse.explorer import similar_games, review_breakdown
from gamepulse.market import (entity_summary, genre_year_trends, genre_growth, price_reception_bands,
                              hidden_gems, build_insights, query_insight, SQL_INSIGHTS)

st.set_page_config(page_title="GamePulse • Steam Intelligence", page_icon="🎮", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { color-scheme: dark; }
html, body, [class*="css"], [data-testid="stApp"] { font-family:'DM Sans', sans-serif; }
.stApp { background:radial-gradient(ellipse 80% 38% at 60% -12%,rgba(51,94,146,.22),transparent 75%), #080e1c; color:#e6edf9; }
[data-testid="stHeader"] { background:rgba(8,14,28,.45); }
[data-testid="stSidebar"] { background: #0d1628; border-right:1px solid #20304a; }
[data-testid="stSidebar"] h2 { font-size:1.15rem; }
.block-container { padding-top:1.1rem; padding-bottom:4rem; max-width:1550px; }
h1,h2,h3 {font-family:'Space Grotesk',sans-serif;letter-spacing:-.035em;}
h1 {font-size:2.4rem !important;}
h3 {font-size:1.2rem !important;}
p {line-height:1.55;}
[data-testid="stMetric"] { background:linear-gradient(140deg,#141f36,#101a2d);border:1px solid #273952;border-radius:15px;padding:17px 17px 14px;min-height:112px; }
[data-testid="stMetricLabel"] {color:#a2b5d0;}
[data-testid="stMetricValue"] {color:#f4f7fc; font-family:'Space Grotesk',sans-serif;letter-spacing:-.04em;}
[data-testid="stTabs"] button[role="tab"] {font-weight:650;white-space:nowrap;}
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:.25rem;overflow-x:auto;scrollbar-width:thin;padding-bottom:.35rem;}
[data-testid="stTabs"] button[aria-selected="true"] {color:#5eead4;}
[data-testid="stVerticalBlockBorderWrapper"] > div {border-color:#28384e;}
[data-testid="stDataFrame"], [data-testid="stTable"] {border-radius:12px;overflow:hidden;}
[data-testid="stDownloadButton"] button, [data-testid="stButton"] button[kind="primary"] {border-radius:10px;background:#15b8af;border-color:#15b8af;color:#06131d;font-weight:800;}
[data-testid="stDownloadButton"] button:hover, [data-testid="stButton"] button[kind="primary"]:hover {background:#5eead4;border-color:#5eead4;color:#06131d;}
[data-testid="stAlert"] {border-radius:12px;}
.gp-topline {font-size:.75rem;letter-spacing:.18em;font-weight:800;color:#5eead4;text-transform:uppercase;margin-top:.6rem}
.gp-brand {font-family:'Space Grotesk',sans-serif;font-size:2.8rem;font-weight:700;letter-spacing:-.06em;line-height:1.15;margin:.35rem 0;}
.gp-brand span {color:#5eead4;}
.gp-muted {color:#a3b4cc;font-size:.94rem;margin-bottom:1rem;}
.gp-section {font-family:'Space Grotesk',sans-serif;font-size:1.27rem;letter-spacing:-.035em;font-weight:700;margin:1.3rem 0 .45rem;}
.gp-eyebrow {color:#64dccc;font-size:.74rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;margin-bottom:.2rem;}
.gp-note {border-left:3px solid #37b8b4;border-radius:0 8px 8px 0;background:#132138;padding:12px 15px;color:#bbcbe0;margin:10px 0 18px 0;font-size:.86rem;}
.gp-chip {display:inline-block;padding:5px 10px;margin:5px 8px 3px 0;border-radius:30px;background:#182941;border:1px solid #294563;color:#b7dbe6;font-size:.74rem;font-weight:700;}
.gp-hero {padding:22px 26px;margin:0 0 20px;background:linear-gradient(116deg,#122945 0%,#101a30 55%,#1a1937 100%);border:1px solid #2a4260;border-radius:18px;}
.gp-sidebrand {font-family:'Space Grotesk',sans-serif;font-weight:800;font-size:1.55rem;letter-spacing:-.04em;color:#f3f7ff;}
.gp-sidebrand b {color:#5eead4;}
.gp-small {color:#94a8bf;font-size:.8rem}
div[data-testid="stRadio"] > label {font-weight:700;}
</style>
""", unsafe_allow_html=True)

AQUA = "#5eead4"
VIOLET = "#a78bfa"
BLUE = "#63aaff"
PINK = "#f4a1c3"
PALETTE = [AQUA, VIOLET, BLUE, PINK, "#f5bf79", "#84ccaa"]


@st.cache_resource
def get_engine():
    engine = engine_from_env()
    create_schema(engine)
    return engine


@st.cache_data(ttl=120, show_spinner="Loading your Steam catalog…")
def fetch_data():
    engine = get_engine()
    return read_games(engine), read_genres(engine), read_runs(engine)


def plot(fig, *, height=340):
    fig.update_layout(
        template="plotly_dark", height=height, margin=dict(l=5, r=8, t=18, b=15),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#cbd8ec", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0),
        hoverlabel=dict(bgcolor="#182841", font_color="#f8fafc"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#20334b", zeroline=False, linecolor="#344760")
    fig.update_yaxes(showgrid=False, zeroline=False, linecolor="#344760")
    st.plotly_chart(fig, use_container_width=True, theme=None)


def subhead(title, detail=None):
    st.markdown(f'<div class="gp-section">{title}</div>', unsafe_allow_html=True)
    if detail:
        st.caption(detail)


def note(message):
    st.markdown(f'<div class="gp-note">{message}</div>', unsafe_allow_html=True)


def compact(value):
    if value is None or pd.isna(value):
        return "N/A"
    value = float(value)
    if abs(value) >= 1e9: return f"{value/1e9:,.2f}B"
    if abs(value) >= 1e6: return f"{value/1e6:,.2f}M"
    if abs(value) >= 1e3: return f"{value/1e3:,.1f}K"
    return f"{value:,.0f}"


def money(value):
    return "N/A" if value is None or pd.isna(value) else f"${float(value):,.2f}"


def pct(value):
    return "N/A" if value is None or pd.isna(value) else f"{float(value):.1%}"


def no_data(subject):
    st.info(f"No data available for {subject} with the selected filters. Widen your filters in the sidebar.")


def game_details(game, genres, catalog):
    """Detail page built from dataset fields; no third-party API or ML required."""
    gid = int(game["appid"])
    st.subheader(str(game["name"]))
    left, right = st.columns([1.8, 1], gap="large")
    with left:
        a,b,c,d = st.columns(4)
        a.metric("Listed price", money(game["price"]))
        b.metric("Steam reviews", compact(game["review_count"]))
        c.metric("Positive share", pct(game["positive_rate"]))
        d.metric("Peak CCU · snapshot", compact(game["peak_ccu"]))
        info = st.columns(2)
        with info[0]:
            st.write("**Released:**", str(game["release_date"])[:10] if pd.notna(game["release_date"]) else "Unknown")
            st.write("**Developer:**", display_credits(game["developers"]))
            st.write("**Publisher:**", display_credits(game["publishers"]))
        with info[1]:
            genre_list = genres.loc[genres["appid"] == gid, "genre"].tolist()
            st.write("**Genres:**", ", ".join(genre_list) if genre_list else "Unclassified")
            st.write("**Platforms:**", ", ".join(x.title() for x in ["windows","mac","linux"] if game[x]) or "Not specified")
            if pd.notna(game["owners_low"]) and pd.notna(game["owners_high"]):
                st.write("**Estimated owners:**", f'{compact(game["owners_low"])}–{compact(game["owners_high"])}')
            else:
                st.write("**Estimated owners:** Not available")
        st.link_button("Open Steam store page", f"https://store.steampowered.com/app/{gid}/")
        if st.button("＋ Add this game to Compare", key=f"profile_compare_{gid}", disabled=gid in st.session_state.get("compare_ids",[]) or len(st.session_state.get("compare_ids",[])) >= 5):
            st.session_state.setdefault("compare_ids", []).append(gid)
            st.success("Added! Open the Compare Games tab to see it.")
    with right:
        st.markdown("**Review breakdown**")
        counts=review_breakdown(game)
        if not counts.empty and counts["Reviews"].sum()>0:
            fig=px.pie(counts,names="Sentiment",values="Reviews",hole=.63,
                       color="Sentiment",color_discrete_map={"Positive":AQUA,"Negative":PINK})
            plot(fig,height=240)
        else:
            st.info("No recorded positive/negative review counts.")
        st.caption("These are review counts, not copies sold.")
    subhead("More games in similar genres", "Ranked by shared genre tags, then review count. This is a simple rule-based list, not a personalized recommendation model.")
    near=similar_games(catalog,genres,gid,8)
    if near.empty:
        st.info("There are no other games with matching genre tags in this dataset.")
    else:
        st.dataframe(near.rename(columns={"name":"Game","release_year":"Year","price":"Price (USD)","review_count":"Reviews","positive_rate":"Positive share","shared_genres":"Shared genres"}).drop(columns=["appid"]),
                     hide_index=True,use_container_width=True,
                     column_config={"Positive share":st.column_config.ProgressColumn("Positive share",min_value=0,max_value=1,format="%.1f")})


try:
    games, genres, runs = fetch_data()
except Exception as exc:
    st.error("The database could not be opened. Check DATABASE_URL and the project README.")
    st.code(str(exc))
    st.stop()
if games.empty:
    st.warning("No games loaded. Run `python -m gamepulse.load data/sample_games.csv` or import your real Steam CSV, then refresh.")
    st.stop()

for column in ["price","release_year","positive","negative","review_count","positive_rate","owners_low","owners_high","owners_mid","peak_ccu","metacritic_score","average_playtime_forever"]:
    games[column] = pd.to_numeric(games[column], errors="coerce")
for column in ["windows","mac","linux"]:
    games[column] = games[column].fillna(False).astype(bool)

with st.sidebar:
    st.markdown('<div class="gp-sidebrand">◈ Game<b>Pulse</b></div><div class="gp-small">STEAM MARKET INTELLIGENCE</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("### Catalog filters")
    st.caption("Filters apply to Overview, Genres, Reception, Explorer, Market Insights, Trends and Studios. Comparison, Data Quality and Case Study use the full catalog.")
    years_available = games["release_year"].dropna()
    y0 = int(years_available.min()) if len(years_available) else 2000
    y1 = int(years_available.max()) if len(years_available) else 2025
    year_range = st.slider("Release years", y0, y1, (y0, y1)) if y0 < y1 else (y0,y1)
    all_genres = sorted(genres["genre"].dropna().unique().tolist())
    selected_genres = st.multiselect("Genres · match any", all_genres)
    max_price = float(max(math.ceil(games["price"].max()) if games["price"].notna().any() else 100, 1))

    price_limit = st.slider("Maximum list price (USD)", min_value=0.0, max_value=max_price, value=max_price, step=1.0)
    paid_filter = st.selectbox("Business model", ["All", "Paid", "Free"])
    minimum_reviews = st.select_slider("At least this many reviews", [0,10,50,100,500,1000,5000,10000], value=0)
    platforms = st.multiselect("Available on all selected", ["windows", "mac", "linux"])
    search = st.text_input("Title contains", placeholder="Search catalog...")
    st.divider()
    if st.button("↻ Refresh from database", use_container_width=True):
        fetch_data.clear()
        st.rerun()
    st.caption(f"{len(games):,} unique AppIDs loaded · historical snapshot")

filtered = filter_games(games, genres, year_range, selected_genres, (0,price_limit), minimum_reviews, platforms, search, paid_filter)

st.markdown('<div class="gp-topline">Historical Steam catalog analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="gp-brand">Game<span>Pulse</span></div>', unsafe_allow_html=True)
st.markdown('<div class="gp-muted">Analyze Steam game pricing, genres, review activity, studios, publishers, and market signals from a historical catalog snapshot.</div>', unsafe_allow_html=True)

pages = st.tabs([
    "◈ Overview", "▤ Genres & Pricing", "✦ Reception & Reach", "⌕ Game Explorer",
    "⚔ Compare Games", "◉ Data Quality & Methods", "✧ Market Insights",
    "↗ Genre Trends", "♜ Studios & Publishers", "⌘ SQL Lab", "▣ Findings & Case Study"
])
st.caption(f"{len(filtered):,} matching games out of {len(games):,} loaded · Filters on the left · Estimated owners are not verified sales")

with pages[0]:
    subhead("Market at a glance", "Key indicators for the games currently selected.")
    if filtered.empty:
        no_data("market overview")
    else:
        stats = overview(filtered)
        metrics = [("Catalog titles",f'{stats["games"]:,}'),("Median paid price",money(stats["paid_median"])),
                   ("Free-to-play share",pct(stats["free_share"])),("Positive review share",pct(stats["positive_share"])),
                   ("Total review volume",compact(stats["review_volume"]))]
        for box,(label,value) in zip(st.columns(5),metrics): box.metric(label,value)
        left,right = st.columns([1.6,1],gap="large")
        with left:
            subhead("Release cadence")
            ys=year_summary(filtered)
            if not ys.empty:
                fig=px.area(ys,x="year",y="releases",markers=True,color_discrete_sequence=[AQUA],labels={"year":"Release year","releases":"Games"})
                plot(fig)
            else: no_data("release dates")
        with right:
            subhead("Free versus paid")
            priced=filtered["price"].dropna()
            if len(priced):
                split=pd.DataFrame({"Category":["Free-to-play","Paid"],"Games":[int(priced.eq(0).sum()),int(priced.gt(0).sum())]})
                fig=px.pie(split,names="Category",values="Games",hole=.67,color_discrete_sequence=[AQUA,VIOLET])
                fig.update_traces(textinfo="percent+label")
                plot(fig)
            else: no_data("price breakdown")
        subhead("Most discussed games")
        top=filtered.nlargest(12,"review_count")[['name','release_year','price','review_count','positive_rate','peak_ccu']].copy()
        top.columns=['Game','Year','Price (USD)','Reviews','Positive share','Peak CCU']
        st.dataframe(top,hide_index=True,use_container_width=True,column_config={"Positive share":st.column_config.ProgressColumn("Positive share",min_value=0,max_value=1,format="%.2f")})
        note("Prices are catalog list prices, not transaction values. The dataset has no verified sales, refunds or profit data.")

with pages[1]:
    subhead("Genres & pricing", "See which categories dominate the catalog and how their listed prices differ.")
    gs=genre_summary(filtered,genres)
    if gs.empty:
        no_data("genres and pricing")
    else:
        num=st.slider("Genres to chart",min_value=1,max_value=min(25,len(gs)),value=min(12,len(gs)),key="genre_count")
        most=gs.nlargest(num,"games")
        a,b=st.columns(2,gap="large")
        with a:
            subhead("Top genres by title count")
            plot(px.bar(most.sort_values("games"),x="games",y="genre",orientation="h",color_discrete_sequence=[AQUA],labels={"games":"Titles","genre":""}),height=420)
        with b:
            subhead("Median paid game price")
            priced=most.dropna(subset=["median_paid_price"]).sort_values("median_paid_price")
            if len(priced): plot(px.bar(priced,x="median_paid_price",y="genre",orientation="h",color_discrete_sequence=[VIOLET],labels={"median_paid_price":"USD","genre":""}),height=420)
            else: no_data("paid prices")
        ys=year_summary(filtered)
        a,b=st.columns(2,gap="large")
        with a:
            subhead("Paid pricing over time")
            value=ys.dropna(subset=["median_paid_price"])
            if len(value): plot(px.line(value,x="year",y="median_paid_price",markers=True,color_discrete_sequence=[BLUE],labels={"year":"Release year","median_paid_price":"Median price · USD"}))
        with b:
            subhead("Free-to-play share over time")
            if len(ys): plot(px.area(ys,x="year",y="free_share",color_discrete_sequence=[PINK],labels={"year":"Release year","free_share":"Share"}))
        with st.expander("See the genre comparison table"):
            st.dataframe(gs,hide_index=True,use_container_width=True)
        note("Genres are multi-label: a title can belong to more than one category. Genre totals should not be added together.")

with pages[2]:
    subhead("Reception & market reach", "Compare observed review sentiment and approximate audience reach.")
    d=filtered.loc[filtered["review_count"]>=10].copy()
    if d.empty:
        no_data("games with at least 10 reviews")
    else:
        a,b=st.columns(2,gap="large")
        with a:
            subhead("Price vs review sentiment")
            sub=d.nlargest(3000,"review_count")
            fig=px.scatter(sub,x="price",y="positive_rate",size="review_count",size_max=35,hover_name="name",opacity=.55,
                           color_discrete_sequence=[AQUA],labels={"price":"List price (USD)","positive_rate":"Positive review share","review_count":"Reviews"})
            plot(fig)
        with b:
            subhead("Review score distribution")
            plot(px.histogram(d,x="positive_rate",nbins=20,color_discrete_sequence=[VIOLET],labels={"positive_rate":"Positive review share"}))
        a,b=st.columns(2,gap="large")
        with a:
            subhead("Most reviewed games")
            st.dataframe(d.nlargest(12,"review_count")[["name","review_count","positive_rate"]],hide_index=True,use_container_width=True)
        with b:
            subhead("Estimated owner midpoint · leading titles")
            known=d.dropna(subset=["owners_mid"]).nlargest(12,"owners_mid").sort_values("owners_mid")
            if len(known): plot(px.bar(known,x="owners_mid",y="name",orientation="h",color_discrete_sequence=[BLUE],labels={"owners_mid":"Estimated owner midpoint","name":""}))
            else: no_data("owner estimates")
        note("Owners are third-party ranges, not confirmed purchases. Review counts are snapshots; correlations do not prove causality.")

with pages[3]:
    subhead("Game Explorer", "Browse the selected catalog, then open a detailed profile for any title.")
    if filtered.empty:
        no_data("game explorer")
    else:
        sort=st.selectbox("Sort games",["Most reviewed","Highest positive share","Newest","Highest price","Estimated owners","Name A–Z"],key="explorer_sort")
        config={"Most reviewed":("review_count",False),"Highest positive share":("positive_rate",False),
                "Newest":("release_year",False),"Highest price":("price",False),
                "Estimated owners":("owners_mid",False),"Name A–Z":("name",True)}
        field,ascending=config[sort]
        display=filtered.sort_values(field,ascending=ascending,na_position="last")
        cols=["appid","name","release_year","price","review_count","positive_rate","owners_low","owners_high","peak_ccu","developers","publishers"]
        a,b=st.columns([1,2])
        count=a.selectbox("Rows in preview",[25,50,100,250,500],index=2,key="explorer_rows")
        b.caption(f"{len(display):,} matches from the sidebar filters. Export includes all matching rows.")
        st.dataframe(display[cols].head(count),hide_index=True,use_container_width=True,height=425)
        st.download_button("↓ Export filtered game catalog",display[cols].to_csv(index=False).encode("utf-8"),file_name="gamepulse_filtered.csv",mime="text/csv")
        st.divider()
        subhead("Game profile", "Search by name or enter a Steam AppID; the profile includes reviews, platform support and similar-genre games.")
        q1,q2=st.columns([2,1])
        lookup=q1.text_input("Search game name",placeholder="At least 2 letters, e.g. portal",key="profile_search")
        id_lookup=q2.text_input("Or enter AppID",placeholder="e.g. 620",key="profile_appid")
        options=pd.DataFrame(columns=["appid","name","release_year"])
        if id_lookup.strip().isdigit():
            options=games.loc[games["appid"]==int(id_lookup),["appid","name","release_year"]]
        elif len(lookup.strip())>=2:
            options=games.loc[games["name"].str.contains(lookup.strip(),case=False,regex=False,na=False),
                              ["appid","name","release_year"]].sort_values("name").head(75)
        if options.empty:
            st.info("Enter at least two characters of a title or a valid AppID to open a game profile.")
        else:
            labels={int(row.appid):f'{row.name} · {int(row.release_year) if pd.notna(row.release_year) else "unknown year"} · #{int(row.appid)}' for row in options.itertuples(index=False)}
            gid=st.selectbox("Select a match",list(labels),format_func=lambda x:labels[x],key="explorer_selected")
            st.divider()
            game_details(games.loc[games["appid"]==gid].iloc[0],genres,games)

with pages[4]:
    subhead("Head-to-head comparison", "Compare any 2–5 games from your entire imported catalog, independently of sidebar filters.")
    if "compare_ids" not in st.session_state:
        st.session_state.compare_ids=[]
    cmp_search=st.text_input("Find a game to compare",placeholder="Enter at least two letters (e.g. portal, hades, stardew)",key="compare_search")
    if len(cmp_search.strip()) >= 2:
        matches=games.loc[games["name"].str.contains(cmp_search.strip(),case=False,regex=False,na=False),["appid","name","release_year"]].sort_values("name").head(75)
        if matches.empty:
            st.info("No matches found. Try a different title.")
        else:
            labels={int(row.appid):f'{row.name} · {int(row.release_year) if pd.notna(row.release_year) else "year unknown"} · #{int(row.appid)}' for row in matches.itertuples(index=False)}
            c1,c2=st.columns([4,1],vertical_alignment="bottom")
            with c1:
                selected=st.selectbox("Matching title (first 75)",list(labels),format_func=lambda aid:labels[aid],key="compare_candidate")
            with c2:
                if st.button("＋ Add game",use_container_width=True,type="primary",disabled=(selected in st.session_state.compare_ids or len(st.session_state.compare_ids)>=5)):
                    st.session_state.compare_ids.append(selected)
                    st.rerun()
    else:
        st.caption("Start by typing a game name above. You can compare titles even when they aren't in the current filtered selection.")
    chosen=st.session_state.compare_ids
    if chosen:
        st.markdown(f"**Selected games ({len(chosen)}/5)**")
        for gid in list(chosen):
            one=games.loc[games["appid"]==gid]
            if one.empty:
                st.session_state.compare_ids.remove(gid)
                continue
            a,b=st.columns([5,1],vertical_alignment="center")
            a.write(f'🎮 **{one.iloc[0]["name"]}** · AppID {gid}')
            if b.button("Remove",key=f"remove_compare_{gid}",use_container_width=True):
                st.session_state.compare_ids.remove(gid)
                st.rerun()
        if st.button("Clear selection",key="clear_compare"):
            st.session_state.compare_ids=[]
            st.rerun()
    if len(chosen)<2:
        st.info("Add at least two games above to unlock comparison charts and the side-by-side metrics table.")
    else:
        chosen_order={gid:i for i,gid in enumerate(chosen)}
        compared=games.loc[games["appid"].isin(chosen)].copy()
        compared["sort_idx"]=compared["appid"].map(chosen_order)
        compared=compared.sort_values("sort_idx")
        show=["name","release_year","price","review_count","positive_rate","owners_low","owners_high","peak_ccu","metacritic_score","average_playtime_forever"]
        details=compared[show].set_index("name").T
        details.index=["Release year","Listed price (USD)","Review count","Positive review share","Est. owners · low","Est. owners · high","Peak CCU (snapshot)","Metacritic score","Avg. lifetime playtime (minutes)"]
        subhead("Side-by-side game metrics")
        st.dataframe(details,use_container_width=True)
        charts=st.tabs(["Review volume","Review sentiment","List price","Estimated ownership"])
        graph_config=[("review_count","Total reviews","Reviews",AQUA),
                      ("positive_rate","Positive review share","Share",VIOLET),
                      ("price","Listed price","USD",BLUE),
                      ("owners_mid","Owner-range midpoints · estimates only","Owners (estimated)",PINK)]
        for tab,(field,title,label,color) in zip(charts,graph_config):
            with tab:
                subhead(title)
                subset=compared.dropna(subset=[field])
                if subset.empty: st.info("No values available for this comparison metric.")
                else:
                    fig=px.bar(subset,x="name",y=field,color_discrete_sequence=[color],text_auto=".2s",
                               labels={"name":"Game",field:label})
                    fig.update_layout(showlegend=False)
                    plot(fig,height=390)
        st.download_button("↓ Export comparison",compared[show].to_csv(index=False).encode("utf-8"),file_name="gamepulse_comparison.csv",mime="text/csv",key="export_comparison")
        note("Comparison reflects the imported dataset snapshot, not live Steam activity. Ownership midpoint is an estimate, and review count is not equivalent to units sold.")

with pages[5]:
    subhead("Data quality & methodology", "Understand data completeness, ingestion history and exactly how each metric is calculated.")
    qm=quality_metrics(games,genres)
    n=len(games)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Stored games",f"{n:,}")
    c2.metric("Duplicate AppIDs",f'{qm["duplicate_appids"]:,}')
    c3.metric("Missing owner ranges",f'{qm["no_owners"]:,}')
    c4.metric("Unclassified genres",f'{qm["without_genres"]:,}')
    note("These audit metrics always describe the full imported catalog, regardless of your sidebar filters.")

    subhead("Completeness by field")
    coverage=pd.DataFrame([
        {"Field":"Release date","Available":n-qm["no_release_date"],"Missing":qm["no_release_date"]},
        {"Field":"Price","Available":n-qm["no_price"],"Missing":qm["no_price"]},
        {"Field":"Owner estimate","Available":n-qm["no_owners"],"Missing":qm["no_owners"]},
        {"Field":"Review activity","Available":n-qm["no_reviews"],"Missing":qm["no_reviews"]},
        {"Field":"Genre classification","Available":n-qm["without_genres"],"Missing":qm["without_genres"]},
    ])
    coverage["Completeness"]=(coverage["Available"]/max(n,1)).round(4)
    left,right=st.columns([1.5,1],gap="large")
    with left:
        fig=px.bar(coverage,x="Completeness",y="Field",orientation="h",range_x=[0,1],text=coverage["Completeness"].map(lambda v:f"{v:.1%}"),
                   color_discrete_sequence=[AQUA])
        fig.update_traces(textposition="outside")
        plot(fig,height=310)
    with right:
        st.dataframe(coverage,hide_index=True,use_container_width=True,
                     column_config={"Completeness":st.column_config.ProgressColumn("Completeness",min_value=0,max_value=1,format="%.2f")})
    st.download_button("↓ Export quality audit",coverage.to_csv(index=False).encode("utf-8"),file_name="gamepulse_quality_audit.csv",mime="text/csv")

    subhead("Import runs & rejected records")
    if runs.empty:
        st.info("No import history is recorded yet. Run the GamePulse loader to populate this table.")
    else:
        shown=runs.rename(columns={"imported_at":"Imported at (UTC)","input_rows":"Input rows","valid_rows":"Valid rows","rejected_rows":"Rejected rows","duplicates":"Duplicates within chunk"})
        st.dataframe(shown,hide_index=True,use_container_width=True,height=240)
        tot_input=pd.to_numeric(runs["input_rows"],errors="coerce").fillna(0).sum()
        tot_rejected=pd.to_numeric(runs["rejected_rows"],errors="coerce").fillna(0).sum()
        st.caption(f"Import log: {len(runs):,} recent chunks/runs shown · {int(tot_input):,} processed rows · {int(tot_rejected):,} rejected rows. Re-imports may appear multiple times and are not added to catalog totals.")

    subhead("Metric dictionary")
    definitions=pd.DataFrame([
        ("Catalog titles","Count of distinct imported Steam AppIDs","Not necessarily all games available today"),
        ("Median paid price","Median recorded USD list price for games above $0","Excludes free/unknown; not historical realized sale price"),
        ("Free-to-play share","Games priced $0 divided by games with known prices","Unknown prices excluded"),
        ("Positive review share","Sum of positive reviews / sum of all positive and negative reviews","Weighted by review counts; not average game rating"),
        ("Owner-range midpoint","(Estimated low + high) / 2","Approximation only; NOT verified sales or revenue"),
        ("Peak CCU","Peak concurrent users captured in the source snapshot","Not a live player counter"),
        ("Genre titles","Distinct AppIDs associated with each genre","Categories overlap and cannot be summed"),
    ],columns=["Metric","Definition","Interpretation / caveat"])
    st.dataframe(definitions,hide_index=True,use_container_width=True)

    subhead("Dataset & research limitations")
    with st.expander("Source, time period and provenance",expanded=True):
        st.markdown("**Source:** [Steam Games Dataset 2025](https://www.kaggle.com/datasets/artermiloff/steam-games-dataset), cleaned March 2025 snapshot. The included sample file is synthetic; verify the source file in import history for your current database.")
        st.markdown("The catalog includes historical release dates, but review counts, prices and ownership ranges are snapshot observations. They are **not time-series transaction data**.")
    with st.expander("Null values, missingness and selection bias"):
        st.markdown("Invalid numeric values are normalized to null. Games without review activity do not have an observed positive-review rate. Filtering on price or release year may exclude missing values. Catalog coverage is not guaranteed to represent all Steam games.")
    with st.expander("Estimated ownership and financial claims"):
        st.markdown("Ownership information comes from broad third-party estimates. It is not an official Steam sales report. This app intentionally does not present estimated owners as revenue, transactions, copies sold, or profit.")
    with st.expander("Reproducibility and QA"):
        st.markdown("Data is normalized from imported CSV into `games` and `game_genres` tables. Each loader chunk writes an audit record to `import_runs`. Validate reproducibility with `python -m pytest -q` and regenerate a report with `python -m gamepulse.report --out docs/ANALYSIS_RESULTS.md`.")


def csv_download(label, table, filename, key):
    st.download_button(label, table.to_csv(index=False).encode('utf-8'),
                       file_name=filename, mime='text/csv',key=key)


def complete_release_years(frame):
    """Conservative default: omit latest observed cohort, which may be partial."""
    known=pd.to_numeric(frame['release_year'],errors='coerce').dropna()
    years=sorted(int(x) for x in known.unique())
    return years[:-1] if len(years)>1 else years


with pages[6]:
    subhead('Market Insights', 'Data-generated findings with explicit denominators and limitations.')
    complete=complete_release_years(filtered)
    if len(complete)>=2:
        eligible=complete[-min(6,len(complete)):]
        st.caption(f'For genre growth cards, default to {eligible[0]} versus {eligible[-1]}; the latest observed year is excluded as potentially incomplete.')
        left_year=eligible[0];right_year=eligible[-1]
    else:
        left_year=right_year=None
    cards=build_insights(filtered,genres,left_year,right_year)
    if not cards: no_data('market insights')
    else:
        for start in range(0,len(cards),2):
            cols=st.columns(2,gap='large')
            for col,insight in zip(cols,cards[start:start+2]):
                with col:
                    with st.container(border=True):
                        st.caption(insight['title'].upper())
                        st.markdown(f"### {insight['value']}")
                        st.write(insight['detail'])
                        st.caption(insight['caveat'])
    subhead('Reception by price tier', 'Weighted positive review share. Includes only games with a minimum of 100 total reviews.')
    bands=price_reception_bands(filtered,min_reviews=100)
    if bands.empty:
        no_data('price tiers with sufficient reviews')
    else:
        left,right=st.columns([1.5,1],gap='large')
        with left:
            fig=px.bar(bands,x='price_band',y='weighted_positive_share',color='titles',
              color_continuous_scale=['#255c75',AQUA],hover_data=['titles','median_reviews'],
              labels={'price_band':'List price band · USD','weighted_positive_share':'Positive review share','titles':'Games'})
            fig.update_yaxes(tickformat='.0%',range=[0,1]);plot(fig,height=370)
        with right:
            st.dataframe(bands,hide_index=True,use_container_width=True)
        csv_download('↓ Export price/reception breakdown',bands,'gamepulse_price_reception.csv','export_bands')
    subhead('Discover lesser-known, highly rated games')
    a,b,c=st.columns(3)
    gems_min=a.number_input('Minimum reviews',min_value=10,max_value=50000,value=100,step=50)
    gems_max=b.number_input('Maximum reviews',min_value=50,max_value=500000,value=5000,step=250)
    gems_score=c.slider('Minimum positive share',min_value=.50,max_value=1.0,value=.90,step=.01,format='%.0f%%')
    if gems_max<gems_min: st.warning('Maximum reviews must be at least minimum reviews.')
    else:
        gems=hidden_gems(filtered,int(gems_min),int(gems_max),float(gems_score),limit=50)
        if gems.empty:no_data('the selected hidden-gem criteria')
        else:
            st.dataframe(gems,hide_index=True,use_container_width=True,height=350)
            csv_download('↓ Export hidden gems',gems,'gamepulse_hidden_gems.csv','export_gems')
    st.caption('“Hidden gems” is an editorial heuristic: high observed positive share with modest review volume. It is not an official classification or low-sales indicator.')

with pages[7]:
    subhead('Genre Release Trends', 'Compare release cohort composition, not historical sales or audience growth.')
    available=complete_release_years(filtered)
    if len(available)<2:
        st.info('At least two distinct release years are required for genre growth analysis.')
    else:
        years_window=available[-min(12,len(available)):]
        lower,upper=st.select_slider('Years to compare (latest observed cohort omitted by default)',
           options=available,value=(years_window[0],years_window[-1]),key='trend_years')
        trends=genre_year_trends(filtered,genres,lower,upper)
        if trends.empty: no_data('genre year trends')
        else:
            counts=trends.groupby('genre')['titles'].sum().nlargest(12)
            focus=st.multiselect('Plot genres',counts.index.tolist(),default=counts.head(6).index.tolist(),key='trend_genres')
            drawn=trends[trends['genre'].isin(focus)]
            if len(drawn):
                plot(px.line(drawn,x='release_year',y='titles',color='genre',markers=True,
                  labels={'release_year':'Release year','titles':'Released titles','genre':'Genre'}),height=435)
            else:st.info('Select at least one genre to show the trend chart.')
            a,b,c=st.columns(3)
            start_year=a.selectbox('Comparison start year',list(range(lower,upper)) or [lower],index=0,key='growth_start')
            end_options=list(range(start_year+1,upper+1)) or [upper]
            end_year=b.selectbox('Comparison end year',end_options,index=len(end_options)-1,key='growth_end')
            min_base=c.number_input('Minimum releases in start year',1,1000,5,key='growth_base')
            growth=genre_growth(trends,start_year,end_year,int(min_base))
            if growth.empty: st.info('No genres meet the minimum baseline volume.')
            else:
                a,b=st.columns(2,gap='large')
                with a:
                    subhead('Largest absolute increases in releases')
                    top=growth.sort_values('change',ascending=False).head(12).sort_values('change')
                    plot(px.bar(top,x='change',y='genre',orientation='h',color='change',
                       color_continuous_scale='Tealgrn',labels={'change':'Change in released titles','genre':''}),height=410)
                with b:
                    subhead('Largest percentage increases')
                    top=growth.sort_values('growth_pct',ascending=False).head(12).sort_values('growth_pct')
                    fig=px.bar(top,x='growth_pct',y='genre',orientation='h',color_discrete_sequence=[VIOLET],
                       labels={'growth_pct':'Change relative to baseline','genre':''})
                    fig.update_xaxes(tickformat='+,.0%')
                    plot(fig,height=410)
                st.dataframe(growth,hide_index=True,use_container_width=True)
                csv_download('↓ Export genre growth',growth,'gamepulse_genre_growth.csv','export_genre_growth')
            with st.expander('Inspect genre-year observations'):
                st.dataframe(trends,hide_index=True,use_container_width=True)
                csv_download('↓ Export genre-year records',trends,'gamepulse_genre_years.csv','export_genre_years')
    note('Genre classifications overlap. A game can appear in several genre lines. The last observed release year may be incomplete; all comparisons are counts of game releases, not revenue, concurrent players or yearly review sentiment.')

with pages[8]:
    subhead('Studios & Publishers', 'Which organizations have the largest catalog footprints or review audiences?')
    a,b,c=st.columns([1,1,1])
    role=a.radio('Entity type',['Developers','Publishers'],horizontal=True,key='entity_role')
    minimum=b.number_input('Minimum credited titles',min_value=1,max_value=1000,value=3,key='entity_min')
    limit=c.slider('Organizations to show',5,40,15,key='entity_limit')
    field='developers' if role=='Developers' else 'publishers'
    entities=entity_summary(filtered,field,int(minimum))
    if entities.empty: no_data(f'{role.lower()} that meet the sample threshold')
    else:
        by=st.selectbox('Rank by',['Title count','Total review activity','Median reviews per game','Weighted positive review share'],key='entity_rank')
        sortcol={'Title count':'titles','Total review activity':'total_reviews',
                 'Median reviews per game':'median_game_reviews','Weighted positive review share':'weighted_positive_share'}[by]
        leaders=entities.sort_values(sortcol,ascending=False).head(limit)
        first,second=st.columns([1.7,1],gap='large')
        with first:
            graph=leaders.sort_values(sortcol)
            fig=px.bar(graph,x=sortcol,y='entity',orientation='h',color_discrete_sequence=[AQUA],
              labels={'entity':'',sortcol:by})
            if sortcol=='weighted_positive_share':fig.update_xaxes(tickformat='.0%')
            plot(fig,height=max(420,limit*29))
        with second:
            st.markdown('#### Read this carefully')
            st.write('**Title count** measures catalog presence, not how many titles sold.')
            st.write('**Total review activity** favors older or widely reviewed catalogs.')
            st.write('**Weighted positive share** aggregates positive versus all reviews for credited games, not an average studio rating.')
            st.write('**Owner midpoint** is estimated and not financial performance.')
        st.dataframe(entities.head(300),hide_index=True,use_container_width=True,height=375)
        csv_download(f'↓ Export {role.lower()} analytics',entities,f'gamepulse_{field}_summary.csv',f'export_{field}')

with pages[9]:
    subhead('SQL Insights Lab', 'Run SQL reports directly against the loaded database and export the results.')
    report_labels={'Publisher catalog footprint (raw field)':'publisher_leaders',
      'Genre releases by year':'genre_years',
      'Games with most reviews':'highly_reviewed',
      'Games across price tiers':'game_price_tiers'}
    label=st.selectbox('Choose a SQL report',list(report_labels),key='sql_report')
    query_name=report_labels[label]
    explanations = {
        "publisher_leaders": "Groups the exact publisher text stored for each game, counts titles and adds review counts. A comma-separated publisher list may contain several companies, so this report is a raw-field example.",
        "genre_years": "Joins each game with its genre labels, groups results by release year and genre, and counts distinct games. One game can belong to multiple genres.",
        "highly_reviewed": "Filters to games meeting your minimum review count, sorts them by review count, and displays the most reviewed entries.",
        "game_price_tiers": "Places games into simple price ranges, then counts games and recorded reviews in each range. It does not measure purchase revenue.",
    }
    with st.expander('View the SQL query',expanded=True):
        st.code(SQL_INSIGHTS[query_name],language='sql')
    col1,col2,col3=st.columns(3)
    sql_start=col1.number_input('Start year',min_value=1980,max_value=2100,value=2019,key='sql_year_start')
    sql_end=col2.number_input('End year',min_value=1980,max_value=2100,value=2024,key='sql_year_end')
    sql_min=col3.number_input('Minimum reviews',min_value=0,max_value=10000000,value=1000,step=100,key='sql_min_reviews')
    if sql_start>sql_end:st.warning('The start year must not be after the end year.')
    else:
        try:
            report=query_insight(engine_from_env(),query_name,start_year=int(sql_start),end_year=int(sql_end),minimum_reviews=int(sql_min),limit=100)
        except Exception as exc:
            st.error('Unable to execute report. Check your database connection.');st.code(str(exc))
        else:
            st.metric('Report rows',f'{len(report):,}')
            st.dataframe(report,hide_index=True,use_container_width=True,height=430)
            csv_download('↓ Export SQL results',report,f'gamepulse_sql_{query_name}.csv','export_sql_report')
    note('The raw publisher field groups identical text values and does not resolve multi-credit organizations. Query parameters are bound separately from the SQL text. All queries are read-only SELECT statements.')


with pages[10]:
    from gamepulse.portfolio import make_case_study, summarize_findings
    subhead("Portfolio findings", "Summary findings generated from your imported catalog.")
    st.caption("This page uses the full imported catalog so the findings remain consistent across filter changes.")
    available_years = complete_release_years(games)
    first = available_years[-min(6, len(available_years))] if len(available_years) >= 2 else None
    last = available_years[-1] if len(available_years) >= 2 else None
    findings = summarize_findings(games, genres, first, last)
    st.markdown("#### The questions I investigated")
    st.write("How many games are free? Which genres appear most often? What does review activity tell us? How has the mix of releases changed?")
    for finding in findings:
        with st.container(border=True):
            st.markdown(f"**{finding['title']}**")
            st.markdown(f"### {finding['value']}")
            st.write(finding['explanation'])
            st.caption("Important context: " + finding['limitation'])
    report = make_case_study(games, genres, first, last)
    st.download_button("↓ Download my findings as Markdown", data=report.encode('utf-8'),
        file_name="gamepulse_case_study.md", mime="text/markdown", type="primary")
    with st.expander("View the full case study"):
        st.markdown(report)
    st.markdown("#### How I built this")
    st.write("1. Imported a historical Steam dataset. 2. Cleaned and stored the games and genre labels. 3. Used Pandas and SQL to calculate metrics. 4. Built charts and tables with Streamlit. 5. Checked data quality and added automated tests.")
