# -*- coding: utf8 -*-
''' Автор ArtyLa '''
''' CBR.RU Получение курсов с сайта ЦБ в логин наименование курса, например USD
    https://cbr.ru/currency_base/daily/
    MOEX Получение курсов с сайта ЦБ в логин наименование курса как на сайте например USD/RUB или MOEX_USD/RUB
    https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities
    Получение котировок с moex.com в логин MOEX_ и код ценной бумаги например MOEX_TATNP
    https://iss.moex.com/iss/engines/stock/markets/shares/securities/TATNP
    https://iss.moex.com/iss/securities/TATNP.xml
    Получение котировок с finance.yahoo.com в логин YAHOO_ и код ценной бумаги, напрмер YAHOO_AAPL
    https://finance.yahoo.com/quote/AAPL
    https://query1.finance.yahoo.com/v8/finance/chart/AAPL
    Получение котировок ETF c Finex-etf
    https://finex-etf.ru/products/FXIT
'''
import os, sys, re, time, logging
import requests, bs4
import store, settings

icon = '789C8D936B2CD5611CC73F6EB15CCA9AADB250C64E8C5C72ACCE4C6ED3668419725FD8B0A67269B149467339B16CCE2BB94FCCA9A154739BD56248A374994463C82D9732AB57F57778C11CCB77FBBE789EDF3ECF7EB7C7D55BAC8E4262C122C187B7AC82C966602BBE5F993A48902464E076B70A17A91CC78C5244E1C9185889515155E5AF20659C8EC151FCA4D584377F2040FE0EEFBA413CAB0770A9E84752DA8BA3EC254E89594A799DE3C604577711DF3A4244F330EED23A6C23AE61E9138A4D483C9EF935F8370C62E5EEB58BD7D2D626BAB6839BAFC6897EDC8FB1D345A178955DF9195AD92BCDFFB46F1459BD1324B40C6164EBF8DFFE6CF027CFD871CAFE1CC63662AED476726F6806A75429FAA696E8998814D637B540F7989152FE6CF8550ADE7CA368680AD9C7394A044B853772DF4E71A76F82F4D7E3A4748D72B9A20D754DAD5DBC969E3E31356DA4B70F5139B6A47827F5591F292D7D2409BEF174D3492DFD9C0F08D9C55B7A87E2752B17DFBC07D48CFF20A77B04D7EB59782467E39596875F66218139C584E6C908CB977150EFD00E5EE4EC49FDE4322D0BEB34CEAED130F593DA89152AC79728FDB288ECF33CF7876729189C21A77F12DB80C81DBCAA9A1A6EB1895C8849A4786094A6EFBF487ED48E475C121EF149B808F792C8041C4262B10B8AC6DCE3D20E7E7B3D01E9D93C5F5CA77C641A634BAB7DCD6FFB594B578FDB2FBA695BFE4D61CF7B4CECC44AB91366E6C25AA928DDDF23A622CA3E4DD0B1F207F9CC2A51C56558FB0462E6E48AD83F98B89232CAC616B07671DFF3FF188A2CC8EBECE1C9FC1AAD422ECD736BC8A75715BD7D38B94AF9D7456126457BF21B52D7D0C0392884CC8626EAC7A6685E58A36A6492B4BA46244161A81DD054F0FF0020982531'


