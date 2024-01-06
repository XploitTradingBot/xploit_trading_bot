#!/usr/bin/python3

from utils.helper import handleEnv
import ccxt
from dotenv import load_dotenv


load_dotenv()

# Crypto Exchanges
binance = ccxt.binance({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
binance.apiKey = handleEnv("binance_apiKey")
binance.secret = handleEnv("binance_secret")


bingx = ccxt.bingx({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
bingx.apiKey = handleEnv("bingx_apiKey")
bingx.secret = handleEnv("bingx_secret")


bitget = ccxt.bitget({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
bitget.apiKey = handleEnv("bitget_apiKey")
bitget.secret = handleEnv("bitget_secret")
bitget.password = handleEnv('bitget_password')


bitmart = ccxt.bitmart({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
bitmart.apiKey = handleEnv("bitmart_apiKey")
bitmart.secret = handleEnv("bitmart_secret")
bitmart.uid = handleEnv("bitmart_uid")


bitmex = ccxt.bitmex({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
bitmex.apiKey = handleEnv("bitmex_apiKey")
bitmex.secret = handleEnv("bitmex_secret")


bybit = ccxt.bybit({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
bybit.apiKey = handleEnv("bybit_apiKey")
bybit.secret = handleEnv("bybit_secret")


coinbase = ccxt.coinbase({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
coinbase.apiKey = handleEnv("coinbase_apiKey")
coinbase.secret = handleEnv("coinbase_secret")


gate = ccxt.gate({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
gate.apiKey = handleEnv("gate_apiKey")
gate.secret = handleEnv("gate_secret")


huobi = ccxt.huobi({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
huobi.apiKey = handleEnv("huobi_apiKey")
huobi.secret = handleEnv("huobi_secret")


# Kraken has to be removed because it does not support deposits and withdrawal
kraken = ccxt.kraken({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
kraken.apiKey = handleEnv("kraken_apiKey")
kraken.secret = handleEnv("kraken_secret")


kucoin = ccxt.kucoin({
    'nonce': ccxt.Exchange.milliseconds
})
kucoin.apiKey = handleEnv("kucoin_apiKey")
kucoin.secret = handleEnv("kucoin_secret")
kucoin.password = handleEnv("kucoin_password")


mexc = ccxt.mexc({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
mexc.apiKey = handleEnv("mexc_apiKey")
mexc.secret = handleEnv("mexc_secret")


okx = ccxt.okx({
    'enableRateLimit': True,
    'nonce': ccxt.Exchange.milliseconds
})
okx.apiKey = handleEnv("okx_apiKey")
okx.secret = handleEnv("okx_secret")
okx.password = handleEnv("okx_password")
