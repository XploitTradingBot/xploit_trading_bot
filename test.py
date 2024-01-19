#!/usr/bin/python3
import time
import ccxt
import threading
import asyncio
import traceback
from pprint import pprint
import requests
from urllib.parse import quote
from utils.helper import handleEnv
from typing import List, Dict
from datetime import datetime, timedelta
from config.exchanges import *
import hashlib
import hmac

init_exchanges = [binance, bitget, bitmex, bitmart, bingx, gate, huobi, kraken, kucoin, mexc, okx]

def load_markets(exchanges):
    cleared_exchanges = []
    for exchange in exchanges:
        try:
            exchange.load_markets()
            if hasattr(exchange, "fetchBalance"):
                try:
                    exchange.fetchBalance()
                    print(f"{exchange.id} has been cleared to trade")
                    cleared_exchanges.append(exchange)
                except Exception as e:
                    print(f"❌❌ {exchange.id} not properly set up: {e}")
            else:
                print(f"{exchange.id} has been cleared to trade, no balance checked")
        except Exception as e:
            # print(traceback.format_exc())
            print("❌❌Unable to load markets of", exchange.id, ":", e)
    return cleared_exchanges

def main(exchanges:List[ccxt.Exchange]):
    print("Initiating bot...⏳⏳")
    cleared_exchanges = load_markets(exchanges)
    return cleared_exchanges

# Balance check
def balance_check(exchange):            # checked
    balance = exchange.fetchBalance(params={})
    balance.pop("info")
    print(f"Balance for {exchange.id}: {balance['USDT']}")

def transfer_funds(exchange):           # checked
    # accounts = exchange.fetchAccounts()
    # print(accounts)
    try:
        exchange.transfer('USDT', 14.4395, 'spot', 'funding', params={})
        print("Transfer successful")
    except Exception as e:
        print("Error:", e)

def buy_coin(exchange):                 # checked
    coin = 'MIR/USDT'
    # amount = 121297
    amount = 11414.699
    try:
        orders = exchange.fetchOrderBook(coin)
        # min_price = orders['asks'][0][0]
        min_price = 0.014137
        print(f"Price of {coin}: {min_price} usdt")
        buy_amount = amount / min_price
        trading_fee = exchange.markets[coin]
        if trading_fee['percentage'] is True:
            print("Percentage used")
            trading_fee = trading_fee['taker'] * amount
        else:
            trading_fee = trading_fee['taker']
        calculated_fee = exchange.calculateFee(coin, 'limit', 'buy', amount, 0.014137, 'taker', params={})
        print(f"Trading fee to buy {coin}: {trading_fee}")
        print("Calculated fee:", calculated_fee)

        # exchange.createLimitBuyOrder(coin, buy_amount, min_price, params={})
        print("Order placed")
    except Exception as e:
        print(f"Error: {e}")
        print()

def sell_coin(exchange):                # checked
    coin = 'IOST/USDT'
    sell_amount = 1583.1322
    try:
        orders = exchange.fetchOrderBook(coin)
        min_price = orders['bids'][0][0]
        print(f"Price of {coin}: {min_price}usdt")
        trading_fee = exchange.markets[coin]
        if trading_fee['percentage'] is True:
            trading_fee = trading_fee['taker'] * sell_amount
        else:
            trading_fee = trading_fee['taker']
        calculated_fee = exchange.calculateFee(coin, 'limit', 'sell', sell_amount, min_price, 'maker', params={})
        print(f"Trading fee to sell {coin}: {trading_fee}")
        print("Calculated fee:", calculated_fee)

        # exchange.createOrder(coin, 'limit', 'buy', buy_amount, price=min_price, params={})
        exchange.createLimitSellOrder(coin, sell_amount, min_price, params={})
        print("Order placed")
    except Exception as e:
        print(f"Error: {e}")
        print()

def withdraw_funds(withdraw_from, deposit_to):      # checked
    # create deposit address
    network_fee = {}
    code = 'AVA'
    fee = withdraw_from.fetchDepositWithdrawFee(code)
    for network in fee['networks']:
        network_fee[network] = fee['networks'][network]['withdraw']['fee']
    network_fee = dict(sorted(network_fee.items(), key=lambda x: x[1]))

    for network, fee in network_fee.items():
        if network in (deposit_to.fetchDepositWithdrawFee(code))['networks']:
            trade_network = network
            trade_fee = fee
            break
    try:
        address = deposit_to.fetchDepositAddress(code, params={'network': trade_network})
    except Exception as e:
        try:
            address = deposit_to.fetchDepositAddress(code, params={})
            trade_network = address['network']
        except Exception as e:
            print(e)
            return
    print(f"Address: {address['address']}, Fee: {trade_fee}, Network: {trade_network}")

    # try:
    #     # withdraw_from.withdraw(code, 29.28, address['address'], tag=None,
    #     #                        params={'chain': trade_network})
    #     print(f"Withdrawal order placed. Fee: {trade_fee}, address: {address}\n")
    # except Exception as e:
    #     print(f"Error: {e}")

