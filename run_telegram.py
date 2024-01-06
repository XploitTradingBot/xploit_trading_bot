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


# Commands
async def start_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text:str = Update.message.text
    chat_id = Update.message.chat.id
    user = storage.search("User", chat_id=chat_id)
    if len(user) > 0:
        name = user[0].username
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
        await Update.message.reply_text("Please enter your username in the format: \"Username - {username}\". eg Username - xploit")

async def subscribe_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    await Update.message.reply_text("This feature is not yet available. Please check back some other time")
    pass

async def start_free_trial_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    users = storage.search("User", chat_id=chat_id)
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
    response = "To recover your account, please enter your recovery key below. Use the format:\n"
    response += "recovery key - <recovery key>\n"
    response += "Replace \"<recovery key>\" with your actual recovery key"
    response += "eg. \"recovery key - 1234567890\""
    await Update.message.reply_text(response)

async def setup_exchanges_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Select an exchange to set up.\n"
    for exchange in ['binance', 'bingx', 'bitget', 'bitmart', 'bitmex', 'bybit',
                     'gate', 'huobi', 'mexc', 'okx']:
        text += f"/{exchange}\n"
    await Update.message.reply_text(text)

async def edit_capital(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    user = storage.search("User", chat_id=chat_id)
    if not user:
        await Update.message.reply_text("You have to register an account first")
    else:
        ret = "Send in your planned capital using the format below:\n\n"
        ret += "\"capital - 100\""
        await Update.message.reply_text(ret)


# Exchange setup
async def binance_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your binance API key and secret key seperated by a comma as in the format below:\n"
    text += "\"binance - apiKeyExample, secretKeyExample\""
    await Update.message.reply_text(text)

async def bingx_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your bingx API key and secret key seperated by a comma as in the format below:\n"
    text += "\"bingx - apiKeyExample, secretExample\""
    await Update.message.reply_text(text)

async def bitget_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your bitget API key, secret key and password seperated by a comma as in the format below:\n"
    text += "\"bitget - apiKeyExample, secretKeyExample, passwordExample\""
    await Update.message.reply_text(text)

async def bitmart_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your bitmart API key, secret key and uid seperated by a comma as in the format below:\n"
    text += "\"bitmart - apiKeyExample, secretKeyExample, uidExample\""
    await Update.message.reply_text(text)

async def bitmex_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your bitmex API key and secret key seperated by a comma as in the format below:\n"
    text += "\"bitmex - apiKeyExample, secretKeyExample\""
    await Update.message.reply_text(text)

async def bybit_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your bybit API key and secret key seperated by a comma as in the format below:\n"
    text += "\"bybit - apiKeyExample, secretKeyExample\""
    await Update.message.reply_text(text)

async def gate_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your gate.io API key and secret key seperated by a comma as in the format below:\n"
    text += "\"gate.io - apiKeyExample, secretKeyExample\""
    await Update.message.reply_text(text)

async def huobi_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your huobi API key and secret key seperated by a comma as in the format below:\n"
    text += "\"huobi - apiKeyExample, secretKeyExample\""
    await Update.message.reply_text(text)

async def mexc_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your mexc API key and secret key seperated by a comma as in the format below:\n"
    text += "\"mexc - apiKeyExample, secretKeyExample\""
    await Update.message.reply_text(text)

async def okx_setup(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "Send your okx API key, secret key and password seperated by a comma as in the format below:\n"
    text += "\"okx - apiKeyExample, secretKeyExample, PasswordExample\""
    await Update.message.reply_text(text)


# Responses
def handle_response(text:str, chat_id) -> str:
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
        if capital < 100:
            return "Capital must be a greater than 100"
        setattr(user, "min_cap", capital)
        user.save()
        return f"Congratulations, you will now receive arbitrage opportunities with at least {capital} of starting capital"
    elif "binance" in text:
        if not user:
            return "Please register "
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(new_keys) < 2:
            return "Please enter both your api key and secret key seperated by a comma"
        keys:Dict[str, str] = user.keys
        keys['binance_apiKey'] = new_keys[0].strip()
        keys['binance_secret'] = new_keys[1].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Binance keys successfully set!"
    elif "bingx" in text:
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(new_keys) < 2:
            return "Please enter both your api key and secret key seperated by a comma"
        keys:Dict = user.keys
        keys['bingx_apiKey'] = new_keys[0].strip()
        keys['bingx_secret'] = new_keys[1].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Bingx keys successfully set!"
    elif "bitget" in text:
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(new_keys) < 3:
            return "Please enter your api key, secret key and password seperated by comma"
        keys:Dict = user.keys
        keys['bitget_apiKey'] = new_keys[0].strip()
        keys['bitget_secret'] = new_keys[1].strip()
        keys['bitget_password'] = new_keys[2].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Bitget keys successfully set!"
    elif "bitmart" in text:
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(new_keys) < 3:
            return "Please enter your api key, secret key and uid seperated by a comma"
        keys:Dict = user.keys
        keys['bitmart_apiKey'] = new_keys[0].strip()
        keys['bitmart_secret'] = new_keys[1].strip()
        keys['bitmart_uid'] = new_keys[2].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Bitmart keys successfully set!"
    elif "bitmex" in text:
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(new_keys) < 2:
            return "Please enter both your api key and secret key seperated by a comma"
        keys:Dict[str, str] = user.keys
        keys['bitmex_apiKey'] = new_keys[0].strip()
        keys['bitmex_secret'] = new_keys[1].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Bitmex keys successfully set!"
    elif "bybit" in text:
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(new_keys) < 2:
            return "Please enter both your api key and secret key seperated by a comma"
        keys:Dict[str, str] = user.keys
        keys['bybit_apiKey'] = new_keys[0].strip()
        keys['bybit_secret'] = new_keys[1].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Bybit keys successfully set!"
    elif "gate" in text:
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(new_keys) < 2:
            return "Please enter both your api key and secret key seperated by a comma"
        keys:Dict[str, str] = user.keys
        keys['gate_apiKey'] = new_keys[0].strip()
        keys['gate_secret'] = new_keys[1].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Gate keys successfully set!"
    elif "huobi" in text:
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(new_keys) < 2:
            return "Please enter both your api key and secret key seperated by a comma"
        keys:Dict[str, str] = user.keys
        keys['huobi_apiKey'] = new_keys[0].strip()
        keys['huobi_secret'] = new_keys[1].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Huobi keys successfully set!"
    elif "mexc" in text:
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(keys) < 2:
            return "Please enter both your api key and secret key seperated by a comma"
        keys:Dict[str, str] = user.keys
        keys['mexc_apiKey'] = new_keys[0].strip()
        keys['mexc_secret'] = new_keys[1].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Mexc keys successfully set!"
    elif "okx" in text:
        inp = text.split("-")[1]
        new_keys = inp.split(",")
        if len(new_keys) < 3:
            return "Please enter both your api key, secret key and password seperated by comma"
        keys:Dict[str, str] = user.keys
        keys['okx_apiKey'] = new_keys[0].strip()
        keys['okx_secret'] = new_keys[1].strip()
        keys['okx_password'] = new_keys[2].strip()
        setattr(user, "keys", keys)
        user.save()
        return "Okx keys successfully set!"
    else:
        if text == f"admin start {handleEnv('admin_key')}":
            from trading_bot import main
            bot_thread = threading.Thread(target=main, args=(100, None, False))
            bot_thread.start()
            # main(100, exchange_list=None, fetch_once=False)
            return "Welcome Dennis, you have started the bot"
        else:
            ret_str = "Sorry I do not understand your command. Send /help to view a list of all available commands"
            return ret_str


# send reports
async def send_trade_report(chat_id, text:str):
    app = Application.builder().token(BOT_TOKEN).build()
    await app.bot.send_message(chat_id, text)

async def send_report(text:str, min_capital:float):
    adapter.info("Sending result...")
    eligible_users = fetch_eligible_users(min_capital)
        
    tasks = [send_trade_report(chat_id, text) for chat_id in eligible_users]
    await asyncio.gather(*tasks)
    adapter.info(f"{text} \nsent to {eligible_users}")
    

# Messages
async def handle_message(update: Update, context:ContextTypes.DEFAULT_TYPE):
    message_type:str = update.message.chat.type
    text:str = update.message.text
    chat_id = update.message.chat.id

    print(f"User ({chat_id}) in {message_type}: \"{text}\"")
    response = handle_response(text, chat_id)
    print("Bot:", response)
    await update.message.reply_text(response)


# Error
async def error(update: Update, context:ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error: {context.error}')


def main():
    print("Starting bot ...")
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('register', register_command))
    app.add_handler(CommandHandler('start_free_trial', start_free_trial_command))
    app.add_handler(CommandHandler('recover_account', recover_account_command))
    app.add_handler(CommandHandler('setup_exchanges', setup_exchanges_command))
    app.add_handler(CommandHandler('subscribe', subscribe_command))
    app.add_handler(CommandHandler("edit_capital", edit_capital))

    # Setups
    app.add_handler(CommandHandler('binance', binance_setup))
    app.add_handler(CommandHandler('bingx', bingx_setup))
    app.add_handler(CommandHandler('bitget', bitget_setup))
    app.add_handler(CommandHandler('bitmex', bitmex_setup))
    app.add_handler(CommandHandler('bitmart', bitmart_setup))
    app.add_handler(CommandHandler('bybit', bybit_setup))
    app.add_handler(CommandHandler('huobi', huobi_setup))
    app.add_handler(CommandHandler('gate', gate_setup))
    app.add_handler(CommandHandler('mexc', mexc_setup))
    app.add_handler(CommandHandler('okx', okx_setup))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print("Polling ...")
    app.run_polling(poll_interval=3)
    print("Code reaches here")

if __name__ == '__main__':
    main()
