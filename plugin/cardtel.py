# -*- coding: utf8 -*-
import sys;sys.dont_write_bytecode = True
import os, sys, re, logging
import requests
import store

re_balance = r'(?usi)Баланс.*?>.*?>(\d*\.\d*)<'


def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    session = store.load_session(storename)
    if session is None:
        logging.info(f'No saved session {login}')
        session = requests.Session()
    # Проверяем залогинены ли ?
    response3 = session.get('https://my.cardtel.ru/home')
    if len(re.findall(re_balance, response3.content.decode('utf8'))) > 0:
        logging.info('Old session is ok')
    else:  # Нет, логинимся
        data = {'op': 'auth', 'login': login,
                'pwd': password, 'red': '1', 'remember': 'false'}
        response2 = session.post('https://my.cardtel.ru/process', data=data)
        if response3.status_code != 200:
            raise RuntimeError(
                f'Login error: status_code {response2.status_code}!=200')
        response3 = session.get('https://my.cardtel.ru/home')
        if response3.status_code != 200:
            raise RuntimeError(
                f'Get balance page error: status_code {response2.status_code}!=200')
    balance = re.findall(re_balance, response3.content.decode('utf8'))
    if len(balance) == 0:
        raise RuntimeError(f'Balance not found on page')
    result['Balance'] = balance[0]
    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module cardtel')
