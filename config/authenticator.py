#!/usr/bin/python3

from config.exchanges import binance, bitfinex, bittrex, kraken, kucoin, mexc, okex, poloniex

exchange_list = []

# binance
try:
    if binance.check_required_credentials():
        exchange_list.append(binance)
except Exception as e:
    print("Binance not Authenticated:", e)

#bitfinex
try:
    if bitfinex.check_required_credentials():
        exchange_list.append(bitfinex)
except Exception as e:
    print("Bitfinex not Authenticated:", e)

#bittrex
try:
    if bittrex.check_required_credentials():
        exchange_list.append(bittrex)
except Exception as e:
    print("Bittrex not Authenticated:", e)

# Kraken
try:
    if kraken.check_required_credentials():
        exchange_list.append(kraken)
except Exception as e:
    print("Kraken not Authenticated:", e)

# kucoin
try:
    if kucoin.check_required_credentials():
        exchange_list.append(kucoin)
except Exception as e:
    print("Kucoin not authenticated:", e)

# mexc
try:
    if mexc.check_required_credentials():
        exchange_list.append(mexc)
except Exception as e:
    print("Mexc not authenticated:", e)

# okex
try:
    if okex.check_required_credentials():
        exchange_list.append(okex)
except Exception as e:
    print("Okex not Authenticated:", e)

# poloniex
try:
    if poloniex.check_required_credentials():
        exchange_list.append(poloniex)
except Exception as e:
    print("Poloniex not Authenticated:", e)