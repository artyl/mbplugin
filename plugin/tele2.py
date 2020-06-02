# -*- coding: utf8 -*-
import sys;sys.dont_write_bytecode = True
import os, sys, re, logging
import requests
import store

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    def check_or_get_bearer(session):
        '''Проверяем если сессия отдает баланс, то ок, если нет, то логинимся заново'''
        if 'Authorization' in session.headers:
            response1 = session.get(
                f'https://api.tele2.ru/api/subscribers/7{login}/balance')
            if response1.status_code == 200:
                logging.info('Old session bearer ok')
                return session
        response2 = session.post(
            f'https://sso.tele2.ru/auth/realms/tele2-b2c/protocol/openid-connect/token?msisdn=7{login}&action=auth&authType=pass', data=data)
        if response2.status_code == 200:
            logging.info('New bearer is ok')
            bearer = response2.json()['access_token']
            session.headers['Authorization'] = 'Bearer ' + bearer
            return session
        logging.error(
            f'Bearer get error {response2.status_code} for login {login}')
        raise RuntimeError(f'Bearer get error {response2.status_code}')

    def get_from_js(response, val):
        return str(response.json()['data'][val]) if response.status_code == 200 else ''

    result = {}
    headers = {
        'Tele2-User-Agent': '"mytele2-app/3.17.0"; "unknown"; "Android/9"; "Build/12998710"',
        'User-Agent': 'okhttp/4.2.0', 'X-API-Version': '1',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': '7'+login,
        'password': password,
        'grant_type': 'password', 'client_id': 'android-app', 'password_type': 'password'
    }
    session = store.load_session(storename)
    if session is None:
        session = requests.Session()
        session.headers.update(headers)
    session = check_or_get_bearer(session)
    response = session.get(
        f'https://api.tele2.ru/api/subscribers/7{login}/balance')
    result['Balance'] = get_from_js(response, 'value')  # баланс
    response = session.get(
        f'https://api.tele2.ru/api/subscribers/7{login}/tariff')
    result['TarifPlan'] = get_from_js(response, 'frontName')  # тариф
    response = session.get(
        f'https://api.tele2.ru/api/subscribers/7{login}/profile')
    result['UserName'] = get_from_js(response, 'fullName')  # ФИО владельца
    response = session.get(
        f'https://api.tele2.ru/api/subscribers/7{login}/rests')
    rests = response.json().get('data', {}).get('rests', [])
    if len(rests) > 0:
        result['Min'] = 0
        result['Internet'] = 0
        result['BlockStatus'] = ''
        for rest in rests:
            if rest['uom'] == 'min':
                result['Min'] += rest['remain']
            if rest['uom'] == 'mb':
                result['Internet'] += rest['remain']
            if 'billingServiceStatus' in rest.get('service', {}):
                result['BlockStatus'] = rest['service']['billingServiceStatus']
    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module tele2')
