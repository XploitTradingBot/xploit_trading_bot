#!/usr/bin/python3

import time
import asyncio
import threading
from utils.logging import adapter
from utils.helper import handleEnv
from typing import Final, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from model import storage
from model.user import User
from utils.user_handler import fetch_eligible_users, check_user_subscribe_status, send_sms
from datetime import datetime, timedelta
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler


BOT_TOKEN: Final = handleEnv("BOT_TOKEN")
BOT_USERNAME: Final = "@Xploit_trading_bot"
timefmt = "%Y-%m-%d %H:%M:%S"

exit_signal = threading.Event()
STATES = {}
admin_key = handleEnv("admin_key")
subscription_fee = 50


# Commands
async def register_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text:str = Update.message.text
    chat_id = Update.message.chat.id
    print(f"User ({chat_id}): {text}")
    users = storage.search("User", chat_id=chat_id)
    if len(users) > 0:
        await Update.message.reply_text("You are already a registered user")
    else:
        STATES[chat_id] = "USERNAME"
        await Update.message.reply_text("Please enter your username...")

async def subscribe_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    txt = f"Welcome, subscription for this service cost {subscription_fee} USDT per month\n"
    txt += "/continue_with_payment\n"
    txt += "/use_coupon"
    chat_id = Update.message.chat.id
    user = storage.search("User", chat_id=chat_id)
    if not user:
        await Update.message.reply_text("You have to register an account first before you can subscribe")
    else:
        user = user[0]
        subscribed = check_user_subscribe_status(user)
        if subscribed:
            await Update.message.reply_text("You have already subscribed for this service")
        else:
            await Update.message.reply_text(txt)

async def continue_with_payment_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    txt = f"Please complete your payment by sending {subscription_fee} USDT to any of the following addresses\n\n"
    txt += "0x4a25bf5ffb9083d894faca43e29407a6c99f03dd\n"
    txt += "BEP20\n\n"
    txt += "TKUzV9HpakiNdMrFC7164Nb67XGvFYS6AA\n"
    txt += "TRC20\n\n"
    txt += "Click here after sending your payment /verify_payment"
    await Update.message.reply_text(txt)

async def verify_payment_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    txt = "Please send the transaction id (txid) of the transaction"
    STATES[chat_id] = "VERIFY_PAYMENT"
    await Update.message.reply_text(txt)

async def use_coupon_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    STATES[chat_id] = "COUPON_CODE"
    await Update.message.reply_text("Enter your coupon code...")

async def start_free_trial_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    text:str = Update.message.text
    users = storage.search("User", chat_id=chat_id)
    print(f"User ({chat_id}): {text}")
    if len(users) > 0:
        user = users[0]
        trial_created_at = None
        subscribed = check_user_subscribe_status(user)
        if subscribed:
            await Update.message.reply_text("You have already subscribed for this service")
            return
        if getattr(user, "free_trial") == "active":
            await Update.message.reply_text("You are already using free trial!")
            return
        if hasattr(user, 'free_trial_started'):
            free_trial_created_at = user.free_trial_started
            trial_created_at = datetime.strptime(free_trial_created_at, timefmt) + timedelta(days=7)
        if trial_created_at and datetime.now() > trial_created_at:
            setattr(user, "free_trial", "used")
            user.save()
            await Update.message.reply_text("You have already used your free trial, Please subscribe!")
        else:
            setattr(user, "free_trial", "active")
            trial_created_at = datetime.now()
            trial_created_at = datetime.strftime(trial_created_at, timefmt)
            setattr(user, 'free_trial_started', trial_created_at)
            user.save()
            text = f"Well-done {user.username} on signing up for free trial. You will now receive arbitrage signal for the next 7 days for free.\n\n"
            text += "To receive sms notification for when new arbitrage opportunities become available, enter your phone number. "
            text += "Phone numbers must be in international format eg \"2348012345678\".\n\n"
            text += "Ignore this if you do not want to receive sms and proceed to /edit_capital"
            STATES[chat_id] = "PHONE_NO"
            await Update.message.reply_text(text)
    else:
        await Update.message.reply_text("You are not registered. Register first to use free trial")

