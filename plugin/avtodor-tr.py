# -*- coding: utf8 -*-
import sys;sys.dont_write_bytecode = True
import os, sys, re, logging
import requests
import store

# Строка для поиска баланса ФИО и лицевого счета на странице
re_balance = r'(?usi)<td>Баланс</td>.*?<td>(.*?)<'
re_userName = r'(?usi)<td>Клиент ?</td>.*?<td>(.*?)<'  
re_licSchet = r'(?usi)<td>Лицевой счет</td>.*?<td>(.*?)<'  


def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    url = 'https://avtodor-tr.ru/account/login'
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
        # https://stackoverflow.com/questions/12385179/how-to-send-a-multipart-form-data-with-requests-in-python
        files = {"email": (None,login), "password": (None,password), "submit0": (None,'Подождите...'), "return_url": (None,''),}
        response1 = session.post(url, files=files)
        if response1.status_code != 200:
            raise RuntimeError(f'POST Login page {url} error: status_code {response1.status_code}')
    bal = re.search(re_balance, response1.text).group(1).replace(',', '.').strip()
    result['Balance'] = re.sub('(?usi)[^\d.,]', '', bal)
    
    try:
        result['userName'] = re.search(re_userName, response1.text).group(1).replace('&nbsp;', '').strip()
    except Exception:
        logging.info(f'Not found userName')
    try:
        result['licSchet'] =  re.search(re_licSchet, response1.text).group(1).replace('&nbsp;', '').strip()
    except Exception:
        logging.info(f'Not found licSchet')
    
    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module avtodor-tr')
