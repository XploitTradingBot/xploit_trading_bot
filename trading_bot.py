#!/usr/bin/python3

import sys
import json
import time
import ccxt
import asyncio
import requests
from requests.exceptions import RequestException
from typing import Dict, List
from utils.logging import adapter
from utils.helper import handleEnv
from info import fiat_set
from config.exchanges import *

exchanges = {"binance": binance, "bingx": bingx, "bitmart": bitmart,
             "bitget": bitget, "bitmex": bitmex, "bybit": bybit,
             "huobi": huobi, "mexc": mexc, "okx": okx, "kucoin": kucoin, "gate": gate}



async def load_market(exchange:ccxt.Exchange):
    exchange.load_markets()

async def get_coins(exchanges:List[ccxt.Exchange], include_fiat=False) -> Dict:
    """This sets up all the coins in the specified exchanges
    Args:
        exchanges: A list of all the cleared ccxt.Exchange exchanges
    Return:
        A dict with keys of ticker symbol and values of list in format <exchange.id>_<symbol>"""
    currency_set = set()
    for exchange in exchanges:
        currency_names = ['{}_{}'.format(exchange.id, cur) for cur in exchange.currencies.keys()
                        if exchange.currencies[cur]['deposit'] is True
                        and exchange.currencies[cur]['withdraw'] is True]
        # remove currencies that do not support usdt trading
        for cur in exchange.currencies:
            curr = cur + '/USDT'
            if curr not in exchange.markets or exchange.markets[curr]['active'] is False:
                try:
                    currency_names.remove(f"{exchange.id}_{cur}")
                except ValueError:
                    pass
        currency_set |= set(currency_names)

        # remove fiat currencies
        if not include_fiat:
            currency_set -= set(['{}_{}'.format(exchange.id, fiat) for fiat in fiat_set])

    # adapter.info("Now setting currency dict")
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

async def setup(exchange_list:List[str]):
    """This sets up the exchanges and fetches the coins from the exchanges
    Args:
        exchange_list: A list of exchanges to work with. Defaults to ['binance', 'gate', 'huobi', 'mexc', 'bybit']
                        if not provided
    Return:
        A dict containing the exchanges and the coins"""
    
    # set up the exchanges
    exchanges = []
    for exchange in exchange_list:
        exc = getattr(ccxt, exchange)()
        setattr(exc, "enableRateLimit", True)
        exchanges.append(exc)

    # load markets and create an exchange dict
    adapter.info("Setting up markets")
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

def get_trading_fee(coin:str, exchange:ccxt.Exchange, type:str, amount:float) -> float:
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

    from_ntwks = from_exchange.currencies[code]['networks']
    if from_ntwks is not None:
        from_networks = {network: from_ntwks[network]['fee'] for network in from_ntwks
                        if from_ntwks[network]['active'] is True}
    else:
        if from_exchange.has.get('fetchDepositWithdrawalFees', None) or from_exchange.has.get('fetchDepositWithdrawFees'):
            try:
                from_networks = {}
                fee_struct = from_exchange.fetchDepositWithdrawFees(code, params={})
                if "T" in fee_struct:
                    fee_struct = fee_struct["T"]
                if 'networks' in fee_struct:
                    fee_struct = fee_struct['networks']
                    for network, info in fee_struct.items():
                        if info['withdraw']['percentage'] is True:
                            from_networks[network] = info['withdraw']['fee'] * amount
                        else:
                            from_networks[network] = info['withdraw']['fee']
            except Exception as e:
                from_ntwks = from_exchange.currencies[code]['networks']
                from_networks = {network: from_ntwks[network]['fee'] for network in from_ntwks
                                if from_ntwks[network]['active'] is True}
        else:
            from_ntwks = from_exchange.currencies[code]['networks']
            from_networks = {network: from_ntwks[network]['fee'] for network in from_ntwks
                            if from_ntwks[network]['active'] is True}
            
    # adapter.info("Code reach here")
    if len(from_networks) == 0:
        from_ntwks = from_exchange.currencies[code]['networks']
        from_networks = {network: from_ntwks[network]['fee'] for network in from_ntwks
                        if from_ntwks[network]['active'] is True}
    # adapter.info("Code reach here too")
    from_networks = dict(sorted(from_networks.items(), key=lambda x: x[1]))
    # adapter.info(f"Available networks in {from_exchange.id}: {from_networks}")
    address_struct = None
    try:
        to_nets = list((to_exchange.fetchDepositWithdrawFee(code, params={}))['networks'].keys())
    except Exception as e:
        try:
            to_nets = to_exchange.currencies[code]['networks']
            to_nets = [net for net in to_nets if to_nets[net]['active'] is True]
        except Exception as e:
            return 1
    # adapter.info(f"Available networks in {to_exchange.id}: {to_nets}")

    sim_addr = {"BEP20": "BSC", "BSC": "BEP20", "ETH": "ERC20", "ERC20": "ETH", "TRX": "TRC20", "TRC20": "TRX",
                "BNB": "BEP2", "BEP2": "BNB", "HT": "HECO", "HECO": "HT", "MATIC": "POLYGON", "POLYGON": "MATIC",
                "ADA": "CARDANO", "CARDANO": "ADA"}
    network = None
    for net in from_networks:
        # print("Finding matching network for", net)
        for to_net in to_nets:
            if net.lower() in to_net.lower() or to_net.lower() in net.lower():
                if (net == "BEP2" and to_net == "BEP20") or (net == "BEP20" and to_net == "BEP2"):
                    continue
                # print("Match found", to_net)
                return {'trade_network': net, 'fee':from_networks[net]}
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

