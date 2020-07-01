# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, io, re, logging, json
import requests
import store, settings

interUnit = 'GB'

icon = '789C73F2DDC6C20006DB8058038805A09891410122019567808A234003183134344028100409018903070E0045FE8311C3FFFF100A044142203E1043F4908769A11FE62E644C8E7E90DF4118C626453FB27A7C6E20463FCC0D83553F3471C0314C3F8C0FD38FAE0EA676B0EB87C51F29FAD1D30F39FA913136BDB8F4938229D50F0052D0650A'

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    result = {}
    pages = []
    session = store.load_or_create_session(storename)
    response2 = session.get('https://my.danycom.ru/User/GetBalance/')
    if 'json' in response2.headers.get('content-type'):
        logging.info('Old session is ok')
    else:  # Нет, логинимся
        logging.info('Old session is bad, relogin')
        session = store.drop_and_create_session(storename)
        data = {'phone': login, 'email': '', 'password': password}
        response1 = session.post('https://my.danycom.ru/User/SignIn', data=data)
        if response1.status_code != 200:
            raise RuntimeError(f'GET Login page error: status_code {response1.status_code}!=200')
        pages.append(response1.text)
        response2 = session.get('https://my.danycom.ru/User/GetBalance/')
        if response2.status_code != 200:
            raise RuntimeError(f'GET GetBalance status_code {response1.status_code}!=200')
        if 'json' not in response2.headers.get('content-type'):
            raise RuntimeError(f'GET GetBalance not return json {response2.headers.get("content-type")}')

    result['Balance'] = float('.'.join(response2.json())) # Баланс

    response3 = session.get('https://my.danycom.ru/User/GetCustomerInfo/') # ФИО
    if response3.status_code == 200 and 'json' in response3.headers.get('content-type'):
        result['UserName'] = response3.json()

    response4 = session.get('https://my.danycom.ru/User/GetBonusBalance/') # Бонусы
    if response4.status_code == 200 and 'json' in response4.headers.get('content-type'):
        result['Balance2'] = response4.json()[0]

    response5 = session.get('https://my.danycom.ru/User/GetCurrentTariff/') # Тариф
    if response5.status_code == 200 and 'json' in response5.headers.get('content-type'):
        result['TarifPlan'] = json.loads(response5.json()).get('Name','')

    response6 = session.get('https://my.danycom.ru/User/GetCustomerStatus/') # Статус блокировки
    if response6.status_code == 200 and 'json' in response6.headers.get('content-type'):
        result['BlockStatus'] = response6.json()

    response7 = session.get('https://my.danycom.ru/User/GetRestTraffic/') # Остатки
    if response7.status_code == 200 and 'json' in response7.headers.get('content-type'):
        rests = json.loads(response7.json())
        result['Min'] = rests.get('CallBalance', 0)
        result['SMS'] = rests.get('SmsBalance', 0)
        k_internet = settings.UNIT.get(rests.get('InternetUnit', 'Мб').upper(), 1024) / 1024
        result['Internet'] = rests.get('InternetBalance', 0) * k_internet
        result['Expired'] = rests.get('EndPeriod','').split('T')[0]

    response8 = session.get('https://my.danycom.ru/Lk/ServicesControl') # Услуги
    if response8.status_code == 200: # это просто html
        services = re.findall(r'(?usi)"Название">(.*?)<.*?руб">\s*(.*?)\s*/\s*(мес|дн|ден)<',response8.text)
        free = len([a for a, b, c in services if b == '0'])  # бесплатные
        paid = len([a for a, b, c in services if b != '0'])  # платные
        paid_sum = round(sum([float(b) for a, b, c in services]), 2)
        result['UslugiOn'] = f'{free}/{paid}({paid_sum})'
        result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b, c in services])  

    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module danycom')
