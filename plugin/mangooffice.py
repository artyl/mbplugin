# -*- coding: utf8 -*-
''' Автор Pasha '''
''' проверка баланса Mango Office https://www.mango-office.ru/ '''
import os, sys, re, logging
import requests
import store

login_url = 'https://auth.mango-office.ru/auth/vpbx'
login_checkers = ['<input[^>]*name="email"[^>]*', '<input[^>]*name="password"[^>]*']

# Строки для поиска баланса и prod_id на странице
re_balance = r'(?usi)info-value">(.*?)</div'
re_prod_id = r'(?usi)data-product-id="(.*?)"'

def get_balance(login, password, storename=None, **kwargs):
    logging.info(f'start get_balance {login}')
    result = {}
    session = store.Session(storename)
    response = session.get(login_url)
    if re.search(re_balance, response.text):
        logging.info(f'Already logoned {login}')
    else:
        # Логинимся
        logging.info(f'relogon {login}')
        session.drop_and_create()
        data = {'app': 'ics','startSession': '1','username': login,'password': password,}
        response = session.post(login_url, data=data)
        if response.status_code != 200:
            raise RuntimeError(f'POST Login page {login_url} error: status_code {response.status_code}')

    # Получаем необходимые значения
    auth_token = response.json().get('auth_token', '')
    refresh_token = response.json().get('refresh_token', '')
    account_id = response.json().get('account_id', '')
    # Заходим в ЛК и получаем prod_id
    data = {'auth_token': auth_token,'refresh_token': refresh_token,'username': login,'app': 'ics','request-uri': '/',}
    response1 = session.post('https://lk.mango-office.ru/auth/create-session', data=data)
    response2 = session.post('https://lk.mango-office.ru/')
    prod_id = re.search(re_prod_id, response2.text).group(1).replace('\'', '')
    # Обновляем токен
    data = {'auth_token': auth_token,'refresh_token': refresh_token}
    response3 = session.post('https://lk.mango-office.ru/' + str(account_id) + '/' + str(prod_id) + '/auth/refresh-token', data=data)
    auth_token = response3.json().get('auth_token', '')
    # Запрашиваем баланс
    data = {'app': 'ics','auth_token': auth_token,'prod_id': prod_id}
    response4 = session.post('https://api-header.mango-office.ru/api/header', data=data)
    data = response4.json()
    balance = data.get('data',[])
    result['Balance'] = balance['account']['fxbalance']

    session.save_session()
    return result

if __name__ == '__main__':
    print('This is module mangooffice')
