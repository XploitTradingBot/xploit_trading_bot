from dotenv import load_dotenv
from helper import handleEnv
from utils.fetch_data import run
import telebot
from datetime import datetime, timedelta
from model import storage
from model.user import User

load_dotenv()

teleBot = telebot.TeleBot(handleEnv("BOT_TOKEN"))
time = "%Y-%m-%d %H:%M:%S"


@teleBot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    users = storage.search("User", chat_id=chat_id)
    if len(users) > 0:
        teleBot.reply_to(
            message, f"""Welcome back {users[0].first_name}.\nChoose an option:\n1. /viewUpcomingTokens
            \n2. /startBot\n2. /viewprevtrades""")
    else:
        sent_msg = teleBot.reply_to(message, f"""Welcome to Xploit trading bot,
                                     please enter your email""")
        teleBot.register_next_step_handler(sent_msg, create_account)

def create_account(message):
    email = message.text
    if "@" not in email:
        teleBot.reply_to(message, """You have entered an invalid format for email. 
                         Please include \"@\" in the email""")
    else:
        name = f"{message.from_user.first_name} {message.from_user.last_name}"
        user = User(name=name, email=email, chat_id=message.chat.id)
        user.save()
        sent_msg = teleBot.reply_to(message, "You have been registered")
        send_welcome(sent_msg)

@teleBot.message_handler(commands=['viewUpcomingTokens'])
def view_new_tokens(message):
    coins = storage.all("Coin")
    new_coin = []
    for coin in coins.values():
        listing_date = datetime.strptime(coin.listing_date, time)
        if datetime.now() > (listing_date - timedelta(hours=1)):
            coin.delete()
        else:
            new_coin.append(coin.to_dict())
    ret = ""
    for coin in new_coin:
        ret += f"{coin.symbol} ---- {coin.listing_date}"
    teleBot.reply_to(message, ret)

@teleBot.send_handler(commands=['viewprevtrades'])
def send_trade_report(message:str, chat_id):
    teleBot.send_message(chat_id, message, parse_mode="Markdown")


if __name__ == '__main__':
    send_trade_report("Hello trader", id)