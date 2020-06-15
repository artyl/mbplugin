# -*- coding: utf8 -*-
''' 
Сумма по всем стокам
Стоки прописаны в mbplugin.ini в виде:

[stocks_broker_ru]
stock1 = AAPL, 1, Y 
stock2 = TATNP, 16, M 
stock3 = FXIT, 1, M
remain1 = USD, 5
remain2 = RUB, 536
currenc = USD

имя набора берется из login - название секции [stocks_<логин>]
строки  stockNN=код стока, количество акций, источник данных (Y yahoo, M moex)
строки remainNN=валюта,сумма
NN должны быть различными
currenc - в какой валюте считать итог
Проверить что код стока корректный можно подставив в ссылку:
https://finance.yahoo.com/quote/AAPL
https://query1.finance.yahoo.com/v8/finance/chart/AAPL 
https://iss.moex.com/iss/engines/stock/markets/shares/securities/TATNP 
https://iss.moex.com/iss/securities/TATNP.xml
'''
''' Автор ArtyLa '''
import os, sys, re, time, logging, threading, queue
import xml.etree.ElementTree as etree
import requests
import store, settings

def get_usd_moex():
    session = requests.Session()
    response = session.get('https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities')
    res = re.findall(r'secid="USD/RUB" rate="(.*?)"',response.text)[0]
    return float(res)

def get_yahoo(security, cnt, qu=None):
    session = requests.Session()
    url = time.strftime(f'https://query1.finance.yahoo.com/v8/finance/chart/{security}')
    response = session.get(url)
    meta = response.json()['chart']['result'][0]['meta']
    meta['regularMarketPrice']
    res = meta['regularMarketPrice']*cnt, security, 'USD'
    if qu:
        qu.put(res)
    return res

def get_moex(security, cnt, qu=None):
    session = requests.Session()
    url = time.strftime(f'https://iss.moex.com/iss/engines/stock/markets/shares/securities/{security}')
    response = session.get(url)
    root=etree.fromstring(response.text)
    rows = root.findall('*[@id="marketdata"]/rows')[0]
    res =  float([c.get('LAST') for c in list(rows) if c.get('LAST')!=''][0])*cnt, security, 'RUB'
    if qu:
        qu.put(res)
    return res
    
def count_all_scocks_multithread(stocks, remain, currenc):
    usd = get_usd_moex()
    k = {'USD': 1, 'RUB': 1}  # Коэффициенты для приведения к одной валюте
    if currenc == 'USD':
        k['RUB'] = 1/usd
    else:
        k['USD'] = usd
    qu = queue.Queue() # Очередь для данных из thread [val, sec_code, currency]
    # Каждое получение данных в отдельном трэде
    for sec,cnt,market in stocks:
        target = get_yahoo if market=='Y' else get_moex
        threading.Thread(target=target, name='stock', args=(sec,cnt,qu)).start()
    # Ждем завершения всех трэдов с получением данных
    while [1 for i in threading.enumerate() if i.name=='stock']:
        time.sleep(0.01)
    data = []
    # Забираем данные от трэдов
    while qu.qsize()>0:
        data.append(qu.get_nowait())
    orderlist = list(zip(*stocks))[0] # Порядок, в котором исходно шли бумаги
    data.sort(key=lambda i:orderlist.index(i[1])) # Сортируем в исходном порядке
    res_full = '\n'.join([f'{sec:5} : {round(val*k[curr],2):7.2f} {curr}' for val,sec,curr in data])+'\n'
    res_balance = round(sum([val*k[curr] for val,sec,curr in data]) + remain['USD']*k['USD'] + remain['RUB']*k['RUB'],2)
    return res_balance, res_full

def get_balance(login, password, storename=None):
    result = {}
    data = store.read_stocks(login.lower())
    stocks = data['stocks']
    remain = data['remain']
    currenc = data['currenc']
    res_balance, res_full = count_all_scocks_multithread(stocks, remain, currenc)
    result['Stock'] = res_full # Полная информация по стокам
    result['Balance'] = res_balance # Сумма в заданной валюте
    result['Currenc'] = currenc # Валюта
    return result


if __name__ == '__main__':
    print('This is module finance.yahoo.com')
