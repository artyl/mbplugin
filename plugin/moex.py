# -*- coding: utf8 -*-
''' Получение котировок с moex.com в логин код ценной бумаги
    https://iss.moex.com/iss/engines/stock/markets/shares/securities/TATNP 
    https://iss.moex.com/iss/securities/TATNP.xml'''
''' Автор ArtyLa '''
import os, sys, re, time, logging
import requests
import xml.etree.ElementTree as etree
import store, settings

def get_balance(login, password, storename=None):
    result = {}
    session = requests.Session()
    url = time.strftime(f'https://iss.moex.com/iss/engines/stock/markets/shares/securities/{login}')
    response = session.get(url)
    root=etree.fromstring(response.text)
    rows = root.findall('*[@id="marketdata"]/rows')[0]
    result['Balance'] = [c.get('LAST') for c in rows.getchildren() if c.get('LAST')!=''][0]
    return result


if __name__ == '__main__':
    print('This is module moex')
