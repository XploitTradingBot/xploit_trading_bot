#!/usr/bin/python3

import sys
import re
import json
import time
import traceback
import ccxt
import asyncio
import random
import requests
from requests.exceptions import RequestException
from typing import Dict, List
from requests import Session
from utils.logging import logger
from utils.helper import handleEnv
from info import fiat_set
from model.notif import Notification
from config.exchanges2 import Exchanges
from config.exchanges import *


def set_up_exchanges(exchanges:List[ccxt.Exchange], id:str="123456789") -> List[ccxt.Exchange]:
    def load_markets(exchanges):
        cleared_exchanges = []
        for exchange in exchanges:
            try:
                exchange.load_markets()
                print(f"Market loaded for {exchange.id}")
                try:
                    exchange.check_required_credentials()
                    if hasattr(exchange, "fetchBalance"):
                        try:
                            bal = (exchange.fetchBalance())['free']
                            if 'USDT' in bal:
                                text = f"{exchange.id} has been cleared to trade. Available balance: {bal['USDT']}"
                            else:
                                text = f"{exchange.id} has been cleared to trade. Available balance: 0.0"
                            print(text)

                            notif_dict = {"text": text, "user_id": id}
                            notif = Notification(**notif_dict)
                            notif.save()
                            cleared_exchanges.append(exchange)
                        except Exception as e:
                            print(f"❌❌ {exchange.id} not properly set up: {e}")

                            text = f"{exchange.id} not properly set up: {e}"
                            notif_dict = {"error": text, "user_id": id}
                            notif = Notification(**notif_dict)
                            notif.save()
                    else:
                        print(f"{exchange.id} has been cleared to trade, no balance checked")
                except Exception as e:
                    print(f"{exchange.id} has missing or incomplete credentials")
                    text = f"{exchange.id} has missing or incomplete credentials: {e}"
                    notif_dict = {"error": text, "user_id": id}
                    notif = Notification(**notif_dict)
                    notif.save()
            except Exception as e:
                text = f"Could not load market for {exchange.id}: {e}"
                print(text)
                notif_dict = {"error": text, "user_id": id}
                notif = Notification(**notif_dict)
                notif.save()
        return cleared_exchanges

    print("Starting bot...⏳⏳")
    cleared_exchanges = load_markets(exchanges)
    text = f"Cleared Exchanges: {[ exc.id for exc in cleared_exchanges ]}"
    notif_dict = {"text": text, "user_id": id}
    model = Notification(**notif_dict)
    model.save()
    return cleared_exchanges

def get_trading_fee(coin: str, exchange: ccxt.Exchange, type: str, amount: float) -> float:
    """This returns the trading fee from a trade
    Args:
        coin: The coin symbol to trade eg. 'IOST/USDT'
        exchange: The ccxt instance of the exchange eg. ccxt.binance()
        type: The trade side, can either be 'taker' or 'maker'
        amount: It is the amount in usdt when type is 'taker' and the amount of coins to sell when type is 'maker'
    Return:
        float type"""
    fee_struct = exchange.markets[coin]
    if fee_struct['percentage'] is True:
        if type == 'taker':
            fee = fee_struct['taker'] * amount
        elif type == 'maker':
            fee = fee_struct['maker']
    else:
        if type == 'taker':
            fee = fee_struct['taker'] * amount
        elif type == 'maker':
            fee = fee_struct['maker']
    return fee

