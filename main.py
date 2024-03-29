#!/usr/bin/python3

import threading
import asyncio
import ccxt
import sys
import requests
from typing import Dict, List
from trading_bot import setup, find_opportunity
from run_telegram import *
from utils.helper import handleEnv


app = Application.builder().token(BOT_TOKEN).build()
baseurl = "https://Dennisco.pythonanywhere.com"
developer_token = handleEnv("developer_token")
# https://www.pythonanywhere.com/user/Dennisco/webapps/#id_dennisco_pythonanywhere_com


def start_telegram():
    print("Telegram bot started")
    # app = Application.builder().token(BOT_TOKEN).build()
    global app

    # Commands
    app.add_handler(CommandHandler('register', register_command))
    app.add_handler(CommandHandler('start_free_trial', start_free_trial_command))
    app.add_handler(CommandHandler('recover_account', recover_account_command))
    app.add_handler(CommandHandler('subscribe', subscribe_command))
    app.add_handler(CommandHandler("edit_capital", edit_capital_command))
    app.add_handler(CommandHandler("continue_with_payment", continue_with_payment_command))
    app.add_handler(CommandHandler("use_coupon", use_coupon_command))
    app.add_handler(CommandHandler("verify_payment", verify_payment_command))
    app.add_handler(CommandHandler("verify_coupon_payment", verify_coupon_payment_command))
    app.add_handler(CommandHandler("edit_phone_number", edit_phone_number_command))
    app.add_handler(CommandHandler("edit_min_profit_percent", edit_minimum_profit_percent_command))

    app.add_handler(CallbackQueryHandler(button_press_handler))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the telegram bot
    print("Polling telegram app ...")
    app.run_polling(poll_interval=3)
    print("Telegram bot has stopped")
    # bot_exit_signal.set()
    # app.stop_running

async def bot_handler(capital:float, exchange_list:List=None, fetch_once=True, paper_trade=False, keys:Dict={}):
    adapter.info("You have started the bot")
    if exchange_list is None:
        exchange_list = ['binance', 'bitmex', 'huobi', 'bingx', 'bitget', 'mexc',
                           'bybit', 'gate', 'okx', 'kucoin']
    wait_time = 5   # minutes
    try:
        # set up all exchanges
        data = await setup(exchange_list)

        if not fetch_once:
            while True:
                url = baseurl + '/users'
                resp = requests.get(url)
                if resp.status_code != 200:
                    adapter.warning(f"Could not get users info from telegram server: {resp.status_code}. {resp.text}")
                else:
                    users = resp.json()
                    storage.recreate(users)
                    adapter.info("User info updated!")
                adapter.info("Fetching opportunities")
                best_opp = await find_opportunity(capital, data)
                if best_opp == "error":
                    await asyncio.sleep(2 * 60)
                else:
                    await asyncio.sleep(wait_time * 60)
            # adapter.info("Arbitrage bot has stopped")
        else:
            best_opp = await find_opportunity(capital, data)
            if not best_opp:
                adapter.warning("No profitable coin gotten")
                sys.exit(1)
            adapter.info(best_opp)
            from run_telegram import send_report
            for opp in best_opp:
                await send_report(opp)

    except ccxt.NetworkError as e:
        adapter.error(f"Bot stopped due to a network error: {e}")
    except ccxt.ExchangeError as e:
        adapter.error(f"Bot stopped due to an exchange error: {e}")
    except Exception as e:
        adapter.error(f"Bot stopped due to an unexpected error: {e}, line: {e.__traceback__.tb_lineno}")
    finally:
        start_arbitrage_bot()
        adapter.info("Bot thread restarted after initial shutdown")

async def checker():
    while True:
        global bot_exit_signal
        if bot_exit_signal.is_set():
            print("Terminating thread!")
            break

def start_arbitrage_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_handler(500, exchange_list=None, fetch_once=False))
    # loop.run_until_complete(checker())

def start_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_telegram())


if __name__ == '__main__':
    try:
        print("starting arbitrage bot...")
        # bot_thread = threading.Thread(target=start_arbitrage_bot, args=(bot_exit_signal,))
        # telegram_thread = threading.Thread(target=start_telegram_bot)
        # bot_thread.start()
        # start_telegram_bot()
        # telegram_thread.start()
        start_arbitrage_bot()
        print("Code reached the end")

        # bot_thread.join()
        # telegram_thread.join()
    except KeyboardInterrupt:
        pass

# if __name__ == '__main__':
#     asyncio.run(main())
