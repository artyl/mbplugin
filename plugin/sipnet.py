# -*- coding: utf8 -*-
import sys;sys.dont_write_bytecode = True
import os, sys, re, logging
import requests
import store

# Строка для поиска баланса на странице
re_balance = r'(?usi)Баланс.*?>.*?>.*?>(.*?) '
# Строка для поиска тарифа
re_tariff = r'(?usi)status-work.*?>.*?>.*?>(.*?)<'  
re_sipid = '(?usi)SIP ID.*?>.*?>(.*?)<'  # SIP ID (лицевой счет)


def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    url = 'https://www.sipnet.ru/cabinet/index'
    session = store.load_session(storename)
    if session is None:
        logging.info(f'No saved session {login}')
        session = requests.Session()
    response1 = session.get(url)
    if re.search(re_balance, response1.text):
        logging.info(f'Already logoned {login}')
    else:
        # Логинимся
        logging.info(f'relogon {login}')
        data = {'CabinetAction': 'login','view': 'ru','Name': login,'Password':password,}
        response1 = session.post(url, data=data)
        if response1.status_code != 200:
            raise RuntimeError(f'POST Login page {url} error: status_code {response1.status_code}')

    result['Balance'] = re.search(re_balance, response1.text).group(1).replace(',', '.').strip()
    try:
        result['TarifPlan'] = re.search(re_tariff, response1.text).group(1).replace('&nbsp;', '').strip()
    except Exception:
        logging.info(f'Not found TarifPlan')
    try:
        result['licSchet'] =  re.search(re_sipid, response1.text).group(1).replace('&nbsp;', '').strip()
    except Exception:
        logging.info(f'Not found licSchet')
    
    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module sipnet')