async def recover_account_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    text:str = Update.message.text
    chat_id = Update.message.chat.id
    print(f"User ({chat_id}): {text}")
    STATES[chat_id] = "RECOVERY_KEY"
    response = "To recover your account, please enter your recovery key"
    await Update.message.reply_text(response)

async def edit_capital_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    text:str = Update.message.text
    user = storage.search("User", chat_id=chat_id)
    print(f"User ({chat_id}): {text}")
    if not user:
        await Update.message.reply_text("You have to register an account first")
    else:
        ret = "Send in your planned capital. "
        ret += "Minimum starting capital is 500"
        STATES[chat_id] = "CAPITAL"
        await Update.message.reply_text(ret)

async def not_received_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    await Update.message.reply_text("Thank you for your response. The user has been notified")
    # pass

async def verify_coupon_payment_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    txt = "Please send the transaction id (txid) of the transaction"
    STATES[chat_id] = "VERIFY_COUPON_PAYMENT"
    await Update.message.reply_text(txt)

async def button_press_handler(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    query = Update.callback_query
    chat_id = query.message.chat_id
    data = query.data
    message_id = query.message.message_id

    status, txid = data.split("_")
    user = storage.search("User", txid=txid)
    user = user[0]
    if status == 'received':
        setattr(user, "subscribed", True)
        current_datetime = datetime.now()
        str_datetime = current_datetime.strftime(timefmt)
        setattr(user, "subscribed_date", str_datetime)
        user.save()
        await send_message(user.chat_id, "Your payment has been confirmed. You are now a subscribed user")
        await notify_admin(f"You have successfully confirmed the payment of txid {txid}")
    elif status == 'notreceived':
        text = "Your payment has been declined. If you think this is an error, send us an sms or whatsapp message on 09035362750"
        await send_message(user.chat_id, text)
        await notify_admin(f"You have declined the payment of {txid}")
    await context.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)

async def edit_phone_number_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat.id
    txt = "Enter your mobile number below. Make sure the number is in the international format\n"
    txt += "eg. 2348011112222"
    STATES[chat_id] = "PHONE_NO"
    await Update.message.reply_text(txt)