def trade_coin(coin:str, exchange:ccxt.Exchange, amount:float, price:float, side='buy') -> (float | None):
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
        adapter.error(e)
        return None

async def fetch_multi_tickers(exchanges:Dict[str, ccxt.Exchange], data:Dict[str, List[str]]) -> Dict[str, Dict]:
    response = {}
    for exchange, tickers in data.items():
        exchange = exchanges[exchange]
        ticker = exchange.fetchTickers(tickers)
        response[exchange.id] = ticker
    return response

def withdraw(from_exchange:ccxt.Exchange, code:str, amount:float, withdraw_detail:Dict):
    if withdraw_detail is None:
        adapter.warning("Details not found")
        return False
    address = withdraw_detail['address']
    network = withdraw_detail['trade_network']
    network = network
    tag = withdraw_detail['tag']
    try:
        withdraw_info = from_exchange.withdraw(code, amount, address, tag=tag, params={'network': network})
        adapter.info(f"Withdrawal request submitted: {withdraw_info}")
    except Exception as e:
        adapter.error(e.json())
        return False

    time.sleep(10)
    while True:
        if from_exchange.has['fetchWithdrawals']:
            withdraws = from_exchange.fetch_withdrawals(code, None, 1)
        elif from_exchange.has['fetchTransactions']:
            withdraws = from_exchange.fetchTransactions(code, None, 1)
        if withdraws[0]['id'] == withdraw_info['id']:
            if withdraws[0]['status'] == 'ok':
                adapter.info("Withdrawal complete.")
                return True
            elif withdraws[0]['status'] == 'pending':
                time.sleep(2)
                continue
            elif withdraws[0]['status'] == 'failed' or withdraws[0]['status'] == 'canceled':
                adapter.warning(f"Withdrawal {withdraws[0]['status']}")
                return False
        else:
            time.sleep(2)

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
        elif exchange_id == "bitmex": # not supported
            bitmex_url = f""
            return None
        elif exchange_id == "gate":
            gate_url = f"https://www.gate.io/apiwap/getCoinInfo"
            data = {"curr_type": symbol.upper()}
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
        elif exchange_id == 'bitget': # not supported
            bitget_url = "https://www.bitget.com/v1/cms/crypto/getCryptoBySymbol"
            data = {"languageType": 0, "symbol": symbol.upper()}
            resp = requests.post(bitget_url, data=data)
        elif exchange_id == 'okx':
            ts = int(time.time() * 1000)
            okx_url = f"https://www.okx.com/v2/support/info/announce/detail?t={ts}&projectName={symbol.upper()}"
            resp = requests.get(okx_url)
            if resp.status_code == 200:
                resp = resp.json()
                fullName = resp['data']['fullName']
                return fullName
        elif exchange_id == 'bingx': # not supported
            symbol + symbol.upper() + "USDT"
            bingx_url = f"https://bingx.com/api/coin/v1/quotation/get-detail-by-symbol?bizType=30&symbol={symbol}"
        elif exchange_id == 'bitmart':
            # could also fetch fullname from exchange.currencies[symbol]['name']
            ts = int(time.time() * 1000)
            bitmart_url = f"https://www.bitmart.com/gw-api/ds/find_coin_details?lang=en_US&timestamp={ts}&type=TOKEN_INSIGHT&coinName={symbol}"
            resp = requests.get(bitmart_url)
            if resp.status_code == 200:
                resp = resp.json()
                fullName = resp['data']['details']['coinFullName']
                return fullName
        elif exchange_id == 'kucoin':
            kucoin_url = f"https://www.kucoin.com/_api/quicksilver/universe-currency/symbols/info/{symbol.upper()}"
            resp = requests.get(kucoin_url)
            if resp.status_code == 200:
                resp = resp.json()
                fullName = resp['data']['coinName']
                return fullName
    except RequestException:
        print("* Your network connection is unstable, please try again later")
        return None
    except Exception as e:
        print("Error:", e)
    return None

