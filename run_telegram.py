#!/usr/bin/python3

import asyncio
import threading
from utils.logging import adapter
from utils.helper import handleEnv
from typing import Final, Dict
from telegram import Update
from model import storage
from model.user import User
from utils.user_handler import fetch_eligible_users
from datetime import datetime, timedelta
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


BOT_TOKEN: Final = "6778474307:AAFOv0T9F3538MFVwyEafJwu15JLnrFHiB8"
BOT_USERNAME: Final = "@Xploit_trading_bot"
time = "%Y-%m-%d %H:%M:%S"

exit_signal = threading.Event()


# Commands
async def start_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text:str = Update.message.text
    chat_id = Update.message.chat.id
    user = storage.search("User", chat_id=chat_id)
    if len(user) > 0:
        name:str = user[0].username
        name = name.capitalize()
    else:
        name = "there"
    print(f"User ({chat_id}): {text}")
    await Update.message.reply_text(f"Hello {name}, welcome to X-ploit cybernetics. Send \"help\" to view a list of all commands")

async def register_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text:str = Update.message.text
    chat_id = Update.message.chat.id
    print(f"User ({chat_id}): {text}")
    users = storage.search("User", chat_id=chat_id)
    if len(users) > 0:
        await Update.message.reply_text("You are already a registered user")
    else:
        await Update.message.reply_text("Please enter your username in the format below \n\n\"Username - {username}\".\n\n eg \"Username - xploit\"")

async def subscribe_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    txt = "Welcome, subscription for this service cost 100 USDT per month\n"
    txt += "/continue_with_payment\n"
    txt += "/use_coupon"
    await Update.message.reply_text(txt)

async def continue_with_payment_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    txt = "Please complete your payment by sending 100 USDT to any of the following addresses\n\n"
    txt += "0x4a25bf5ffb9083d894faca43e29407a6c99f03dd\n"
    txt += "BEP20\n\n"
    txt += "TKUzV9HpakiNdMrFC7164Nb67XGvFYS6AA\n"
    txt += "TRC20\n\n"
    txt += "Click here after sending your payment /verify_payment"
    await Update.message.reply_text(txt)

async def verify_payment_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    txt = "Please send the transaction id (txid) of the transaction\n\n"
    txt += "Use the format:  \"txid - 0x12example\""
    await Update.message.reply_text(txt)

async def use_coupon_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    await Update.message.reply_text("Sorry no coupon available now")

async def start_free_trial_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    text:str = Update.message.text
    users = storage.search("User", chat_id=chat_id)
    print(f"User ({chat_id}): {text}")
    if len(users) > 0:
        user = users[0]
        trial_created_at = None
        if getattr(user, "free_trial") == "active":
            await Update.message.reply_text("You are actively using free trial!")
            return
        if hasattr(user, 'free_trial_started'):
            free_trial_created_at = user.free_trial_started
            trial_created_at = datetime.strptime(free_trial_created_at, time) + timedelta(days=7)
        if trial_created_at and datetime.now() > trial_created_at:
            setattr(user, "free_trial", "used")
            user.save()
            await Update.message.reply_text("You have already used your free trial, Please subscribe!")
        else:
            setattr(user, "free_trial", "active")
            trial_created_at = datetime.now()
            trial_created_at = datetime.strftime(trial_created_at, time)
            setattr(user, 'free_trial_started', trial_created_at)
            user.save()
            text = f"Well-done on signing up for free trial. You will now receive arbitrage signal for the next 7 days for free.\n\n"
            text = "Please send your planned capital so you can receive arbitrage opportunities that fall within your capital."
            text += " Remember, the higher your capital, the more opportunities will come your way\n\n"
            text += "Use the format below to send your required capital.\ncapital - 100\n Replace '100' with your planned capital"
            await Update.message.reply_text(text)
    else:
        await Update.message.reply_text("You are not registered. Register first to use free trial")

