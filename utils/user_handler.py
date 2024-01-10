#!/usr/bin/python3

import requests
from typing import Dict, List
from utils.logging import adapter
from model import storage
from model.user import User
from utils.helper import handleEnv
from datetime import datetime, timedelta

time = "%Y-%m-%d %H:%M:%S"

def fetch_eligible_users(opp:Dict)->Dict:
    cap = opp['min_cap']
    eligible_users = {}
    users = storage.all("User")
    for _, user in users.items():
        if user.subscribed is True:
            if user.min_cap >= cap:
                net_profit = ((user.min_cap / opp['buy_price']) * opp['sell_price']) - opp['total_fee'] - user.min_cap
                profit_percent = (net_profit / user.min_cap) * 100
                eligible_users[user.id] = (profit_percent, user.min_cap)
        else:
            if user.free_trial == 'active':
                trial_start = user.free_trial_started
                trial_start = datetime.strptime(trial_start, time)
                if datetime.now() > trial_start + timedelta(days=7):
                    user.free_trial = 'used'
                    user.save()
                else:
                    if user.min_cap >= cap:
                        net_profit = ((user.min_cap / opp['buy_price']) * opp['sell_price']) - opp['total_fee'] - user.min_cap
                        profit_percent = (net_profit / user.min_cap) * 100
                        eligible_users[user.id] = (profit_percent, user.min_cap)
    return eligible_users

def send_sms(phones:List, text:str):
    base_url = "https://api.ng.termii.com/api"
    api_key = handleEnv('TERMII_APIKEY')
    headers = {'Content-Type': 'application/json'}
    url = base_url + '/sms/send/bulk'

    data = {"api_key":api_key, "to": phones, "from": "Xploit", "sms": text,
            "type": "plain", "channel": "dnd"}
    
    res = requests.post(url, json=data, headers=headers)
    if res.status_code != 200:
        adapter.warning(f"Could not send sms notification {phones}, err: {res.text}")
    else:
        adapter.info(f"sms successfully sent to {phones}")

def check_user_subscribe_status(user:User):
    if not user.subscribed:
        return False
    current_datetime = datetime.now()
    if hasattr(user, "subscribed_date"):
        subscribed_date = user.subscribed_date
    else:
        return False
    subscribed_datetime = datetime.strptime(subscribed_date, time)
    valid_till = subscribed_datetime + timedelta(days=30)
    if current_datetime > valid_till:
        return False
    else:
        return True