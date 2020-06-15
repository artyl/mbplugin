# -*- coding: utf8 -*-
''' Получение котировок с finance.yahoo.com в логин код ценной бумаги
    https://finance.yahoo.com/quote/AAPL
    https://query1.finance.yahoo.com/v8/finance/chart/AAPL '''
''' Автор ArtyLa '''
import os, sys, re, time, logging
import requests
import store, settings

def get_balance(login, password, storename=None):
    result = {}
    session = requests.Session()
    url = time.strftime(f'https://query1.finance.yahoo.com/v8/finance/chart/{login}')
    response = session.get(url)
    meta = response.json()['chart']['result'][0]['meta']
    meta['regularMarketPrice']
    result['Balance'] = meta['regularMarketPrice']
    return result


if __name__ == '__main__':
    print('This is module finance.yahoo.com')
