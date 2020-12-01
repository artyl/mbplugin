# -*- coding: utf8 -*-
''' 
Сумма по всем стокам
Стоки прописаны в mbplugin.ini в виде:

[stocks_broker_ru]
stock1 = AAPL, 1, Y 
stock2 = TATNP, 16, M 
stock3 = FXIT, 1, F
remain1 = USD, 5
remain2 = RUB, 536
currenc = USD

имя набора берется из login - название секции [stocks_<логин>]
строки  stockNN=код стока, количество акций, источник данных (Y yahoo, M moex, F finex-etf)
строки remainNN=валюта,сумма
NN должны быть различными
currenc - в какой валюте считать итог
Проверить что код стока корректный можно подставив в ссылку:
https://finance.yahoo.com/quote/AAPL
https://query1.finance.yahoo.com/v8/finance/chart/AAPL 
https://iss.moex.com/iss/engines/stock/markets/shares/securities/TATNP 
https://iss.moex.com/iss/securities/TATNP.xml
Для moex можно указать рынок в виде M_TQBR M_TQTF M_TQTD  если не указывать - то M_TQBR
Акции
https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.xml?iss.meta=off&iss.only=marketdata&marketdata.columns=SECID,LAST
ETF в рублях
https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQTF/securities.xml?iss.meta=off&iss.only=marketdata&marketdata.columns=SECID,LAST
ETF в USD
https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQTD/securities.xml?iss.meta=off&iss.only=marketdata&marketdata.columns=SECID,LAST
ETF в EUR
https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQTE/securities.xml?iss.meta=off&iss.only=marketdata&marketdata.columns=SECID,LAST
https://finex-etf.ru/products/FXIT
'''
''' Автор ArtyLa '''
import os, sys, re, time, logging, threading, traceback, queue, json
import xml.etree.ElementTree as etree
import requests
import store, settings

icon = '789C73F235636100033320D600620128666450804840E591C1F7EFDF19BE7DFB06A641F8C78F1F0C7FFEFC61F8FBF72FC3FFFFFFC118C4068981E460EA607A90F582D4C0F4E0C22035E8668030B27D84F0BF7FFFE0FA90ED7DF5F2274365DE1D86C6B27B0CF3A73F659837F529437CD0558669BD8F19E64F7BCA30A5FB11863B407E8289BD7EF58BE1C695AF0CE9D1D719BA1A1F3074363C60B0D33BC3D000340FC4AF2DBE8BE20E585881D8EFDEFC62B0503FCD90147A8D61E796B70C0B663E63B874FE334373E53D9CFA91C3F9CFEF7F607B8D144F82CD7878EF3B43B0EB2586558B5F82DD8F4D3F281C90F9DFBFFD65488F829861AA720A4C1B2B9D6458BEE005C32EA09BD0F563C3DF8066A4455E03EBCD8ABBC160AD7D1A6CC6CA452F180EEC7AC7F0F8E17714F5D8E20D64C68219CF80FEFBC770F6E427B81993BB1E31043A5F44713F3169066606C84D4E466751C20F39FE70E11B57BF32381A9EC5D00F4BCF84DC70FAF84786DDDBDE82F1C9A31F31D23125E9971AF9075BFE454E1BB070C6967F01C1D1A7CC'

def get_usd_moex():
    session = requests.Session()
    response = session.get('https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities')
    res = re.findall(r'secid="USD/RUB" rate="(.*?)"',response.text)[0]
    return float(res)


def get_yahoo(market, security, cnt, qu=None):
    session = requests.Session()
    url = time.strftime(f'https://query1.finance.yahoo.com/v8/finance/chart/{security}')
    response = session.get(url)
    meta = response.json()['chart']['result'][0]['meta']
    meta['regularMarketPrice']
    res = meta['regularMarketPrice']*cnt, security, 'USD'
    if qu:
        qu.put(res)
    return res


def get_finex(market, security, cnt, qu=None):
    session = requests.Session()
    #url = f'https://finex-etf.ru/products/{security}'
    #response = session.get(url)
    #res = float(re.sub(r'[^\d\.]', '', re.findall(r'singleStockPrice.*?>(.*?)<', response.text)[0]))*cnt, security, 'RUB'
    url = 'https://api.finex-etf.ru/graphql/'
    data = {"operationName": "GetFondDetail",
            "variables": json.dumps({"ticker": security}),
            "query": "query GetFondDetail($ticker: String!) {fonds(ticker: $ticker){edges {node{price} __typename } __typename }}"}
    response = session.post(url, data)
    res = response.json()['data']['fonds']['edges'][0]['node']['price'], security, 'RUB'  # 
    if qu:
        qu.put(res)
    return res