async def verify_with_fullName(symbol:str, exchange_1:str, exchange_2:str)->bool:
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

    # verify with cmc first, then with fullNames
    if fullName_1 is None or fullName_2 is None:
        return False

    if fullName_1.lower() not in fullName_2.lower():
        return False

    if fullName_1 is not None:
        status = verify_with_cmc(fullName_1, exchange_1, exchange_2)
        if status is True:
            # adapter.info(f"{symbol} verified with cmc")
            return True
    if fullName_2 is not None:
        status = verify_with_cmc(fullName_2, exchange_1, exchange_2)
        if status is True:
            # adapter.info(f"{symbol} verified with cmc")
            return True
        
    if fullName_1.lower() == fullName_2.lower():
        return True
    else:
        if "".join(fullName_1.split()).lower() in fullName_2.lower() or "".join(fullName_2.split()).lower() in fullName_1.lower():
            return True
    return False

def verify_with_cmc(coinName:str, exchange_1:str, exchange_2:str) ->bool:
    coinName = "-".join(coinName.split())
    coinName = coinName.lower()
    baseurl = f"https://api.coinmarketcap.com"
    endpoint = f"/data-api/v3/cryptocurrency/market-pairs/latest"
    query_string = f"?slug={coinName}&start=1&limit=20&quoteCurrencyId=825&category=spot&centerType=cex&sort=cmc_rank_advanced&direction=desc&spotUntracked=true"
    url = baseurl + endpoint + query_string
    resp = requests.get(url)
    second_names = {"gate": "gate-io", "huobi": "htx"}
    if resp.status_code == 200:
        resp = resp.json()
        if resp['status']['error_message'] == 'SUCCESS':
            marketPairs = [mp['exchangeSlug'] for mp in resp['data']['marketPairs']]
            if exchange_1.lower() in marketPairs and exchange_2.lower() in marketPairs:
                return True
            else:
                if exchange_1 in second_names:
                    exchange_1 = second_names[exchange_1]
                if exchange_2 in second_names:
                    exchange_2 = second_names[exchange_2]
                if exchange_1.lower() in marketPairs and exchange_2.lower() in marketPairs:
                    return True
        else:
            adapter.warning(f"Could not verify {coinName} with cmc")
            return False
    else:
        adapter.warning(f"Error obtained while verifying {coinName} with cmc")
        return False

