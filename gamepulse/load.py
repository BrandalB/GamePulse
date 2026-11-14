"""Usage: python -m gamepulse.load data/raw/games_march2025_cleaned.csv"""
import argparse
from pathlib import Path
import pandas as pd
from .db import engine_from_env, ingest_frame

def load_file(path, chunksize=10000, database_url=None):
    path=Path(path)
    if not path.exists(): raise FileNotFoundError(path)
    engine=engine_from_env(database_url)
    reader=pd.read_csv(path,chunksize=chunksize,low_memory=False,encoding='utf-8-sig') if path.suffix.lower()=='.csv' else [pd.read_parquet(path)] if path.suffix.lower()=='.parquet' else [pd.read_excel(path)]
    totals={'input_rows':0,'valid_rows':0,'rejected_rows':0,'duplicate_appids_in_chunk':0}
    for i,chunk in enumerate(reader,1):
        result=ingest_frame(engine,chunk,str(path))
        for k in totals: totals[k]+=result[k]
        print(f'Batch {i}: {result["valid_rows"]:,} games, {result["rejected_rows"]:,} rejected')
    print('Complete:',totals)
    return totals

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Import Steam CSV / parquet / Excel records')
    parser.add_argument('path');parser.add_argument('--chunksize',type=int,default=10000)
    parser.add_argument('--database-url',default=None)
    args=parser.parse_args()
    load_file(args.path,args.chunksize,args.database_url)
