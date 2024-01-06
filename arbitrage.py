#!/usr/bin/python3

import time
import asyncio
import requests
from typing import List, Dict
import ccxt
from datetime import datetime

current_timestamp = int(time.time())
timestamp = current_timestamp * 1000
mexc_url = f"https://www.mexc.com/api/operation/new_coin_calendar?timestamp={timestamp}"
gate_url = "https://www.gate.io/market_price/get_coin_list"


class NewListing:
    def __init__(self):
        asyncio.run(self.self_initialize())

    async def self_initialize(self):
        print("Loading markets...")
        self.exchanges = await self.load_all_markets()
        print("Markets loaded")
        # self.tickers = self.fetch_tickers(self.exchanges)
        print("Fetching new tokens...")
        self.new_coins = await self.get_coins()
        print("New tokens obtained")
        await self.find_new_coin()

    async def load_markets(self, exchange:str):
        try:
            exchange = getattr(ccxt, exchange)()
            exchange.load_markets()
            print(f"Markets has been loaded for {exchange}")
            return exchange
        except Exception as e:
            print(f"Error encountered when loading markets for {exchange}")
            # await exchange.close()
            return

    async def load_all_markets(self):
        exchanges = ccxt.exchanges
        tasks = [self.load_markets(exchange) for exchange in exchanges]
        return await asyncio.gather(*tasks)

    async def fetch_ticker(self, exchange:ccxt.Exchange):
        active_markets = [mkt for mkt in exchange.markets
                        if exchange.markets[mkt]['active'] if True]
        tickers = await exchange.fetchTickers(active_markets)
        tickers = list(tickers.keys())
        return tickers

    async def fetch_tickers(self, exchanges:List):
        tasks = [self.fetch_ticker(exchange) for exchange in exchanges]
        tickers = await asyncio.gather(*tasks)
        return tickers

    async def get_coins(self)->Dict:
        current_timestamp = int(time.time())
        timestamp = current_timestamp * 1000
        new_coins = {}

        data = requests.get(mexc_url)
        data = data.json()
        mexc_coins = data['data']['newCoins']

        gate_data = requests.post(gate_url, data={'coin_type': 'new-cryptocurrencies',
                                                'page': 1, 'category': 'USDT'})
        gate_data = gate_data.json()['data']['data']
        # print("Data obtained\n")
        for item in gate_data:
            if item['buy_start_timest'] > current_timestamp:
                list_time = item['buy_start_timest']
                dt = datetime.fromtimestamp(list_time)
                # print(f"{item['symbol']} will be listed on gateio on {dt}")
                new_coins[item['symbol']] = dt
        
        for item in mexc_coins:
            list_time = item['firstOpenTime']
            if list_time > timestamp:
                list_time = list_time // 1000
                dt = datetime.fromtimestamp(list_time)
                # print(f"{item['vcoinName']} will be listed on mexc on {dt}")
                new_coins[item['vcoinName']] = dt
        # print("")
        return new_coins

    async def find_new_coin(self):
        coins = self.new_coins
        new_coins = []
        for coin in coins:
            coin = coin + '/USDT'
            new_coins.append(coin)

        for exchange in self.exchanges:
            for coin in new_coins:
                if exchange is not None and coin in exchange.symbols:
                    price = exchange.fetchTicker(coin)['last']
                    if not price:
                        continue
                    print(f"{coin} is already available in {exchange} at {price}")


if __name__ == '__main__':
    coins = asyncio.run(NewListing().self_initialize())