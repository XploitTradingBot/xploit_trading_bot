#!/usr/bin/python3

import random
from config.exchanges import binance, bitfinex, bittrex, gate, kraken, kucoin, mexc, okex, poloniex

init_exchanges = [binance, bitfinex, bittrex, gate, kraken, kucoin, mexc, okex, poloniex]

def load_markets(exchanges):
    cleared_exchanges = []
    for exchange in exchanges:
        try:
            exchange.load_markets()
            try:
                if exchange.check_required_credentials():
                    if hasattr(exchange, "fetchBalance"):
                        try:
                            exchange.fetchBalance()
                            print(f"{exchange.id} has been cleared to trade")
                            cleared_exchanges.append(exchange)
                        except Exception as e:
                            print(f"❌❌ {exchange.id} not properly set up: {e}")
                            print(f"API key = {exchange.apiKey}")
                            print(f"Secret = {exchange.secret}")
                            print(f"passphrase = {exchange.password}")
                    else:
                        print(f"{exchange.id} has been cleared to trade, no balance checked")
                else:
                    print(f"{exchange.id} has missing or incomplete credentials")
            except Exception as e:
                print(f"Incomplete/Invalid credentials passed for {exchange.id}:", e)
        except Exception as e:
            print("Unable to load markets of", exchange.id, ":", e)
            print(f"ApiKey = {exchange.apiKey}")
            print(f"Secret key = {exchange.secret}")
    return cleared_exchanges

def main():
    print("Initiating bot...⏳⏳")
    cleared_exchanges = load_markets(init_exchanges)
    return cleared_exchanges

exchanges = main()
print()
transact_fees = {}
exchanges2 = []
for exchange in exchanges:
    dict_fee = {}
    try:
        network_fee_struct = exchange.fetchDepositWithdrawFee('USDT')
    except Exception as e:
        print(f"Could not fetch transaction fee info for {exchange.id}")
        # exchanges.remove(exchange)
        continue
    try:
        for network in network_fee_struct['networks']:
            dict_fee[network] = network_fee_struct['networks'][network]['withdraw']['fee']
    except Exception as e:
        continue
    exchanges2.append(exchange)
    dict_fee = dict(sorted(dict_fee.items(), key=lambda x: x[1]))
    transact_fees[exchange.id] = dict_fee
print(transact_fees)
exchanges = exchanges2

print("✅Initiation completed with exchanges:", [ exchange.id for exchange in exchanges ])
print("==========================================")
print()

coins = ['BTC/USDT', 'XRP/USDT', 'IOST/USDT', 'ZIL/USDT', 'VET/USDT', 'DOGE/USDT', 'TRX/USDT',
         'ALGO/USDT', 'XLM/USDT', 'IOTA/USDT', 'ONT/USDT', 'BAT/USDT', 'ZRX/USDT', 'ADA/USDT',
         'ATOM/USDT', 'AAVE/USDT', 'ALICE/USDT', 'APE/USDT', 'AVAX/USDT', 'AVA/USDT', 'BTT/USDT']

n = 0
total_profits = 0
capital = 500       # in usdt
trade_network = None
current_holder = exchanges[0]

