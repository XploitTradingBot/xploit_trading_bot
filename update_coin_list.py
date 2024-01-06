#!/usr/bin/python3

import time
import requests
# from config.exchanges import mexc, gate
from datetime import datetime, timedelta
from model.coin import Coin
from model import storage
# from new_listing import execute, monitor_price


def get_new_coins():
    current_timestamp = int(time.time())
    timestamp = current_timestamp * 1000
    new_coins = []
    mexc_url = f"https://www.mexc.com/api/operation/new_coin_calendar?timestamp={timestamp}"
    gate_url = "https://www.gate.io/apiweb/v1/home/getCoinList?type=4&page=1&pageSize=6&subType=1"
    kucoin_url = "https://www.kucoin.com/_api/currency-front/recently/activities?type=NEWEST&lang=en_US"
    mexc_data = requests.get(mexc_url)
    mexc_data = mexc_data.json()
    mexc_data = mexc_data['data']['newCoins']
    print("Mexc data obtained")

    kucoin_data = requests.get(kucoin_url)
    if kucoin_data.status_code == 200:
        kucoin_data = kucoin_data.json()
        kucoin_data = kucoin_data['data']
        for item in kucoin_data:
            symbol = item['currencyName']
            listing_timest = item['tradeStartAt'] / 1000
            dt = datetime.fromtimestamp(listing_timest)
            print(f"{symbol} will be listed on kucoin on {dt}")
            coin_dict = {'symbol': symbol, "dt": dt, "exchange": "kucoin"}
            new_coins.append(coin_dict)
    else:
        print(f"Error obtaining data from kucoin: {kucoin_data['msg']}")
    print("")

    try:
        for n in range(1, 6):
            gate_url = f"https://www.gate.io/apiweb/v1/home/getCoinList?type=4&page={n}&pageSize=6&subType=1"
            gate_data = requests.get(gate_url)
            if gate_data.status_code != 200:
                print(f"Error: {gate_data.status_code}")
            else:
                gate_data = gate_data.json()['data']['marketList']
                gate_coins = []
                print("Gate data obtained\n")
                for item in gate_data:
                    if item['buy_start_timest'] > current_timestamp:
                        list_time = item['buy_start_timest']
                        dt = datetime.fromtimestamp(list_time)
                        print(f"{item['symbol']} will be listed on gateio on {dt}")
                        coin_dict = {"symbol": item['symbol'], "dt": dt, "exchange": "gate"}
                        gate_coins.append(coin_dict)
                if len(gate_coins) == 0:
                    break
                new_coins.extend(gate_coins)
            time.sleep(1)
    except Exception as e:
        print(f"Error obtaining data from gate.io: {e}")
    print("")
    
    for item in mexc_data:
        list_time = item['firstOpenTime']
        if list_time > timestamp:
            list_time = list_time // 1000
            dt = datetime.fromtimestamp(list_time)
            print(f"{item['vcoinName']} will be listed on mexc on {dt}")
            coin_dict = {"symbol": item['vcoinName'], "dt": dt, "exchange": "mexc"}
            new_coins.append(coin_dict)
    print("")
    return new_coins

def add_coins():
    new_coins = get_new_coins()
    print(new_coins)
    for item in new_coins:
        symbol = item['symbol'] + '/USDT'
        listing_date = item['dt'] + timedelta(hours=1)
        exchange = item['exchange']
        coin_dict = {"symbol": symbol, "exchange": exchange, "listing_date": listing_date}
        coin = storage.search("Coin", symbol=symbol, exchange=exchange)
        if len(coin) > 0:
            print(f"Coin {symbol} already exists")
            if len(coin) > 1:
                for item in coin[1:]:
                    print(f"Coin: {symbol} already exists")
                    item.delete()
            continue
        print(f"Saving {symbol}")
        model = Coin(**coin_dict)
        model.save()


if __name__ == "__main__":
    new_coins = get_new_coins()
    print(new_coins)
    for symbol, info in new_coins.items():
        symbol += '/USDT'
        listing_date = info[0] + timedelta(hours=1)
        coin_dict = {"symbol": symbol, "exchange": info[1], "listing_date": listing_date}
        coin = storage.search("Coin", symbol=symbol, exchange=info[1])
        if len(coin) > 0:
            print(f"Coin {coin[0].symbol} already exists")
            if len(coin) > 1:
                print(f"Multiple coin found for {coin[0].symbol}")
                for item in coin[1:]:
                    item.delete()
            continue
        model = Coin(**coin_dict)
        model.save()
        print(f"{symbol} has been created")
    new_coins = sorted(new_coins.items(), key=lambda x: x[1])
    coin = new_coins[0][0]
    listing_time = new_coins[0][1]
    current_datetime = datetime.now()
    print(f"Time for {coin} listing: {listing_time}")
    # execute(f'{coin}/USDT', listing_time, gate)
    # monitor_price(f'{coin}/USDT', listing_time, mexc)
    