from __future__ import annotations
import pandas as pd


def similar_games(games: pd.DataFrame, genres: pd.DataFrame, appid: int, limit: int = 8) -> pd.DataFrame:
    "Find titles with overlapping genres, then rank by overlap and review volume."

    fields = ['appid','name','release_year','price','review_count','positive_rate','shared_genres']
    target = set(genres.loc[genres['appid'] == appid, 'genre'].dropna())
    if not target or games.empty: return pd.DataFrame(columns=fields)
    matches=genres.loc[genres['genre'].isin(target) & genres['appid'].ne(appid), ['appid','genre']]
    counts=matches.groupby('appid')['genre'].nunique().rename('shared_genres')
    candidates=games.merge(counts, left_on='appid',right_index=True,how='inner')
    candidates=candidates[candidates['appid'].ne(appid)].copy()
    candidates['review_count']=pd.to_numeric(candidates['review_count'],errors='coerce').fillna(0)
    candidates=candidates.sort_values(['shared_genres','review_count','name'],ascending=[False,False,True])
    return candidates.reindex(columns=fields).head(max(1,limit)).reset_index(drop=True)


def review_breakdown(game: pd.Series) -> pd.DataFrame:
    "Steam positive/negative counts for one game. Missing is not zero."
    
    result=[]
    for col, label in [('positive','Positive'),('negative','Negative')]:
        count=pd.to_numeric(game.get(col),errors='coerce')
        if pd.notna(count): result.append({'Sentiment':label,'Reviews':max(int(count),0)})
    return pd.DataFrame(result,columns=['Sentiment','Reviews'])
