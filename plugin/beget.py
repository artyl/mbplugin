#проверка баланса хостинг-провайдера BEGET
#https://beget.com/ru
#https://beget.com/ru/kb/api/beget-api
# -*- coding: utf8 -*-
''' Автор d1mas '''
import os, sys, re, logging
import store

def get_balance(login, password, storename=None, **kwargs):
    logging.info(f'start get_balance {login}')
    result = {}
    url = 'https://api.beget.com/api/user/getAccountInfo?login=' + login + '&passwd=' + password + '&output_format=json'
    session = store.Session(storename)
    response = session.get(url)
    if response.status_code != 200:
        raise RuntimeError(f'Login error: status_code {response.status_code}!=200')
    # Не отдают они content-type=json в заголовках
    #if 'json' not in response.headers.get('content-type'):
    #    raise RuntimeError(f'Login error: {response.text}')

    # Разбираем полученный json
    if response.json()['status'] != 'success':
        raise RuntimeError(f'Login error: reply {response.text}')
    logging.info(f'Parsing data')
    data = response.json()['answer']['result']
    result['Balance'] = data['user_balance']

    try:
        result['TarifPlan'] =  data['plan_name']
    except Exception:
        logging.info(f'Not found TarifPlan')
    try:
        result['TurnOff'] = data['user_days_to_block']
    except Exception:
        logging.info(f'Not found TurnOff')

    session.save_session()
    return result


if __name__ == '__main__':
    print('This is module beget')
