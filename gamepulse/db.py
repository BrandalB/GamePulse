"""Database engine and idempotent, normalized data ingestion."""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, BigInteger, Integer, Float, String, Text, Boolean, Date, ForeignKey, text
from sqlalchemy.engine import Engine
from .transform import normalize

METADATA=MetaData()
GAMES=Table('games',METADATA,
    Column('appid',BigInteger,primary_key=True),Column('name',Text,nullable=False),
    Column('release_date',Date),Column('release_year',Integer),Column('price',Float),
    Column('positive',BigInteger),Column('negative',BigInteger),Column('peak_ccu',BigInteger),
    Column('metacritic_score',Float),Column('average_playtime_forever',BigInteger),
    Column('windows',Boolean),Column('mac',Boolean),Column('linux',Boolean),
    Column('developers',Text),Column('publishers',Text),Column('header_image',Text),
    Column('recommendations',BigInteger),Column('owners_low',BigInteger),Column('owners_high',BigInteger),
    Column('owners_mid',Float),Column('review_count',BigInteger),Column('positive_rate',Float),Column('is_free',Boolean))
GENRES=Table('game_genres',METADATA,Column('appid',BigInteger,ForeignKey('games.appid',ondelete='CASCADE'),primary_key=True),
             Column('genre',String(120),primary_key=True))
IMPORTS=Table('import_runs',METADATA,Column('id',Integer,primary_key=True,autoincrement=True),
             Column('source',Text),Column('imported_at',Text),Column('input_rows',Integer),
             Column('valid_rows',Integer),Column('rejected_rows',Integer),Column('duplicates',Integer))

def engine_from_env(url=None)->Engine:
    from dotenv import load_dotenv
    load_dotenv()
    url=url or os.getenv('DATABASE_URL','sqlite:///data/gamepulse.db')
    if url.startswith('sqlite:///') and url!='sqlite:///:memory:':
        Path(url.replace('sqlite:///','',1)).parent.mkdir(parents=True,exist_ok=True)
    return create_engine(url,pool_pre_ping=True)

def create_schema(engine):
    METADATA.create_all(engine)
    if engine.dialect.name=='sqlite':
        from sqlalchemy import event
        @event.listens_for(engine,'connect')
        def set_fk(dbapi_connection, connection_record):
            dbapi_connection.execute('PRAGMA foreign_keys=ON')

def ingest_frame(engine, raw:pd.DataFrame, source='uploaded'):
    create_schema(engine)
    games,genres,rejected,quality=normalize(raw)
    # Update existing rows and rebuild genre associations transactionally (batch-friendly).
    with engine.begin() as conn:
        if len(games):
            ids=games['appid'].astype('int64').tolist()
            for i in range(0,len(ids),500):
                batch=ids[i:i+500]
                conn.execute(GENRES.delete().where(GENRES.c.appid.in_(batch)))
                conn.execute(GAMES.delete().where(GAMES.c.appid.in_(batch)))
            records=games.astype(object).where(pd.notnull(games),None).to_dict('records')
            # Python date objects preserved; nullable pandas booleans converted to native values.
            records=[{k: (v.item() if hasattr(v,'item') else v) for k,v in r.items()} for r in records]
            for i in range(0,len(records),1000): conn.execute(GAMES.insert(),records[i:i+1000])
            if len(genres):
                links=genres.to_dict('records')
                for i in range(0,len(links),2000): conn.execute(GENRES.insert(),links[i:i+2000])
        from datetime import datetime,timezone
        conn.execute(IMPORTS.insert().values(source=str(source),imported_at=datetime.now(timezone.utc).isoformat(),
            input_rows=quality['input_rows'],valid_rows=quality['valid_rows'],
            rejected_rows=quality['rejected_rows'],duplicates=quality['duplicate_appids_in_chunk']))
    return quality

def read_games(engine):
    with engine.connect() as c:
        df=pd.read_sql(text('SELECT * FROM games'),c)
    return df

def read_genres(engine):
    with engine.connect() as c:
        return pd.read_sql(text('SELECT appid,genre FROM game_genres'),c)

def read_runs(engine):
    with engine.connect() as c:
        return pd.read_sql(text('SELECT * FROM import_runs ORDER BY id DESC LIMIT 50'),c)
