"""Reusable, unit-tested market analytics metrics."""
from __future__ import annotations
import pandas as pd
import numpy as np

def filter_games(games, genres, years=None, selected_genres=None, price_range=None,
                 min_reviews=0, platforms=None, search='', paid_filter='All'):
    d=games.copy()
    if years and 'release_year' in d:
        d=d.loc[pd.to_numeric(d['release_year'],errors='coerce').between(*years)]
    if selected_genres:
        ids=genres.loc[genres['genre'].isin(selected_genres),'appid'].unique()
        d=d[d['appid'].isin(ids)]
    if price_range:
        d=d[pd.to_numeric(d['price'],errors='coerce').between(*price_range)]
    if min_reviews:
        d=d[d['review_count'].fillna(0)>=min_reviews]
    if search: d=d[d['name'].str.contains(search,case=False,regex=False,na=False)]
    if paid_filter=='Free': d=d[d['price']==0]
    elif paid_filter=='Paid': d=d[d['price']>0]
    if platforms:
        # A title is included if available on every selected platform.
        for p in platforms: d=d[d[p].fillna(False).astype(bool)]
    return d.copy()

def overview(d):
    counted=int(pd.to_numeric(d['review_count'],errors='coerce').fillna(0).sum())
    positive=int(pd.to_numeric(d['positive'],errors='coerce').fillna(0).sum())
    paid=pd.to_numeric(d.loc[d['price']>0,'price'],errors='coerce')
    known_prices=d['price'].notna().sum()
    return {'games':len(d),'paid_median':float(paid.median()) if len(paid) else None,
            'free_share':float((d['price']==0).sum()/known_prices) if known_prices else None,
            'positive_share':positive/counted if counted else None,
            'review_volume':counted,
            'estimated_owners_mid_sum':float(pd.to_numeric(d['owners_mid'],errors='coerce').sum())}

def genre_summary(games,genres):
    joined=genres.merge(games[['appid','price','review_count','positive','owners_mid','positive_rate']],on='appid',how='inner')
    if joined.empty:return pd.DataFrame(columns=['genre','games','median_paid_price','review_volume','positive_share','owner_mid_sum'])
    joined['paid_price']=joined['price'].where(joined['price']>0)
    out=joined.groupby('genre',as_index=False).agg(games=('appid','nunique'),median_paid_price=('paid_price','median'),
          review_volume=('review_count','sum'),positive=('positive','sum'),owner_mid_sum=('owners_mid','sum'))
    out['positive_share']=out['positive']/out['review_volume'].replace(0,np.nan)
    return out.drop(columns='positive').sort_values('games',ascending=False)

def year_summary(games):
    d=games.dropna(subset=['release_year']).copy()
    d['year']=pd.to_numeric(d['release_year']).astype(int)
    d['paid_price']=d['price'].where(d['price']>0)
    d['free_flag']=d['price'].eq(0).astype(float)
    return d.groupby('year',as_index=False).agg(releases=('appid','nunique'),median_paid_price=('paid_price','median'),free_share=('free_flag','mean'),reviews=('review_count','sum')).sort_values('year')

def quality_metrics(games,genres):
    n=len(games)
    return {'records':n,'no_release_date':int(games['release_date'].isna().sum()),
            'no_price':int(games['price'].isna().sum()),'no_owners':int(games['owners_mid'].isna().sum()),
            'no_reviews':int((games['review_count'].fillna(0)==0).sum()),
            'without_genres':int((~games['appid'].isin(genres['appid'])).sum()),
            'duplicate_appids':int(games['appid'].duplicated().sum())}
