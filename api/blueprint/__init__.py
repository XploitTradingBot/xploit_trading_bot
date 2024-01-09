#!/usr/bin/python3

from flask import Blueprint
from model import storage
from model.usersession import UserSession
from flask_httpauth import HTTPTokenAuth

app_views = Blueprint('app_views', __name__, url_prefix='/bot')
auth = HTTPTokenAuth(scheme='TradingBot')
sessions = UserSession()

@auth.verify_token
def verify_token(token):
    """This validates the token presented by the user"""
    sess = sessions.get(token)
    if not sess:
        print("No user found")
        return None
    else:
        user = storage.get("User", sess.user_id)
        return user
    

# from api.blueprint.user import *
from api.blueprint.bot2 import *
# from api.blueprint.coin import *