#!/usr/bin/python3

import threading
import asyncio
import ccxt
import sys
# import time
from typing import Dict, List
from trading_bot import setup, find_opportunity
from run_telegram import *
import time

exit_signal = threading.Event()

def start_telegram():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('register', register_command))
    app.add_handler(CommandHandler('start_free_trial', start_free_trial_command))
    app.add_handler(CommandHandler('recover_account', recover_account_command))
    app.add_handler(CommandHandler('subscribe', subscribe_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the telegram bot
    print("Polling telegram app ...")
    app.run_polling(poll_interval=3)
    print("Telegram bot stopped")
    exit_signal.set()

async def bot_handler(capital:float, exchange_list:List=None, fetch_once=True, paper_trade=False, keys:Dict={}):
    adapter.info("You have started the bot")
    if exchange_list is None:
        exchange_list = ['binance', 'bitmex', 'huobi', 'bingx', 'bitget', 'mexc',
                           'bybit', 'gate', 'okx', 'kucoin']
    wait_time = 5   # minutes
    try:
        data = await setup(exchange_list)

        if not fetch_once:
            while True:
                if exit_signal.is_set():
                    break
                adapter.info("Fetching opportunities")
                best_opp = await find_opportunity(capital, data)
                adapter.info(best_opp)
                if not best_opp:
                    adapter.warning("No profitable coin gotten")
                    time.sleep(wait_time * 60)
                    continue
                for opp in best_opp:
                    from run_telegram import send_report
                    await send_report(opp)
                time.sleep(wait_time * 60)
        else:
            best_opp = await find_opportunity(capital, data)
            if not best_opp:
                adapter.warning("No profitable coin gotten")
                sys.exit(1)
            adapter.info(best_opp)
            for opp in best_opp:
                from run_telegram import send_report
                await send_report(opp)

    except ccxt.NetworkError as e:
        adapter.error(f"Bot stopped due to a network error: {e}")
        sys.exit(1)
    except ccxt.ExchangeError as e:
        adapter.error(f"Bot stopped due to an exchange error: {e}")
        asyncio.run(bot_handler(capital, fetch_once=fetch_once))
    except Exception as e:
        adapter.error(f"Bot stopped due to an unexpected error: {e}, line: {e.__traceback__.tb_lineno}")

def start_arbitrage_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_handler(500, exchange_list=None, fetch_once=False))

def start_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_telegram())

if __name__ == '__main__':
    print("starting arbitrage bot...")
    bot_thread = threading.Thread(target=start_arbitrage_bot)
    telegram_thread = threading.Thread(target=start_telegram_bot)
    bot_thread.start()
    telegram_thread.start()

    bot_thread.join()
    telegram_thread.join()
