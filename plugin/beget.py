# -*- coding: utf8 -*-
''' Автор d1mas '''
''' проверка баланса хостинг-провайдера BEGET
https://beget.com/ru
https://beget.com/ru/kb/api/beget-api '''

import os, sys, re, logging
import store, json

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

def get_balance(login, password, storename=None, **kwargs):
    logging.info(f'start get_balance {login}')
    baseurl = 'https://api.beget.com'
    url = 'https://api.beget.com/api/user/getAccountInfo?login=' + login + '&passwd=' + password + '&output_format=json'
    cookies = dict(beget='begetok')
    session = store.Session(storename)
    session.disable_warnings()
    response = session.get(url, cookies=cookies,headers={'Referer': baseurl + '/'}, verify=False)
    if response.status_code != 200:
        raise RuntimeError(f'Login error: status_code {response.status_code}!=200')
    if not is_json(response.text):
        raise RuntimeError(f'No JSON in reply: {response.text}')
    if response.json()['status'] != 'success':
        raise RuntimeError(f'Login error: reply {response.text}')
    logging.info(f'Parsing data')
    result = {}
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
