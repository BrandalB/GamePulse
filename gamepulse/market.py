from __future__ import annotations
import pandas as pd
import numpy as np
from sqlalchemy import text
from .entities import parse_credits


def _numeric(frame, column):
    return pd.to_numeric(frame[column], errors='coerce')


def entity_summary(games: pd.DataFrame, field: str, min_titles: int = 2) -> pd.DataFrame:
    if field not in ('developers', 'publishers'):
        raise ValueError('field must be developers or publishers')
    columns = ['entity','titles','median_paid_price','total_reviews','weighted_positive_share','median_game_reviews','median_owners_mid']
    if games.empty: return pd.DataFrame(columns=columns)
    cols = ['appid',field,'price','review_count','positive','owners_mid']
    frame = games[cols].copy()
    frame[field] = frame[field].map(parse_credits)
    frame = frame.explode(field)
    frame['entity'] = frame[field].astype(str).str.strip()
    frame = frame[(frame['entity'].str.len()>0) & (frame['entity'].str.lower()!='nan')].drop_duplicates(['appid','entity']).copy()
    if frame.empty: return pd.DataFrame(columns=columns)
    for c in ['price','review_count','positive','owners_mid']:
        frame[c]=pd.to_numeric(frame[c], errors='coerce')
    frame['paid_price']=frame['price'].where(frame['price']>0)
    result=frame.groupby('entity',as_index=False).agg(
        titles=('appid','nunique'),median_paid_price=('paid_price','median'),
        total_reviews=('review_count','sum'),positive=('positive','sum'),
        median_game_reviews=('review_count','median'),median_owners_mid=('owners_mid','median'))
    result['weighted_positive_share']=result['positive']/result['total_reviews'].replace(0,np.nan)
    return result.loc[result['titles']>=min_titles,columns].sort_values(['titles','total_reviews'],ascending=False).reset_index(drop=True)


def genre_year_trends(games:pd.DataFrame, genres:pd.DataFrame, min_year:int|None=None, max_year:int|None=None)->pd.DataFrame:
    """Counts of releases by genre and release year; genre labels overlap."""
    cols=['genre','release_year','titles','reviews_per_title_median','positive_share_weighted','total_reviews']
    if games.empty or genres.empty: return pd.DataFrame(columns=cols)
    base=games[['appid','release_year','review_count','positive']].copy()
    base['release_year']=pd.to_numeric(base['release_year'],errors='coerce')
    base=base.dropna(subset=['release_year']);base['release_year']=base['release_year'].astype(int)
    if min_year is not None: base=base[base['release_year']>=min_year]
    if max_year is not None: base=base[base['release_year']<=max_year]
    d=genres.merge(base,on='appid',how='inner').drop_duplicates(['appid','genre'])
    if d.empty:return pd.DataFrame(columns=cols)
    d['review_count']=_numeric(d,'review_count').fillna(0)
    d['positive']=_numeric(d,'positive').fillna(0)
    result=d.groupby(['genre','release_year'],as_index=False).agg(
        titles=('appid','nunique'),reviews_per_title_median=('review_count','median'),
        positive=('positive','sum'),total_reviews=('review_count','sum'))
    result['positive_share_weighted']=result['positive']/result['total_reviews'].replace(0,np.nan)
    return result[cols].sort_values(['genre','release_year']).reset_index(drop=True)


def genre_growth(trends:pd.DataFrame, start_year:int, end_year:int, min_base:int=5)->pd.DataFrame:
    cols=['genre','start_titles','end_titles','change','growth_pct']
    if trends.empty or start_year>=end_year:return pd.DataFrame(columns=cols)
    pivot=trends.loc[trends['release_year'].isin([start_year,end_year])].pivot_table(
        index='genre',columns='release_year',values='titles',aggfunc='sum',fill_value=0)
    for year in (start_year,end_year):
        if year not in pivot.columns:pivot[year]=0
    out=pivot[[start_year,end_year]].reset_index().rename(columns={start_year:'start_titles',end_year:'end_titles'})
    out=out[out['start_titles']>=min_base].copy()
    out['change']=out['end_titles']-out['start_titles']
    out['growth_pct']=out['change']/out['start_titles']
    return out[cols].sort_values('change',ascending=False).reset_index(drop=True)


def price_reception_bands(games:pd.DataFrame, min_reviews:int=100)->pd.DataFrame:
    cols=['price_band','titles','median_reviews','weighted_positive_share','median_owners_mid']
    if games.empty:return pd.DataFrame(columns=cols)
    d=games.copy()
    d['price']=_numeric(d,'price'); d['review_count']=_numeric(d,'review_count').fillna(0)
    d['positive']=_numeric(d,'positive').fillna(0);d['owners_mid']=_numeric(d,'owners_mid')
    d=d[(d['price']>=0)&(d['review_count']>=min_reviews)].copy()
    if d.empty:return pd.DataFrame(columns=cols)
    edges=[-0.001,0,5,15,30,60,float('inf')]
    labels=['Free','$0.01–5','$5–15','$15–30','$30–60','$60+']
    d['price_band']=pd.cut(d['price'],bins=edges,labels=labels,include_lowest=True)
    out=d.groupby('price_band',observed=True).agg(
        titles=('appid','nunique'),median_reviews=('review_count','median'),
        reviews=('review_count','sum'),positive=('positive','sum'),
        median_owners_mid=('owners_mid','median')).reset_index()
    out['weighted_positive_share']=out['positive']/out['reviews'].replace(0,np.nan)
    return out[cols]


