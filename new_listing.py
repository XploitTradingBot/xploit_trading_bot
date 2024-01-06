#!/usr/bin/python3

import ccxt
import pytz
import time
import uuid
# import asyncio
from datetime import datetime, timedelta
from model import storage


class Executor():
    stopFlag = False
    tz = pytz.timezone("Africa/Lagos")
    time = "%Y-%m-%d %H:%M:%S"
    max_retries = 20

    def __init__(self, *args, **kwargs):
        self.id = str(uuid.uuid4())
        print(f"Created executor id: {self.id}")
        if "bot" not in kwargs:
            raise ValueError("Please include the bot instance")

        bot = kwargs['bot']
        if isinstance(bot, str):
            bot = storage.get("Bot", bot)
        self.bot = bot
        self.bot.active = True
        self.bot.save()
        if "capital" not in kwargs:
            raise ValueError("Please enter a valid capital")
        try:
            self.balance = float(kwargs['capital'])
        except ValueError:
            raise ValueError("Please enter a valid number as capital")

        exchange = kwargs['exchange']
        if isinstance(exchange, str):
            exchange = getattr(ccxt, exchange)
            setattr(exchange, "apiKey", kwargs.get("exchange_apiKey", None))
            setattr(exchange, "secret", kwargs.get("exchange_secret", None))
        self.exchange = exchange
        self.exchange.load_markets()
        try:
            bal = self.exchange.fetchBalance()['free']
        except Exception as e:
            raise ValueError("Could not check your wallet balance, please ensure your keys are correct")
        bal = bal.get("USDT", 0)
        if bal < self.balance:
            text = f"Insufficient balance. Available balance: {bal}"
            print(text)
            self.add_message(text)
            self.stop_bot()

    async def wait_and_buy(self)->None:
        coins = storage.all("Coin")
        coins = dict(sorted(coins.items(), key=lambda x: x[1].listing_date))
        coins = list(coins.values())
        for co in coins:
            if co.exchange == self.exchange.id:
                token = co
                break
        coin = token.symbol
        start_time = token.listing_date
        start_time = datetime.strptime(start_time, self.time)
        text = f"Waiting for {coin} listing at {start_time}."
        print(text)
        self.add_message(text)
        print(f"Current time is {datetime.now()}")
        self.exchange.options['createMarketBuyOrderRequiresPrice'] = False
        start_time = start_time - timedelta(seconds=3.0) - timedelta(hours=1)
        print(f"Trading starts at {start_time}")
        n = 0

        while self.stopFlag is False:
            if datetime.now() >= start_time:
                order = None
                # place a buy order
                for i in range(self.max_retries):
                    try:
                        order = self.exchange.createMarketOrder(coin, "buy", self.balance)
                        print(f"#{i} Order placed: {order}")
                        break
                    except Exception as e:
                        print(f"Error obtained while placing buy order: {e}")
                        time.sleep(0.5)
                        if i == self.max_retries - 1:
                            text = f"Max retries reached. Unable to place buy order: {e}"
                            text += "\n--------------------------\n"
                            print(text)
                            self.add_message(text)
                            try:
                                token.delete()
                            except:
                                pass
                            return
                # monitor the placed buy order
                try:
                    buy_price = None
                    for _ in range(self.max_retries):
                        try:
                            order = self.exchange.fetchOrder(order['id'], coin)
                        except Exception as e:
                            text = f"Could not monitor placed buy order: {e}"
                            print(text)
                            continue
                        print(f"Fetched orders: {order}")
                        if order:
                            status = order['status']
                            if order['id'] != order['id']:
                                print("orders does not match")
                                continue
                            if status == "open":
                                print("Order is not yet closed")
                                time.sleep(0.5)
                                continue
                            elif status == 'canceled' or status == 'rejected' or status == 'expired':
                                if order['filled'] == 0:
                                    text = f"Buy order {status}\n--------------------------\n"
                                    print(text)
                                    self.add_message(text)
                                    try:
                                        token.delete()
                                    except:
                                        pass
                                    return
                                else:
                                    text = f"Buy order partially {status}"
                                    self.add_message(text)
                            buy_amount = order['filled']
                            if order.get("fee"):
                                sell_amount = buy_amount - order.get("fee").get("cost", 0)
                            else:
                                sell_amount = buy_amount
                            buy_price = order['average']
                            cost = order['cost']
                            break
                        time.sleep(0.5)

                    if buy_price is None:
                        text = f"Could not monitor placed order, trigerring emergency sell"
                        print(text)
                        self.add_message(text)
                        self.emergency_sell(coin)
                        try:
                            token.delete()
                        except Exception as e:
                            pass
                        return

                    stop_loss = (cost * 0.92) / sell_amount
                    take_profit = (cost * 1.22) / sell_amount
                    text = f"#0 {coin} bought\nAmount: {sell_amount}\nCost: {cost}\nBuy price: {buy_price}\n"
                    text += f"Expected take profit: {take_profit}\nExpected stop loss: {stop_loss}"
                    print(text)
                    self.add_message(text)
                    self.sell_token(coin, sell_amount, cost)
                    try:
                        token.delete()
                    except Exception as e:
                        print(f"Error encountered while deleting {coin}: {e}")
                        pass
                    return
                except Exception as e:
                    print(f"Error obtained while processing: {e}")
                    time.sleep(0.25)
                    n += 1
                    if n >= self.max_retries:
                        text = f"Max retries reached, unable to buy {coin}: {e}"
                        self.add_message(text)
                        self.stop_bot()
                        return
                    else:
                        continue
            else:
                time.sleep(0.25)
                continue
        print("Executor has been stopped")
        return

    def sell_token(self, coin:str, sell_amount:float, buy_cost:float):
        stop_loss = (buy_cost * 0.92) / sell_amount
        take_profit = (buy_cost * 1.22) / sell_amount
        while self.stopFlag is False:
            ticker = self.exchange.fetchTicker(coin)
            price = ticker['bid']

            if price is not None:
                if price <= stop_loss or price >= take_profit:
                    for i in range(self.max_retries):
                        try:
                            order = self.exchange.createMarketOrder(coin, "sell", sell_amount)
                            time.sleep(0.5)
                            sell_flag = 0

                            for _ in range(self.max_retries):
                                order = self.exchange.fetchOrder(order['id'], coin)
                                status = order['status']
                                if status == 'open':
                                    time.sleep(0.5)
                                    continue
                                elif status == 'canceled' or status == 'rejected' or status == 'expired':
                                    text = f"Sell order {status}"
                                    print(text)
                                    sell_amount -= order['filled']
                                    # self.add_message(text)
                                    if i == (self.max_retries - 1):
                                        text = f"Max retries reached. Sell market order could not be filled for {coin}\n"
                                        print(text)
                                        self.add_message(text)
                                        self.emergency_sell(coin)
                                        break
                                    break
                                sell_cost = order['cost']
                                text = f"Successfully sold {coin} at {order['price']}\n"
                                text += f"Cost: {order['cost']}\n"
                                text += f"Total profit: {sell_cost - buy_cost}\n"
                                text += "--------------------------\n"
                                sell_flag = 1
                                print(text)
                                self.add_message(text)
                                return
                            if sell_flag == 0:
                                time.sleep(0.5)
                                continue
                        except Exception as e:
                            print(e)
                            if i == (self.max_retries - 1):
                                text = f"Error encountered while selling {coin}: {e}"
                                self.add_message(text)
                                self.stop_bot()
                                return
                else:
                    time.sleep(0.5)
            else:
                time.sleep(0.5)
        return

    def add_message(self, message:str):
        log_date = datetime.now() - timedelta(hours=1)
        log_date = datetime.strftime(log_date, self.time)
        self.bot.unread_logs.append({"log_time": log_date, "msg": message})
        self.bot.save()

    def stop_bot(self):
        print(f"Stopping bot {self.id}")
        self.add_message("Bot stopped")
        self.stopFlag = True
        self.bot.active = False
        self.bot.save()

    def emergency_sell(self, symbol:str):
        base = symbol.split("/")[0]
        try:
            orders = self.exchange.fetchOrders(symbol, None, 2)
            for order in orders:
                if order['status'] == "open":
                    self.exchange.cancelOrder(order['id'], symbol)
        except:
            print(f"Error encountered while canceling opened orders: {e}")
            pass
        
        try:
            bal = self.exchange.fetchBalance()['free'][base]
            self.exchange.createMarketOrder(symbol, "sell", bal)
            text = f"{symbol} has been sold off"
            self.add_message(text)
        except IndexError as e:
            pass
        except Exception as e:
            print(e)
            text = f"Error encountered while selling {symbol}, please sell off manually"
            self.add_message(text)

        # self.stop_bot()
        return
    
    def save(self):
        storage.new(self)
        storage.save()

    def to_dict(self, fs=None):
        dictionary = self.__dict__.copy()
        dictionary['__class__'] = self.__class__.__name__
        if "bot" in dictionary:
            dictionary["bot"] = self.bot.id
        if "exchange" in dictionary:
            dictionary["exchange"] = self.exchange.id
            dictionary['exchange_apiKey'] = self.exchange.apiKey
            dictionary['exchange_secret'] = self.exchange.secret
        return dictionary
    