def get_deposit_address(code, exchange):
    try:
        address_struct = exchange.fetchDepositAddress(code, params={'network': 'BEP20'})
        address_network = 'BEP20'
    except Exception as e:
        address_struct = exchange.fetchDepositAddress(code, params={})
        address_network = address_struct['network']
    fee_struct = exchange.fetchDepositWithdrawFee(code, params={})
    fee_struct.pop('info')
    fee = fee_struct['networks'][address_network]['withdraw']['fee']
    print(f"Address network: {address_network}")
    print(f"Address: {address_struct}")
    print(f"Fee struct: {fee_struct}")
    print(f"Fee: {fee}")

def get_withdrawal_fee(from_exchange:ccxt.Exchange, to_exchange:ccxt, code:str, amount:float):   # checked
    if from_exchange == to_exchange:
        return {"trade_network":None, "fee":0, "address":None, "tag": None}
    trade_network, fee = None, None

    fee_struct = from_exchange.fetchDepositWithdrawFee(code, params={})
    from_networks = {}
    from_exchange_networks = fee_struct['networks'].keys()
    for from_network in from_exchange_networks:
        if fee_struct['networks'][from_network]['withdraw']['percentage'] is True:
            fee = fee_struct['networks'][from_network]['withdraw']['fee'] * amount
        else:
            fee = fee_struct['networks'][from_network]['withdraw']['fee']
        from_networks[from_network] = fee
    from_networks = dict(sorted(from_networks.items(), key=lambda x: x[1]))
    address_struct = None
    transf_fee = None
    try:
        to_nets = list((to_exchange.fetchDepositWithdrawFee(code, params={}))['networks'].keys())
        # to_nets = to_exchange.currencies[code]
        # print(f"Fee from currencies: {to_nets}")
    except Exception as e:
        to_nets = to_exchange.currencies[code]
        # print(f"Fee from currencies: {to_nets}")
        return None
    # print(to_exchange.fetchDepositWithdrawFee(code, params={}))
    # print(f"From networks: {from_networks}")
    # print(f"To networks: {to_nets}")
    for net, fee in from_networks.items():
        if net in to_nets:
            try:
                address_struct = to_exchange.fetchDepositAddress(code, params={'network': net})
                network = net
                transf_fee = fee
                break
            except Exception as e:
                try:
                    address_struct = to_exchange.createDepositAddress(code, params={'network': net})
                    if address_struct['network'] != net:
                        continue
                    transf_fee = fee
                    break
                except Exception as e:
                    print(e)
                    continue

    if not address_struct:
        print("Address struct not found")
        return None
    trade_network = network
    address = address_struct['address']
    tag = address_struct['tag']
    return {"trade_network":trade_network, "fee":transf_fee, "address":address, "tag": tag}

