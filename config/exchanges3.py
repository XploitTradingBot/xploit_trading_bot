#!/usr/bin/python3

import ccxt

# Crypto Exchanges
Exchanges = {
    'binance': ccxt.binance({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'bingx': ccxt.bingx({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'bitget': ccxt.bitget({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'bitmart': ccxt.bitmart({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'bitmex': ccxt.bitmex({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'bybit': ccxt.bybit({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'coinbase': ccxt.coinbase({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'gate': ccxt.gate({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'huobi': ccxt.huobi({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    # Kraken has to be removed because it does not support deposits and withdrawal
    'kraken': ccxt.kraken({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'kucoin': ccxt.kucoin({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'mexc': ccxt.mexc({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    }),

    'okx': ccxt.okx({
        'enableRateLimit': True,
        'nonce': ccxt.Exchange.milliseconds
    })
}