def get_balance(login, password, storename=None, **kwargs):
    result = {}
    user_agent = store.options('user_agent', pkey=store.get_pkey(login, plugin_name=__name__))
    if user_agent.strip() == '':
        user_agent = settings.default_user_agent
    session = store.Session(storename, headers={'User-Agent': user_agent})
    login_ori = login
    login = login.strip().upper().replace('\\','/')
    if re.match(r'^\w\w\w$', login):  # USD - курс цб
        response = session.get("https://cbr.ru/currency_base/daily/")
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        try:
            cdate = soup.find('div', class_='filter').get_text().strip()
        except Exception:
            cdate = '???'
        table = soup.find('table', class_='data')
        for line in table.findAll('tr')[1:]:
            cod, val, ed, val_text, cur = [i.get_text() for i in line.findAll('td')]
            # ['036', 'AUD', '1', 'Австралийский доллар', '54,9008']
            if login.lower() == val.lower():
                result['Balance'] = round(float(cur.replace(',', '.')), 4)
                result['TarifPlan'] = f'ЦБ РФ рублей за {ed} {val_text} c {cdate}'
    elif re.match(r'(?usi)^(?:RBC)[ _]?\w{3}$', login):  # Курсы ЦБ с РБК например RBC_USD
        login = re.findall(r'(?:RBC)[ _]?(\w{3})', login)[0]
        url = time.strftime("http://cbrates.rbc.ru/tsv/840/%Y/%m/%d.tsv")
        response = session.get(url)
        result['Balance'] = float(response.text.split()[-1])
        result['userName'] = f"Курс {login} от РБК (ЦБ) на {time.strftime('%Y-%m-%d')}"
        result['TarifPlan'] = result['userName']
    elif re.match(r'(?usi)^(?:MOEX)?[ _]?\w{3}/\w{3}$', login):  # USD/RUB или MOEX USD/RUB - MOEX
        login = re.findall(r'\w{3}/\w{3}', login)[0]
        response = session.get('https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities.json?iss.meta=off')
        data = response.json()
        headers = data['securities']['columns']
        lines = [dict(zip(headers,i)) for i in data['securities']['data']]
        securities = {i['secid']:i for i in lines}
        result['Balance'] = round(float(securities[login]['rate']), 4)
        result['TarifPlan'] = f"MOEX курс {login} на {securities[login]['tradedate']} {securities[login]['tradetime']}"
    elif re.match(r'(?usi)^MOEX[ _](\w+?)[ _](\w+?)[ _](\w+?)$', login):  # Получить данные по конкретному инструменту рынка.
        # Получить данные по конкретному инструменту рынка.
        # MOEX_engine_market_security
        # https://iss.moex.com/iss/engines/[engine]/markets/[market]/securities/[security]
        # https://iss.moex.com/iss/reference/52
        # Engines смотрим на
        # https://iss.moex.com/iss/engines
        # Markets для конкретного Engines смотрим (напрмер для engines=currency)
        # https://iss.moex.com/iss/engines/currency/markets/
        # например [engine] = currency, [market] = selt, [security] = USD000UTSTOM
        # Список бумаг смотрим на странице без указания бумаги (первая колонка SECID):
        # https://iss.moex.com/iss/engines/currency/markets/selt/securities
        # Данные по бумаге
        # MOEX_currency_selt_EUR_RUB__TOM
        # https://iss.moex.com/iss/engines/currency/markets/selt/securities/USD000UTSTOM
        # Еще пример: MOEX_stock_shares_AFLT
        # https://iss.moex.com/iss/engines/stock/markets/shares/securities/AFLT.xml
        engine, market, securiti = re.match(r'(?usi)^MOEX[ _](\w+?)[ _](\w+?)[ _](\w+?)$', login).groups()
        url = f'https://iss.moex.com/iss/engines/{engine.lower()}/markets/{market.lower()}/securities/{securiti.upper()}.json?iss.meta=off'
        response = session.get(url)
        data = response.json()
        securities = dict(zip(data['securities']['columns'], data['securities']['data'][0]))
        lines = [dict(zip(data['marketdata']['columns'], line)) for line in data['marketdata']['data']]
        res_lines = [line for line in lines if line['LAST'] is not None and line['MARKETPRICE'] is not None]
        if len(res_lines) >0:
            marketdata = res_lines[0]
            result['Balance'] = round(float(marketdata['LAST'] if marketdata['LAST'] is not None else marketdata['MARKETPRICE']), 4)
            result['TariffPlan'] = f"{securities['SECNAME']} на {marketdata['SYSTIME']}"
        else:
            result['Balance'] = round(float(securities['PREVPRICE'] if securities['PREVPRICE'] is not None else securities['PREVWAPRICE']), 4)
            result['TariffPlan'] = f"{securities['SECNAME']} на {securities['PREVDATE']}"
    elif re.match(r'(?usi)^(?:MOEX)[ _]?\w+$', login):  # Курсы акций на - MOEX, напр MOEX_TATNP
        login = re.findall(r'(?:MOEX)[ _]?(\w+)', login)[0]
        url = f'https://iss.moex.com/iss/engines/stock/markets/shares/securities/{login}.json?iss.meta=off'
        response = session.get(url)
        data = response.json()
        securities = dict(zip(data['securities']['columns'], data['securities']['data'][0]))
        marketdata = dict(zip(data['marketdata']['columns'], data['marketdata']['data'][0]))
        # Если сегодня торгов не было возьмем из rows_securities
        price = round(float(marketdata['LAST'] if marketdata['LAST'] is not None else marketdata['MARKETPRICE']), 4)
        result['TarifPlan'] = securities['SECNAME']  # Название бумаги
        result['Balance'] = price
    elif re.match(r'(?usi)^(?:YAHOO)[ _]?\w+$', login):  # Курсы акций на - YAHOO finance, напр YAHOO_AAPL
        login = re.findall(r'(?:YAHOO)[ _]?(\w+)', login)[0]
        url = time.strftime(f'https://query1.finance.yahoo.com/v8/finance/chart/{login}')
        response = session.get(url)
        meta = response.json()['chart']['result'][0]['meta']
        meta['regularMarketPrice']
        result['Balance'] = meta['regularMarketPrice']
    elif re.match(r'(?usi)^(?:FINEX)[ _]?\w+$', login):  # Курсы ETF на - finex-etf например FINEX_FXIT
        login = re.findall(r'(?:FINEX)[ _]?(\w+)', login)[0]
        url = time.strftime(f'https://finex-etf.ru/products/{login}')
        response = session.get(url)
        result['Balance'] = float(re.sub(r'[^\d\.]','',re.findall(r'singleStockPrice.*?>(.*?)<',response.text)[0]))

    return result


if __name__ == '__main__':
    print('This is module CURRENCY')
