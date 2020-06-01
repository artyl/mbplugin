# -*- coding: utf8 -*- 
''' Автор ArtyLa
Огромная благодарность pasha за его плагин МТС_Pasha_wR used internet, который сильно ускорил процесс '''
import sys;sys.dont_write_bytecode = True
import os, sys, re, time, logging
import requests
import store, settings

interUnit = 'GB' # В каких единицах идет выдача по интернету

def do_login(session, pages, login, password):
    # Заходим на главную страницу
    response1 = session.get('https://login.mts.ru/amserver/UI/Login')
    if response1.status_code != 200:
        raise RuntimeError(f'GET Login page error: status_code {response1.status_code}!=200')
    pages.append(response1.text)
    csrf_sign = re.search('(?usi)name="csrf.sign" value="([^\"]+)"',response1.text).group(1)
    csrf_ts = re.search('(?usi)name="csrf.ts" value="([^\"]+)"',response1.text).group(1)
    data = {
        'IDToken2': password,
        'rememberme': 'on',
        'IDButton': 'Submit',
        'IDToken1': login,
        'encoded': 'false',
        'loginURL': '/amserver/UI/Login?gx_charset=UTF-8',
        'csrf.sign': csrf_sign,
        'csrf.ts': csrf_ts
    }
    # POST логин и пароль
    logging.info(f'POST: https://login.mts.ru/amserver/UI/Login')
    response2 = session.post('https://login.mts.ru/amserver/UI/Login', data=data)
    pages.append(response2.text)
    if response2.status_code != 200:
        raise RuntimeError(f'POST Login page error: status_code {response2.status_code}!=200') 

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    result = {}
    headers = {'Accept-Language': 'ru',} # !!! Без этого ругается на несовместимый браузер
    pages=['']
    session = store.load_session(storename)
    if session is None:  # Сессия не сохранена - создаем
        session = requests.Session()
        session.headers.update(headers)    

    # TODO Start mobile modem correction - не могу проверить у меня такого нет
    # Пришлось добавить это из-за попыток МТС автоматически залогинить с номером симки модема
    
    # Проверяем залогинены ли ?
    response3 = session.get('https://lk.mts.ru/api/login/userInfo')
    if 'json' in response3.headers.get('content-type'):
        logging.info('Old session is ok')
        logging.info(f'{response3.json()["loginStatus"]=}')
    else: # Нет, логинимся
        logging.info('Old session is bad, relogin')
        do_login(session, pages, login, password)
    # Даже если мы были залогинены, в первый момент userInfo возвращяет InProgress надо подождать
    retry_attempts = 0
    for i in range(10):
        time.sleep(1) # Еще не зашли - подождем
        uri = 'https://lk.mts.ru/api/login/userInfo'
        response3 = session.get(uri)
        if response3.status_code != 200:
            raise RuntimeError(f'{uri}: status_code={response3.status_code}')
        if 'json' not in response3.headers.get('content-type'):
            # Если вернули не json, значит незалогинились, делаем логон заново но только 1 раз чтобы не забанили
            if retry_attempts > 0:
                logging.info(f'{uri} not return JSON try relogin')
                do_login(session, pages, login, password)
                retry_attempts += 1
            else:
                raise RuntimeError(f'No json on userInfo page: content-type={response3.headers.get("content-type")}')
        if response3.json()['loginStatus'] == 'Success':
            break
        if response3.json()['loginStatus'] != 'InProgress':
            raise RuntimeError(f'Unknown loginStatus {response3.json()["loginStatus"]}')
    else:
        raise RuntimeError(f'Limit retry for {uri}')
    pages.append(response3.text)
    profile = response3.json()['userProfile']
    result['Balance'] = round(profile.get('balance',0),2) 
    result['TarifPlan'] = profile.get('tariff','')
    result['UserName'] = profile.get('displayName','')
    
    logging.info(f'GET: https://lk.mts.ru/api/sharing/counters')
    response4 = session.get('https://lk.mts.ru/api/sharing/counters')
    logging.info(f'{response4.status_code}')
    pages.append(response4.text)
    CountersKey = response4.text.strip('"')
    uri = 'https://lk.mts.ru/api/longtask/check/' + CountersKey + '?for=api/sharing/counters';
    for i in range(10):
        time.sleep(2)
        logging.info(f'{uri}')
        response5 = session.get(uri)
        logging.info(f'{response5.status_code}')
        if response5.status_code != 200:
            continue # Надо чуть подождать
        if 'json' in response5.headers.get('content-type'):
            break
    if 'json' in response5.headers.get('content-type'):
        counters = response5.json()['data']['counters']
        # Минуты
        calling = [i for i in counters if i['packageType'] == 'Calling']
        if calling != []:
            unit = {'Second':60, 'Minute':1}.get(calling[0]['unitType'], 1)
            nonused = [i['amount'] for i in calling[0]['parts'] if i['partType'] == 'NonUsed']
            usedbyme = [i['amount'] for i in calling[0]['parts'] if i['partType'] == 'UsedByMe']
            if nonused != []:
                result['Min'] = int(nonused[0]/unit)
            if usedbyme != []:
                result['SpendMin'] = int(usedbyme[0]/unit)
        # SMS
        messaging = [i for i in counters if i['packageType'] == 'Messaging']        
        if messaging != []:
            nonused = [i['amount'] for i in messaging[0]['parts'] if i['partType'] == 'NonUsed']
            if nonused != []:
                result['SMS'] = int(nonused[0])
        # Интернет
        internet =[i for i in counters if i['packageType'] == 'Internet']
        if internet != []:
            unitMult = settings.UNIT.get(internet[0]['unitType'],1)
            unitDiv = settings.UNIT.get(interUnit,1)
            nonused = [i['amount'] for i in internet[0]['parts'] if i['partType'] == 'NonUsed']
            if nonused != []:
                result['Internet'] = round(nonused[0]*unitMult/unitDiv,2)

    store.save_session(storename, session)
    return result
    
if __name__ == '__main__':
    print('This is module mts')