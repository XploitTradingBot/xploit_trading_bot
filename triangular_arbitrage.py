# -*- coding: utf-8 -*-
"""
Created on Wed Jul 22 19:53:25 2020

@author: Ale10
"""
import ccxt
import time
import threading
import concurrent.futures
import pandas as pd
import winsound

#We search for the exchanges supported by CCXT
exchanges = ccxt.exchanges

#We create a global dict to store the results
global general
general ={}



#function to receive and process all the exchanges and filter the ones with les than 10 cryptos

def scanExchanges2(exch): 
    global general
    exchange = getattr(ccxt, exch)({'enableRateLimit':True,})
    try:
        markets = exchange.load_markets()
        if len(markets) > 10:
            general[exch]=markets.keys()
            print(f'Exchange : {exchange} - Size {len(markets)}')
    except Exception as e:
        print(f'Error in the function ScanExchanges2: {e}')



#starting concurrent threads for obtaining exchange information
def multiScan3(exch):
    start = time.perf_counter()  
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(scanExchanges2, exch)
  
    finish = time.perf_counter()
    print('time {}'.format(finish-start))

multiScan3(exchanges)



#we define a function to obtain the order book for a pair
def get_bid_ask(exchange,pair):
    exchange = getattr(ccxt, exchange)()
    #time.sleep(exchange.rateLimit / 1000)
    book = exchange.fetchOrderBook(pair,5)
    #timestamp = time.ctime()
    bid = book['bids'][0]
    ask = book['asks'][0]
    print(exchange," ", bid,ask)
    return bid,ask

#Checks the arbitrage for the three symbols in the exchange
def checkarb(exc, moneda1, moneda2, moneda3):
    print(f'\n \n ----------------------CRYPTO LEG : {moneda1}, {moneda2} ,{moneda3}')
    ask1,vol1 = get_bid_ask(exc,moneda2+'/'+moneda1)[1]
    print(f'sell  {moneda1} buy {moneda2} at price {ask1} --  vol {vol1}')
    resultado1 = 100/ask1
    print(f'{resultado1}')
    bid2,vol2 = get_bid_ask(exc, moneda2+'/'+moneda3)[0]
    print(f'sell {moneda2} buy {moneda3} at price {bid2} -- vol {vol2}')
    resultado2 = resultado1 * bid2
    print(f'{resultado2}')
    bid3,vol3 = get_bid_ask(exc, moneda3+'/'+moneda1)[0]
    print(f'sell {moneda3} buy {moneda1} at price {bid3} -- vol {vol3}')
    resultado3 = resultado2*bid3
    print(f' final result : ----------------------------------------  {resultado3}')
    if resultado3 > 100.50:
        winsound.Beep(2342,1000)
    return time.ctime(), exc, moneda1, moneda2, moneda3, ask1,resultado1, vol1, bid2, resultado2, vol2, bid3, resultado3, vol3


filename = 'resultadosArb.csv'
resultados = open(filename,'a')

def buscaOportunidades(exchange):
    Mercado = exchange
    exchange = general[Mercado]
  
    #We define the starting and ending symbol
    moneda1 = 'USDT'
    moneda3 = 'BTC'
    unionEntreMo1yMo3 =[] #Cryptos with common intermediate coin 
    currencies2 = [] #List of coins that trade with 1st
    
    #we select the coins in common between third and 1st
    for x in exchange:
        try:
            if moneda1 in x.split('/')[1]:
                currencies2.append(x.split('/')[0])
        except:
            pass
    
    # deletes coin 1 if exists in the list
    try:
        for x in currencies2:
            if moneda1 == x:
                currencies2.remove(moneda1)
    except Exception as e:
        print (f'error {e} in the function buscarOportunidades')
    
    # Generates a list of all the coins that link coin 2 and 3
    for x in currencies2:
        for y in currencies2:
            if x+'/'+y in exchange:
                if y ==moneda3:
                    print (f' {Mercado} FOUND {x} / {y}')
                    if x != moneda1:
                            unionEntreMo1yMo3.append(x)    
    print(f'Union between coin 1 and 3 {unionEntreMo1yMo3}')
    
    #Get prices of the current leg
    for x in unionEntreMo1yMo3:
        try:
            time, exc, moneda1, moneda2, moneda3, ask1,resultado1, vol1, bid2, resultado2, vol2, bid3, resultado3,vol3 = checkarb(Mercado,moneda1, x,moneda3)
            #yield exc, moneda1, moneda2, moneda3, ask1,resultado1, ask2, resultado2, bid3, resultado3
            resultados.write(str(time)+','+str(exc)+','+str(moneda1)+','+str(moneda2)+','+str(moneda3)+','+str(ask1)+','+str(vol1)+','+str(bid2)+','+str(vol2)+','+str(bid3)+','+str(vol3)+','+str(resultado3)+'\n')
            resultados.flush()
        except Exception as e:
            print ('-'*60 + str(e))
        
def leg(exch,par1,par2,par3):
    exchange = getattr(ccxt, exch)()
    if exchange.has['fetchTickers']:
        pierna = exchange.fetchTickers([par1,par2,par3])
        leg1 = pierna[par1]['bid']
        leg2 = pierna[par2]['bid']
        leg3 = pierna[par3]['bid']
        return(leg1,leg2,leg3)

#function to retrieve the taker fee. Not used currently.    
def pairFeeTaker(exch, pair):
    exchange = getattr(ccxt, exch)()
    exchange.load_markets()
    fee = exchange.markets[pair]['taker']
    return fee
    
#We use concurrent process to send as much threads as exchanges are.    
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = executor.map(buscaOportunidades, general)

resultados.close()