def test_withdrawal_time(from_exchange:ccxt.Exchange, to_exchange:ccxt.Exchange, code:str, amount:float, withdraw_detail:Dict):
    # withdraw_detail = get_withdrawal_fee(from_exchange, to_exchange, code, amount)
    if withdraw_detail is None:
        print("Details not found")
        return
    address = withdraw_detail['address']
    network = withdraw_detail['trade_network']
    network = str(network)
    tag = withdraw_detail['tag']
    fee = withdraw_detail['fee']
    pprint(f"Sending {amount} {code} from {from_exchange.id} to {to_exchange.id} to {address} through {network} and tag {tag} at a fee of {fee}")

    # return
    start_time = datetime.now()
    start_ts = time.time()
    try:
        print("Code:", code, "\nNetwork:", network)
        withdraw_info = from_exchange.withdraw(code, amount, address, None, params={'chain': network})
        print(f"Withdrawal request submitted: {withdraw_info}")
    except Exception as e:
        print(traceback.format_exc())
        return

    print("Now waiting for deposit confirmation...")
    time.sleep(10)
    while True:
        if from_exchange.has['fetchWithdrawals']:
            withdraws = from_exchange.fetch_withdrawals(code, None, 1)
        elif from_exchange.has['fetchTransactions']:
            withdraws = from_exchange.fetchTransactions(code, None, 1)
        if withdraws[0]['id'] == withdraw_info['id']:
            if withdraws[0]['status'] == 'ok':
                break
            elif withdraws[0]['status'] == 'pending':
                time.sleep(2)
                continue
            elif withdraws[0]['status'] == 'failed' or withdraws[0]['status'] == 'canceled':
                print(f"Withdrawal {withdraws[0]['status']}")
                break
    while True:
        if to_exchange.has['fetchDeposits']:
            deposit = (to_exchange.fetch_deposits(code, start_time, 1, params={}))
            print(deposit)
            if deposit:
                if deposit['status'] == 'ok':
                    break
                elif deposit['status'] == 'pending':
                    time.sleep(2)
                elif deposit['status'] == 'failed' or deposit['status'] == 'canceled':
                    print("Deposit failed")
                    break
                continue
            else:
                time.sleep(2)
                continue
        else:
            print("Exchange has no fetchDeposits method")
            time.sleep(45)
            break
    end_time = datetime.now()
    run_time = end_time - start_time
    print(f"Withdrawal took {run_time} to complete")