def get_withdrawal_detail(from_exchange:ccxt.Exchange, to_exchange:ccxt, code:str, amount:float):
    """The obtains info about a withdraw request
    Args:
        from_exchange: the ccxt instance of the exchange which fund is to be withdrawn
        to_exchange: the ccxt instance of the exchange which funds is to be deposited
        code: The string representing the symbol to withdraw eg. 'USDT'
        amount: the amount of the code to withdraw
    Returns:
        A dict containing the address, network, tag, fee
        Also returns -1 if there is a problem with the from_exchange
        returns 1 if there is a problem with the to_exchange"""
    
    if from_exchange == to_exchange:
        return {"trade_network":None, "fee":0, "address":None, "tag": None}
    # print("Getting withdrawal details...")

    if from_exchange.has.get('fetchDepositWithdrawalFees', None) or from_exchange.has.get('fetchDepositWithdrawFees'):
        try:
            from_networks = {}
            fee_struct = from_exchange.fetchDepositWithdrawFees(code, params={})
            if 'networks' in fee_struct:
                fee_struct = fee_struct['networks']
                for network, info in fee_struct.items():
                    if info['withdraw']['percentage'] is True:
                        from_networks[network] = info['withdraw']['fee'] * amount
                    else:
                        from_networks[network] = info['withdraw']['fee']
        except Exception:
            from_ntwks = from_exchange.currencies[code]['networks']
            from_networks = {network: from_ntwks[network]['fee'] for network in from_ntwks
                            if from_ntwks[network]['active'] is True}

    else:
        from_ntwks = from_exchange.currencies[code]['networks']
        from_networks = {network: from_ntwks[network]['fee'] for network in from_ntwks
                        if from_ntwks[network]['active'] is True}
    if len(from_networks) == 0:
        from_ntwks = from_exchange.currencies[code]['networks']
        from_networks = {network: from_ntwks[network]['fee'] for network in from_ntwks
                        if from_ntwks[network]['active'] is True}
    from_networks = dict(sorted(from_networks.items(), key=lambda x: x[1]))
    # print(f"Available networks in {from_exchange.id}: {from_networks}")
    address_struct = None
    try:
        to_nets = list((to_exchange.fetchDepositWithdrawFee(code, params={}))['networks'].keys())
    except Exception as e:
        try:
            to_nets = to_exchange.currencies[code]['networks']
            to_nets = [net for net in to_nets if to_nets[net]['active'] is True]
        except Exception as e:
            return 1
    # print(f"Available networks in {to_exchange.id}: {to_nets}")

    sim_addr = {"BEP20": "BSC", "BSC": "BEP20", "ETH": "ERC20", "ERC20": "ETH", "TRX": "TRC20", "TRC20": "TRX",
                "BNB": "BEP2", "BEP2": "BNB", "HT": "HECO", "HECO": "HT", "MATIC": "POLYGON", "POLYGON": "MATIC"}
    network = None
    for net in from_networks:
        # print("Finding matching network for", net)
        for to_net in to_nets:
            if net.lower() in to_net.lower() or to_net.lower() in net.lower():
                if (net == "BEP2" and to_net == "BEP20") or (net == "BEP20" and to_net == "BEP2"):
                    continue
                # print("Match found", to_net)
                try:
                    address_struct = to_exchange.fetchDepositAddress(code, params={"network": to_net})
                except Exception:
                    continue
                info = {"trade_network": net, "tag": address_struct.get("tag", None),
                        "fee": from_networks[net], "address": address_struct['address']}
                return info
            else:
                if net in sim_addr:
                    net = sim_addr[net]
                    if net.lower() in to_net.lower() or to_net.lower() in net.lower():
                        if (net == "BEP2" and to_net == "BEP20") or (net == "BEP20" and to_net == "BEP2"):
                            continue
                        try:
                            address_struct = to_exchange.fetchDepositAddress(code, params={"network": to_net})
                        except Exception:
                            continue
                        info = {"trade_network": net, "tag": address_struct.get("tag", None),
                                "fee": from_networks[net], "address": address_struct['address']}
                        return info
                elif to_net in sim_addr:
                    to_net = sim_addr[to_net]
                    if net.lower() in to_net.lower() or to_net.lower() in net.lower():
                        if (net == "BEP2" and to_net == "BEP20") or (net == "BEP20" and to_net == "BEP2"):
                            continue
                        try:
                            address_struct = to_exchange.fetchDepositAddress(code, params={"network": to_net})
                        except Exception:
                            continue
                        info = {"trade_network": net, "tag": address_struct.get("tag", None),
                                "fee": from_networks[net], "address": address_struct['address']}
                        return info

def trade_coin(coin:str, exchange:ccxt.Exchange, amount: float, price: float, side='buy') -> (float | None):
    """This place a buy order in an exchange
    Args:
        coin: The coin to be bought eg BTC/USDT
        exchange: The exchange in which the order should be placed
        amount: The cost of the trade in usdt
        price: The price at which the order should be 
        side: str, can only either be 'buy' or 'sell'
    Returns:
        Order cost if order closed successfully or None if otherwise"""
    
    if side not in ['buy', 'sell']:
        return None
    
    try:
        if side == 'buy':
            order_dict = exchange.createOrder(coin, 'market', side, amount)
        else:
            order_dict = exchange.createOrder(coin, 'market', side, amount)

        while True:
            if exchange.has['fetchOrder']:
                order = exchange.fetchOrder(order_dict['id'], coin)
                if order:
                    if order['status'] == 'open':
                        time.sleep(2)
                        continue
                    elif order['status'] == 'closed':
                        cost = order['cost']
                        return cost
                    elif order['status'] == 'canceled' or order['status'] == 'expired' or order['status'] == "rejected":
                        return None
                else:
                    time.sleep(2)
                    continue
            elif exchange.has['fetchOrderTrades']:
                trades = exchange.fetchOrderTrades(order_dict['id'], coin, None, 1)
                if len(trades) > 0:
                    trade = trades[0]
                    if trade['id'] == order_dict['id']:
                        return trade['cost']
                time.sleep(2)
            else:
                return None
    except Exception as e:
        logger.error(e)
        return None

def get_crypto_prices(coin_set, convert='USD'):
    '''fetch crypto currencies price from coin market cap api'''
    coin_set = set([i for i in coin_set if i.isalpha()])
    output = {}
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
        'symbol': ','.join(coin_set),
        'convert': convert
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': handleEnv("cmc_key"),
    }

    session = Session()
    session.headers.update(headers)
    response = session.get(url, params=parameters)
    data = json.loads(response.text)

    if response.ok:
        for key, val in data['data'].items():
            output[key] = {
                'price': val['quote']['USD']['price'],
                'cmc_rank': val['cmc_rank']
            }
    else:
        if response.status_code == 400:
            msg = data['status']['error_message']
            not_avail_coins = re.findall(r'[0-9A-Z]+', msg.split(':')[-1])
            new_coin_set = coin_set - set(not_avail_coins)
            output = get_crypto_prices(new_coin_set, convert)
        else:
            raise ConnectionError

    return output

