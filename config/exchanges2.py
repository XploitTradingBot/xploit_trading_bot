#!/usr/bin/python3

# from utils.helper import handleEnv
import ccxt
from dotenv import load_dotenv
from utils.helper import handleEnv


load_dotenv()

class Exchanges():
    # Crypto Exchanges
    def __init__(self, keys:dict):
        self.binance = ccxt.binance({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.binance.apiKey = keys.get("binance_key", handleEnv("binance_apiKey"))
        self.binance.secret = keys.get("binance_secret", handleEnv("binance_secret"))


        self.bingx = ccxt.bingx({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.bingx.apiKey = keys.get("bingx_key", handleEnv("bingx_apiKey"))
        self.bingx.secret = keys.get("bingx_secret", handleEnv("bingx_secret"))


        self.bitget = ccxt.bitget({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.bitget.apiKey = keys.get("bitget_key", handleEnv("bitget_apiKey"))
        self.bitget.secret = keys.get("bitget_secret", handleEnv("bitget_secret"))
        self.bitget.password = keys.get("bitget_password", handleEnv("bitget_password"))


        self.bitmart = ccxt.bitmart({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.bitmart.apiKey = keys.get("bitmart_key", handleEnv("bitmart_apiKey"))
        self.bitmart.secret = keys.get("bitmart_secret", handleEnv("bitmart_secret"))
        self.bitmart.password = keys.get("bitmart_uid", handleEnv("bitmart_uid"))


        self.bitmex = ccxt.bitmex({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.bitmex.apiKey = keys.get("bitmex_key", handleEnv("bitmex_apiKey"))
        self.bitmex.secret = keys.get("bitmex_secret", handleEnv("bitmex_secret"))


        self.bybit = ccxt.bybit({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.bybit.apiKey = keys.get("bybit_key", handleEnv("bybit_apiKey"))
        self.bybit.secret = keys.get("bybit_secret", handleEnv("bybit_secret"))


        self.gate = ccxt.gate({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.gate.apiKey = keys.get("gate_key", handleEnv("gateio_apiKey"))
        self.gate.secret = keys.get("gate_secret", handleEnv("gateio_secret"))


        self.kucoin = ccxt.kucoin({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.kucoin.apiKey = keys.get("kucoin_key", handleEnv("kucoin_apiKey"))
        self.kucoin.secret = keys.get("kucoin_secret", handleEnv("kucoin_secret"))
        self.kucoin.password = keys.get("kucoin_password", handleEnv("kucoin_password"))


        self.huobi = ccxt.huobi({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.huobi.apiKey = keys.get("huobi_key", handleEnv("huobi_apiKey"))
        self.huobi.secret = keys.get("huobi_secret", handleEnv("huobi_secret"))


        self.mexc = ccxt.mexc({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.mexc.apiKey = keys.get("mexc_key", handleEnv("mexc_apiKey"))
        self.mexc.secret = keys.get("mexc_secret", handleEnv("mexc_secret"))


        self.okex = ccxt.okx({
            'enableRateLimit': True,
            'nonce': ccxt.Exchange.milliseconds
        })
        self.okex.apiKey = keys.get("okex_key", handleEnv("okex_apiKey"))
        self.okex.secret = keys.get("okex_secret", handleEnv("okex_secret"))
        self.okex.password = keys.get("okex_password", handleEnv("okex_password"))
