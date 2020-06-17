# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store, settings

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

    def get_data(response):
        return response.json().get('data',{}) if response.status_code == 200 else ''

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
    response_b = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/balance')
    result['Balance'] = get_data(response_b).get('value')  # баланс
    response_t = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/tariff')
    result['TarifPlan'] = get_data(response_t).get('frontName', '')  # тариф
    response_p = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/profile')
    result['UserName'] = get_data(response_p).get('fullName', '')  # ФИО владельца
    siteId = get_data(response_p).get('siteId','')  # регион 

    # список услуг
    response_с = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/{siteId}/services?status=connected')
    # Тарифный план у tele2 за услугу не считается, так что просто прибавляем его цену
    tarif_fee = get_data(response_t).get('currentAbonentFee', {}).get('amount', 0)
    tarif_period = get_data(response_t).get('period')
    paid_sum = tarif_fee*settings.UNIT.get(tarif_period, 1)
    services = []
    for el in get_data(response_с):
        name = el.get('name', '')
        abonentFee = el.get('abonentFee', {})
        fee = abonentFee.get('amount', 0)
        fee = 0 if fee is None else fee
        kperiod = settings.UNIT.get(abonentFee.get('period', ''), 1)
        services.append((name, fee*kperiod))
    free = len([a for a, b in services if b == 0])  # бесплатные
    paid = len([a for a, b in services if b != 0])  # платные
    paid_sum = paid_sum+round(sum([b for a, b in services if b != 0]), 2)
    result['UslugiOn'] = f'{free}/{paid}({paid_sum})'
    result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in services])

    # остатки
    response_r = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/rests')
    rests = get_data(response_r).get('rests', [])
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
