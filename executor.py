#!/usr/bin/python3
import ccxt
import time
from typing import List, Dict
from model import storage
import asyncio
import uuid
from os import getenv
from datetime import datetime, timedelta
from peregrinearb import load_exchange_graph, print_profit_opportunity_for_path, bellman_ford

typ = getenv("TYPE")


class Executor():
    apiKey = ""
    secret = ""
    password = ""
    uid = ""
    capital = 0
    startFlag = False
    accumulated_profit = 0
    demoMode = False
    max_retries = 3
    insufficient_balance_count = 0

    def __init__(self, user_id:str, bot_id:str, exchange:str='mexc', **params):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
    
        bot = storage.get("Bot", bot_id)
        if not bot:
            raise ValueError("Invalid bot passed")
        self.bot = bot
        
        try:
            self.exchange = getattr(ccxt, exchange)()
            # self.exchange = getattr(ccxt, 'kraken')()
            setattr(self.exchange, "enableRateLimit", True)
            setattr(self.exchange, "nonce", ccxt.Exchange.milliseconds)
            self.exchange.load_markets()
        except Exception as e:
            print(e)
            self.add_message("Error: Could not identify exchange")
            return
        
        if self.demoMode:
            self.exchange.set_sandbox_mode(True)
        
        for key, val in params.items():
            if hasattr(self, key):
                setattr(self.exchange, key, val)
            else:
                raise ValueError('{} is not a valid attribute in model'.format(key))
            
        self.exchange_symbols = self.exchange.symbols
            
        # verify account balance is up to selected capital
        self.capital = float(self.bot.capital)
        if typ != "test":
            balance = self.exchange.fetchBalance()['free']
            usdt_balance = balance.get('USDT', 0)
            if usdt_balance < self.capital:
                text = f"Not enough balance to start bot. Available blc: {usdt_balance}"
                raise ValueError(text)
        
    def findPath(self):
        paths = []
        try:
            print("Getting graph...")
            graph = asyncio.get_event_loop().run_until_complete(load_exchange_graph(self.exchange.id, fees=True))
            print("Getting paths")
            paths = bellman_ford(graph)
            print("Paths obtained")
        except Exception as e:
            print(e)
            return
        
        data = []
        for path in paths:
            datum = print_profit_opportunity_for_path(graph, path, starting_amount=self.capital)
            print("Path opportunity obtained")
            data.append(datum)

        if len(data) > 0:
            for dt in data:
                print(dt)
                self.execute(dt)
        else:
            print("No profitable path found")
            return

    def execute(self, pairs:List):
        """This decodes the recovered data and sends it to trade executor"""

        first = pairs[0]
        for pair, info in first.items():
            if pair.split('/')[0] != 'USDT' and pair.split('/')[0] != 'USD':
                print("Invalid trade found")
                return
            
        all_pair = []
        for item in pairs:
            for pair in list(item.keys()):
                if pair in self.exchange_symbols:
                    all_pair.append({'pair': pair, 'side': 'sell'})
                else:
                    reverse_pair = '{}/{}'.format(pair.split('/')[1], pair.split('/')[0])
                    if reverse_pair in self.exchange_symbols:
                        all_pair.append({'pair': reverse_pair, 'side': 'buy'})

        # n = 1
        # enum_pair_dict = {}
        # # all_pair = []
        # for item in pairs:
        #     for pair, info in item.items():
        #         pair_format = {}
        #         if pair in self.exchange_symbols:
        #             side = 'sell'
        #             try:
        #                 amount = enum_pair_dict[n - 1]['balance']
        #             except IndexError as e:
        #                 continue

        #             balance = amount * info['price']
        #             pair_format.update({'pair': pair, 'side': side, 'price': info['price'],
        #                                 'amount': amount, 'balance': balance})
        #             enum_pair_dict[n] = pair_format
        #             n += 1
        #         else:
        #             base = pair.split('/')[0]
        #             quote = pair.split('/')[1]
        #             reverse_pair = "{}/{}".format(quote, base)
        #             if reverse_pair in self.exchange_symbols:
        #                 price = 1 / info['price']
        #                 side = "buy"
        #                 amount = info['amount']

        #                 balance = amount
        #                 # fee = self.exchange.calculateFee(reverse_pair, 'limit', 'buy', amount, info['price'], 'taker')
        #                 # balance -= fee['cost']
        #                 pair_format.update({'pair': reverse_pair, 'side': side, 'price': price,
        #                                             'amount': amount, 'balance': balance})
        #                 enum_pair_dict[n] = pair_format
        #                 # all_pair.append(pair_format)
        #                 n += 1

        # all_pair = list(enum_pair_dict.values())
        print(f"All pair: {all_pair}")

        # Get the start balance
        if typ == "test":
            start_blc = self.capital
        else:
            blc = self.exchange.fetchBalance()['free']
            start_blc = blc.get('USDT', 0)

        if start_blc <= 0.9 * self.capital:
            text = "Balance too low, stopping bot."
            print(text)
            self.add_message(text)
            self.stop()
            return

        if start_blc > self.capital:
            starting_amount = self.capital
        else:
            starting_amount = start_blc

        # check the profitability of the trade before executing
        first_pair = all_pair[0]['pair']
        # starting_amount = self.exchange.markets[first_pair]['limits']['cost']['min'] + 0.5
        stat = self.screen_trade(starting_amount, all_pair)
        if stat is not False:
            print("Trade is profitable. Proceeding...")
            message = f"Found a path:\nStarting with {starting_amount}usdt\nUSDT "
            for item in all_pair:
                if item['side'] == 'buy':
                    curr = item['pair'].split('/')[0]
                    message += f'--> {curr} '
                else:
                    curr = item['pair'].split('/')[1]
                    message += f'--> {curr} '
            print(message)
            self.add_message(message)

            if typ != "test":
                for item in all_pair:
                    status = self.trade_executor(item['pair'], item['side'], stat[item['pair']], starting_amount)
                    if status != True:
                        return
            print("A trade has been completed")
            end_blc = self.exchange.fetchBalance()['free'].get('USDT', 0)
            net_gain = end_blc - start_blc
            if typ == 'test':
                text = f"No real profit was made. This is a demo ({stat['profit']})"
            else:
                if net_gain > 0:
                    text = f"Actual profit made: {net_gain}"
                else:
                    text = f"A loss was incurred: {net_gain}"
            self.add_message(text)
        else:
            print("Trade is not profitable, Finding another...\n")
            return

    def trade_executor(self, pair:str, side:str, price:float, amount:float=None):
        if side == 'buy':
            # while i < self.max_retries:
            print(f"Trying to buy {pair}, price: {price}, amount: {amount}")
            buyStatus = self.trade_coin(pair, self.exchange, amount,
                                        price, 'buy')
            if buyStatus is True:
                text = f"Successfully bought {pair}"
                print(text)
                self.add_message(text)
                return True
            else:
                print(f"Failed: {buyStatus}")

            if pair.split('/')[1] == 'USDT':
                text = f"Unable to buy {pair}, exiting trade\n"
                text += f"msg: {buyStatus}."
                print(text)
                self.add_message(text)
            else:
                text = f"Unable to buy {pair}, converting funds back to usdt and exiting trade\n"
                text += f"msg: {buyStatus}."
                print(text)
                self.add_message(text)
                base = pair.split('/')[1]
                amt = amount * price
                self.reload_funds(base, amount=amt)
            return False

        elif side == 'sell':
            # while i < self.max_retries:
            print(f"Trying to sell {pair}, price: {price}, amount: {amount}")
            sellStatus = self.trade_coin(pair, self.exchange, amount,
                                            price, 'sell')
            if sellStatus is True:
                text = f"Successfully sold {pair}"
                print(text)
                self.add_message(text)
                return True
            else:
                print(f"Failed: {sellStatus}")
                
            if pair.split('/')[0] == 'USDT':
                text = f"Unable to sell {pair}, exiting trade\n"
                text += f"msg: {sellStatus}."
                print(text)
                self.add_message(text)
            else:
                text = f"Unable to sell {pair}, converting funds back to usdt and exiting trade\n"
                text += f"msg: {sellStatus}"
                print(text)
                self.add_message(text)
                base = pair.split('/')[0]
                self.reload_funds(base, amount=amount)
            return False

    def start(self):
        self.startFlag = True
        print("Bot started...")
        while self.startFlag:
            try:
                print("")
                self.findPath()
                time.sleep(1)
            except Exception as e:
                print(e)
        print("Bot stopped")
        self.add_message("Bot has been stopped")
        return

    def stop(self):
        self.startFlag = False
        # print("Bot has been stopped")
        # self.add_message("Bot has been stopped")
        # return

    def add_message(self, message):
        self.bot.transactions.append(message)
        self.bot.save()

    @staticmethod
    def trade_coin(coin:str, exchange:ccxt.Exchange, amount: float, price: float, side:str):
        """This place a buy or sell order in an exchange
        Args:
            coin: The coin to be bought
            exchange: The exchange in which the order should be placed
            amount: The cost of the trade in usdt
            price: The price at which the order should be 
            side: str, can only either be 'buy' or 'sell'
        Returns:
            True if order is placed successfully and filled or error msg if otherwise"""
        
        if side not in ['buy', 'sell']:
            return False
        
        wait_time = 10

        start_time = datetime.now()
        valid_till = start_time + timedelta(minutes=wait_time)
        while datetime.now() < valid_till:
            try:
                if side == 'buy':
                    cost = amount * price
                    quote = coin.split('/')[1]
                    balance = exchange.fetchBalance()['free']
                    blc = balance.get(quote, 0)
                    if blc < cost:
                        cost = blc
                    print(f"Balance found: {blc}, and cost: {amount}")
                    order_dict = exchange.createLimitBuyOrder(coin, amount, price)
                    # exchange.options['createMarketBuyOrderRequiresPrice'] = False
                    # order_dict = exchange.createMarketBuyOrder(coin, amount)
                elif side == 'sell':
                    base = coin.split('/')[0]
                    balance = exchange.fetchBalance()['free']
                    blc = balance.get(base, 0)
                    if blc < amount:
                        amount = blc
                    # exchange.options['createMarketBuyOrderRequiresPrice'] = False
                    order_dict = exchange.createLimitSellOrder(coin, amount, price)
                    # order_dict = exchange.createMarketSellOrder(coin, amount)

                # Start monitoring order
                # Will not be needed if set to make market orders
                while datetime.now() < valid_till:
                    if exchange.has['fetchOrders']:
                        orders = (exchange.fetchOrders(coin, since=None, limit=1))
                    elif exchange.has['fetchOpenOrders']:
                        orders = exchange.fetchOpenOrders(coin, since=None, limit=1)
                    else:
                        print("Could not monitor order")
                        return "Could not monitor trade"
                    if len(orders) > 0 and "id" in orders[0]:
                        order = orders[0]
                        if order['id'] == order_dict['id']:
                            if order['status'] == 'open':
                                time.sleep(1)
                            elif order['status'] == 'closed':
                                return True
                            elif order['status'] == 'canceled' or order['status'] == 'expired' or order['status'] == "rejected":
                                return f"Order {order['status']}"
                        else:
                            time.sleep(1)
                    else:
                        # query the trades
                        if exchange.has['fetchOrderTrades']:
                            trades = exchange.fetchOrderTrades(order_dict['id'], coin, None, 1)
                            if len(trades) > 0:
                                trade = trades[0]
                                if trade['order'] == order_dict['id']:
                                    return True
                            time.sleep(2)
                        elif exchange.has['fetchMyTrades']:
                            trades = exchange.fetchMyTrades(coin, None, 1)
                            if len(trades) > 0:
                                trade = trades[0]
                                if trade['order'] == order_dict['id']:
                                    return True
                        elif exchange.has['fetchTrades']:
                            trades = exchange.fetchMyTrades(coin, None, 1)
                            if len(trades) > 0:
                                if trades[0]['order'] == order_dict['id']:
                                    return True
                        else:
                            return "Unable to monitor trade"
                        
                # fetch any opened order and cancel orders that are not filled after timeout
                if exchange.has['fetchOrders']:
                    orders = exchange.fetchOrders(coin, since=None, limit=1)
                elif exchange.has['fetchOpenOrders']:
                    orders = exchange.fetchOpenOrders(coin, since=None, limit=1)
                
                order = orders[0]
                if order['filled'] <= 0.00000000:
                    exchange.cancelOrder(order['id'], coin)
                    text = f"Order for {coin} has been cancelled.\n"
                    text += "Order took too long to close"
                    return text
                elif order['filled'] > 0 and order['filled'] < amount:
                    text = f"Order timeout \npartially filled ({order['filled']}/{amount})"
                    # Need to include a logic here for partially filled orders
                    # For now I stop the transaction if I encounter this problem
                    return text
            except Exception as e:
                print(e)
                return f"Error: {e}"

    def reload_funds(self, quote, amount):
        if quote == 'USDT':
            return

        pair = f"{quote}/USDT"
        price = self.exchange.fetchTicker(pair)['last']
        self.trade_coin(pair, self.exchange, amount, price, 'sell')

    def screen_trade(self, balance:float, transaction_data:List) -> Dict:
        print("Now screening trade...")
        order_trades = {}
        start_amount = balance

        for trade in transaction_data:
            order_book = self.exchange.fetchOrderBook(trade['pair'], limit=10)
            info = self.calc_order_amount(order_book, balance,
                                             trade['side'])
            if info is None:
                return False
            balance = info['balance']
            if balance < self.exchange.markets[trade['pair']]['limits']['cost']['min']:
                print("Minimum tradeable balance reached.")
                return False
            order_trades[trade['pair']] = (info['price'])

        profit = balance - start_amount
        print(order_trades)
        if profit < 0:
            print(f"Potential loss: {profit}")
            # order_trades['status'] = 'loss'
            return False
        print(f"Potential gain: {profit}")
        order_trades['profit'] = profit
        return order_trades

    @staticmethod
    def calc_order_amount(order_book:Dict, cost:float, side:str) -> Dict:
        if side == 'buy':
            amount = 0
            n = 0
            # filled_price = 0
            try:
                while cost > 0:
                    price, volume = order_book['asks'][n][0], order_book['asks'][n][1]
                    # if price > filled_price:
                    #     filled_price = price
                    if (cost / price) > volume:
                        amount += volume
                        cost -= price * volume
                        print(f"Bought {volume} at {price}")
                        n += 1
                    else:
                        amount += cost / price
                        print(f"Bought {cost / price} at {price}")
                        break

                return {'price': price, 'balance': amount, 'amount': amount}
            except Exception as e:
                print(e)
                return None
        elif side == 'sell':
            amount = 0
            n = 0
            # filled_price = 0
            try:
                while cost > 0:
                    price, volume = order_book['bids'][n][0], order_book['bids'][n][1]
                    # if price > filled_price:
                    #     filled_price = price
                    if cost > volume:
                        amount += price * volume
                        cost -= volume
                        print(f"Sold {volume} at {price}")
                        n += 1
                    else:
                        # print(order_book)
                        amount += price * cost
                        print(f"Sold {cost} at {price}")
                        break
                return {'price': price, 'balance': amount}
            except Exception as e:
                print(e)
                return None