def hidden_gems(games:pd.DataFrame, min_reviews:int=100, max_reviews:int=5000, min_positive:float=.90, limit:int=25)->pd.DataFrame:
    fields=['appid','name','release_year','price','review_count','positive_rate','owners_low','owners_high','developers']
    if games.empty:return games.reindex(columns=fields).head(0)
    d=games.copy()
    d['review_count']=_numeric(d,'review_count');d['positive_rate']=_numeric(d,'positive_rate')
    d=d[d['review_count'].between(min_reviews,max_reviews)&d['positive_rate'].ge(min_positive)]
    return d.sort_values(['positive_rate','review_count'],ascending=[False,False])[fields].head(limit).reset_index(drop=True)


def build_insights(games:pd.DataFrame,genres:pd.DataFrame, start_year:int|None=None,end_year:int|None=None)->list[dict]:
    result=[]
    if games.empty:return result
    filtered=games.copy()
    paid=_numeric(filtered,'price').dropna()
    if len(paid):
        free_n=int(paid.eq(0).sum())
        result.append({'title':'Free-to-play footprint','value':f'{free_n/len(paid):.1%}',
          'detail':f'{free_n:,} of {len(paid):,} titles with a known price are listed as free.',
          'caveat':'Current snapshot list price; does not reflect historical pricing.'})
    if 'review_count' in filtered:
        reviews=_numeric(filtered,'review_count').fillna(0)
        active=int(reviews.ge(100).sum())
        result.append({'title':'Games with substantial review activity','value':f'{active:,}',
          'detail':f'{active:,} of {len(filtered):,} selected titles have at least 100 counted reviews.',
          'caveat':'Review counts indicate review activity, not confirmed purchases.'})
    gs=genre_year_trends(filtered,genres,min_year=start_year,max_year=end_year)
    if start_year is not None and end_year is not None and start_year<end_year:
        growth=genre_growth(gs,start_year,end_year,min_base=5)
        if not growth.empty and growth.iloc[0]['change']>0:
            top=growth.iloc[0]
            result.append({'title':'Largest genre release-count increase','value':str(top['genre']),
              'detail':f"{int(top['start_titles']):,} releases in {start_year} versus {int(top['end_titles']):,} in {end_year} ({int(top['change']):+,} titles).",
              'caveat':'Genre memberships overlap; cohort counts are not sales or player growth. Compare complete calendar years.'})
    bands=price_reception_bands(filtered,min_reviews=100)
    robust=bands[bands['titles']>=10]
    if not robust.empty:
        highest=robust.sort_values('weighted_positive_share',ascending=False).iloc[0]
        result.append({'title':'Strongest reviewed price tier','value':str(highest['price_band']),
           'detail':f"{highest['weighted_positive_share']:.1%} positive across reviewed titles in this tier ({int(highest['titles']):,} games with 100+ reviews).",
           'caveat':'Descriptive association; not causal. Weighted by review volume and affected by selection bias.'})
    return result


SQL_INSIGHTS = {
  'publisher_leaders': '''SELECT publishers AS publisher_field, COUNT(*) AS titles,
        SUM(COALESCE(review_count,0)) AS reviews
        FROM games WHERE publishers IS NOT NULL AND TRIM(publishers)<>''
        GROUP BY publishers ORDER BY titles DESC LIMIT :limit''',
  'genre_years': '''SELECT gg.genre, g.release_year, COUNT(DISTINCT g.appid) AS releases,
       SUM(COALESCE(g.review_count,0)) AS reviews
       FROM game_genres gg JOIN games g ON g.appid=gg.appid
       WHERE g.release_year BETWEEN :start_year AND :end_year
       GROUP BY gg.genre,g.release_year ORDER BY g.release_year, releases DESC''',
  'highly_reviewed': '''SELECT name, release_year, price, review_count, positive_rate
        FROM games WHERE review_count>=:minimum_reviews
        ORDER BY review_count DESC LIMIT :limit''',
  'game_price_tiers': '''SELECT CASE WHEN price=0 THEN 'Free' WHEN price<=5 THEN '$0.01–5'
         WHEN price<=15 THEN '$5–15' WHEN price<=30 THEN '$15–30'
         WHEN price<=60 THEN '$30–60' ELSE '$60+' END AS tier,
         COUNT(*) AS titles, SUM(COALESCE(review_count,0)) AS reviews
         FROM games WHERE price>=0 GROUP BY tier ORDER BY titles DESC''',
}

def query_insight(engine, query_name:str, **kwargs)->pd.DataFrame:
    if query_name not in SQL_INSIGHTS: raise ValueError('Unknown SQL insight')
    params={'limit':25,'start_year':2019,'end_year':2024,'minimum_reviews':1000}
    params.update(kwargs)
    with engine.connect() as conn:
        return pd.read_sql(text(SQL_INSIGHTS[query_name]),conn,params=params)