async def get_coins(exchanges:List[ccxt.Exchange], include_fiat=False) -> Dict:
    """This sets up all the coins in the specified exchanges
    Args:
        exchanges: A list of all the cleared ccxt.Exchange exchanges
    Return:
        A dict with keys of ticker symbol and values of list in format <exchange.id>_<symbol>"""
    currency_set = set()
    for exchange in exchanges:
        # exchange.load_markets()
        currency_names = ['{}_{}'.format(exchange.id, cur) for cur in exchange.currencies.keys()
                          if f"{cur}/USDT" in exchange.markets
                          and exchange.markets[f"{cur}/USDT"]['active'] is True]
        # remove currencies that do not support usdt trading
        for cur in exchange.currencies:
            curr = cur + '/USDT'
            if curr not in exchange.markets:
                try:
                    currency_names.remove(f"{exchange.id}_{cur}")
                except ValueError:
                    pass
        currency_set |= set(currency_names)

        # remove fiat currencies
        if not include_fiat:
            currency_set -= set(['{}_{}'.format(exchange.id, fiat) for fiat in fiat_set])

    logger.info("Now setting currency dict")
    currency_dict = {}
    for curr in currency_set:
        currency = curr.split("_")[-1]
        if currency in currency_dict:
            currency_dict[currency].append(curr)
        else:
            currency_dict[currency] = [curr]
    curr_dict = {}
    for key, val in currency_dict.items():
        if len(val) >= 2:
            curr_dict[key] = val


    return curr_dict

async def get_prices(exchange, coins):
    prices = exchange.fetchTickers(coins)
    return prices

async def fetch_multi_tickers(exchanges:Dict[str, ccxt.Exchange], data:Dict[str, List[str]]) -> Dict[str, Dict]:
    response = {}
    for exchange, tickers in data.items():
        exchange = exchanges[exchange]
        ticker = exchange.fetchTickers(tickers)
        response[exchange.id] = ticker
    return response

def withdraw(from_exchange:ccxt.Exchange, code:str, amount:float, withdraw_detail:Dict):
    if withdraw_detail is None:
        logger.warning("Details not found")
        return False
    address = withdraw_detail['address']
    network = withdraw_detail['trade_network']
    network = network
    tag = withdraw_detail['tag']
    try:
        withdraw_info = from_exchange.withdraw(code, amount, address, tag=tag, params={'network': network})
        logger.info(f"Withdrawal request submitted: {withdraw_info}")
    except Exception as e:
        logger.error(e.json())
        return False

    time.sleep(10)
    while True:
        if from_exchange.has['fetchWithdrawals']:
            withdraws = from_exchange.fetch_withdrawals(code, None, 1)
        elif from_exchange.has['fetchTransactions']:
            withdraws = from_exchange.fetchTransactions(code, None, 1)
        if withdraws[0]['id'] == withdraw_info['id']:
            if withdraws[0]['status'] == 'ok':
                logger.info("Withdrawal complete.")
                return True
            elif withdraws[0]['status'] == 'pending':
                time.sleep(2)
                continue
            elif withdraws[0]['status'] == 'failed' or withdraws[0]['status'] == 'canceled':
                logger.warning(f"Withdrawal {withdraws[0]['status']}")
                return False
        else:
            time.sleep(2)

def monitor_deposit(to_exchange:ccxt.Exchange, quote:str, withdraw:Dict):
    """This monitor a withdraw
    Args:
        to_exchange: The recipient exchange
        quote: The currency to be withdrawn
        withdraw: the dict returned when withdraw was made
    Return:
        True if withdrawal is successful and False if otherwise"""
    
    for _ in range(20):
        if to_exchange.has['fetchDeposits']:
            deposits = (to_exchange.fetch_deposits(quote, None, 1, params={}))
            if len(deposits) > 0:
                if deposits[0]['txid'] == withdraw['txid']:
                    deposit = deposits[0]
                else:
                    print("ids do not match")
                    time.sleep(5)
                    continue
            else:
                time.sleep(2)
                continue
        else:
            time.sleep(180)
            return True

        if deposit['status'] == 'ok':
            return True
        elif deposit['status'] == 'pending':
            time.sleep(5)
            continue
        elif deposit['status'] == 'canceled' or deposit['status'] == 'failed':
            break
        
    return False