async def edit_minimum_profit_percent_command(Update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = Update.message.chat_id
    STATES[chat_id] = "SET_MIN_PROFIT"
    await Update.message.reply_text("Enter your prefered minimum profit percent")


# Responses
async def handle_response(orig_text:str, chat_id) -> str:
    text = orig_text.lower()
    text = text.strip()
    orig_text = orig_text.strip()
    user = storage.search("User", chat_id=chat_id)
    if len(user) > 0:
        user = user[0]
    else:
        user = None

    if "help" in text:
        response = "Here is a list of all the available commands:\n\n"
        response += "/edit_capital - Set your capital to receive signals according to your budget\n"
        response += "/edit_phone_number - Edit your mobile number to receive sms notification\n"
        response += "/recover_account - Recover your account on another telegram account\n"
        response += "/register - Create a new account\n"
        response += "/start_free_trial - Start free trial for 24 hours\n"
        response += "/subscribe - Subscribe to continue receiving trade reports"
        return response
    if chat_id in STATES:
        if STATES[chat_id] == "USERNAME":
            users = storage.search("User", chat_id=chat_id)
            if len(users) > 0:
                return "You already have an account! Multiple accounts not allowed"
            username = orig_text.strip()
            existing_names = storage.search("User", username=username)
            if len(existing_names) > 0:
                return "Sorry username is already taken, please select another"
            user = User(username=username, chat_id=chat_id)
            user.save()
            response = f"Welcome {username} your account has been created. Here's a recovery key for you: {user.id}, \n"
            response += "please keep it safe and private. You can use it to recover your account if your lose it\n\n"
            del STATES[chat_id]
            # return response
        elif STATES[chat_id] == "VERIFY_PAYMENT":
            txid = orig_text
            txt = f"A user has sent {subscription_fee} USDT to your wallet. Confirm the payment with txid:\n\n{txid}\n\n"
            txt += "Wait for 5 minutes if you haven't received it to make sure it is not a delay in network\n\n"
            await notify_admin(txt, txid, "verify")
            setattr(user, "txid", orig_text)
            user.save()
            response = "Please hold on while we verify. This usually takes a few minutes"
            del STATES[chat_id]
            # return response
        elif STATES[chat_id] == "VERIFY_COUPON_PAYMENT":
            txt = f"A user just activated a 50% coupon. Confirm the payment of {subscription_fee * 0.5} USDT with txid:\n\n{orig_text}\n\n"
            txt += "Wait for 5 minutes if you haven't received it to make sure it is not a delay in network\n\n"
            await notify_admin(txt, orig_text, "verify")
            setattr(user, "txid", orig_text)
            user.save()
            response = "Please hold on while we verify your payment, this usually takes a few minutes"
            del STATES[chat_id]
            # return response
        elif STATES[chat_id] == "COUPON_CODE":
            if orig_text == "XXPLOIT":
                await coupon_payment(user.chat_id)
                response = f"You have activated a 50% coupon code. Your subscription fee is {subscription_fee * 0.5} USDT"
            elif orig_text == "XXPLOITT":
                await notify_admin(f"User {chat_id} just activated a 100% coupon")
                setattr(user, "subscribed", True)
                current_datetime = datetime.now()
                str_datetime = current_datetime.strftime(timefmt)
                setattr(user, "subscribed_date", str_datetime)
                user.save()
                response = "Congratulations! You have activated a 100% coupon code. You are now a subscribed user"
                del STATES[chat_id]
            else:
                response = "You have entered an invalid/expired code"
            # return response
        elif STATES[chat_id] == "PHONE_NO":
            phone_no = orig_text
            if not phone_no.startswith("234"):
                response = "Please use the correct format, example: 2348012121212"
            else:
                setattr(user, "phone_no", phone_no)
                user.save()
                response = "Your phone number has been recorded, you will receive sms notifications when new signals become available\n\n"
                response += "To conclude your registration, Enter your intended capital below"
                STATES[chat_id] = "CAPITAL"
        elif STATES[chat_id] == "CAPITAL":
            capital = orig_text
            try:
                capital = float(capital)
                if capital < 500:
                    response = "Capital must be greater than 500"
                else:
                    setattr(user, "min_cap", capital)
                    user.save()
                    response = f"Setup complete, you will now receive arbitrage opportunities with {capital} USDT of starting capital\n\n"
                    del STATES[chat_id]
            except ValueError:
                response = "Capital must be a number or decimal"
            # return response
        elif STATES[chat_id] == "RECOVERY_KEY":
            key = orig_text
            user = storage.get("User", key)
            if user:
                setattr(user, "chat_id", chat_id)
                user.save()
                response = f"Welcome back {user.username} Your account has now been linked to this telegram account"
                del STATES[chat_id]
            else:
                response = "No user linked with this recovery key"
            # return response
        elif STATES[chat_id] == "SET_MIN_PROFIT":
            profit_percent = orig_text
            try:
                profit_percent = float(profit_percent)
                if profit_percent >= 100 or profit_percent <= 0:
                    response = "Please select a number between 0 and 100"
                else:
                    setattr(user, "min_profit_percent", profit_percent)
                    user.save()
                    del STATES[chat_id]
                    response = "Thank you, your input has been saved"
            except Exception:
                response = "Please use a number as your profit percent"
        else:
            response = "I do not understand your command. send \"help\" for a list of all available commands"
            if chat_id == 1209605960:
                if orig_text == "admin start":
                    from main import start_arbitrage_bot, bot_exit_signal
                    asyncio.run(start_arbitrage_bot(bot_exit_signal))
                    return "You have successfully started the arbitrage bot"
        return response
    else:
        if chat_id == 1209605960:
            if orig_text == "admin start":
                from main import start_arbitrage_bot, bot_exit_signal
                asyncio.run(start_arbitrage_bot(bot_exit_signal))
                return "You have successfully started the arbitrage bot"
        return "I do not understand your command, send \"help\" to view a list of all available commands"


# send messages
async def send_message(chat_id:int, text:str, reply_markup=None):
    app = Application.builder().token(BOT_TOKEN).build()
    message_id = await app.bot.send_message(chat_id, text, reply_markup=reply_markup)
    return message_id

async def send_report(opp:Dict):
    users_profit = fetch_eligible_users(opp)
    messages = {}
    recieved_users = []
    for user_id, profit in users_profit.items():
        user = storage.get("User", user_id)
        result_string = f"Symbol      - {opp['coin']}\n"
        result_string += f"Capital     - {profit[1]} USDT\n"
        result_string += f"Buy on      - {opp['buy_exchange']}\n"
        result_string += f"Buy price   - {opp['buy_price']} or current market price\n"
        if "withdraw_network" in opp:
            result_string += f"Withdraw network - {opp['withdraw_network']}\n"
        result_string += f"Sell on     - {opp['sell_exchange']}\n"
        result_string += f"sell price  - {opp['sell_price']} or current market price\n"
        txt = result_string + f"\nProfit rate  - {profit[0]:.2f}%"
        if profit[0] >= user.min_profit_percent:
            messages[user.chat_id] = txt
            adapter.info(f"Result {txt} sent to {user.username}")
            user = storage.search("User", chat_id=user.chat_id)
            user = user[0]
            if hasattr(user, "phone_no"):
                recieved_users.append(user.phone_no)
        else:
            adapter.info(f"Could not send {opp['coin']} to {user.username} cause of low profit ({profit[0]:.2f}%)")

    tasks = [send_message(chat_id, messages[chat_id]) for chat_id in messages]
    await asyncio.gather(*tasks)
    # send_sms(recieved_users, "Hurry now, a new arbitrage opportunity is now available at Xploit cybernetics")
    # adapter.info(f"{txt} \nsent to {users_profit}")

async def notify_admin(txt:str, txid:str=None, message_type:str=None):
    """This sends a message to the admin
    Args:
        txt: The content of the message
        txid: txid. Must be passed if message_type is provided
        message_type: The category of the message"""
    admin = storage.get("User", admin_key)
    admin_chat_id = admin.chat_id
    if message_type == "verify":
        # Create buttons
        received_button = InlineKeyboardButton("Received", callback_data=f"received_{txid}")
        not_received_button = InlineKeyboardButton("Not Received", callback_data=f"notreceived_{txid}")
        reply_markup = InlineKeyboardMarkup([[received_button, not_received_button]])
        return await send_message(admin_chat_id, txt, reply_markup)
    return await send_message(admin_chat_id, txt)


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


async def coupon_payment(chat_id):
    txt = f"Please complete your payment by sending {subscription_fee * 0.5} USDT to any of the following addresses\n\n"
    txt += "0x4a25bf5ffb9083d894faca43e29407a6c99f03dd\n"
    txt += "BEP20\n\n"
    txt += "TKUzV9HpakiNdMrFC7164Nb67XGvFYS6AA\n"
    txt += "TRC20\n\n"
    txt += "Click here after sending your payment /verify_coupon_payment"
    await send_message(chat_id, txt)


def start_telegram():
    print("Starting bot ...")
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    # app.add_handler(CommandHandler('start', start_command))
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

    app.add_handler(CallbackQueryHandler(button_press_handler))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print("Polling ...")
    app.run_polling(poll_interval=3)
    print("Telegram bot stopped")

def bot_handler():
    from trading_bot import main
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(500, exchange_list=None, fetch_once=False))


def my_thread():
    # while not event.is_set():
    #     print("Thread is active...")
    #     time.sleep(2)

    # print("Thread received exit signal and is terminating.")
    from main import bot_exit_signal
    bot_exit_signal.set()



if __name__ == '__main__':
    # telegram_thread = threading.Thread(target=start_telegram)
    # bot_thread = threading.Thread(target=bot_handler)
    # bot_thread.start()
    start_telegram()

    # telegram_thread.join()
    # bot_thread.join()
    
    # my_thread()
    # exit_event = threading.Event()
    # my_thread_thread = threading.Thread(target=my_thread)
    # my_thread_thread.start()
    # time.sleep(5)
    # exit_event.set()
    # my_thread_thread.join()

    print("Main program completed.")
