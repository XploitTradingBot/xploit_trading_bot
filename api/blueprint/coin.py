#!/usr/bin/python3

import threading
import ccxt
import tracemalloc
import asyncio
from model import storage
from model.bot import Bot
from model.keys import Key
from datetime import datetime, timedelta
from new_listing import Executor
from update_coin_list import add_coins
from flask import jsonify, request
from api.blueprint import auth, app_views

active_threads = {}
time = "%Y-%m-%d %H:%M:%S"
coinlist_updated = False
coinlist_next_update = datetime.now()
first_update = True


def start_executor(capital:float, bot_id:str, exchange:ccxt.Exchange):
    bot = storage.get("Bot", bot_id)
    executor = Executor(capital=capital, bot=bot, exchange=exchange)
    active_threads[bot.id].append(executor)
    while True:
        bot = storage.get("Bot", bot_id)
        if bot.active is True:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(executor.wait_and_buy())
            print("Trade completed")
            refresh_coin_list()
        else:
            return

def refresh_coin_list():
    try:
        for key, coin in storage.all("Coin").items():
            listing_date = datetime.strptime(coin.listing_date, time)
            if datetime.now() > (listing_date - timedelta(hours=1)):
                coin.delete()
    except Exception as e:
        print(f"Error obtained while refreshing tokens: {e}")
        pass

@app_views.route('/get-coins', methods=['GET'], strict_slashes=False)
def get_coins():
    global coinlist_next_update
    global coinlist_updated
    global first_update
    if datetime.now() >= coinlist_next_update and coinlist_updated is False:
        print("Updating coin list...")
        add_coins()
        coinlist_next_update = datetime.now() + timedelta(hours=4)
        coinlist_updated = True
        first_update = False
    if datetime.now() > coinlist_next_update and first_update is False:
        if coinlist_updated is True:
            coinlist_updated = False

    coins = storage.all("Coin")
    coins = dict(sorted(coins.items(), key=lambda x: x[1].listing_date))
    new_coin = []
    for coin in coins.values():
        listing_date = datetime.strptime(coin.listing_date, time)
        if datetime.now() > (listing_date - timedelta(hours=1)):
            print(f"Deleting {coin.symbol}")
            coin.delete()
        else:
            new_coin.append(coin.to_dict())
    return jsonify(new_coin), 200

@app_views.route('/start-trade', methods=['POST'], strict_slashes=False)
@auth.login_required
def start_trade():
    if not request.json:
        return jsonify("Not a valid json"), 400
    
    user = auth.current_user()
    
    data = request.get_json()
    data = {item: data[item] for item in data if data[item] != ""}
    if "capital" not in data or data["capital"] == "":
        return jsonify("Please include the starting capital"), 400
    
    if "apiKey" not in data or "secret" not in data:
        return jsonify("Please include both your apiKey and secret keys"), 400
    
    try:
        capital = float(data['capital'])
    except ValueError:
        return jsonify("Capital must be a number"), 400
    
    exchange_id = data.get("exchange", "gate")
    coins = storage.all("Coin")
    coins = dict(sorted(coins.items(), key=lambda x: x[1].listing_date))
    coins = list(coins.values())

    # Save the user keys
    key_dict = {f"{exchange_id}_key": data['apiKey'], f"{exchange_id}_secret": data['secret'], "user_id":user.id}
    key = Key(**key_dict)
    key.save()

    # Create the exchange instance
    try:
        exchange = getattr(ccxt, exchange_id)()
    except Exception as e:
        return jsonify("Exchange not found"), 404
    setattr(exchange, "nonce", ccxt.Exchange.milliseconds())
    setattr(exchange, "enableRateLimit", True)
    exchange.apiKey = data['apiKey']
    exchange.secret = data['secret']
    for coin in coins:
        if coin.exchange == exchange_id:
            new_coin = coin
            break
    coin = new_coin.symbol
    try:
        tracemalloc.start()
        bot_dict = {"capital": capital, "user_id": user.id, "exchange": exchange_id,
                    "active": True}
        bot = Bot(**bot_dict)
        setattr(user, "bot_id", bot.id)
        user.save()
        print(f"Created bot id: {bot.id}")
        bot.save()
        stop_flag = threading.Event()
        thread = threading.Thread(target=start_executor, args=(capital, bot.id, exchange))
        thread.start()
        active_threads[bot.id] = [thread, stop_flag]
        bot.save()
        return jsonify({"msg": f"Execution for {coin} listing started", "bot_id": bot.id})
    except Exception as e:
        return jsonify(f"Error encountered: {e}"), 404

@app_views.route('/stop-trade/<bot_id>', methods=['DELETE'], strict_slashes=False)
@auth.login_required
def stop_trade(bot_id:str):
    if bot_id in active_threads:
        thread = active_threads[bot_id][0]
        stop_flag = active_threads[bot_id][1]
        executor = active_threads[bot_id][2]
        print(f"Executor id found: {executor.id}")
        executor.stop_bot()
        print(f"Executor stop_bot function has finished")
        stop_flag.set()
        thread.join()
        print("Thread has join to main loop")
        active_threads.pop(bot_id)
        return jsonify("Bot stopped succesfully")
    else:
        return jsonify("You have no active bot"), 404
    
@app_views.route('/get-user-bots', methods=['GET'], strict_slashes=False)
@auth.login_required
def get_user_bots():
    user = auth.current_user()
    if user.bot_id is None:
        return jsonify(None)
    # bot = storage.get("Bot", user.bot_id)
    bots = storage.search("Bot", user_id=user.id)
    for bot in bots:
        if bot.active is False:
            return jsonify(None)
        return jsonify([bot.id])
    return jsonify(None)