def bot(capital:float, exchange:str, keys:Dict, id:str='123456789'):
    n = 0
    total_profits = 0
    prioritized_coin = 'random'
    
    exc = Exchanges(keys)
    init_exchanges = [exc.binance, exc.bingx, exc.bitget, exc.bitmart, exc.bitmex,
                      exc.bybit, exc.gate, exc.huobi, exc.mexc, exc.okex]
    exchanges = set_up_exchanges(init_exchanges, id)
    print("getting coins")
    coins = get_coins(exchanges)
    print("Coins gotten")
    exchange_dict = {}
    for ex in exchanges:
        exchange_dict[ex.id] = ex
    print(exchange_dict)
        
    if exchange not in exchange_dict:
        text = f"Could not authenticate the exchange holding capital: {exchange}"
        print(text)
        notif_dict = {"error": text, "user_id": id, "exit": True}
        notif = Notification(**notif_dict)
        notif.save()
        return

    current_holder = exchange_dict[exchange]
    try:
        capital = float(capital)
    except TypeError:
        text = "Capital must be a number"
        print(text)
        notif_dict = {"error": text, "user_id": id, "exit": True}
        notif = Notification(**notif_dict)
        notif.save()
        return

    # verify capital availability in the selected exchange
    # try:
    #     usdt_balance = (current_holder.fetchBalance())['free'].get('USDT', 0)
    #     if usdt_balance < capital:
    #         text = f"Insufficient balance in {current_holder.id}, available balance: {usdt_balance}"
    #         print(text)
    #         notif_dict = {"error": text, "user_id": id, "exit": True}
    #         notif = Notification(**notif_dict)
    #         notif.save()
    #         return
    # except IndexError as e:
    #     text = f"Insufficient balance in {current_holder.id}, available balance: 0.0"
    #     notif_dict = {"error": text, "user_id": id, "exit": True}
    #     notif = Notification(**notif_dict)
    #     notif.save()
    #     return
    # except Exception as e:
    #     text = f"Error occured: {e}"
    #     notif_dict = {"text": text, "user_id": id, "exit": True}
    #     notif = Notification(**notif_dict)
    #     notif.save()
    #     return

    while True:
        try:
            if prioritized_coin == 'random':
                coin = random.choice(list(coins.keys()))
            else:
                coin = prioritized_coin
            base = coin
            coin += '/USDT'
            quote = coin.split('/')[1]

            # To contain the exchange as key and the coin price as value
            all_prices = {}
            for exchange in exchanges:
                key = f"{exchange.id}_{base}"
                if key in coins[base]:
                    try:
                        price_struct = exchange.fetchTicker(coin)
                        if price_struct['last'] is None:
                            continue
                        all_prices[exchange] = {'ask_price': price_struct['ask'], 'bid_price': price_struct['bid'],
                                                'last': price_struct['last']}
                    except Exception as e:
                        continue
                else:
                    continue

            tickers_sorted_by_ask_price = sorted(all_prices.items(), key=lambda x: x[1]['ask_price'])
            tickers_sorted_by_bid_price = sorted(all_prices.items(), key=lambda x: x[1]['bid_price'])
            buy_price = tickers_sorted_by_ask_price[0][1]['ask_price']
            sell_price = tickers_sorted_by_bid_price[-1][1]['bid_price']
            buy_exchange = tickers_sorted_by_ask_price[0][0]
            sell_exchange = tickers_sorted_by_bid_price[-1][0]

            # calculate all fee
            amount = capital + total_profits
            # fee to withdraw from current_holder to "buy" exchange
            withdraw_detail = get_withdrawal_detail(current_holder, buy_exchange, quote, amount)
            if withdraw_detail == -1:
                print(f"Can not withdraw {quote} from {current_holder}")
                break
            elif withdraw_detail == 1:
                buy_exchange = tickers_sorted_by_ask_price[1][0]
                buy_price = tickers_sorted_by_ask_price[1][1]['last']
                # print(f"Trying the next exchange: {buy_exchange.id}...")
                withdraw_detail = get_withdrawal_detail(current_holder, buy_exchange, quote, amount)
                if withdraw_detail == 1 or withdraw_detail == -1:
                    continue
            trade_network1 = withdraw_detail['trade_network']
            transaction_fee1 = withdraw_detail['fee']
            address1 = withdraw_detail['address']
            tag1 = withdraw_detail['tag']
            rem = capital - transaction_fee1

            # fee to buy coin in "buy" exchange
            buy_amount = rem // buy_price            # Quantity of the coin to buy
            # fee to buy from "buy" exchange
            buy_fee = get_trading_fee(coin, buy_exchange, 'taker', capital)

            # fee to withdraw from "buy" exchange to "sell" exchange
            withdraw_detail2 = get_withdrawal_detail(buy_exchange, sell_exchange, base, buy_amount)

            if withdraw_detail2 == 1:
                # print(f"Could not fetch {base} deposit details on {sell_exchange.id}")
                sell_exchange = tickers_sorted_by_bid_price[-2][0]
                sell_price = tickers_sorted_by_bid_price[-2][1]['last']
                withdraw_detail2 = get_withdrawal_detail(buy_exchange, sell_exchange, base, buy_amount)
                if withdraw_detail2 == 1 or withdraw_detail2 == -1:
                    continue
            elif withdraw_detail2 == -1:
                continue
            trade_network2 = withdraw_detail2['trade_network']
            transaction_fee2 = withdraw_detail2['fee']
            address2 = withdraw_detail2['address']
            tag2 = withdraw_detail2['tag']

            # fee to sell coin in "sell" exchange
            sell_amount = buy_amount - transaction_fee2
            sell_fee = (get_trading_fee(coin, sell_exchange, 'maker', sell_amount)) * sell_price

            sell_cost = sell_amount * sell_price
            transaction_fee = transaction_fee1 + (transaction_fee2 * buy_price)
            gross_profit = sell_cost - capital
            trading_fee = buy_fee + sell_fee

            net_profit = gross_profit - trading_fee - transaction_fee
            if net_profit < 0.04:
                print(f"Discarded {coin}, ({net_profit})")
                prioritized_coin = 'random'
                continue

            text = f"Starting to execute trade with {coin} between {buy_exchange.id} and {sell_exchange.id}\n"
            text += f"Potential profit: {net_profit}"
            print(text)
            notif_dict = {"text": text, "user_id": id}
            notif = Notification(**notif_dict)
            notif.save()
            continue

            # execute the actual trade

            # move funds from current holder to "buy" exchange
            amount = capital + total_profits
            if current_holder != buy_exchange:
                try:
                    withdraw = current_holder.withdraw(quote, amount, address1,
                                                       tag=tag1, params={'network': trade_network1})
                except ccxt.InsufficientBalance:
                    print(f"Not enough balance in {current_holder.id}")
                except Exception as e:
                    print(f"Error encountered while withdrawing {quote} from {current_holder.id} to {sell_exchange.id}")
                    return
                # time.sleep(45)
                stat = monitor_deposit(buy_exchange, quote, withdraw)
                if stat is False:
                    continue

                rem = amount - transaction_fee1
                actual_buy_price = (buy_exchange.fetchTicker(coin))['bids'][0][0]
                actual_buy_amount = rem // actual_buy_price
            else:
                actual_buy_price = buy_price
                actual_buy_amount = amount // actual_buy_price

            # transfer funds to spot wallet and place a buy order
            try:
                buy_exchange.transfer(quote, buy_amount, 'funding', 'spot', params={})
            except Exception as e:
                print(f"Error encountered while transferring funds in {buy_exchange.id} from funding to spot: {e}")
                pass

            cost = trade_coin(coin, buy_exchange, actual_buy_amount, actual_buy_price)
            if not cost:
                # make a second buy attempt if the first fails
                cost = trade_coin(coin, buy_exchange, actual_buy_amount, actual_buy_price)
                if not cost:
                    current_holder = buy_exchange
                    continue

            # buy_cost = actual_buy_amount * actual_buy_price
            buy_cost = cost
            actual_buy_fee = get_trading_fee(coin, buy_exchange, 'taker', buy_cost)

            # withdraw coin from "buy" exchange to "sell" exchange
            withdraw_detail2 = get_withdrawal_detail(buy_exchange, sell_exchange, base, actual_buy_amount)
            if withdraw_detail2 == -1 or withdraw_detail2 == 1:
                # sell the asset if it can't be withdrawn to the sell exchange
                continue
            trade_network2 = withdraw_detail2['trade_network']
            transaction_fee2 = withdraw_detail2['fee']
            address2 = withdraw_detail2['address']
            tag2 = withdraw_detail2['tag']
            try:
                withdraw2 = buy_exchange.withdraw(base, actual_buy_amount, address2, tag=tag2, params={})
            except Exception as e:
                text = f"Error occured while withdrawing {base}: {e}"
                notif_dict = {"error": text, "user_id": id}
                notif = Notification(**notif_dict)
                notif.save()
                return
            # time.sleep(180)
            stat = monitor_deposit(sell_exchange, base, withdraw2)

            # sell the coin in the "sell" exchange
            actual_sell_price = (sell_exchange.fetchTicker(coin))['asks'][0][0]
            actual_sell_amount = actual_buy_amount - transaction_fee2
            try:
                sell_exchange.transfer(base, sell_amount, 'funding', 'spot', params={})
            except Exception as e:
                print(f"Error encountered while transferring {base} in {sell_exchange.id}: {e}")
                pass

            sellsuccess = trade_coin(coin, sell_exchange, actual_sell_amount, actual_sell_price, 'sell')
            if not sellsuccess:
                sellsuccess = trade_coin(coin, sell_exchange, actual_sell_amount, actual_sell_price, 'sell')
                if not sellsuccess:
                    print(f"Could not sell exchange in {sell_exchange.id}")
                    return
                
            # sell_exchange.createLimitSellOrder(coin, actual_sell_amount, actual_sell_price, params={})
            actual_sell_fee = (get_trading_fee(
                coin, sell_exchange, 'maker', actual_sell_amount)) * actual_sell_price
            try:
                sell_exchange.transfer(quote, sell_amount, 'spot', 'funding', params={})
            except Exception as e:
                print("Error encountered while transferring funds:", e)
                pass

            # calculate net profit and gross profit
            actual_trading_fee = actual_buy_fee + actual_sell_fee
            actual_transaction_fee = transaction_fee1 + (transaction_fee2 * actual_buy_price)
            actual_gross_profit = (actual_sell_amount * actual_sell_price) - amount
            total_fee = actual_transaction_fee + actual_trading_fee
            actual_net_profit = actual_gross_profit - total_fee
            total_profits += actual_net_profit

            print(f"Trade {n+1} completed\n")
            print(f"Coin: {coin}")
            if trade_network1:
                print(f"Moved {amount} USDT to {buy_exchange} through \"{trade_network1}\" at a transaction fee of: {transaction_fee1} usdt")
            print(f"Bought {actual_buy_amount:.2f} {base} on {buy_exchange.id} at {actual_buy_price} usdt and a fee of {actual_buy_fee} usdt")
            print(f"Moved {base} from {buy_exchange} to {sell_exchange} through \"{trade_network2}\" at a fee of {transaction_fee2} {base}")
            print(f"Sold {actual_sell_amount:.2f} on {sell_exchange.id} at {actual_sell_price} usdt and a fee of {actual_sell_fee}")
            print(f"Gross profit: {actual_gross_profit} USDT")
            print(f"Total gas fee: {total_fee} USDT")
            print(f"Theoretical net profit: {net_profit} USDT")
            print(f"{Fore.CYAN}Actual net profit: {actual_net_profit} USDT{Style.RESET_ALL}")
            if actual_net_profit < 0:
                print("A loss was incurred")
            else:
                print("Profit was made")
            print(f"Total profits: {total_profits}")
            print(f"Current holder: {sell_exchange.id}")
            current_holder = sell_exchange
            result = f"Trade {n+1} initiated\n\nCoin: {coin}\n"
            if trade_network1:
                result += f"Moved USDT to {buy_exchange} through \"{trade_network1}\" at a transaction fee of: {transaction_fee1} usdt\n\n"
            result += f"Bought {actual_buy_amount:.2f} on {buy_exchange.id} at {actual_buy_price} usdt and a fee of {actual_buy_fee:.2f} usdt\n\n"
            result += f"Moved {base} from {buy_exchange} to {sell_exchange} through \"{trade_network2}\" at a fee of {transaction_fee2:.2f} {base}\n\n"
            result += f"Sold {actual_sell_amount:.2f} on {sell_exchange.id} at {actual_sell_price} usdt and a fee of {actual_sell_fee}\n\n"
            result += f"Gross profit: {actual_gross_profit:.2f}\n\n"
            result += f"Total gas fee: {total_fee:.2f} USDT\n\n"
            result += f"Theoretical net profit: {net_profit:.2f} USDT\n\n"
            result += f"Actual net profit: {actual_net_profit:.2f} usdt\n\n"
            result += f"Total profit: {total_profits:.2f}\n\n"
            result += f"current holder: {current_holder.id}"

            notif_dict = {"text": result, "user_id": id}
            notif = Notification(**notif_dict)
            notif.save()
            # runner.sendTradeData(result)

            # This gives priority to a coin in next trade if its profit is high enough
            if actual_net_profit >= (capital * 0.005):
                prioritized_coin = base
            else:
                prioritized_coin = 'random'
            print()
            n += 1
        except Exception as e:
            text = f"An Error has occured: {e}"
            notif_dict = {"error": text, "user_id": id}
            notif = Notification(**notif_dict)
            notif.save()
            continue