def trade_coin(coin:str, exchange:ccxt.Exchange, amount: float, price: float, side='buy'):
        """This place a buy order in an exchange
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
        
        start_time = datetime.now()
        valid_period = 5 * 60      # minutes
        valid_till = start_time + timedelta(seconds=valid_period)
        try:
            if side == 'buy':
                order_dict = exchange.createLimitBuyOrder(coin, amount, price)
            elif side == 'sell':
                order_dict = exchange.createLimitSellOrder(coin, amount, price)

            # Start monitoring order
            while datetime.now() < valid_till:
                if exchange.has['fetchOrders']:
                    orders = (exchange.fetchOrders(coin, since=None, limit=1))
                elif exchange.has['fetchOpenOrders']:
                    orders = exchange.fetchOpenOrders(coin, since=None, limit=1)
                else:
                    print("Could not monitor order")
                    time.sleep(5)
                    return True
                if len(orders) > 0 and "id" in orders[0]:
                    order = orders[0]
                    if order['id'] == order_dict['id']:
                        if order['status'] == 'open':
                            time.sleep(2)
                        elif order['status'] == 'closed':
                            return True
                        elif order['status'] == 'canceled' or order['status'] == 'expired' or order['status'] == "rejected":
                            return f"Order {order['status']}"
                    else:
                        time.sleep(1)
                else:
                    if exchange.has['fetchOrderTrades']:
                        trades = exchange.fetchOrderTrades(order_dict['id'], coin, None, 1)
                        if len(trades) > 0:
                            trade = trades[0]
                            if trade['id'] == order_dict['id']:
                                return True
                        time.sleep(2)
                    else:
                        return "Unable to monitor trade"
            return "Trade took too long to complete"
        except Exception as e:
            print(e)
            return f"Error: {e}"

def find_new_coins(exchanges):
    from update_coin_list import get_new_coins
    new_coins = []
    coins = get_new_coins()
    for coin in coins:
        coin = coin + '/USDT'
        new_coins.append(coin)

    for exchange in exchanges:
        for coin in new_coins:
            if coin in exchange.symbols:
                price = exchange.fetchTicker(coin)['last']
                if not price:
                    continue
                print(f"{coin} is already available in {exchange} at {price}")

def place_market_buy_order(exchange:ccxt.Exchange, coin:str, cost:float):
    try:
        print(f"Trying to place a buy market order on {coin} at a cost of {cost}")
        exchange.options['createMarketBuyOrderRequiresPrice'] = False
        order = exchange.createMarketBuyOrder(coin, cost)
        print(f"Order executed: {order}")
        buy_amount = order['info']['origQty']
    except Exception as e:
        print(f"Error encountered when placing buy order: {e}")
        return
    
    time.sleep(2)
    
    try:
        print(f"Trying to place a sell market order on {coin} for a quantity of {buy_amount}")
        order = exchange.createMarketSellOrder(coin, buy_amount)
        print(f"Order executed: {e}")
    except Exception as e:
        print(f"Error encountered when placing sell order: {e}")
        return

def generate_signature(data:Dict, secret_key:str):
    encoded_data = ""
    for key, val in data.items():
        encoded_data += f"{key}={val}&"
    encoded_data = encoded_data[:-1]
    secret_key_bytes = secret_key.encode('utf-8')
    print(encoded_data)
    data_bytes = encoded_data.encode('utf-8')
    digest = hmac.new(secret_key_bytes, msg=data_bytes, digestmod=hashlib.sha256).hexdigest()
    return digest

def place_mexc_buy_order(coin:str, cost:float, start_time:datetime):
    secret = handleEnv("mexc_secret")
    header = {"X-MEXC-APIKEY": handleEnv("mexc_apiKey")}
    url = "https://api.mexc.com/api/v3/order"
    timestamp = int(time.time())
    if "/" in coin:
        coin = coin.split("/")
        coin = "".join(coin)
        print(coin)
    data = f"symbol={coin}&side=BUY&type=MARKET&cost={cost}&recvWindow=5000"
    signature_data = data + f"&timestamp={timestamp}"
    signature = generate_signature(signature_data, secret)
    print(signature)
    target_timestamp = start_time.timestamp()
    while True:
        if datetime.now() >= start_time:
            try:
                data += f"&timestamp={target_timestamp}&signature={signature}"
                res = requests.post(url, headers=header, data=data)
                print(f"{res.text}. {res.status_code} at {datetime.now()}")
            except Exception as e:
                print(e)
            break

def create_withdraw(coin:str, amount:float, network:str, address:str):
    ts = int(time.time() * 1000)
    data = f"coin={coin}&address{address}&amount={amount}&network={network}&timestamp={ts}"
    signature = generate_signature(data, handleEnv("mexc_secret"))
    url = f"https://api.mexc.com/api/v3/capital/withdraw/apply?coin={coin}&address={address}"
    url += f"&amount={amount}&network={network}&timestamp={ts}&recvWindow=5000&signature={signature}"
    header = {"X-MEXC-APIKEY": handleEnv("mexc_apiKey")}
    resp = requests.get(url, headers=header)
    if resp.status_code == 200:
        resp = resp.json()
        print(resp)
    else:
        print("Error:", resp.status_code, resp.text)

def test_threading(stop_event):
    while not stop_event.is_set():
        print("thread is running")
        time.sleep(1)

def test_peregrine():
    from peregrinearb import load_exchange_graph, print_profit_opportunity_for_path, bellman_ford
    graph = asyncio.get_event_loop().run_until_complete(load_exchange_graph('gate'))
    paths = bellman_ford(graph, depth=True)
    for path, starting_amount in paths:
        print_profit_opportunity_for_path(graph, path, depth=True, starting_amount=100)

if __name__ == '__main__':
    test_peregrine()
    # stop_event = threading.Event()
    # func_thread = threading.Thread(target=test_threading, args=(stop_event,))
    # func_thread.start()
    # time.sleep(5)
    # stop_event.set()
    # func_thread.join()

    # try:
    #     # exchanges = []
    #     # for exchange in init_exchanges:
    #     #     try:
    #     #         exchange.load_markets()
    #     #         exchanges.append(exchange)
    #     #         print(f"{exchange} has been cleared")
    #     #     except Exception as e:
    #     #         print(e)
    #     exc = [bybit, huobi, bitget]
    #     exchanges = main(exc)
    #     print()
    #     print(exchanges)
    #     from trading_bot import get_withdrawal_detail

    #     withdraw_from, deposit_to = None, None
    #     for exchange in exchanges:
    #         if exchange.id == 'bitget':
    #             withdraw_from = exchange
    #         if exchange.id == 'bybit':
    #             deposit_to = exchange
    #     if withdraw_from and deposit_to:
    #         withdraw_detail = get_withdrawal_detail(withdraw_from, deposit_to, 'USDT', 15)
    #         # withdraw_detail = get_withdrawal_fee(withdraw_from, deposit_to, 'USDT', 14.43)
    #         print(withdraw_detail)
    #         # test_withdrawal_time(withdraw_from, deposit_to, 'USDT', 13, withdraw_detail)
    #     else:
    #         print("Exchanges not found")

    #     # find_new_coins(exchanges)

    #     # for exchange in exchanges:
    #     #     if exchange.id == 'mexc':
    #     #         place_market_buy_order(exchange, 'IOST/USDT', 6.6)
    #     #         # balance_check(exchange)
    #     #         buy_coin(exchange)
    #     #         # sell_coin(exchange)
    #     #         # transfer_funds(exchange)
    # except Exception:
    #     print(traceback.format_exc())
    #     pass