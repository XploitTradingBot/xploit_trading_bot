#!/usr/bin/python3

import time

from Work.trading_bot.config.exchange import ExchangePair
from decimal import Decimal
from Work.trading_bot.config.config import ArbitrageConfig

class Arbitrage():
    """entry point for a trade"""

    unit_order = Decimal("50")
    min_profit = Decimal("0.004")

    active_buys = []
    active_sells = []
    closed_trades = []
    
    def __init__(self, pair_1, pair_2):
        """This sets up the exchange pairs"""
        self.exchange_pair_1 = ExchangePair(exchange=pair_1.exchange, trading_coin=pair_1.coin)
        self.exchange_pair_2 = ExchangePair(exchange=pair_2.exchange, trading_coin=pair_2.coin)

    def reset(self):
        """Main function"""
        self.cleanup_trades()
        if len(self.active_buys) < 1:
            buy_executor = self.create_arbitrage(
                buying_pair = self.exchange_pair_1,
                selling_pair = self.exchange_pair_2
            )
            if buy_executor:
                self.active_buys.append(buy_executor)
        if len(self.active_sells) < 1:
            sell_executor = self.create_arbitrage(
                buying_pair = self.exchange_pair_2,
                selling_pair = self.exchange_pair_1
            )
            if sell_executor:
                self.active_sells.append(sell_executor)

    def create_arbitrage(self, buying_pair: ExchangePair, selling_pair: ExchangePair):
        """Initiates trade"""
        coin_balance = 20 # connects to the selling exchange API to obtain available balance
        if self.unit_order > coin_balance:
            raise ValueError("Insufficient tokens found in selling wallet")
        
        # get rate price of coin from selling exchange API
        price = 10000

        # Get available assest balance from buying exchange API
        quote_asset = 500000

        if self.unit_order * price > quote_asset:
            raise ValueError("Insufficient balance in buying wallet")
        
        # Execute the actual trading here
        arb = ArbitrageConfig(buying_market=buying_pair, selling_market=selling_pair,
                              order_amount=self.unit_order, min_profit=self.min_profit)
        pass
        # return arbitrageExecutor instance
        # This arbitrageExecutor instance must have a method "is_closed" which checks if
        # the transaction has been succesfully completed

    def cleanup_trades(self):
        """Ensures completed trades are removed from list"""
        for trade in self.active_buys:
            if trade.is_closed:
                self.closed_trades.append(trade)
                self.active_buys.remove(trade)
        for trade in self.active_sells:
            if trade.is_closed:
                self.closed_trades.append(trade)
                self.active_sells.remove(trade)

if __name__ == '__main__':
    pair_1 = ExchangePair(exchange="binance", trading_coin="BTC-USDT")
    pair_2 = ExchangePair(exchange="gateio", trading_coin="BTC-USDT")
    model = Arbitrage(pair_1, pair_2)

    while True:
        model.reset()
        time.sleep(1)