async def find_opp(exchange_tickers:Dict[str, Dict], coin:str, capital:float) -> Dict:
    tickers = {}
    coin = f"{coin}/USDT"
    for exchange, ticks in exchange_tickers.items():
        if coin in ticks:
            tickers[exchange] = ticks[coin]
    tickers_sorted_by_ask = sorted(tickers.items(), key=lambda x: x[1]['ask'] if x[1]['ask'] is not None else float("inf"))
    tickers_sorted_by_bid = sorted(tickers.items(), key=lambda x: x[1]['bid'] if x[1]['bid'] is not None else float("inf"))
    buy_price = tickers_sorted_by_ask[0][1]['ask']
    buy_exchange = tickers_sorted_by_ask[0][0]
    sell_price = tickers_sorted_by_bid[-1][1]['bid']
    sell_exchange = tickers_sorted_by_bid[-1][0]
    if buy_price is None or sell_price is None:
        return {"profit": 0}
    gross_profit = (capital / buy_price) * sell_price
    net_profit = gross_profit - capital
    return {"profit": net_profit, "buy_exchange": buy_exchange, "sell_exchange": sell_exchange,
            "buy_price": buy_price, "sell_price": sell_price, "coin": coin}

async def get_fullName(symbol:str, exchange_id:str)->str:
    try:
        if exchange_id == "binance":
            binance_url = f"https://www.binance.com/bapi/composite/v1/public/marketing/tardingPair/detail?symbol={symbol.upper()}"
            resp = requests.get(binance_url)
            if resp.status_code == 200:
                resp = resp.json()
                fullName = resp['data'][0]['symbol']
                return fullName
        elif exchange_id == "bitmex":
            bitmex_url = f""
            return None
        elif exchange_id == "gate":
            gate_url = f"https://www.gate.io/apiwap/getCoinInfo"
            data = {"curr_type": "SOL"}
            headers = {"Content-Type": "application/json"}
            resp = requests.post(gate_url, data=data, headers=headers)
            if resp.status_code == 200:
                resp = resp.json()
                try:
                    fullName = resp.get['datas']['coininfo']['name']
                except:
                    return None
                return fullName
        elif exchange_id == "bybit":
            bybit_url = f"https://api2.bybit.com/spot/api/token/get/detail?tokenId={symbol.upper()}"
            header = {"Cookie": "deviceId=6253a6c6-50fa-b619-3229-048442b7401a"}
            resp = requests.get(bybit_url, headers=header)
            if resp.status_code == 200:
                resp = resp.json()
                fullName = resp['result']['tokenFullName']
                return fullName
        elif exchange_id == "huobi":
            huobi_url = f"https://www.htx.com/-/x/hbg/v1/important/currency/introduction/detail?currency={symbol.lower()}&r=l5fqb&x-b3-traceid=94b1a61f06e74906d47e25d0a7a9d03f"
            resp = requests.get(huobi_url)
            if resp.status_code == 200:
                resp = resp.json()
                fullName = resp['data']['fullName']
                return fullName
        elif exchange_id == "mexc":
            mexc_url = f"https://www.mexc.com/api/platform/spot/market-v2/web/coin/introduce?coinName={symbol.upper()}"
            resp = requests.get(mexc_url)
            if resp.status_code == 200:
                resp = resp.json()
                fullName = resp['data'].get('sfn')
                return fullName
    except RequestException:
        print("* Your network connection is unstable, please try again later")
        sys.exit(1)
    except Exception as e:
        print("Error:", e)
    return None

