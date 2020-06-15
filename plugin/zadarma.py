# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store

# Строка для поиска баланса на странице
re_balance = r'(?usi)balance.*?>\D*?(\d*?[\.,]\d*?)\D*?<'
re_tariff = r'(?usi)tariffInfo\W+>([^\<]+)<'  # Строка для поиска тарифа
re_min = '(?usi)доступно: (\d+) минут'  # Строка для поиска доступных минут


def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    }
    data = {
        'answer': 'json',
        'email': login,
        'password': password,
    }
    session = store.load_session(storename)
    if session is None:
        logging.info(f'No saved session {login}')
        session = requests.Session()
    response3 = session.get('https://my.zadarma.com/')
    if re.search(re_balance, response3.text):
        logging.info(f'Already logoned {login}')
    else:
        logging.info(f'Session timeout, relogon {login}')
        response1 = session.get(
            'https://my.zadarma.com/auth/', headers=headers)
        response2 = session.post(
            'https://my.zadarma.com/auth/login/', data=data)
        response3 = session.get('https://my.zadarma.com/')

    result['Balance'] = re.search(
        re_balance, response3.text).group(1).replace(',', '.')
    result['TarifPlan'] = re.search(re_tariff, response3.text).group(
        1).replace('&nbsp;', '').replace('Текущий тарифный план -', '').strip()
    avail_min = re.search(re_min, response3.text)
    if avail_min:
        result['Min'] = avail_min.group(1)
    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module zadarma')