async def recover_account_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text:str = Update.message.text
    chat_id = Update.message.chat.id
    print(f"User ({chat_id}): {text}")
    response = "To recover your account, please enter your recovery key below. Use the format:\n\n"
    response += "\"recovery key - <recovery key>\"\n\n"
    response += "Replace \"<recovery key>\" with your actual recovery key\n"
    response += "eg. \"recovery key - 1234567890\""
    await Update.message.reply_text(response)

async def edit_capital_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    text:str = Update.message.text
    user = storage.search("User", chat_id=chat_id)
    print(f"User ({chat_id}): {text}")
    if not user:
        await Update.message.reply_text("You have to register an account first")
    else:
        ret = "Send in your planned capital using the format below:\n\n"
        ret += "\"capital - 500\"\n\n"
        ret += "Minimum starting capital is 500"
        await Update.message.reply_text(ret)


# Responses
async def handle_response(text:str, chat_id) -> str:
    text = text.lower()
    text = text.strip()
    user = storage.search("User", chat_id=chat_id)
    if len(user) > 0:
        user = user[0]
    else:
        user = None
    if "help" in text:
        response = "Here is a list of all the available commands:\n\n"
        response += "/start - Starts xploit bot\n"
        response += "/recover_account - Recover your account on another telegram account\n"
        response += "/register - Create a new account\n"
        response += "/setup_exchanges - Add your api keys to the bot\n"
        response += "/start_free_trial - Start free trial for 24 hours\n"
        response += "/subscribe - Subscribe to continue receiving trade reports"
        return response
    elif "username" in text:
        adapter.info("Using username")
        users = storage.search("User", chat_id=chat_id)
        if len(users) > 0:
            return "You already have an account! Multiple accounts not supported"
        username = text.split("-")
        if len(username) < 2:
            return "Please use the correct format\nUsername - johnDoe"
        username = username[1].strip()
        existing_names = storage.search("User", username=username)
        if len(existing_names) > 0:
            return "Sorry username is already taken, please select another"
        user = User(username=username, chat_id=chat_id)
        user.save()
        ret_str = f"Your account has been created. Here's a recovery key for you: {user.id}, \n"
        ret_str += "please keep it safe and private. You can use it to recover your account if your lose it"
        return ret_str
    elif "recovery key" in text:
        key = text.split("-")[1].strip()
        user = storage.get("User", key)
        if user:
            setattr(user, "chat_id", chat_id)
            user.save()
            return f"Welcome back {user.username} Your account has now been linked to this telegram account"
        else:
            return "Sorry, no user linked with this recovery key"
    elif "capital" in text:
        if not user:
            return "Please register an account first"
        capital = text.split("-")
        if len(capital) < 2:
            return "please enter your capital in the format: capital - 100"
        capital = capital[1]
        try:
            capital = float(capital)
        except ValueError:
            return "Capital must be a number or decimal"
        if capital < 500:
            return "Capital must be a greater than 500"
        setattr(user, "min_cap", capital)
        user.save()
        return f"Setup complete, you will now receive arbitrage opportunities with at most {capital} USDT of starting capital"
    elif "txid" in text:
        txid = text.split("-")
        if len(txid) < 2:
            return "Please use the correct format: \"txid - 0x123example\""
        txid = txid[1]
        await notify_admin(txid)
        return "Please hold on while we verify. This usually takes a few minutes"
    elif "recieved 100usdt" in text:
        if user.id not in ['41c68165-929c-46c2-baee-d936b5d1714f']:
            return "Sorry I do not understand your command, send \"help\" for a list of all available commands"
        txts = text.split()
        txid = txts[-2]
        # admin_id = txts[-1]
        usr = storage.search("User", txid=txid)
        if not usr:
            return "There was an error, confirm the text you're sending is accurate"
        else:
            setattr(usr, "subscribed", True)
            usr.save()
            send_message(usr.chat_id, "Your payment has been confirmed and you will now recieve arbitrage signals")
            return "Alright, the user has been notified"
    else:
        if text == f"admin start {handleEnv('admin_key')}":
            bot_thread = threading.Thread(target=bot_handler)
            bot_thread.start()
            return "Welcome Dennis, you have started the bot"
        else:
            ret_str = "Sorry I do not understand your command. Send /help to view a list of all available commands"
            return ret_str