async def verify_with_fullName(symbol:str, exchange_1:str, exchange_2)->bool:
    fileName = "fullNames.json"
    if "/" in symbol:
        symbol = symbol.split("/")[0]
    # if exchange_1 == "bitget" or exchange_2 == "bitget":
    #     return True
    try:
        with open(fileName, 'r', encoding='utf-8') as f:
            fullNames = json.load(f)
    except FileNotFoundError:
        fullNames = {}
    fullName_1 = None
    fullName_2 = None

    changeFlag = False
    
    if symbol in fullNames:
        if exchange_1 in fullNames[symbol]:
            fullName_1 = fullNames[symbol][exchange_1]
        if exchange_2 in fullNames[symbol]:
            fullName_2 = fullNames[symbol][exchange_2]
    if fullName_1 is None:
        fullName_1 = await get_fullName(symbol, exchange_1)
        if symbol in fullNames:
            fullNames[symbol][exchange_1] = fullName_1
        else:
            fullNames[symbol] = {exchange_1: fullName_1}
        changeFlag = True
    if fullName_2 is None:
        fullName_2 = await get_fullName(symbol, exchange_2)
        if symbol in fullNames:
            fullNames[symbol][exchange_2] = fullName_2
        else:
            fullNames[symbol] = {exchange_2: fullName_2}
        changeFlag = True

    if changeFlag is True:
        with open(fileName, 'w') as f:
            json.dump(fullNames, f)
    if fullName_1 is None or fullName_2 is None:
        return False
    
    if fullName_1.lower() == fullName_2.lower():
        return True
    else:
        if "".join(fullName_1.split()).lower() in fullName_2.lower() or "".join(fullName_2.split()).lower() in fullName_1.lower():
            return True
    return False

