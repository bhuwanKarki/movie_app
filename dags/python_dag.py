import datetime as dt
import logging
import json
import os
from pathlib import Path
import pandas as pd
from pandas.core.indexes.range import RangeIndex
import requests

from airflow import DAG
from airflow.operators.python import PythonOperator
from requests.sessions import session
from airflow.operators.dummy import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator


MOVIELENS_HOST = os.environ.get("MOVIELENS_HOST", "movielens")
MOVIELENS_SCHEMA = os.environ.get("MOVIELENS_SCHEMA", "http")
MOVIELENS_PORT = os.environ.get("MOVIELENS_PORT", "5005")

MOVIELENS_USER = os.environ["MOVIELENS_USER"]
MOVIELENS_PASSWORD = os.environ["MOVIELENS_PASSWORD"]

def get_session():
    logger=logging.getLogger(__name__)
    session=requests.Session()
    session.auth=(MOVIELENS_USER,MOVIELENS_PASSWORD)
    schema=MOVIELENS_SCHEMA
    host=MOVIELENS_HOST
    port=MOVIELENS_PORT
    
    base_url=f"{schema}://{host}:{port}"
    logger.info(base_url)
    print(f"bae_url: {base_url}")
    return session, base_url

def _get_rating(start_date,end_date,batch_size=100):
    session,base_url=get_session()
    
    yield from get_data(session,base_url+"/ratings",{"start_date":start_date,"end_date":end_date},batch_size)

def get_data(session,url,params,batch_size=100):
    offset=0
    total=None
    while total is None or offset<total:
        response=session.get(url,params={**params,**{"offset":offset,"limit":batch_size}})
        response.raise_for_status()
        response_json=response.json()
        yield from response_json["result"]
        offset += batch_size
        total=response_json["total"]
        



def rank_movies_by_rating(ratings, min_ratings=2):
    ranking = (
        ratings.groupby("movie_id")
        .agg(
            avg_rating=pd.NamedAgg(column="ratings", aggfunc="mean"),
            num_ratings=pd.NamedAgg(column="user_id", aggfunc="nunique"),
        )
        .loc[lambda df: df["num_ratings"] > min_ratings]
        .sort_values(["avg_rating", "num_ratings"], ascending=False)
    )
    return ranking

    
with DAG(dag_id="python_rating",
         description="fecth the rating from moivelens data",
         start_date=dt.datetime(2001, 1, 1),
         end_date=dt.datetime(2002, 1, 10),
         schedule_interval="@daily",
          template_searchpath="/opt/airflow",) as dag:
    def hello_world():
        logging.info("Hello world!")
        
    
    def get_rating(templates_dict,batch_size=1000,**_):
        logger=logging.getLogger(__name__)
        start_date=templates_dict["start_date"]
        end_date=templates_dict["end_date"]
        output_path=templates_dict["output_path"]
        
        logger.info(f"fetching the rating for {start_date} to {end_date}")
        rating=list(
            _get_rating(start_date,end_date,batch_size)
        )
        logger.info(f"fetched {len(rating)} ratings")
        logger.info(f"writing the rating to {output_path}")
        #output_dir=os.path.dirname(output_path)
        #os.makedirs(output_dir,exist_ok=True)
        Path(output_path).parent.mkdir(exist_ok=True)
        with open(output_path,"w") as file_:
            print(file_)
            logger.info("file name",file_)
            json.dump(rating,fp=file_)
       
           
    fetch_rating=PythonOperator(
        task_id="fetch_rating",
        python_callable=get_rating,
        templates_dict={
            "start_date":"2001-01-01",
            "end_date":"2002-01-01",
            "output_path":f"/home/airflow/_rating.json"
        }
        )
    
    def movie_rank(templates_dict,min_ratins=2,**_):
        input_path=templates_dict["input_path"]
        output_path=templates_dict["output_path"]
        ratings=pd.read_json(input_path)
        ranking=rank_movies_by_rating(ratings,min_ratins)
        #outtput_path=os.path.dirname(outtput_path)
        #os.makedirs(outtput_path,exist_ok=True)
        ranking.to_csv(output_path,index=True)
        data=pd.read_json(input_path)
        print(data)
        
        with open("/opt/airflow/postgres_query.sql","w") as f:
            for movie_id,rating,timestamp,user_id in data.values:
                f.write(
                "INSERT INTO page VALUES ("
                f"'{movie_id}', {rating}, '{timestamp}','{user_id}'"
                ");\n"
            )
                
        
        
    rank_movies=PythonOperator(
        task_id="rank_movies",
        python_callable=movie_rank,
        templates_dict={
            "input_path":"/home/airflow/_rating.json",
            "output_path":"/home/airflow/_ranking.csv"
        }
    )
    
  
    start=DummyOperator(task_id="start")

    
    
    write_to_postgres=PostgresOperator(
    task_id="write_to_postgres",
    postgres_conn_id="my_postgres",
    sql="postgres_query.sql",
   )


    
    start>>fetch_rating>>rank_movies>>write_to_postgres