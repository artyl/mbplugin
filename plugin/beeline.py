# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import sys;sys.dont_write_bytecode = True
import os, sys, re, time, logging
import requests
import store, settings


def api(session, token, login, item):
    apiURL = 'https://my.beeline.ru/api/1.0/' + \
        item + '?ctn=' + login + '&token=' + token
    response = session.get(apiURL)
    if response.status_code != 200:
        raise RuntimeError(
            f'api get {item} error status_code {response2.status_code}!=200')
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
            f'Login error: status_code {response2.status_code}!=200')

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