async def load_market(exchange:ccxt.Exchange):
    exchange.load_markets()
    # print("Market loaded for", exchange.id)

def verify_with_cmc(symbols_list:List[str]):
    fileName = 'blacklist.json'
    status = {}
    try:
        with open(fileName, 'r', encoding='utf-8') as f:
            blacklist = json.load(f)
    except FileNotFoundError:
        blacklist = {'blacklist': [], 'whitelist': []}
        pass

    blacklisted_coins = blacklist['blacklist']
    whitelisted_coins = blacklist['whitelist']

    for coin in blacklisted_coins:
        try:
            symbols_list.remove(coin)
        except ValueError:
            pass
    symbols = ",".join(symbols_list)

    headers = {"X-CMC_PRO_API_KEY": handleEnv("cmc_key")}
    url = f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/info?symbol={symbols}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        if resp.status_code == 400:
            err = resp.json()
            bad_coins = err['status']['error_message']
            bad_coins = bad_coins.split(":")[1][1:-1]
            bad_coins = bad_coins[1:]
            print("Bad coins:", bad_coins)
            bad_coins = bad_coins.split(",")
            blacklisted_coins.extend(bad_coins)
            blacklist['blacklist'] = blacklisted_coins
            blacklist['whitelist'] = whitelisted_coins
            with open(fileName, 'w') as f:
                json.dump(blacklist, f)
            return verify_with_cmc(symbols_list)
        print("An error occured while verifying", resp.text, resp.status_code)
        if resp.status_code == 429:
            time.sleep(30)
            verify_with_cmc(symbol)
        sys.exit(1)
    resp = resp.json()

    for symbol in symbols.split(","):
        if symbol in blacklisted_coins:
            status[symbol] = False
            continue
        else:
            for vn, fullName in whitelisted_coins:
                if vn == symbol:
                    status[symbol] = fullName
                    continue
    
            if len(resp['data'][symbol]) > 1:
                blacklisted_coins.append(symbol)
                status[symbol] = False
            else:
                fullName = resp['data'][symbol][0]['name']
                whitelisted_coins.append((symbol, fullName))
                status[symbol] = fullName
    blacklist['blacklist'] = blacklisted_coins
    blacklist['whitelist'] = whitelisted_coins
    with open(fileName, 'w') as f:
        json.dump(blacklist, f)
    return status

async def setup(exchange_list:List[str]=None):
    if exchange_list is None:
        exchange_list = ["binance", "gate", "huobi", "mexc", "bybit"]
    
    # set up the exchanges
    exchanges = []
    for exchange in exchange_list:
        exc = getattr(ccxt, exchange)()
        setattr(exc, "enableRateLimit", True)
        exchanges.append(exc)

    # load markets and create an exchange dict
    logger.info("Loading markets")
    tasks = [load_market(exchange) for exchange in exchanges]
    await asyncio.gather(*tasks)
    exchanges = {exchange.id : exchange for exchange in exchanges}

    # fetch all the coins in each exchange
    coins = await get_coins(list(exchanges.values()))
    exchange_coins = {}
    for coin in coins:
        for market_coin in coins[coin]:
            exchange = market_coin.split("_")[0]
            if exchange in exchange_coins:
                exchange_coins[exchange].append(f"{coin}/USDT")
            else:
                exchange_coins[exchange] = [f"{coin}/USDT"]
    return {"exchanges": exchanges, "exchange_coins": exchange_coins, "coins": coins}

