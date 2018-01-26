#!/usr/bin/env python
# coding=utf-8

from client import Client
from exceptions import BinanceAPIException, BinanceRequestException, BinanceWithdrawException
from enums import *
from depthcache import DepthCacheManager
from websockets import BinanceSocketManager

import pytest
import requests_mock
import sys
import time



client = Client('BqhDZTv85kkwsQQBV8njSdBeOENiFhEfoQciAmq4DImxQ9Cqe3pmBigpZppSbit6', 'CDkh04rFHGPjTPBRsiJI4WMmuYpgT8HsmLwJ1INJP8hW7wBFYnCuViVtW6FywoUy')

class DataCache:
    def __init__(self, symbol, money, profit, stepSize, tickSize, bid ):
        self.bid = bid
        self.ask = 0.0
        self.money = money
        self.Amount = 0.0
        self.symbol = symbol
        self.buyAmount = 0
        self.buyLst = []
        self.cost = money
        self.profit = profit
        self.stepSize = stepSize
        self.tickSize = tickSize









def test_invalid_json():
    """Test Invalid response Exception"""

    with pytest.raises(BinanceRequestException):
        with requests_mock.mock() as m:
            m.get('https://www.binance.com/exchange/public/product', text='<head></html>')
            param = client.get_products()
            return


def test_api_exception():
    """Test API response Exception"""

    with pytest.raises(BinanceAPIException):
        with requests_mock.mock() as m:
            json_obj = {"code": 1002, "msg": "Invalid API call"}
            m.get('https://api.binance.com/api/v1/time', json=json_obj, status_code=400)
            param = client.get_server_time()
            print(param)

            return


def test_withdraw_api_exception():
    """Test Withdraw API response Exception"""

    with pytest.raises(BinanceWithdrawException):

        with requests_mock.mock() as m:
            json_obj = {"success": False, "msg": "Insufficient funds"}
            m.register_uri('POST', requests_mock.ANY, json=json_obj, status_code=200)
            client.withdraw(asset='BTC', address='BTCADDRESS', amount=100)



def get_dec(a):
    c = 0
    while a != 1:
        a = a * 10
        c += 1

    return c

def float_n(f, n):
    s = str(f)
    i = s.find('.')
    if i != -1:
        return float(s[:i+n+1])
    return f

def process_depth(depth_cache):
    print("symbol {}".format(depth_cache.symbol))
    print("top 5 bids")
    print(depth_cache.get_bids()[:5])
    print("top 5 asks")
    print(depth_cache.get_asks()[:5])

def process_m_message(msg):
        #print("stream: {} data: {}".format(msg['stream'], msg['data']))
        data = msg['data']
        trade_data = datas[data['s']]
        q = float(data['q'])
        h = float(data['h'])
        l = float(data['l'])
        if trade_data.ask == 0:
            if q >= 1000 and l / h >= 0.1:#24小时交易量必须大于1000ETH,且24小时振幅大于10%

                trade_data.ask = float(data['a'])
                trade_data.bid = float(data['b'])
                trade_data.buyAmount = trade_data.money / (trade_data.ask * trade_data.number)
        else:
            cur_ask = float(data['a'])
            cur_bid = float(data['b'])
            if cur_ask <= trade_data.ask * (1 - trade_data.step ):
                if trade_data.money - cur_ask * trade_data.buyAmount >= 0:
                    trade_data.Amount = trade_data.Amount + trade_data.buyAmount
                    trade_data.money = trade_data.money - cur_ask * trade_data.buyAmount
                    trade_data.ask = cur_ask
                    trade_data.buyLst.append(cur_ask)

                    print('\n买入%s 价格:%12.8f, 数量:%12.8f'%(trade_data.symbol, cur_ask, trade_data.buyAmount))


            for item in trade_data.buyLst:
                if cur_bid >= item * (1 + trade_data.profit):
                    trade_data.Amount = trade_data.Amount - trade_data.buyAmount
                    trade_data.money = trade_data.money + cur_bid * trade_data.buyAmount
                    trade_data.ask = cur_bid

                    print('\n卖出%s 价格:%12.8f, 数量:%12.8f' % (trade_data.symbol, cur_bid, trade_data.buyAmount))
                    revenue = trade_data.money + trade_data.Amount * cur_bid
                    print('\n%s 总金额:%12.8f, 利润率:%2.2f%%' % (
                    trade_data.symbol, revenue, (revenue - trade_data.cost) / trade_data.cost * 100))
                    trade_data.buyLst.remove(item)
            #sys.stdout.write('\r %s 当前价格: %12.8f'%(trade_data.symbol, cur_ask))
            #sys.stdout.flush()

