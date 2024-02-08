#!/usr/bin/python3

from api.blueprint import app_views
import threading
from flask import jsonify
from utils.helper import handleEnv
from utils.logging import adapter
from main import start_arbitrage_bot, start_telegram_bot, app

developer_token = handleEnv("developer_token")

@app_views.route('/start_telegram/<admin_key>', strict_slashes=False, methods=['GET'])
def start_telegram(admin_key):
    if admin_key == developer_token:
        telegram_thread = threading.Thread(target=start_telegram_bot)
        adapter.info("Telegram bot started")
        telegram_thread.start()
        return jsonify("Telegram thread successfully started")
    else:
        return jsonify("Sorry, your developer_token is invalid"), 403
    

@app_views.route('/start_arbitrage_bot/<admin_key>', strict_slashes=False)
def start_arbitrage(admin_key):
    if admin_key == developer_token:
        bot_thread = threading.Thread(target=start_arbitrage_bot)
        adapter.info("Arbitrage bot started")
        bot_thread.start()
        return jsonify("You have successfully started the arbitrage bot")
    else:
        return jsonify("Sorry, your developer_token is invalid"), 403
    
@app_views.route('/stop_telegram_bot/<admin_key>', strict_slashes=False)
def stop_arbitrage_bot(admin_key):
    if admin_key == developer_token:
        app.stop_running()
        return jsonify("Telegram bot stopped successfully")
    else:
        return jsonify("Sorry, your developer_token is invalid"), 403
    