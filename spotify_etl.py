#!/usr/bin/env python3

import os
import json
import base64
import requests
import datetime
import pandas as pd
from requests import post
from google.cloud import bigquery


CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
DB_ID = os.environ.get('DB_ID')


def get_auth_code():
  AUTH_URL = 'https://accounts.spotify.com/authorize'

  params = {
      'client_id': CLIENT_ID,
      'response_type': 'code',
      'redirect_uri': REDIRECT_URI,
      'scope': 'user-read-recently-played'
  }

  auth_url = '{}?{}'.format(AUTH_URL, '&'.join(['{}={}'.format(key, val) for key, val in params.items()]))

  print('Please go to the following URL and copy the code:', auth_url)

  authorization_code = input('Enter the authorization code from the URL: ')

  return authorization_code


def get_token():

  URL = "https://accounts.spotify.com/api/token"

  auth_string = CLIENT_ID + ":" + CLIENT_SECRET
  auth_bytes = auth_string.encode("utf-8")
  auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
  authorization_code = get_auth_code()

  token_params = {
      'grant_type': 'authorization_code',
      'code': authorization_code,
      'redirect_uri': REDIRECT_URI,
      'client_id': CLIENT_ID,
      'client_secret': CLIENT_SECRET
  }

  result = requests.post(URL, data=token_params)

  json_result = json.loads(result.content)

  token = json_result["access_token"]

  return token


def get_auth_header(token):
  return {"Authorization": "Bearer " + token}


def get_history(token):
  today = datetime.datetime.now()
  yesterday = today - datetime.timedelta(days=1)
  yesterday_unix_timestamp = int(yesterday.timestamp()) * 1000

  headers = {
      "Accept": "application/json",
      "Content-Type": "application/json"
  }

  headers.update(get_auth_header(token))

  url = "https://api.spotify.com/v1/me/player/recently-played?limit=50&after={time}".format(time=yesterday_unix_timestamp)


  r = requests.get(url, headers = headers)

  data = r.json()

  return data


def format_dict(history):
  song_name = []
  artist_name = []
  played_at = []
  timestamp = []

  for song in history["items"]:
    song_name.append(song["track"]["name"])
    artist_name.append(song["track"]["album"]["artists"][0]["name"])
    played_at.append(song["played_at"])
    timestamp.append(song["played_at"][0:10])


  song_dict = {
    "song_name": song_name,
    "artist_name": artist_name,
    "played_at": played_at,
    "timestamp": timestamp
  }

  song_df = pd.DataFrame(song_dict, columns = ["song_name", "artist_name", "played_at", "timestamp"])

  return song_df


def load_bq(dataframe):
  client = bigquery.Client()

  table_id = DB_ID + ".played_tracks"

  job_config = bigquery.LoadJobConfig(
    schema=[

        bigquery.SchemaField("song_name", "STRING"),
        bigquery.SchemaField("artist_name", "STRING"),
        bigquery.SchemaField("played_at", "DATETIME"),
        bigquery.SchemaField("timestamp", "DATE")
    ]
  )

  job = client.load_table_from_dataframe(
      dataframe, table_id, job_config=job_config
  )

  job.result()

  table = client.get_table(table_id)
  print("Loaded {} rows and {} columns to {}".format(table.num_rows, len(table.schema), table_id))


def main():

  token = get_token()

  history = get_history(token)

  song_df = format_dict(history)

  if song_df.size > 0:
    print(song_df)

  load_bq(song_df)


if __name__ == '__main__':

  main()