datas = {}

def process_message(msg):
    print("message type: {}".format(msg['e']))
    if msg['e'] == 'executionReport':
        if msg['S'] == 'BUY' and msg['X'] == 'FILLED':

            if msg['s'] in datas:
                print('%s 买入价格: %s, 数量:%s ' % (msg['s'], msg['p'], msg['q']))

                cache = datas[msg['s']]
                sell = float(msg['p'])
                sell = sell * (1 + cache.profit)
                sell = float_n(sell, cache.tickSize)
                q = float(msg['q'])
                q = q * (1 - 0.002) #减掉手续费
                q = float_n(q, cache.stepSize)

                try:
                    order = client.order_limit_sell(
                        symbol=msg['s'],
                        quantity=q,
                        price=sell)




                except BaseException as e:
                    print(e)


        elif msg['S'] == 'SELL' and msg['X'] == 'FILLED':

            if msg['s'] in datas:
                print ('卖出%s, 价格:%s' % (msg['s'], msg['p']))
                cache = datas[msg['s']]
                p = float(msg['p'])
                q = float(msg['q'])
                print ('%s 买入价格:%12.8f, 卖出价格:%12.8f, 利润率:%3.2f'%(msg['s'], cache.bid, p, (p - cache.bid) /cache.bid * 100 ))