# send reports
async def send_message(chat_id:int, text:str):
    app = Application.builder().token(BOT_TOKEN).build()
    await app.bot.send_message(chat_id, text)

async def send_report(opp:Dict):
    adapter.info("Sending result...")
    users_profit = fetch_eligible_users(opp)
    messages = {}
    for user_chat_id, profit in users_profit.items():
        result_string = f"Symbol      - {opp['coin']}\n"
        result_string += f"Capital     - {profit[1]} USDT\n"
        result_string += f"Buy on      - {opp['buy_exchange']}\n"
        result_string += f"Buy price   - {opp['buy_price']} or current market price\n"
        if "withdraw_network" in opp:
            result_string += f"Withdraw network - {opp['withdraw_network']}\n"
        result_string += f"Sell on     - {opp['sell_exchange']}\n"
        result_string += f"sell price  - {opp['sell_price']} or current market price\n"
        txt = result_string + f"\nProfit rate  - {profit[0]:.2f}%"
        if profit[0] >= 5:
            messages[user_chat_id] = txt
        else:
            adapter.info(f"Could not send {txt} cause of low profit")

    tasks = [send_message(chat_id, messages[chat_id]) for chat_id in messages]
    await asyncio.gather(*tasks)
    adapter.info(f"{txt} \nsent to {users_profit}")

async def notify_admin(txid:str):
    admin_id = "41c68165-929c-46c2-baee-d936b5d1714f"
    admin = storage.get("User", admin_id)
    if not admin:
        return
    txt = f"A user has sent 100 USDT to your wallet. The transaction id is {txid}\n\n"
    txt += "Wait for 5 minutes if you haven't received it to make sure it is not a delay in network\n\n"
    txt += "If you have confirmed the payment, copy and paste the following text followed by a space and your admin key\n"
    txt += f"\"Received 100USDT from {txid} ((your admin key here))\"\n"
    txt += "eg. \"Received 100USDT from 0x123example789 123youradminkey789\n\n"
    txt += "/Not_received"
    await send_message(admin.chat_id, txt)


# Messages
async def handle_message(update: Update, context:ContextTypes.DEFAULT_TYPE):
    message_type:str = update.message.chat.type
    text:str = update.message.text
    chat_id = update.message.chat.id

    print(f"User ({chat_id}) in {message_type}: \"{text}\"")
    response = await handle_response(text, chat_id)
    print("Bot:", response)
    await update.message.reply_text(response)


# Error
async def error(update: Update, context:ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error: {context.error}')


def start_telegram():
    print("Starting bot ...")
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('register', register_command))
    app.add_handler(CommandHandler('start_free_trial', start_free_trial_command))
    app.add_handler(CommandHandler('recover_account', recover_account_command))
    app.add_handler(CommandHandler('subscribe', subscribe_command))
    app.add_handler(CommandHandler("edit_capital", edit_capital_command))
    app.add_handler(CommandHandler("continue_with_payment", continue_with_payment_command))
    app.add_handler(CommandHandler("use_coupon", use_coupon_command))
    app.add_handler(CommandHandler("verify_payment", verify_payment_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print("Polling ...")
    app.run_polling(poll_interval=3)
    global exit_signal
    exit_signal.set()
    print("Telegram bot stopped")

def bot_handler():
    from trading_bot import main
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(500, exchange_list=None, fetch_once=False))

if __name__ == '__main__':
    # telegram_thread = threading.Thread(target=start_telegram)
    bot_thread = threading.Thread(target=bot_handler)
    bot_thread.start()
    start_telegram()

    # telegram_thread.join()
    bot_thread.join()
