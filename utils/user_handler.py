#!/usr/bin/python3

import uuid
import requests
from utils.logging import adapter
from model import storage
from utils.helper import handleEnv
from datetime import datetime, timedelta

time = "%Y-%m-%d %H:%M:%S"

def fetch_eligible_users(cap:float):
    eligible_users = []
    users = storage.all("User")
    for _, user in users.items():
        if user.subscribed is True:
            if user.min_cap >= cap:
                eligible_users.append(user.chat_id)
        else:
            if user.free_trial == 'active':
                trial_start = user.free_trial_started
                trial_start = datetime.strptime(trial_start, time)
                if datetime.now() > trial_start + timedelta(days=7):
                    user.free_trial = 'used'
                    user.save()
                else:
                    if user.min_cap >= cap:
                        eligible_users.append(user.chat_id)
    return eligible_users

def payment_handler():
    url = "https://api.paystack.co/transaction/initialize"
    amount = 50000 * 100
    reference = str(uuid.uuid4())
    key = handleEnv("paystack_key")
    authorization = "Bearer " + key
    email = "akinwonjowodennisco@gmail.com"

    res = requests.post(url, data={"amount": amount, "email": email, "reference": reference},
                        headers={"Authorization": authorization, "content_type": "application/json"})
    
    if res.status_code == 200:
        res = res.json()
        return res['data']['authorization_url']
    pass

def verify_transaction(reference):
    url = 'https://api.paystack.co/transaction/verify/' + reference
    key = handleEnv("paystack_key")
    authorization = "Bearer " + key
    resp = requests.get(url, headers={"Authorization": authorization, "content_type": "application/json"})
    if resp.status_code == 200:
        resp = resp.json()
        if resp['data']['status'] == 'success':
            return True
        else:
            return False
    else:
        adapter.warning("Could not fetch verification status")
        return False
