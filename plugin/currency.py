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
import xml.etree.ElementTree as etree
import requests, bs4
import store

icon = '789C8D936B2CD5611CC73F6EB15CCA9AADB250C64E8C5C72ACCE4C6ED3668419725FD8B0A67269B149467339B16CCE2BB94FCCA9A154739BD56248A374994463C82D9732AB57F57778C11CCB77FBBE789EDF3ECF7EB7C7D55BAC8E4262C122C187B7AC82C966602BBE5F993A48902464E076B70A17A91CC78C5244E1C9185889515155E5AF20659C8EC151FCA4D584377F2040FE0EEFBA413CAB0770A9E84752DA8BA3EC254E89594A799DE3C604577711DF3A4244F330EED23A6C23AE61E9138A4D483C9EF935F8370C62E5EEB58BD7D2D626BAB6839BAFC6897EDC8FB1D345A178955DF9195AD92BCDFFB46F1459BD1324B40C6164EBF8DFFE6CF027CFD871CAFE1CC63662AED476726F6806A75429FAA696E8998814D637B540F7989152FE6CF8550ADE7CA368680AD9C7394A044B853772DF4E71A76F82F4D7E3A4748D72B9A20D754DAD5DBC969E3E31356DA4B70F5139B6A47827F5591F292D7D2409BEF174D3492DFD9C0F08D9C55B7A87E2752B17DFBC07D48CFF20A77B04D7EB59782467E39596875F66218139C584E6C908CB977150EFD00E5EE4EC49FDE4322D0BEB34CEAED130F593DA89152AC79728FDB288ECF33CF7876729189C21A77F12DB80C81DBCAA9A1A6EB1895C8849A4786094A6EFBF487ED48E475C121EF149B808F792C8041C4262B10B8AC6DCE3D20E7E7B3D01E9D93C5F5CA77C641A634BAB7DCD6FFB594B578FDB2FBA695BFE4D61CF7B4CECC44AB91366E6C25AA928DDDF23A622CA3E4DD0B1F207F9CC2A51C56558FB0462E6E48AD83F98B89232CAC616B07671DFF3FF188A2CC8EBECE1C9FC1AAD422ECD736BC8A75715BD7D38B94AF9D7456126457BF21B52D7D0C0392884CC8626EAC7A6685E58A36A6492B4BA46244161A81DD054F0FF0020982531'


def get_balance(login, password, storename=None, **kwargs):
    result = {}
    session = store.Session(storename, headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"})
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
    elif re.match(r'^(?usi)(?:RBC)[ _]?\w{3}$', login):  # Курсы ЦБ с РБК например RBC_USD
        login = re.findall(r'(?:RBC)[ _]?(\w{3})', login)[0]
        url = time.strftime("http://cbrates.rbc.ru/tsv/840/%Y/%m/%d.tsv")
        response = session.get(url)
        result['Balance'] = response.text.split()[-1]
        result['userName'] = f'Курс {login} от РБК'
    elif re.match(r'^(?usi)(?:MOEX)?[ _]?\w{3}/\w{3}$', login):  # USD/RUB или MOEX USD/RUB - MOEX
        login = re.findall(r'\w{3}/\w{3}', login)[0]
        response = session.get('https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities')
        currs = dict(re.findall(r'secid="(\w{3}/\w{3})" rate="(.*?)"',response.text))
        result['Balance'] = round(float(currs[login]), 4)
        result['TarifPlan'] = f'MOEX курс {login}'
    elif re.match(r'^(?usi)(?:MOEX)[ _]?\w+$', login):  # Курсы акций на - MOEX, напр MOEX_TATNP
        login = re.findall(r'(?:MOEX)[ _]?(\w+)', login)[0]
        url = f'https://iss.moex.com/iss/engines/stock/markets/shares/securities/{login}'
        response = session.get(url)
        root=etree.fromstring(response.text)
        rows_securities = root.findall('*[@id="securities"]/rows')[0]  # Данные по бумаге
        rows_market = root.findall('*[@id="marketdata"]/rows')[0]  # Последние данные по торгам
        lasts = [c.get('LAST') for c in list(rows_market) if c.get('LAST')!='']  # берем последнюю цену по торгам
        prevwarprices = [c.get('PREVWAPRICE') for c in list(rows_securities) if c.get('PREVWAPRICE')!='']  # Если сегодня торгов не было возьмем из rows_securities
        result['TarifPlan'] = [c.get('SECNAME') for c in rows_securities if c.get('SECNAME')!=''][0]  # Название бумаги
        result['Balance'] = float(lasts[0] if lasts != [] else prevwarprices[0])
    elif re.match(r'^(?usi)(?:YAHOO)[ _]?\w+$', login):  # Курсы акций на - YAHOO finance, напр YAHOO_AAPL
        login = re.findall(r'(?:YAHOO)[ _]?(\w+)', login)[0]
        url = time.strftime(f'https://query1.finance.yahoo.com/v8/finance/chart/{login}')
        response = session.get(url)
        meta = response.json()['chart']['result'][0]['meta']
        meta['regularMarketPrice']
        result['Balance'] = meta['regularMarketPrice']
    elif re.match(r'^(?usi)(?:FINEX)[ _]?\w+$', login):  # Курсы ETF на - finex-etf например FINEX_FXIT
        login = re.findall(r'(?:FINEX)[ _]?(\w+)', login)[0]
        url = time.strftime(f'https://finex-etf.ru/products/{login}')
        response = session.get(url)
        result['Balance'] = float(re.sub(r'[^\d\.]','',re.findall(r'singleStockPrice.*?>(.*?)<',response.text)[0]))

    return result


if __name__ == '__main__':
    print('This is module CURRENCY')
