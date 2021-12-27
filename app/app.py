import os
import time
import pandas as pd
from flask import Flask,jsonify,request
from pandas.io.parsers import read_csv
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

DEFAULT_ITEMS_PER_PAGE = 100

def _read_rating(file_path):
    rating=pd.read_csv(file_path)
    rating=rating.sample(n=100000,random_state=0)
    rating.sort_values(by=["timestamp","user_id","movie_id"],inplace=True)
    return rating
    
app=Flask(__name__)
app.config["ratings"]=_read_rating("rating.csv")

auth=HTTPBasicAuth()
user={os.environ["API_USER"]: generate_password_hash(os.environ["API_PASSWORD"])}
@auth.verify_password
def verify_password(username,password):
    if username in user:
        return check_password_hash(user.get(username),password)
    return False
@app.route("/")
def hello():
    return "hello to the website for getting the movie ratings"


def _date_to_timestamp(date_str):
    if date_str is None:
        return None
    return int(time.mktime(time.strptime(date_str, "%Y-%m-%d")))


@app.route("/ratings")
@auth.login_required
def rating():
    start_date=_date_to_timestamp(request.args.get("start_date"))
    print(((request.args.get("start_date"))))
    end_date=_date_to_timestamp(request.args.get("end_date"))
    print(start_date)
    print(end_date)
    
    offset=int(request.args.get("offset",0))
    limit=int(request.args.get("limit",DEFAULT_ITEMS_PER_PAGE))
    rating_df=app.config.get("ratings")
    #print(rating_df[rating_df["timestamp"]>=947455200])
    if start_date:
        rating_df=rating_df[rating_df["timestamp"]>=start_date]
    if end_date:
        rating_df=rating_df[rating_df["timestamp"]<end_date]
    subset=rating_df.iloc[offset:offset+limit]
    
    return jsonify(
        {
            "result":subset.to_dict(orient="records"),
            "offset":offset,
            "limit":limit,
            "total":rating_df.shape[0]
        }
       
        )
if __name__=="__main__":
    app.run(host="0.0.0.0",port=5005,debug=True)


