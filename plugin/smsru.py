# -*- coding: utf8 -*-
''' Автор Pasha '''
''' проверка баланса SMS.RU https://sms.ru/ '''
import os, sys, re, logging
import requests
import store

login_url = 'https://sms.ru/?panel=login&action=login'
login_checkers = ['<input[^>]*name="user_phone"[^>]*', '<input[^>]*name="user_password"[^>]*', '<input[^>]*type="submit"[^>]*']

# Строка для поиска баланса
re_balance = r'(?usi)background-image(.*?)>(.*?) руб.<.div><.td>'

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
        data = {'user_phone': login,'user_password': password,}
        response = session.post(login_url, data=data)
        if response.status_code != 200:
            raise RuntimeError(f'POST Login page {login_url} error: status_code {response.status_code}')

    result['Balance'] = re.search(re_balance, response.text).group(2)

    session.save_session()
    return result

if __name__ == '__main__':
    print('This is module sms')
