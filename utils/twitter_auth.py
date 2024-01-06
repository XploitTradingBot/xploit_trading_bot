#!/usr/bin/python3

import time
import tweepy
import webbrowser
from utils.helper import handleEnv
from dotenv import load_dotenv

load_dotenv()

consumer_key = handleEnv("consumer_key")
consumer_secret = handleEnv("consumer_secret")
access_token = handleEnv("access_token")
access_token_secret = handleEnv("access_token_secret")
bearer_token = handleEnv("bearer_token")
client_id = handleEnv("client_id")
client_secret = handleEnv("client_secret")


client = tweepy.Client(
    consumer_key=consumer_key, consumer_secret=consumer_secret,
    access_token=access_token, access_token_secret=access_token_secret,
)
print(f"Consumer key: {client.consumer_key}")

oauth2_user_handler = tweepy.OAuth2UserHandler(
    client_id=client_id,
    redirect_uri="https://www.unikrib.com",
    scope=["tweet.read"],
    client_secret=client_secret
)

# auth_url = oauth2_user_handler.get_authorization_url()
# print(f"Auth url: {auth_url}\n")
# webbrowser.open(auth_url)

# auth_code = input("Please enter the authorisation code: ")
# access_token = oauth2_user_handler.fetch_token(auth_code)
# print(f"Access token: {access_token}")
# client = tweepy.Client(access_token)

# query = "listed on binance"
# tweets = client.search_recent_tweets(query=query, max_results=2)
bookmarks = client.get_bookmarks(max_results=2)
for tweet in bookmarks:
    print(tweet.id)
    print(tweet.text)