while n < 10:                        # This runs only 10 trades before terminating
    try:
        coin = random.choice(coins)     # choose a random coin from the coins list
        all_prices = {}                 # To contain the exchange as key and the coin price as value
        for exchange in exchanges:
            symbols = exchange.symbols  # symbols is a list of all the supported coins on the exchange
            if coin in symbols:         # If the randomly selected coin is supported on the exchange
                try:
                    orders = exchange.fetchOrderBook(coin)
                except Exception as e:
                    print(e)
                    try:
                        orders = exchange.fetchOrderBook(coin)
                    except Exception as e:
                        print(e)
                        continue
                # orders = exchange.fetchOrderBook(coin)
                price = orders['bids'][0][0]    # Get the current price of the coin from the exchange
                all_prices[exchange] = price
        
        all_prices = sorted(all_prices.items(), key=lambda x: x[1])
        min_price = all_prices[0][1]            # This is the minimum price from all the exchanges
        max_price = all_prices[-1][1]           # This is the max price from all the exchanges
        buy_exchange = all_prices[0][0]
        sell_exchange = all_prices[-1][0]

        # calculate trading fee
        buy_amount = capital / min_price            # Quantity of the coin to buy assuming a starting capital of 100usdt
        buy_fee_struct = buy_exchange.markets[coin]     # obtain the fee structure to buy the coin from the exchange
        if buy_fee_struct['percentage'] is True:
            # print("Trading fee is a percentage")
            buy_fee = buy_fee_struct['taker'] * capital # multiply by the intended buy volume (1000)
        else:
            buy_fee = buy_fee_struct['taker']
        
        sell_cost = buy_amount * max_price
        sell_fee_struct = sell_exchange.markets[coin]
        if sell_fee_struct['percentage']:
            sell_fee = sell_fee_struct['maker'] * sell_cost
        else:
            sell_fee = sell_fee_struct['maker']

        # calculate transaction fee
        # This is divided into two parts: withdrawal from current holder to "buy" exchange 
        # and withdrawal from "buy" exchange to "sell" exchange
        transaction_fee1 = None      # fee to move funds from current holding exchange to the buy exchange
        trade_network1 = None
        if current_holder.id != buy_exchange.id:
            for network, fee in transact_fees[current_holder.id].items():
                if network in transact_fees[buy_exchange.id]:
                    transaction_fee1 = fee
                    trade_network1 = network
                    break
            if not transaction_fee1 or not trade_network1:
                continue
        else:
            transaction_fee1 = 0
        
        transaction_fee2 = None         # fee to move funds from buy exchange to sell exchange
        trade_network2 = ""
        for network, fee in transact_fees[buy_exchange.id].items():
            if network in transact_fees[sell_exchange.id]:
                transaction_fee2 = fee
                trade_network2 = network
                break
        if not transaction_fee2:
            continue

        transaction_fee = transaction_fee1 + transaction_fee2
        gross_profit = sell_cost - capital
        trading_fee = buy_fee + sell_fee
        net_profit = gross_profit - trading_fee - transaction_fee
        if net_profit < 0:
            continue
        code = coin.split('/')[1]
        
        if buy_exchange.has['fetchDepositAddress']:
            try:
                address1 = buy_exchange.fetchDepositAddress(code, params={"network": trade_network1})
                address2 = buy_exchange.fetchDepositAddress(code, params={"network": trade_network2})
            except Exception as e:
                print(e)
                try:
                    address1 = buy_exchange.createDepositAddress(code, params = {"network": trade_network1})
                    address2 = buy_exchange.createDepositAddress(code, params = {"network": trade_network2})
                except Exception as e:
                    print(trade_network)
                    print(f"No address found for {code} in {buy_exchange.id}:", e)
                    continue
        elif buy_exchange.has['createDepositAddress']:
            address1 = buy_exchange.createDepositAddress(code, params = {"network": trade_network1})
            address2 = buy_exchange.createDepositAddress(code, params = {"network": trade_network2})
        else:
            print(f"No address found for {code} in {buy_exchange.id}")
            continue
        # if current_holder != buy_exchange:      # withdraw funds from current holding exchange to buy exchange
            # current_holder.withdraw(code, buy_amount, address1, tag=None, params={})
        # buy_exchange.createLimitBuyOrder(coin, buy_amount, min_price, params={})
        # buy_exchange.withdraw(code, buy_amount, address2, tag=None, params={})
        # sell_exchange.createOrder(coin, 'limit', 'sell', buy_amount, price=max_price, params={})

        print(f"Trade {n+1} initiated:")
        print(f"Bought on {buy_exchange.id} at {all_prices[0][1]} and sold on {sell_exchange.id} at {all_prices[-1][1]}")
        print(f"Gross profit: {gross_profit}\nTrading fee: {trading_fee}")
        print(f"Moved to {buy_exchange} through \"{trade_network}\" at a transaction fee of: {transaction_fee1}")
        print(f"Moved from {buy_exchange} to {sell_exchange} through \"{trade_network2}\" at a fee of {transaction_fee2}")
        print(f"Coin: {coin}")
        print(f"Total transaction fee: {transaction_fee}")
        print(f"Net profit: {net_profit}")
        print(f"Current holder: {current_holder.id}")
        total_profits += net_profit
        if net_profit < 0:
            print("A loss was incurred")
        else:
            print("Profit was made")
        print(f"Total profits: {total_profits}")
        print()
        current_holder = sell_exchange
        n += 1
    except Exception as e:
        print(f"Error: {e}")
        continue
    