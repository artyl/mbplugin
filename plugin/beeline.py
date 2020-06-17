# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, time, logging
import requests
import store, settings


def api(session, token, login, item):
    apiURL = 'https://my.beeline.ru/api/1.0/' + item + '?ctn=' + login + '&token=' + token
    response = session.get(apiURL)
    if response.status_code != 200:
        raise RuntimeError(
            f'api get {item} error status_code {response.status_code}!=200')
    if 'json' not in response.headers.get('content-type'):
        raise RuntimeError(f'api {item} not return json {response.text}')
    return response.json()


def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    result = {}
    pages = ['']
    session = store.load_session(storename)
    if session is None:  # Сессия не сохранена - создаем
        session = requests.Session()
        headers = {'User-Agent': 'tiehttp', }
        session.headers.update(headers)

    uri = 'https://my.beeline.ru/api/1.0/auth/auth?login=' + \
        login + '&password=' + password
    response1 = session.get(uri)
    if response1.status_code != 200:
        raise RuntimeError(
            f'Login error: status_code {response1.status_code}!=200')

    if 'json' not in response1.headers.get('content-type') or response1.json()['meta']['status'] != 'OK':
        raise RuntimeError(f'Login error: .meta.status!=OK {response1.text}')
    token = response1.json()['token']

    jsonBalance = api(session, token, login, 'info/prepaidBalance')
    if jsonBalance['meta']['status'] == 'ERROR' and jsonBalance['meta']['code'] == 49999:
        jsonBalance = api(session, token, login, 'info/postpaidBalance')
    if jsonBalance['meta']['status'] == 'OK':
        result['Balance'] = round(jsonBalance['balance'], 2)
    else:
        raise RuntimeError(f'Balance not found in {jsonBalance}')

    jsonTariff = api(session, token, login, 'info/pricePlan')
    if jsonTariff['meta']['status'] == 'OK':
        result['TarifPlan'] = jsonTariff['pricePlanInfo']['entityName']

    # список услуг
    jsonSubscr = api(session, token, login, 'info/subscriptions')
    subscr = len(jsonSubscr.get('subscriptions',[]))
    jsonServices = api(session, token, login, 'info/serviceList')
    paid_sum = 0
    ppi = jsonTariff['pricePlanInfo']
    if ppi['rcRate'] is not None and ppi['rcRatePeriod'] is not None:
        kperiod = 30 if jsonTariff['pricePlanInfo']['rcRatePeriod'].split('.')[-1]=='dayly' else 1
        paid_sum = ppi['rcRate'] * kperiod
    services = []
    for el in jsonServices['services']:
        if el['rcRate'] is not None and el['rcRatePeriod'] is not None:
            kperiod = 30 if el['rcRatePeriod'].split('.')[-1]=='dayly' else 1
            fee = el['rcRate'] * kperiod
        else:
            fee = 0
        services.append((el['entityName'],fee))
    free = len([a for a, b in services if b == 0])  # бесплатные
    paid = len([a for a, b in services if b != 0])  # платные
    paid_sum = paid_sum+round(sum([b for a, b in services if b != 0]), 2)
    result['UslugiOn'] = f'{free}/{subscr}/{paid}({paid_sum})'
    result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in services])

    jsonStatus = api(session, token, login, 'info/status')
    if jsonStatus['meta']['status'] == 'OK':
        result['BlockStatus'] = jsonStatus['status']

    jsonRests = api(session, token, login, 'info/rests')
    if jsonRests['meta']['status'] == 'OK' and 'rests' in jsonRests:
        result['Min'] = 0
        result['Internet'] = 0
        result['SMS'] = 0
        for elem in jsonRests['rests']:
            if elem['unitType'] == 'VOICE':
                result['Min'] += elem['currValue']
            if elem['unitType'] == 'INTERNET':
                result['Internet'] += elem['currValue']
            if elem['unitType'] == 'SMS_MMS':
                result['SMS'] += elem['currValue']

    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module mts')
