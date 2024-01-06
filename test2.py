#!/usr/bin/python3

from info import fiat_set
from typing import List, Dict
from update_coin_list import get_new_coins
import ccxt
import asyncio

class FindArbitrage():
    async def load_market(self, exchange:str):
        exchange = getattr(ccxt, exchange)()
        setattr(exchange, 'enableRateLimit', True)
        setattr(exchange, 'nonce', ccxt.Exchange.milliseconds())
        try:
            exchange.load_markets()
            return exchange
        except Exception as e:
            return None

    async def setup_all_exchanges(self)->Dict:
        exchanges = ccxt.exchanges
        tasks = [self.load_market(exchange) for exchange in exchanges]
        exchanges = await asyncio.gather(*tasks)
        return {exchange.id: exchange for exchange in exchanges if exchange is not None}

    def get_coins(self, exchanges:List):
        include_fiat = False
        currency_set = set()
        for exchange in exchanges:
            market_names = [mkt for mkt in exchange.markets if exchange.markets[mkt]['active'] is True]
            usdt_market_names = []
            for mkt in market_names:
                if '/' in mkt and mkt.split('/')[1] == 'USDT':
                    usdt_market_names.append('{}_{}'.format(exchange.id, mkt.split('/')[0]))
            currency_set |= set(usdt_market_names)

            # remove fiat currencies
            if not include_fiat:
                currency_set -= set(['{}_{}'.format(exchange.id, fiat) for fiat in fiat_set])

        currency_dict = {}
        for curr in currency_set:
            currency = curr.split("_")[-1]
            if currency in currency_dict:
                currency_dict[currency].append(curr)
            else:
                currency_dict[currency] = [curr]
        curr_dict = {}
        for key, val in currency_dict.items():
            if len(val) > 2:
                curr_dict[key] = val

        return curr_dict
    # An example of what this function returns: {'BTC': ['binance_BTC', 'kucoin_BTC', 'mexc_BTC', ...], ...}

    async def find_opportunity(self, base:str, capital):
        quote = '/USDT'
        symbol = base + quote
        # print(f"Finding opportunity for {symbol}")
        pair_tickers = {}
        try:
            for exc_mkt in coins[base]:
                exchange = exc_mkt.split('_')[0]
                exchange = exchanges[exchange]
                ticker = exchange.fetchTicker(symbol)
                pair_tickers[exchange.id] = ticker

            price_sorted_by_ask = sorted(pair_tickers.items(), key=lambda x: x[1]['ask'])
            price_sorted_by_bid = sorted(pair_tickers.items(), key=lambda x: x[1]['bid'])

            potential_buy_price = price_sorted_by_ask[0][1]['ask']
            potential_sell_price = price_sorted_by_bid[-1][1]['bid']
            potential_buy_exchange = price_sorted_by_ask[0][0]
            potential_sell_exchange = price_sorted_by_bid[-1][0]

            potential_profit = ((capital / potential_buy_price) * potential_sell_price) - capital

            # print(f"#Market {symbol}: lowest ask order -> {potential_buy_price} on {potential_buy_exchange}\n"
            #     f"highest bid order -> {potential_sell_price} on {potential_sell_exchange}\n"
            #     f"Potential profit (withdrawal fee not included): {potential_profit}")
            return {"symbol": symbol, "profit": potential_profit, "buy_exchange": potential_buy_exchange,
                    "sell_exchange": potential_sell_exchange, "best_bid": potential_sell_price,
                    "best_ask": potential_buy_price}
        except Exception as e:
            print(e)
            return None

    async def find_best_opportunity(self, coins:List, capital):
        bases = list(coins.keys())
        tasks = [self.find_opportunity(base, capital) for base in bases]
        info = await asyncio.gather(*tasks)
        opportunities = [item for item in info if info is not None]
        sorted_opps = sorted(opportunities, key=lambda x: x['profit'], reverse=True)
        best_opp = sorted_opps[0]
        print(best_opp)

    def find_coins(self, new_pairs, exchanges):
        new_coins = []
        for coin in new_pairs:
            coin = coin + '/USDT'
            new_coins.append(coin)

        for exchange in exchanges.values():
            for coin in new_coins:
                if coin in exchange.symbols:
                    try:
                        price = exchange.fetchTicker(coin)['last']
                        if not price:
                            continue
                        print(f"{coin} is already available in {exchange} at {price}")
                    except Exception as e:
                        continue

if __name__ == '__main__':
    print("Setting up exchanges, This may take some seconds...")
    finder = FindArbitrage()
    exchanges = asyncio.run(finder.setup_all_exchanges())
    print(f"Cleared exchanges: {exchanges}")
    print("All exchanges set up, now getting pairs in each exchange...")
    coins = finder.get_coins(list(exchanges.values()))
    print("Coins gotten, now finding opportunities")
    # coins = list(coins.keys())
    while True:
        print("")
        capital = int(input("Please Enter your capital in USDT: "))
        if capital == 0:
            new_pairs = get_new_coins()
            asyncio.run(finder.find_coins(new_pairs, exchanges))
        else:
            finder.find_best_opportunity(coins, capital)
