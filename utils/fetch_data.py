from config import exchanges
import pandas as pd
from pprint import pprint


def run(ticker):
    exchanges.kucoin.load_markets()
    orderbook = exchanges.kucoin.fetch_order_book(ticker)
    bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
    ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
    spread = (ask - bid) if (bid and ask) else None

    if (bid and ask and spread):
        return 'Market price for {} \nbid: {}\nask: {}\nspread: {}'.format(ticker, bid, ask, spread)
    else:
        return 'no market price for {}'.format(ticker)