if __name__ == '__main__':


    print (sys.argv)

    if sys.argv.__len__() < 4:
        print ('参数错误')
        exit(1)

    #dcm = DepthCacheManager(client, 'BNBBTC', process_depth)


    bm = BinanceSocketManager(client)
    # start any sockets here, i.e a trade socket
    #conn_key = bm.start_trade_socket('BNBBTC', process_message)
    #conn_key = bm.start_symbol_ticker_socket('BNBBTC', process_message)
    #conn_key = bm.start_symbol_ticker_socket('ETHBTC', process_message)
    # then start the socket manager
    symbolLst = []

    profit = 0.0
    conn_key = bm.start_user_socket(process_message)
    bm.start()
    mMoney = float(sys.argv[1])
    mNumbers = float(sys.argv[2])
    profit = float(sys.argv[3])

    i = mNumbers
    res = client.get_exchange_info()
    for item in res['symbols']:
        if i <= 0:
            break;
        if item['symbol'][-3:] == 'ETH':

            info = client.get_ticker(symbol = item['symbol'])
            filters = item['filters']
            stepSize = float(filters[1]['stepSize'])
            tickSize = float(filters[0]['tickSize'])


            q = float(info['quoteVolume'])
            h = float(info['highPrice'])
            l = float(info['lowPrice'])
            ask = float(info['askPrice'])
            P = float(info['priceChangePercent'])


            if q >= 1000 and (1- l / h) >=0.20 and (P >= -20 and P <= 40):#24小时交易量大于1000ETH,且24小时振幅大于20%,且跌幅小于20%

                cur_bid = l +  (h - l ) * 0.20  #最低价+振幅的15%设为初始买入价
                if ask < cur_bid:
                    cur_bid = ask

                cTick = get_dec(tickSize)
                if cTick >= 8:
                    cTick = 7

                cur_bid = float_n(cur_bid, cTick)




                mAmount = mMoney / (mNumbers * cur_bid) #买入数量

                cStep = get_dec(stepSize)
                mAmount = float_n(mAmount, cStep)
                print('%s 24小时交易量:%12.8f, 24小时振幅:%3.2f%%, 24小时涨跌:%3.2f%%' % (item['symbol'], q, (1 - l / h) * 100, P))
                print ('当前价格:%12.8f, 买入价格:%12.8f' % (ask, cur_bid))


                datas[item['symbol']] = DataCache(item['symbol'], mMoney / mNumbers, profit, cStep, cTick, cur_bid)
                try:
                    order = client.order_limit_buy(
                        symbol=item['symbol'],
                        quantity=mAmount,
                        price=(cur_bid))
                    i -= 1

                except BaseException as e:
                    print (e);

                #if (b - cur_bid) / cur_bid >= 0.1:

            #symbolLst.append(item['symbol'].lower() + '@ticker')



   

    #conn_key = bm.start_multiplex_socket(symbolLst, process_m_message)


    while (True):
        time.sleep(1)


    sys.exit(0)


    print(sys.argv)

    if sys.argv.__len__() < 5:
        print('参数错误!')
        sys.exit(1)

    sym = sys.argv[1]
    cost = float(sys.argv[2])
    step = float(sys.argv[3])
    num = float(sys.argv[4])
    profit = float(sys.argv[5])
    g_sum = {}
    g_sum['total_Amount'] = 0
    g_sum['total_Money'] = cost

    # buymoney = total_money * (1 - scale) / (1 - scale**10)

    price = 0.0
    lastprice = 0.0
    boughtLst = []
    detail = {}
    timeOut = 0
    stepSize = 1
    detail = client.get_ticker(symbol = sym)

    price = float(detail['askPrice'])
    ask = float(detail['askPrice'])
    buyAmount = float('%.2f' % (g_sum['total_Money'] / (ask * num)))
    lastprice = ask
    print('%d %s 当前价格: %12.8f' % (time.time(), sym, ask))
    info = client.get_symbol_info(sym)

    filters = info['filters']

    for filter in filters:
        if filter['filterType'] == 'LOT_SIZE':
            stepSize = float(filter['stepSize'])
            break

    buyAmount = (buyAmount // stepSize) *stepSize
    bIsout = True
    # 取币的当前价格
    while (True):

        try:
            detail = client.get_ticker(symbol=sym)
            price = float(detail['askPrice'])
            ask = float(detail['askPrice'])
            bid = float(detail['bidPrice'])
        except BaseException as e:
            print('\n获取%s 价格失败'%sym)

        sys.stdout.write("\r%f    %s 当前价格: %12.8f " % (time.time(),sym, ask))
        sys.stdout.flush()

        if  ask <= lastprice * (1 - step):
            # print('提交订单%s,数量:%f,价格:%12.8f' % (sym, buyAmount, price))
            # param = do_Work(buyAmount * ask, sym, 'buy-market', 0, True, boughtLst, g_sum)
            try:
                if (g_sum['total_Money'] - ask * buyAmount) >= 0:
                    param = client.order_market_buy(symbol = sym, quantity = buyAmount)
                    g_sum['total_Amount'] = g_sum['total_Amount'] - buyAmount
                    g_sum['total_Money'] = g_sum['total_Money'] + buyAmount * ask

                    print('\n买入%s 价格：%s, 成交量：%s, 金额：%s' % (
                        sym, ask, buyAmount, buyAmount * ask))
                    bIsout = True
                    boughtLst.append(ask)
                    lastprice = ask
                #else:
                 #   print ('当前余额: %f, 余额不足.'%g_sum['total_Money'] )

            except BaseException as e:
                print('\n买入%s 交易出错, %s'%(sym,e))
                bIsout = True

        for x in boughtLst:
            if bid >= x * (1 + profit):
                # param = do_Work(float(x['data']['field-amount']), sym, 'sell-market', 0, False, boughtLst, g_sum)
                try:
                    param = client.order_market_sell(symbol = sym, quantity = buyAmount)
                    g_sum['total_Amount'] = g_sum['total_Amount'] - buyAmount
                    g_sum['total_Money'] = g_sum['total_Money'] + buyAmount * bid

                    print('\n卖出%s 价格：%s, 成交量：%s, 金额：%s' % (
                        sym, bid, buyAmount, buyAmount * bid))
                    revenue = g_sum['total_Money'] + g_sum['total_Amount'] * bid
                    realPrifit = (revenue - cost) / cost
                    print('\n总金额:%f, 利润率:%f' % (revenue, realPrifit))
                    lastprice = bid
                    boughtLst.remove(x)
                    bIsout = True
                except BaseException as e:
                    print('卖出%s 交易出错, %s' %(sym, e))
                    bIsout = True

        timeOut = timeOut + 1
        if timeOut >= 600:
            timeOut = 0
            revenue = g_sum['total_Money'] + g_sum['total_Amount'] * ask
            realPrifit = (revenue - cost) / cost
            print('\n总金额:%f, 利润率:%f' % (revenue, realPrifit))
            bIsout = True

        time.sleep(1)

    revenue = g_sum['total_Money'] + g_sum['total_Amount'] * bid
    realPrifit = (revenue - cost) / cost
    print('\n总金额:%f, 利润率:%f' % (revenue, realPrifit))
    print('happy ending.')


