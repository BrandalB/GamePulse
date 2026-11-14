import pandas as pd
from sqlalchemy import create_engine
from gamepulse.db import create_schema,ingest_frame,read_games,read_genres

def test_idempotent_load_and_genres():
    eng=create_engine('sqlite:///:memory:')
    create_schema(eng)
    sample=pd.DataFrame({'appid':[1,2], 'name':['A','B'],'price':[0,15],
                         'positive':[8,9],'negative':[2,1],
                         'genres':["['Action','Indie']","['RPG']"]})
    ingest_frame(eng,sample)
    ingest_frame(eng,sample)
    assert len(read_games(eng))==2
    assert len(read_genres(eng))==3
