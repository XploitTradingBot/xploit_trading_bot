#!/usr/bin/python3

import threading
import asyncio
import ccxt
import sys
from typing import Dict, List
from trading_bot import setup, find_opportunity
from run_telegram import *
import time

bot_exit_signal = threading.Event()

app = Application.builder().token(BOT_TOKEN).build()


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
    app.add_handler(CommandHandler("Not_received", not_received_command))

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

async def bot_handler(capital:float, exchange_list:List=None, fetch_once=True, paper_trade=False, keys:Dict={}, exit_signal:threading.Event=None):
    adapter.info("You have started the bot")
    if exchange_list is None:
        exchange_list = ['binance', 'bitmex', 'huobi', 'bingx', 'bitget', 'mexc',
                           'bybit', 'gate', 'okx', 'kucoin']
    wait_time = 5   # minutes
    try:
        data = await setup(exchange_list)

        if not fetch_once:
            if not exit_signal:
                return "Include an exit_signal"
            while not exit_signal.is_set():
                adapter.info("Fetching opportunities")
                best_opp = await find_opportunity(capital, data)
                # adapter.info(best_opp)
                if not best_opp:
                    adapter.warning("No profitable coin gotten")
                    time.sleep(wait_time * 60)
                    continue
                for opp in best_opp:
                    from run_telegram import send_report
                    await send_report(opp)
                if not exit_signal.is_set():
                    await asyncio.sleep(wait_time * 60)
                else:
                    break
            adapter.info("Arbitrage bot has stopped")
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
        asyncio.run(bot_handler(capital, fetch_once=fetch_once))
    except ccxt.ExchangeError as e:
        adapter.error(f"Bot stopped due to an exchange error: {e}")
        asyncio.run(bot_handler(capital, fetch_once=fetch_once))
    except Exception as e:
        adapter.error(f"Bot stopped due to an unexpected error: {e}, line: {e.__traceback__.tb_lineno}")
        asyncio.run(bot_handler(capital, fetch_once=fetch_once))

def start_arbitrage_bot(exit_signal=None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_handler(500, exchange_list=None, fetch_once=False, exit_signal=exit_signal))

def start_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_telegram())


async def main():
    try:
        print("starting arbitrage bot...")
        bot_thread = threading.Thread(target=start_arbitrage_bot, args=(bot_exit_signal,))
        telegram_thread = threading.Thread(target=start_telegram_bot)
        bot_thread.start()
        telegram_thread.start()
        print("Code reached the end")

        bot_thread.join()
        telegram_thread.join()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    asyncio.run(main())
