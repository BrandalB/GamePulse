import pandas as pd
from gamepulse.transform import parse_list,parse_owners,normalize

def test_lists():
    assert parse_list("['Action', 'Indie']")==['Action','Indie']
    assert parse_list('RPG, Strategy')==['RPG','Strategy']
    assert parse_list(None)==[]

def test_owner_ranges():
    assert parse_owners('20,000 - 50,000')==(20000,50000)
    assert parse_owners('unknown')==(None,None)

def test_transform_quality():
    raw=pd.DataFrame({'appid':[10,11,None,12,12],'name':['A','B','Bad','C','C latest'],
         'price':[0,19.99,4,-1,12],'positive':[0,8,2,20,30], 'negative':[0,2,1,0,0],
         'estimated_owners':['0 - 20000','20000 - 50000','x','bad','bad'],
         'genres':["['Indie', 'Action']",'RPG','Action','Action','RPG']})
    g,gr,reject,stats=normalize(raw)
    assert stats['rejected_rows']==1
    assert stats['duplicate_appids_in_chunk']==1
    assert len(g)==3
    assert len(gr)==4
    assert pd.isna(g.loc[g['appid']==10,'positive_rate'].iloc[0])
    assert g.loc[g['appid']==11,'positive_rate'].iloc[0]==.8
    assert g.loc[g['appid']==12,'name'].iloc[0]=='C latest'