async def find_opportunity(capital:float, data:Dict):
    """This finds the best arbitrage path
    Args:
        capital: The starting balance
        Data: A dict containing all the necessary info
    Returns:
        None if no profitable path is found else Dict containing path info if otherwise"""

    exchanges = data['exchanges']
    exchange_coins = data['exchange_coins']
    coins = data['coins']
    try:
        # Fetch current prices of each coin from each exchange
        tickers = await fetch_multi_tickers(exchanges, exchange_coins)

        # Find opportunities
        tasks = [find_opp(tickers, coin, capital) for coin in coins.keys()]
        opps = await asyncio.gather(*tasks)
        opps = sorted(opps, key=lambda x: x['profit'], reverse=True)
        opps = [opp for opp in opps if "coin" in opp and opp['profit'] > 1]
        adapter.info(f"{len(opps)} opportunities found")
        # best_opps = []

        # Verify and filter each opportunity
        adapter.info("Now verifying opportunities")

        # for opp in opps:
        async def get_best_opp(opp:Dict):
            if "coin" not in opp or opp['profit'] <= 0:
                return None
                # continue
            if opp['profit'] > capital:
                return None
                # continue
            # blacklist
            if opp['coin'] in ["VELO/USDT"]:
                return None
                # continue
            try:
                verified = await verify_with_fullName(opp['coin'], opp['buy_exchange'], opp['sell_exchange'])
            except Exception:
                return None
            if verified is True:
                # adapter.info(f"{opp['coin']} has been verified between {opp['buy_exchange']} and {opp['sell_exchange']}")
                status = await executor(capital, opp, exchanges)
                if status is False:
                    return None
                    # continue
                if status['total_fee'] > opp['profit'] - 5:
                    gross_profit = status['total_fee'] + 5
                    min_capital = (capital * gross_profit) / opp['profit']
                    opp['min_cap'] = min_capital
                    adapter.info(f"coin found: {opp}")
                    # best_opps.append(opp)
                    return opp
                else:
                    opp['min_cap'] = capital
                    adapter.info(f"coin found: {opp}")
                    return opp
            else:
                # time.sleep(0.5)
                return None
            # if len(best_opps) >= 3:
            #     break

        tasks = [get_best_opp(opp) for opp in opps]
        verified_opps = await asyncio.gather(*tasks)
        verified_opps = [opp for opp in verified_opps if opp is not None and opp['profit'] > 5]
        sorted_verified_opps = sorted(verified_opps, key=lambda x: x['min_cap'])
        
        # if len(best_opps) == 0:
        #     adapter.info("* No profitable coin found in the selected exchanges *")
        #     return None
        adapter.info(sorted_verified_opps[:10])
        return sorted_verified_opps
    except ccxt.NetworkError:
        adapter.error("* Seems your network connection is inactive. Try again later *")
        sys.exit(1)
    except Exception as e:
        print(e.__traceback__.tb_lineno)
        # adapter.warning(traceback.format_exc())
        adapter.warning(e)
        return None

    # return best_opps

async def executor(capital:float, opportunity:Dict, exchanges:Dict, keys:Dict={}, execute:bool=False):
    """This executes the trade on both exchanges
    Args:
        capital: The starting balance
        opportunity: A dict containing necessary info
        keys: A dict containing the user api keys in a format
    Return:
        True if transaction completes, and False if otherwise"""
    
    if opportunity is None:
        return False
    symbol = opportunity['coin']
    buy_exchange = opportunity.get('buy_exchange', None)
    sell_exchange = opportunity.get('sell_exchange', None)
    buy_price = opportunity.get("buy_price", None)
    sell_price = opportunity.get("sell_price", None)

    # set up the exchange instances
    exchange_1 = exchanges[buy_exchange]
    exchange_2 = exchanges[sell_exchange]
    if buy_exchange:
        for key, val in exchange_1.requiredCredentials.items():
            if val:
                ky = keys.get(f"{buy_exchange}_{key}", handleEnv(f"{buy_exchange}_{key}"))
                setattr(exchange_1, key, ky)
    if sell_exchange:
        for key, val in exchange_2.requiredCredentials.items():
            if val:
                setattr(exchange_2, key, keys.get(f"{sell_exchange}_{key}",
                                                handleEnv(f"{sell_exchange}_{key}")))

    # calculate the total gas fee paid
    buy_amount = capital / buy_price
    buy_amount = float(exchange_1.amount_to_precision(symbol, buy_amount))
    buy_fee = get_trading_fee(symbol, exchange_1, 'taker', buy_amount) # in trade currency
    actual_buy_amount = buy_amount - buy_fee
    # adapter.info("Obtained taker trading fee")
    withdraw_detail = get_withdrawal_detail(exchange_1, exchange_2, symbol.split("/")[0], actual_buy_amount)
    # adapter.info("Withdrawal details obtained")
    if not withdraw_detail:
        adapter.warning(f"No withdrawal path found for {symbol} between {exchange_1} and {exchange_2}")
        return False
    if withdraw_detail['fee']:
        withdraw_fee = withdraw_detail['fee'] * buy_price
    else:
        withdraw_fee = 0
    sell_amount = actual_buy_amount - withdraw_fee
    sell_fee = get_trading_fee(symbol, exchange_2, 'maker', sell_amount) # in usdt
    total_fee = (buy_fee * buy_price) + sell_fee + withdraw_fee
    # if opportunity['profit'] < total_fee:
    #     adapter.warning("Total gas fee for execution greater than profit.")
    #     return False

    # opportunity['profit'] = opportunity['profit'] - total_fee
    opportunity['total_fee'] = total_fee
    opportunity['withdraw_network'] = withdraw_detail['trade_network']
    opportunity['withdraw_fee'] = withdraw_fee
    # opportunity['profit'] = opportunity['profit'] - total_fee
    # adapter.info(f"Executor completed: {opportunity}")
    if not execute:
        return opportunity

    # buy symbol in the buy_exchange
    buy_cost = await trade_coin(symbol, exchange_1, buy_amount, buy_price, 'buy')
    if not buy_cost:
        adapter.warning(f"Unable to buy {symbol} in {buy_exchange}")
        return False

    # withdraw the currency to sell exchange
    status = await withdraw(exchange_1, symbol.split("/")[0], sell_amount, withdraw_detail)
    if status is False:
        return False
    
    # sell the coin in the sell exchange
    sell_cost = await trade_coin(symbol, exchange_2, sell_amount, sell_price, 'sell')
    if not sell_cost:
        adapter.warning(f"Unable to sell {symbol} in {sell_exchange}")
        return False

    actual_profit = sell_cost - buy_cost

    adapter.info(f"Arbitrage completed! profit made: {actual_profit}")
    return True