def get_moex_old(market, security, cnt, qu=None):
    'Старая версия берет данные со страницы о бумаге'
    session = requests.Session()
    url = time.strftime(f'https://iss.moex.com/iss/engines/stock/markets/shares/securities/{security}')
    response = session.get(url)
    root=etree.fromstring(response.text)
    # из securities возьмем стоимость бумаги за вчерашний день, если нет торгов
    rows_securities = root.findall('*[@id="securities"]/rows')[0]
    # из market возьмем стоимость самую свежую по торгам
    rows_market = root.findall('*[@id="marketdata"]/rows')[0]
    prevwarprices = [c.get('PREVWAPRICE') for c in list(rows_securities) if c.get('PREVWAPRICE')!='']
    lasts = [c.get('LAST') for c in list(rows_market) if c.get('LAST')!='']
    res =  float(lasts[0] if lasts != [] else prevwarprices[0])*cnt, security, 'RUB'
    if qu:
        qu.put(res)
    return res

def get_moex(market, security, cnt, qu=None):
    session = requests.Session()
    moexmarket = market.upper()[-4:] if len(market)>2 else 'TQBR'
    marketval = {'TQBR': 'RUB', 'TQTF': 'RUB', 'TQTD': 'USD', 'TQTE': 'EUR'}
    url = f'https://iss.moex.com/iss/engines/stock/markets/shares/boards/{moexmarket}/securities.xml?iss.meta=off&iss.only=marketdata&marketdata.columns=SECID,LAST'
    response = session.get(url)
    root=etree.fromstring(response.text)
    rows = root.find('*[@id="marketdata"]/rows')
    allsec = {l.items()[0][1]:l.items()[1][1] for l in rows}
    res =  float(allsec[security.upper()])*cnt, security, marketval[moexmarket]
    if qu:
        qu.put(res)
    return res

def thread_call_market(market,security,cnt,qu):
    logging.debug(f'Collect {market}:{security}')
    try:    
        if market.upper().startswith('Y'):
            return get_yahoo(market,security,cnt,qu)
        elif market.upper().startswith('M'):
            return get_moex(market,security,cnt,qu)
        elif market.upper().startswith('F'):
            return get_finex(market,security,cnt,qu)
        else:
            raise RuntimeError(f'Unknown market marker {market} for {security}')
    except:
        exception_text = f'Error {market},{security}:{"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)    

    
def count_all_scocks_multithread(stocks, remain, currenc):
    usd = get_usd_moex()
    k = {'USD': 1, 'RUB': 1}  # Коэффициенты для приведения к одной валюте
    if currenc == 'USD':
        k['RUB'] = 1/usd
    else:
        k['USD'] = usd
    qu = queue.Queue() # Очередь для данных из thread [val, sec_code, currency]
    # Каждое получение данных в отдельном трэде для ускорения
    for sec,cnt,market in stocks:
        threading.Thread(target=thread_call_market, name='stock', args=(market,sec,cnt,qu)).start()
    # Ждем завершения всех трэдов с получением данных
    while [1 for i in threading.enumerate() if i.name=='stock']:
        time.sleep(0.01)
    data = []
    # Забираем данные от трэдов
    while qu.qsize()>0:
        data.append(qu.get_nowait())
    orderlist = list(zip(*stocks))[0] # Порядок, в котором исходно шли бумаги
    data.sort(key=lambda i:orderlist.index(i[1])) # Сортируем в исходном порядке
    res_full = '\n'.join([f'{sec+"("+curr+")":10} : {round(val*k[curr],2):9.2f} {currenc}' for val,sec,curr in data])+'\n'
    res_balance = round(sum([val*k[curr] for val,sec,curr in data]) + remain['USD']*k['USD'] + remain['RUB']*k['RUB'],2)
    if len(data) != len(stocks):
        diff = ','.join(set([i[1] for i in data]).symmetric_difference(set([i[0] for i in stocks])))
        raise RuntimeError(f'Not all stock was return ({len(data)} of {len(stocks)}):{diff}')
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
    print('This is module stock calculator')
