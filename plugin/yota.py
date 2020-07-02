# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store

icon = '789C73F235636100033320D600620128666450804840E591C1FFFFFF071CCF4C6320099F011277EFDE255B3FCC0C4AF48330797E35A6BA7E505880FC43AEFBC9D14B49F8E18E3F630AD30FA5FA49F1C34C0AC30FA19F9CF843D64F090600F649FC19'

# Строка для поиска баланса на странице
re_balance = r'(?usi)id\W+balance-holder\W+span\W*(\d+,?\d*)\W*span'
# Строка для поиска тарифа
re_tariff = r'(?usi)status-work.*?>.*?>.*?>(.*?)<'  

def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    url_post = 'https://login.yota.ru/UI/Login'
    url_balance = 'https://my.yota.ru/selfcare/devices'
    session = store.Session(storename)
    response2 = session.get(url_balance)
    if re.search(re_balance, response2.text):
        logging.info(f'Already logoned {login}')
    else:
        # Логинимся
        logging.info(f'relogon {login}')
        session.drop_and_create()
        data = {'IDToken1': login,
                'IDToken2': password,
                'goto': 'https://my.yota.ru:443/selfcare/loginSuccess',
                'gotoOnFail': '=https://my.yota.ru:443/selfcare/loginError',
                'org': 'customer',
                'ForceAuth': 'true',
                'login': login,
                'password': password, }
        response1 = session.post(url_post, data=data)
        if response1.status_code != 200:
            raise RuntimeError(f'POST Login page {url_post} error: status_code {response1.status_code}')
        response2 = session.get(url_balance)

    result['Balance'] = float(re.search(re_balance, response2.text).group(1).replace(',', '.').strip())
    #try:
    #    result['TarifPlan'] = re.search(re_tariff, response2.text).group(1).replace('&nbsp;', '').strip()
    #except Exception:
    #    logging.info(f'Not found TarifPlan')
    
    session.save_session()
    return result


if __name__ == '__main__':
    print('This is module yota')
