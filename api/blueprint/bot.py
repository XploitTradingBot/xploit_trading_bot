#!/usr/bin/python3

import json
from model import storage
# from model.keys import Key
# from model.bot import Bot
from trading_bot import executor
# import threading
# from celery import Celery
import asyncio
# from concurrent.futures import ThreadPoolExecutor
# # import websockets
# import traceback
# import tracemalloc
from typing import Dict
from uuid import uuid4
from api.blueprint import app_views, auth
from flask import request, jsonify
from datetime import datetime, timedelta
# from executor import Executor
# from utils.queue import runner
from dotenv import load_dotenv

load_dotenv()

threads = {}
time = "%Y-%m-%d %H:%M:%S"
active_threads = {}
all_executors = {}


def start_executor(capital, keys):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    fileName = 'opportunity.json'
    with open(fileName, 'r', encoding='utf-8') as fp:
        opportunity = json.load(fp)
    loop.run_until_complete(executor())
    
    executor(capital, opportunity, keys)
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(executor.start())

# @app_views.route('/start-bot', methods=['POST'], strict_slashes=False)
# @auth.login_required
# def start_bot():
#     if not request.json:
#         return jsonify("Not a valid json"), 400
#     user = auth.current_user()
#     token = user.id
    
#     data = request.get_json()
#     if "capital" not in data or "exchange" not in data:
#         return jsonify("Please include a capital and the holding exchange"), 400
    
#     capital = data.pop('capital', None)
#     exchange = data.pop('exchange', None)

#     data['user_id'] = token
#     key = Key(**data)
#     key.save()
#     try:
#         capital = float(capital)
#     except Exception as e:
#         return jsonify("Capital must be a number"), 400

#     stop_flag = threading.Event()
#     thread = threading.Thread(target=bot, args=(capital, exchange, data, token))
#     threads[token] = (thread, stop_flag)
#     thread.start()

#     return jsonify("Bot started"), 200

# @app_views.route('/create-bot', methods=['POST'], strict_slashes=False)
# @auth.login_required
# def create_bot():
#     if not request.json:
#         return jsonify("Not a valid json"), 400

#     data = request.get_json()
#     if "exchange" not in data:
#         return jsonify("Please signify your holding exchange"), 400

#     if "apiKey" not in data or 'secret' not in data:
#         return jsonify("Please include an apiKey and a secret key"), 400

#     user = auth.current_user()
#     exchange = data.pop('exchange')
#     capital = data.get('capital', 100)
#     if capital == "":
#         capital = 100
#     key_dict = {f"{exchange}_key": data['apiKey'], f"{exchange}_secret": data['secret'],
#                 "user_id": user.id}
#     if "password" in data:
#         key_dict[f'{exchange}_password'] = data['password']
#     if "uid" in data:
#         key_dict[f"{exchange}_uid"] = data['uid']
#     print(key_dict)
#     user_key = Key(**key_dict)
#     user_key.save()

#     bot_id = str(uuid4())
#     bot_dict = {"id": bot_id, "user_id": user.id, 'capital': capital, 'exchange': exchange}
#     bot = Bot(**bot_dict)
#     bot.save()
#     user.update(bot_id=bot.id)
#     try:
#         executor = Executor(user.id, bot.id, exchange, **data)
#         all_executors["executor_{}".format(executor.id)] = executor
#         bot.executor_id = executor.id
#         bot.update(executor_id=executor.id)
#         return jsonify({"bot_id": bot.id}), 200
#     except Exception as e:
#         return jsonify("Bot Error: {}".format(e)), 404

@app_views.route('/start/<bot_id>', methods=['GET'], strict_slashes=False)
@auth.login_required
def start(capital:float, keys:Dict):
    fileName = 'opportunity.json'
    with open(fileName, 'r', encoding='utf-8') as fp:
        opportunity = json.load(fp)
    
    executor(capital, opportunity, keys)

# @app_views.route('/stop-bot', methods=['DELETE'], strict_slashes=False)
# @auth.login_required
# def stop_bot():
#     user = auth.current_user()
#     token = user.id
    
