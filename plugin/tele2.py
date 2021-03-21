# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging
import requests
import store, settings

icon = '789CAD532DA8C250143E0F5E31080B83D581618F056141EBE00583F0C06235D9865530894D64C13010C12C68B50D8345C3FA82C16A90051141C7E6DF39CF5DAE6F4E1EBCF7C11776EE77CE3DDF39BB9F5FF97720E46FFCB851B8F30DE4EF83FB398FCBE5F267FABE0F994C060A85029CCF678AD56A358ABDE2683422EDE170A05E645966F9BAAEC79BFD01CBB2487B3C1EE95B5114963F180CC0300CEAA35AAD42A5528172B90CB95C0E5455A5BB86C361623E72329940B3D9846EB70BBD5E0F1CC7A1386A4EA713D326E5E35C70263C168B456C7E49F948BC07FBE7B15C2E1F346118422A95225FCFF68335F91A8220D0CCF16C3C1E93CF76BB4D1E77BB1DF3C6F78231DE4BBD5EA7F833341A0D9A99A669502A95C81F6AB7DB2DF519017B984EA7D0E974683FD96C96CE716FA669329DE779AC0FFEBF705D37E613678E75715711B01ECE68BD5E8324492F771131080210459169E7F379CCE766B379F92E56AB15A4D369D2CE66B387DC56ABF5ABB7B5DFEFA1DFEF9357DC6FB15804DBB6FFE5DD22AF62AEE146'

api_url = 'https://api.tele2.ru/api/subscribers/'

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    def check_or_get_bearer():
        '''Проверяем если сессия отдает баланс, то ок, если нет, то логинимся заново'''
        session = store.Session(storename, headers = headers)
        if 'Authorization' in session.headers:
            response1 = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/balance')
            if response1.status_code == 200:
                logging.info('Old session bearer ok')
                return session
        session.drop_and_create(headers = headers) # TODO непонятно как лучше рубить концы или нет
        response2 = session.post(f'https://sso.tele2.ru/auth/realms/tele2-b2c/protocol/openid-connect/token?msisdn=7{login}&action=auth&authType=pass', data=data)
        if response2.status_code == 200:
            logging.info('New bearer is ok')
            bearer = response2.json()['access_token']
            # !!! TODO теперь session.session.headers подумать как лучше 
            session.update_headers({'Authorization': 'Bearer ' + bearer})
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
    session = check_or_get_bearer()
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
    paid_tarif = tarif_fee*settings.UNIT.get(tarif_period, 1)
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
    paid_sum = paid_tarif+round(sum([b for a, b in services if b != 0]), 2)
    result['UslugiOn'] = f'{free}/{paid}({paid_sum})'
    services.append(['Tarif:'+result['TarifPlan'], paid_tarif])  # Добавляем тарифный план как бы как услугу (но после того как все посчитали)
    result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in services])

    # остатки
    response_r = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/rests')
    rests = get_data(response_r).get('rests', [])
    if len(rests) > 0:
        result['Min'] = 0
        result['Internet'] = 0
        result['SMS'] = 0
        result['BlockStatus'] = ''
        for rest in rests:
            if rest['uom'] == 'min':
                result['Min'] += rest['remain']
            if rest['uom'] == 'mb':
                result['Internet'] += rest['remain']*(settings.UNIT['MB']/settings.UNIT.get(store.options('interUnit'), settings.UNIT['MB']))
            if rest['uom'] == 'pcs':
                result['SMS'] += rest['remain']
            if 'billingServiceStatus' in rest.get('service', {}):
                result['BlockStatus'] = rest['service']['billingServiceStatus']
    session.save_session()
    return result


if __name__ == '__main__':
    print('This is module tele2')
