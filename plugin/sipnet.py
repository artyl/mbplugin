# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store

icon = '789C73F235636100033320D600620128666450804840E591C1FFFFFF071CCF4C6320099F011277EFDE255B3FCC0C4AF48330797E35A6BA7E505880FC43AEFBC9D14B49F8E18E3F630AD30FA5FA49F1C34C0AC30FA19F9CF843D64F090600F649FC19'

# Строка для поиска баланса на странице
re_balance = r'(?usi)Баланс.*?>.*?>.*?>(.*?) '
# Строка для поиска тарифа
re_tariff = r'(?usi)status-work.*?>.*?>.*?>(.*?)<'  
re_sipid = r'(?usi)SIP ID.*?>.*?>(.*?)<'  # SIP ID (лицевой счет)


def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    url = 'https://www.sipnet.ru/cabinet/index'
    session = store.load_or_create_session(storename)
    response1 = session.get(url)
    if re.search(re_balance, response1.text):
        logging.info(f'Already logoned {login}')
    else:
        # Логинимся
        logging.info(f'relogon {login}')
        session = store.drop_and_create_session(storename)
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
