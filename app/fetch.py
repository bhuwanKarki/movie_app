import logging
import click
import pandas as pd
from pathlib import Path
import tempfile
from urllib.request import urlretrieve
import zipfile
import io
logging.basicConfig(format="[%(asctime)-15s] %(levelname)s - %(message)s", level=logging.INFO)

@click.command()
@click.option("--start_date", default="2000-01-01", type=click.DateTime())
@click.option("--end_date", default="2002-01-01", type=click.DateTime())
@click.option("--output_path", required=True)
def main(start_date,end_date,output_path):
    logging.info("fetching the data....")
    rating = fetch_ratings()
    logging.info(f"filtering for dates {start_date} - {end_date}")
    print(rating)
    ts_parsed = pd.to_datetime(rating["timestamp"],unit="s")
    rating=rating.loc[(ts_parsed>=start_date)&(ts_parsed<end_date)]
    logging.info(f"writing ratings to {output_path}")
    rating.to_csv(output_path,index=False)    

def fetch_ratings():
    url="http://files.grouplens.org/datasets/movielens/ml-1m.zip"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path=Path(tmp,"download.zip")
        logging.info(f"downloading zip file from {url} to {tmp_path}")
        urlretrieve(url,tmp_path)

        with zipfile.ZipFile(tmp_path) as zip_:
            logging.info(f"Downloaded zip file with contents: {zip_.namelist()}")

            logging.info("Reading ml-1/ratings.csv from zip file")
            with zip_.open("ml-1m/ratings.dat") as file_:
                logging.info(f"Reading ml-1/ratings.csv from zip file {file_}")
                
                #ratings=pd.read_csv(file_,sep="::",header=None,names=["user_id","movie_id","ratings","timestamp"])
                ratings=pd.read_csv(io.BytesIO(file_.read()),sep="::",header=None,engine="python",names=["user_id","movie_id","ratings","timestamp"])
            #print(ratings.head())
    return ratings

if __name__=="__main__":
    main()