#!/usr/bin/python3

import asyncio
import requests
from typing import Dict, List
from utils.logging import adapter
from model import storage
from model.user import User
from utils.helper import handleEnv
from datetime import datetime, timedelta

timefmt = "%Y-%m-%d %H:%M:%S"

async def fetch_eligible_users(opp:Dict)->Dict:
    cap = opp['min_cap']
    eligible_users = {}
    users = storage.all("User")
    for _, user in users.items():
        # print("checking user status")
        subscribe_stat = await check_user_subscribe_status(user)
        # print("sub stat:", subscribe_stat)
        trial_stat = await check_user_free_trial_status(user)
        # print(f"User stat: subscribed: {subscribe_stat}, trial: {trial_stat}")
        if subscribe_stat is True or trial_stat is True:
            if user.min_cap >= cap:
                net_profit = ((user.min_cap / opp['buy_price']) * opp['sell_price']) - opp['total_fee'] - user.min_cap
                profit_percent = (net_profit / user.min_cap) * 100
                eligible_users[user.id] = (profit_percent, user.min_cap)
    # print("Eligible users:", eligible_users)
    return eligible_users

# def fetch_eligible_users(opp:Dict)->Dict:
#     return asyncio.run(fetch_eligible_users_for_opp(opp))

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

async def check_user_subscribe_status(user:User):
    if user.chat_id in [5199997067, 5620934799, 1209605960]:
        return True
    if not user.subscribed:
        return False
    current_datetime = datetime.now()
    if hasattr(user, "subscribed_date"):
        subscribed_date = user.subscribed_date
    else:
        return False
    subscribed_datetime = datetime.strptime(subscribed_date, timefmt)
    valid_till = subscribed_datetime + timedelta(days=30)
    if current_datetime > valid_till:
        return False
    else:
        if current_datetime > valid_till - timedelta(days=1) and current_datetime < valid_till:
            if not hasattr(user, "alerted") or user.alerted is False:
                from run_telegram import send_message
                expire_on = valid_till.strftime(timefmt)
                text = f"Hello {user.username}, your subscription for this service will expire on {expire_on}.\n\n"
                text += "Subscribe to continue receiving top verified arbitrage opportunities on this bot\n\n"
                text += "/subscribe"
                setattr(user, "alerted", True)
                user.save()
                await send_message(user.chat_id, text)
        return True
    
async def check_user_free_trial_status(user:User):
    if user.free_trial == "used":
        return "used"
    elif user.free_trial == "unused":
        return False
    current_datetime = datetime.now()
    if hasattr(user, "free_trial_started"):
        free_trial_started = user.free_trial_started
    else:
        return False
    free_trial_start_date = datetime.strptime(free_trial_started, timefmt)
    valid_till = free_trial_start_date + timedelta(days=7)
    if current_datetime > valid_till:
        return False
    else:
        if current_datetime > valid_till - timedelta(days=1) and current_datetime < valid_till:
            from run_telegram import send_message
            if not hasattr(user, "trial_alerted") or user.trial_alerted is False:
                expire_on = valid_till.strftime(timefmt)
                text = f"Hello {user.username}, your free trial will end on {expire_on}.\n\n"
                text += "Subscribe now to continue receiving top verified arbitrage signals from this bot\n\n"
                text += "/subscribe"
                setattr(user, "trial_alerted", True)
                user.save()
                await send_message(user.chat_id, text)
        return True