#     if token in threads:
#         thread, stop_flag = threads[token][0], threads[token][1]
#         stop_flag.set()
#         thread.join()
#         threads.pop(token, None)
#         return jsonify("Bot stopped"), 200
#     else:
#         return jsonify("You have no instance of bot running"), 400

# @app_views.route('/stop-tri-bot/<bot_id>', methods=['DELETE'], strict_slashes=False)
# @auth.login_required
# def stop_tri_bot(bot_id):
#     user = auth.current_user()
#     if user.bot_id is None:
#         return jsonify("You have no active bot"), 404
#     bot_id = user.bot_id
#     bot = storage.get("Bot", bot_id)

#     if bot.user_id != user.id:
#         return jsonify("Unauthorized: You don't have access to this bot"), 401
    
#     key = f"executor_{bot.executor_id}"
#     if key in all_executors:
#         try:
#             executor = all_executors[key]
#             if executor.id in active_threads:
#                 thread, stop_flag = active_threads[executor.id][0], active_threads[executor.id][1]
#                 executor.stop()
#                 stop_flag.set()
#                 thread.join()
#                 active_threads.pop(executor.id)
#                 del all_executors[key]
#             user.bot_id = None
#             user.save()
#             return jsonify("Bot stopped successfully"), 200
#         except Exception as e:
#             return jsonify("Error: {}".format(e)), 404
#     else:
#         return jsonify("Bot not active"), 404

@app_views.route('/get_keys', methods=['GET'], strict_slashes=False)
@auth.login_required
def get_keys():
    user = auth.current_user()
    keys = storage.get("Key", user.id)
    if keys:
        return jsonify(keys.to_dict()), 200
    else:
        return jsonify({})

# @app_views.route('/get-notif', methods=['GET'], strict_slashes=False)
# @auth.login_required
# def get_notif():
#     user = auth.current_user()
#     if not user.bot_id:
#         return jsonify("You have no active bots"), 404
    
#     bot_id = user.bot_id
#     bot = storage.get("Bot", bot_id)
#     if not bot:
#         return jsonify("You have no active bots"), 404
    
#     msg = bot.transactions.pop(0)
#     if msg:
#         return jsonify(msg)
#     else:
#         return jsonify({})
    
#     # notifs = storage.all("Notification")
#     # for key, notif in notifs.items():
#     #     if notif.user_id == user.id:
#     #         notif.delete()
#     #         return jsonify(notif.to_dict())
#     # return jsonify({})

@app_views.route('/get-bot-msg/<bot_id>', methods=['GET'], strict_slashes=False)
@auth.login_required
def get_bot_msg(bot_id):
    bot = storage.get("Bot", bot_id)
    if not bot:
        return jsonify("Bot not found"), 404
    
    # if bot.active is False:
    #     bot.unread_log.append("Bot stopped")
    #     return jsonify(["Bot has been deactivated"])
    
    if request.args.get("show_read", None) == "1":
        current_dt = datetime.now()
        today = current_dt.day
        today_logs = []
        if len(bot.read_logs) == 0:
            return jsonify([]), 200
        for log in bot.read_logs:
            log_date_str = log['log_time']
            log_date_dt = datetime.strptime(log_date_str, time) + timedelta(hours=1)
            if log_date_dt.day == today:
                today_logs.append(log)
        bot.read_logs = today_logs
        ret = [log['msg'] for log in bot.read_logs]
        return jsonify(ret), 200

    if len(bot.unread_logs) > 0:
        ret = [log['msg'] for log in bot.unread_logs]
        for log in bot.unread_logs:
            # ret.append(log['msg'])
            bot.read_logs.append(log)
        setattr(bot, "unread_logs", [])
        bot.save()
        return jsonify(ret), 200
    else:
        return jsonify(None)

@app_views.route('/count/notif', methods=['GET'], strict_slashes=False)
def count_notif():
    count = storage.count("Notification")
    return jsonify(count)
