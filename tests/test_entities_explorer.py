import json
import pandas as pd
from gamepulse.entities import parse_credits, display_credits
from gamepulse.explorer import similar_games, review_breakdown
from gamepulse.market import entity_summary
from gamepulse.transform import normalize


def test_company_suffix_is_not_a_separate_entity():
    assert parse_credits('Valve, Inc., Rockstar North, Example LLC') == ['Valve, Inc.', 'Rockstar North', 'Example LLC']
    assert parse_credits('Inc., Ltd., LLC') == []
    assert parse_credits('["Valve, Inc.", "Rockstar North"]') == ['Valve, Inc.', 'Rockstar North']


def test_entity_summary_does_not_show_inc_ltd():
    rows = pd.DataFrame({'appid':[1,2,3], 'developers':['Valve, Inc.', 'Valve, Inc.', 'Studio A, Ltd.'],
        'publishers':['Example, Ltd.', 'Example, Ltd.', 'Publisher'], 'price':[10,20,0],
        'review_count':[100,50,0], 'positive':[90,40,0], 'owners_mid':[1000,2000,100]})
    result=entity_summary(rows,'developers',1)
    assert 'Inc.' not in set(result.entity)
    assert 'Ltd.' not in set(result.entity)
    assert result.loc[result.entity=='Valve, Inc.','titles'].iloc[0]==2


def test_new_import_preserves_companies_with_commas():
    raw=pd.DataFrame({'appid':[1], 'name':['Sample'], 'developers':['["Valve, Inc.", "Other Studio"]'],
        'publishers':['["Example Co., Ltd."]'], 'genres':['["Action"]']})
    games,*_=normalize(raw)
    assert parse_credits(games.iloc[0]['developers'])==['Valve, Inc.','Other Studio']
    assert display_credits(games.iloc[0]['publishers'])=='Example Co., Ltd.'


def test_similar_titles_use_shared_genres():
    games=pd.DataFrame({'appid':[1,2,3,4],'name':['A','B','C','D'],'release_year':[2020]*4,
        'price':[10]*4,'review_count':[5,50,100,0],'positive_rate':[.5]*4})
    links=pd.DataFrame({'appid':[1,1,2,2,3,4],'genre':['Action','RPG','Action','RPG','Action','Puzzle']})
    suggestions=similar_games(games,links,1)
    assert suggestions.appid.tolist()==[2,3]
    assert suggestions.shared_genres.tolist()==[2,1]
    assert review_breakdown(pd.Series({'positive':12,'negative':3}))['Reviews'].tolist()==[12,3]
