import pandas as pd
import pytest
from sqlalchemy import create_engine
from gamepulse.db import ingest_frame
from gamepulse.market import (entity_summary,genre_year_trends,genre_growth,
        price_reception_bands,hidden_gems,build_insights,query_insight)

@pytest.fixture
def records():
    g=pd.DataFrame([
      [1,'A',2023,0,100,95,.95,1000,'Studio X, Studio Y','Pub A'],
      [2,'B',2024,15,200,180,.90,3000,'Studio X','Pub A'],
      [3,'C',2024,45,50,48,.96,300,'Studio Y','Pub B'],
      [4,'D',2023,10,150,120,.80,400,'Studio X','Pub B']],
      columns=['appid','name','release_year','price','review_count','positive','positive_rate','owners_mid','developers','publishers'])
    g['owners_low']=g['owners_mid']*.5;g['owners_high']=g['owners_mid']*1.5
    gg=pd.DataFrame({'appid':[1,2,3,4,2],'genre':['Action','Action','RPG','Action','RPG']})
    return g,gg

def test_entity_summary(records):
    g,_=records
    pubs=entity_summary(g,'publishers',2)
    assert set(pubs.entity)=={'Pub A','Pub B'}
    assert pubs.loc[pubs.entity=='Pub A','total_reviews'].iloc[0]==300
    dev=entity_summary(g,'developers',2)
    assert dev.loc[dev.entity=='Studio X','titles'].iloc[0]==3
    with pytest.raises(ValueError):entity_summary(g,'bogus')

def test_trends_and_growth(records):
    g,gg=records
    tr=genre_year_trends(g,gg)
    row=tr[(tr.genre=='Action')&(tr.release_year==2023)].iloc[0]
    assert row.titles==2
    growth=genre_growth(tr,2023,2024,min_base=1)
    assert growth.loc[growth.genre=='Action','change'].iloc[0]==-1

def test_reception_and_gems(records):
    g,_=records
    bands=price_reception_bands(g,min_reviews=100)
    assert bands['titles'].sum()==3
    gems=hidden_gems(g,min_reviews=100,max_reviews=200,min_positive=.9)
    assert set(gems.appid)=={1,2}

def test_dynamic_insights(records):
    g,gg=records
    info=build_insights(g,gg,2023,2024)
    assert any(x['title']=='Free-to-play footprint' and x['value']=='25.0%' for x in info)
    assert all(x['detail'] and x['caveat'] for x in info)

def test_portable_sql():
    eng=create_engine('sqlite:///:memory:')
    raw=pd.DataFrame({'appid':[1,2],'name':['A','B'],'price':[0,20],
      'release_date':['2023-01-01','2024-01-01'],'positive':[120,500],
      'negative':[10,20],'genres':['Action','Action, Indie'],
      'publishers':['Pub A','Pub B']})
    ingest_frame(eng,raw)
    for key in ('publisher_leaders','genre_years','highly_reviewed','game_price_tiers'):
        frame=query_insight(eng,key,start_year=2023,end_year=2024,minimum_reviews=100)
        assert not frame.empty
    with pytest.raises(ValueError):query_insight(eng,'DROP TABLE games')
