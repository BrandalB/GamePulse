import pandas as pd
from gamepulse.analytics import overview,filter_games,genre_summary

def test_analytics():
    g=pd.DataFrame({'appid':[1,2],'name':['Alpha','Beta'],'price':[0,20],
       'release_year':[2020,2021],'review_count':[10,20],'positive':[8,10],
       'owners_mid':[1000,2000],'positive_rate':[.8,.5],'windows':[True,True],
       'mac':[False,True],'linux':[False,False]})
    genres=pd.DataFrame({'appid':[1,1,2],'genre':['Action','Indie','Action']})
    o=overview(g)
    assert o['positive_share']==18/30
    assert o['paid_median']==20
    assert len(filter_games(g,genres,selected_genres=['Indie']))==1
    assert len(filter_games(g,genres,platforms=['mac']))==1
    s=genre_summary(g,genres)
    assert s.loc[s['genre']=='Action','games'].iloc[0]==2
