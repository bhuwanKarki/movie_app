from datetime import datetime
from typing import Optional
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import pandas as pd

import time

DEFAULT_ITEMS_PER_PAGE = 100
app = FastAPI()

def _read_ratings(file_path):
    ratings = pd.read_csv(file_path)

    # Subsample dataset.
    ratings = ratings.sample(n=100000, random_state=0)

    # Sort by ts, user, movie for convenience.
    ratings = ratings.sort_values(by=["timestamp", "user_id", "movie_id"])

    return ratings
@app.get("/")
def hello():
    return "Hello from the Movie Rating API!"

@app.get("/ratings/")
def ratings(start_date: str,end_date:str,offset: int =1, limit: int = DEFAULT_ITEMS_PER_PAGE):
    

    start_date_ts = _date_to_timestamp(start_date)
    end_date_ts = _date_to_timestamp(end_date)
    print(start_date)
    print(end_date)

    ratings_df = _read_ratings("rating.csv")

    if start_date_ts:
        ratings_df = ratings_df.loc[ratings_df["timestamp"] >= start_date_ts]

    if end_date_ts:
        ratings_df = ratings_df.loc[ratings_df["timestamp"] < end_date_ts]

    subset = ratings_df.iloc[offset : offset + limit]

    return (
        {
            "result": subset.to_dict(orient="records"),
            "offset": offset,
            "limit": limit,
            "total": ratings_df.shape[0],
        }
    )


def _date_to_timestamp(date_str):
    if date_str is None:
        return None
    return int(time.mktime(time.strptime(date_str, "%Y-%m-%d")))

