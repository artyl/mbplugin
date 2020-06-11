# -*- coding: utf8 -*-
import sys;sys.dont_write_bytecode = True
import os, sys, re, logging
import requests
import store

# regexp для поиска баланса на странице
re_balance = r'(?usi)>Баланс.*?value.*?>\s*(\d+[.,]\d+) '
re_expired = r'(?usi)Дата окончания.*?value.*?>\s*(.*?)<'
re_userName = r'(?usi)handler=Customer.*?>(.*?)<'
re_licSchet = r'(?usi)Номер лицевого счета.*?value.*?>\s*(.*?)<'
re_tarifPlan = r'(?usi)Название текущего тарифа.*?value.*?href.*?>\s*(.*?)<'
re_BlockStatus = r'(?usi)>Статус<.*?value.*?>\s*(.*?)<'

def find_by_regexp(text, param, regexp):
    try:
        return {param: re.search(regexp, text).group(1).strip()}
    except Exception:
        logging.info(f'Not found {param}')    
        return {}

def get_balance(login, password, storename=None):
    logging.info(f'start get_balance {login}')
    result = {}
    url = 'https://user.smile-net.ru/newpa/?handler=Login'
    session = store.load_session(storename)
    if session is None:
        logging.info(f'No saved session {login}')
        session = requests.Session()
    response = session.get(url)
    if re.search(re_balance, response.text):
        logging.info(f'Already logoned {login}')
    else:
        # Логинимся
        logging.info(f'relogon {login}')
        data = {'login': login,'password': password,}
        response = session.post(url, data=data)
        if response.status_code != 200:
            raise RuntimeError(f'POST Login page {url} error: status_code {response.status_code}')

    result['Balance'] = re.search(re_balance, response.text).group(1).replace(',', '.').strip()
    result.update(find_by_regexp(response.text, 'Expired', re_expired))
    result.update(find_by_regexp(response.text, 'UserName', re_userName))
    result.update(find_by_regexp(response.text, 'licSchet', re_licSchet))
    result.update(find_by_regexp(response.text, 'TarifPlan', re_tarifPlan))
    result.update(find_by_regexp(response.text, 'BlockStatus', re_BlockStatus))
   
    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module smile-net')