async def find_opportunity(capital:float, data:Dict):
    exchanges = data['exchanges']
    exchange_coins = data['exchange_coins']
    coins = data['coins']
    try:
        # fetch current prices of each coin from each exchange
        tickers = await fetch_multi_tickers(exchanges, exchange_coins)

        # Find opportunities
        tasks = [find_opp(tickers, coin, capital) for coin in coins.keys()]
        opps = await asyncio.gather(*tasks)
        opps = sorted(opps, key=lambda x: x['profit'], reverse=True)
        best_opp = None

        # Verify and filter each opportunity
        for opp in opps:
            if "coin" not in opp or opp['profit'] <= 0:
                continue
            if opp['profit'] > capital:
                continue
            if opp['coin'] in ["MULTI/USDT", "SAITAMA/USDT", "MDX/USDT", "TRIBE/USDT"]:
                continue
            verified = await verify_with_fullName(opp['coin'], opp['buy_exchange'], opp['sell_exchange'])
            if verified is True:
                best_opp = opp
                break
            else:
                time.sleep(1)
        
        if not best_opp:
            logger.info("* No profitable coin found in the selected exchanges *")
            return None
        logger.info(best_opp)
    except ccxt.NetworkError:
        logger.error("* Seems your network connection is inactive. Try again later *\n")
        return None
    except Exception as e:
        logger.warning(traceback.format_exc())
        logger.warning(e)
        return None

    return best_opp

def executor(capital:float, opportunity:Dict):
    if opportunity is None:
        return
    symbol = opportunity['coin']
    buy_exchange = opportunity.get('buy_exchange', None)
    sell_exchange = opportunity.get('sell_exchange', None)
    buy_price = opportunity.get("buy_price", None)
    sell_price = opportunity.get("sell_price", None)

    # set up the exchange instances
    if buy_exchange:
        exchange_1 = getattr(ccxt, buy_exchange)()
        for key, val in exchange_1.requiredCredentials.items():
            if val:
                setattr(exchange_1, key, handleEnv(f"{buy_exchange}_{key}"))
        exchange_1.load_markets()
    if sell_exchange:
        exchange_2 = getattr(ccxt, sell_exchange)()
        for key, val in exchange_2.requiredCredentials.items():
            if val:
                setattr(exchange_2, key, handleEnv(f"{sell_exchange}_{key}"))
        exchange_2.load_markets()

    # calculate the total gas fee paid
    buy_amount = capital / buy_price
    buy_amount = exchange_1.amount_to_precision(symbol, buy_amount)
    buy_fee = get_trading_fee(symbol, exchange_1, 'taker', buy_amount) # in trade currency
    actual_buy_amount = buy_amount - buy_fee
    withdraw_detail = get_withdrawal_detail(exchange_1, exchange_2, symbol.split("/")[0], actual_buy_amount)
    withdraw_fee = withdraw_detail['fee']
    sell_amount = actual_buy_amount - withdraw_fee
    sell_fee = get_trading_fee(symbol, exchange_2, 'maker', sell_amount) # in usdt
    total_fee = (buy_fee * buy_price) + sell_fee + withdraw_fee
    if opportunity['profit'] < total_fee:
        logger.warning("Total gas fee for execution greater than profit.")
        return False

    # buy symbol in the buy_exchange
    buy_cost = trade_coin(symbol, exchange_1, buy_amount, buy_price, 'buy')
    if not buy_cost:
        logger.warning(f"Unable to buy {symbol} in {buy_exchange}")
        return False

    # withdraw the currency to sell exchange
    status = withdraw(exchange_1, symbol.split("/")[0], sell_amount, withdraw_detail)
    if status is False:
        return False
    
    # sell the coin in the sell exchange
    sell_cost = trade_coin(symbol, exchange_2, sell_amount, sell_price, 'sell')
    if not sell_cost:
        logger.warning(f"Unable to sell {symbol} in {sell_exchange}")
        return False

    actual_profit = sell_cost - buy_cost

    logger.info(f"Arbitrage completed! profit made: {actual_profit}")
    return True

async def main(capital:float=100, fetch_once=True, paper_trade=False):
    # exchange_list = []
    wait_time = 5   # minutes
    data = await setup()
    logger.info("Setup complete. Now fetching opportunities")

    if not fetch_once:
        while True:
            best_opp = await find_opportunity(capital, data)
            if paper_trade:
                logger.info("Starting to execute trade...")
                await executor(capital, best_opp)
            time.sleep(wait_time * 60)
    else:
        best_opp = await find_opportunity(capital, data)
        if paper_trade:
            logger.info("Starting to execute trade...")
            await executor(capital, best_opp)

if __name__ == '__main__':
    asyncio.run(main())