async def main(capital:float, exchange_list:List=None, fetch_once=True, paper_trade=False, keys:Dict={}):
    adapter.info("You have started the bot")
    if exchange_list is None:
        exchange_list = ['binance', 'bitmex', 'huobi', 'bingx', 'bitget', 'mexc',
                           'bybit', 'gate', 'okx', 'kucoin']
    wait_time = 5   # minutes
    try:
        data = await setup(exchange_list)

        if not fetch_once:
            while True:
                from run_telegram import exit_signal
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
                    # result_string = f"Symbol      - {opp['coin']}\n"
                    # result_string += f"Minimum capital - {opp['min_cap']:.2f}\n"
                    # result_string += f"Buy on      - {opp['buy_exchange']}\n"
                    # result_string += f"Buy price   - {opp['buy_price']} or current market price\n"
                    # if "withdraw_network" in opp:
                    #     result_string += f"Withdraw network - {opp['withdraw_network']}\n"
                    # result_string += f"Sell on     - {opp['sell_exchange']}\n"
                    # result_string += f"sell price  - {opp['sell_price']} or current market price\n"
                    # # result_string += f"Potential profit - {opp['profit']:.2f}%"
                    
                    # await send_report(result_string, opp)
                time.sleep(wait_time * 60)
        else:
            best_opp = await find_opportunity(capital, data)
            if not best_opp:
                adapter.warning("No profitable coin gotten")
                sys.exit(1)
            adapter.info(best_opp)
            for opp in best_opp:
                # result_string = f"Symbol     - {opp['coin']}\n"
                # result_string += f"Minimum capital - {opp['min_cap']:.2f}\n"
                # result_string += f"Buy on     - {opp['buy_exchange']}\n"
                # result_string += f"Buy price  - {opp['buy_price']} or current market price\n"
                # if "withdraw_network" in opp:
                #     result_string += f"Withdraw network - {opp['withdraw_network']}\n"
                # result_string += f"Sell on    - {opp['sell_exchange']}\n"
                # result_string += f"sell price - {opp['sell_price']} or current market price\n"
                # # result_string += f"Potential profit - {opp['profit']:.2f}%"
                from run_telegram import send_report
                await send_report(opp)

    except ccxt.NetworkError as e:
        adapter.error(f"Bot stopped due to a network error: {e}")
        sys.exit(1)
    except ccxt.ExchangeError as e:
        adapter.error(f"Bot stopped due to an exchange error: {e}")
        asyncio.run(main(capital, fetch_once=fetch_once))
    except Exception as e:
        adapter.error(f"Bot stopped due to an unexpected error: {e}, line: {e.__traceback__.tb_lineno}")

if __name__ == '__main__':
    asyncio.run(main(100, ['binance', 'bitmex', 'huobi', 'bingx', 'bitget', 'mexc',
                           'bybit', 'gate', 'okx', 'kucoin'], paper_trade=False, fetch_once=True))
