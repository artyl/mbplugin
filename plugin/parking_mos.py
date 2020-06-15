# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, io, re, logging, json, random
import requests
import store, settings


def get_balance(login, password, storename=None):
    result = {}
    session = store.load_session(storename)
    if session is None:  # Сессия не сохранена - создаем
        session = requests.Session()
    response3 = session.get('https://lk.parking.mos.ru/ru/cabinet')
    if re.findall("(?usi)accountId\":(.*?),", response3.text) != []:
        logging.info('Old session is ok')
    else:
        logging.info('Old session is bad, relogin')
        response1 = session.get(
            'https://lk.parking.mos.ru/auth/social/sudir?returnTo=/../cabinet')
        csrf = re.findall(
            "(?usi)csrf-token-value.*?content='(.*?)'", response1.text)[0]
        bfp = ''.join([hex(random.randrange(15))[-1] for i in range(32)])
        data = {'isDelayed': 'false', 'login': login, 'password': password,
                'csrftoken_w': csrf, 'bfp': bfp, 'alien': 'false', }
        response2 = session.post(
            'https://login.mos.ru/sps/login/methods/password', data=data)
        response3 = session.get('https://lk.parking.mos.ru/ru/cabinet')

    accountId = re.findall("(?usi)accountId\":(.*?),", response3.text)[0]
    response4 = session.put(
        'https://lk.parking.mos.ru/api/2.40/accounts/getbalance', data={"accountId": accountId})
    result['Balance'] = response4.json()['balance']/100.

    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module megafon')
