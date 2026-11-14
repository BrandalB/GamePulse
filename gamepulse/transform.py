from __future__ import annotations
import ast
import json
import re
import pandas as pd
import numpy as np

FIELDS = ['appid','name','release_date','price','positive','negative','estimated_owners',
          'peak_ccu','metacritic_score','average_playtime_forever','windows','mac','linux',
          'genres','developers','publishers','header_image','recommendations']
ALIASES = {'appid':['appid','appID','AppID','app_id'], 'name':['name','Name','title'],
           'release_date':['release_date','Release date','Release Date'],
           'price':['price','Price','price_usd'], 'positive':['positive','Positive'],
           'negative':['negative','Negative'], 'estimated_owners':['estimated_owners','Estimated owners','estimatedOwners'],
           'peak_ccu':['peak_ccu','Peak CCU'], 'metacritic_score':['metacritic_score','Metacritic score'],
           'average_playtime_forever':['average_playtime_forever','Average playtime forever'],
           'windows':['windows','Windows'], 'mac':['mac','Mac'], 'linux':['linux','Linux'],
           'genres':['genres','Genres'], 'developers':['developers','Developers'],
           'publishers':['publishers','Publishers'], 'header_image':['header_image','Header image'],
           'recommendations':['recommendations','Recommendations']}

def parse_list(value):
    if isinstance(value,(list,tuple,set)): return [str(v).strip() for v in value if str(v).strip()]
    if value is None or (not isinstance(value,(dict,list)) and pd.isna(value)): return []
    if isinstance(value,dict): return list(map(str,value.keys()))
    s=str(value).strip()
    if not s or s.lower() in ('nan','none','[]','{}'): return []
    if s[0] in '[{(':
        for parser in (json.loads,ast.literal_eval):
            try:
                x=parser(s)
                if isinstance(x,dict): return [str(v) for v in x]
                if isinstance(x,(list,tuple,set)): return [str(v).strip() for v in x if str(v).strip()]
            except (ValueError,SyntaxError,TypeError, json.JSONDecodeError): pass
    return [p.strip().strip("'\"") for p in s.split(',') if p.strip()]

def parse_owners(value):
    if value is None or pd.isna(value): return (None,None)
    nums=re.findall(r'\d[\d,]*',str(value))
    if len(nums)<2: return (None,None)
    lo,hi=(int(n.replace(',','')) for n in nums[:2])
    return (lo,hi) if hi>=lo else (None,None)

def as_bool(value):
    if value is None or pd.isna(value): return None
    if isinstance(value,bool): return value
    s=str(value).strip().lower()
    if s in ('true','1','yes','y'): return True
    if s in ('false','0','no','n'): return False
    return None

def normalize(raw:pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame,dict]:
    """Return games, game_genres, rejected_rows, quality report.

    Duplicate appids are deduplicated inside this chunk; loader upserts across chunks.
    """
    df=pd.DataFrame(index=raw.index)
    for target in FIELDS:
        found=next((col for col in ALIASES[target] if col in raw.columns),None)
        df[target]=raw[found] if found else None
    count=len(df)
    df['appid']=pd.to_numeric(df['appid'],errors='coerce')
    df['name']=df['name'].astype('string').str.strip()
    bad=df['appid'].isna() | (df['appid']<=0) | df['name'].isna() | (df['name']=='')
    rejected=raw.loc[bad].copy()
    df=df.loc[~bad].copy()
    df['appid']=df['appid'].astype('int64')
    duplicate_count=int(df.duplicated('appid').sum())
    df=df.drop_duplicates('appid',keep='last')
    df['release_date']=pd.to_datetime(df['release_date'],errors='coerce',format='mixed').dt.date
    df['release_year']=pd.to_datetime(df['release_date'],errors='coerce').dt.year.astype('Int64')
    for col in ['price','positive','negative','peak_ccu','metacritic_score','average_playtime_forever','recommendations']:
        df[col]=pd.to_numeric(df[col],errors='coerce')
        df.loc[df[col]<0,col]=np.nan
    df.loc[df['price']>10000,'price']=np.nan
    for col in ('positive','negative','peak_ccu','average_playtime_forever','recommendations'):
        df[col]=df[col].astype('Int64')
    df.loc[~df['metacritic_score'].between(0,100),'metacritic_score']=np.nan
    owners=df['estimated_owners'].map(parse_owners)
    df['owners_low']=owners.map(lambda t:t[0]).astype('Int64')
    df['owners_high']=owners.map(lambda t:t[1]).astype('Int64')
    df['owners_mid']=((df['owners_low']+df['owners_high'])/2).astype('Float64')
    for col in ('windows','mac','linux'): df[col]=df[col].map(as_bool)
    df['review_count']=df[['positive','negative']].fillna(0).sum(axis=1).astype('int64')
    df['positive_rate']=np.where(df['review_count']>0,df['positive'].fillna(0)/df['review_count'],np.nan)
    df['is_free']=df['price'].eq(0)
    genre_rows=[]
    for appid, gs in zip(df['appid'],df['genres']):
        for g in dict.fromkeys(parse_list(gs)):
            genre_rows.append({'appid':int(appid),'genre':g[:120]})
    genre_df=pd.DataFrame(genre_rows,columns=['appid','genre']).drop_duplicates()
    for col in ('developers','publishers'):
        df[col]=df[col].map(lambda v:json.dumps(parse_list(v), ensure_ascii=False))
    df['header_image']=df['header_image'].fillna('').astype(str).str.slice(0,1000)
    df=df.drop(columns=['genres','estimated_owners'])
    quality={'input_rows':count,'valid_rows':len(df),'rejected_rows':len(rejected),
             'duplicate_appids_in_chunk':duplicate_count,'missing_prices':int(df['price'].isna().sum()),
             'missing_release_dates':int(df['release_date'].isna().sum()),
             'missing_owner_ranges':int(df['owners_mid'].isna().sum()),
             'games_without_reviews':int((df['review_count']==0).sum()),
             'genre_links':len(genre_df)}
    return df,genre_df,rejected,quality
