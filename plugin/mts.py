# -*- coding: utf8 -*-
''' Автор ArtyLa
Огромная благодарность pasha за его плагин МТС_Pasha_wR used internet, который сильно ускорил процесс '''
import os, sys, re, time, logging, traceback
import requests
import store, settings

interUnit = 'GB'  # В каких единицах идет выдача по интернету


def do_login(session, pages, login, password):
    # Заходим на главную страницу
    response1 = session.get('https://login.mts.ru/amserver/UI/Login')
    if response1.status_code != 200:
        raise RuntimeError(
            f'GET Login page error: status_code {response1.status_code}!=200')
    pages.append(response1.text)
    csrf_sign = re.search(
        '(?usi)name="csrf.sign" value="([^\"]+)"', response1.text).group(1)
    csrf_ts = re.search(
        '(?usi)name="csrf.ts" value="([^\"]+)"', response1.text).group(1)
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
    response2 = session.post(
        'https://login.mts.ru/amserver/UI/Login', data=data)
    pages.append(response2.text)
    if response2.status_code != 200:
        raise RuntimeError(
            f'POST Login page error: status_code {response2.status_code}!=200')


def get_api_url(session, pages, token, longtask=False):
    '''у МТС некоторые операции делаются в два приема (longtask==True), сначала берется одноразовый токен, 
    а затем с этим токеном выдается страничка, иногда если слишком быстро попросить ответ  вместо нужного json
    возвращает json {'loginStatus':'InProgress'}  '''
    url = f'https://lk.mts.ru/api/{token}'
    if longtask:
        logging.info(url)
        response1 = session.get(url)
        logging.info(f'{response1.status_code}')
        pages.append(response1.text)
        CountersKey = response1.text.strip('"')
        url = f'https://lk.mts.ru/api/longtask/check/{CountersKey}?for=api{token}'
    for _ in range(10):  # 10 попыток TODO вынести в settings
        time.sleep(2)
        logging.info(f'{url}')
        response2 = session.get(url)
        logging.info(f'{response2.status_code}')
        if response2.status_code != 200:
            # Надо чуть подождать (бывает что и 6 секунд можно прождать)
            continue
        if 'json' in response2.headers.get('content-type'):
            # если у json есть 'loginStatus'=='InProgress' уходим на дополнительный круг
            if response2.json().get('loginStatus', '') != 'InProgress':
                break  # результат есть выходим из цикла
        else:
            logging.info(f"Not json:{response2.headers.get('content-type')}")
            # ответ есть и это не json - выходим
            break
    else:
        raise RuntimeError(f'Limit retry for {url}')
    return response2


def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    result = {}
    # !!! Без этого ругается на несовместимый браузер
    headers = {'Accept-Language': 'ru', }
    pages = ['']
    session = store.load_session(storename)
    if session is None:  # Сессия не сохранена - создаем
        session = requests.Session()
        session.headers.update(headers)

    # TODO Start mobile modem correction - не могу проверить у меня такого нет
    # Пришлось добавить это из-за попыток МТС автоматически залогинить с номером симки модема

    # Проверяем залогинены ли ?
    url = 'https://lk.mts.ru/api/login/userInfo'
    response3 = session.get(url)
    if 'json' in response3.headers.get('content-type'):
        logging.info('Old session is ok')
        logging.info(f'{response3.json()["loginStatus"]=}')
    else:  # Нет, логинимся
        logging.info('Old session is bad, relogin')
        do_login(session, pages, login, password)
    
    response3 = get_api_url(session, pages, 'login/userInfo', longtask=False)
    pages.append(response3.text)
    ct = response3.headers.get('content-type')
    if 'json' not in ct:
        # Отдали не json, попробуем перелогиниться 1 раз
        logging.info('userInfo not return json try relogon, relogin')
        response3 = get_api_url(session, pages, 'userInfo', longtask=False)
        pages.append(response3.text)
        ct = response3.headers.get('content-type')
        if 'json' not in ct:
            # снова не json - тогда в другой раз заново
            store.drop_session(storename)
            raise RuntimeError(f'login/userInfo not return json: {ct}')
    profile = response3.json()['userProfile']
    # Это баланс с login/userInfo (он не всегда обновляется, так что может отстать от реальности)
    result['Balance'] = round(profile.get('balance', 0), 2)
    result['TarifPlan'] = profile.get('tariff', '')
    result['UserName'] = profile.get('displayName', '')

    response4 = get_api_url(session, pages, 'accountInfo/balance', longtask=True)
    if 'json' in response4.headers.get('content-type'):
        try:
            data = response4.json().get('data', {})
            result['Balance'] = round(data['amount'], 2)
        except Exception:
            tb = "".join(traceback.format_exception(*sys.exc_info()))
            logging.info(f'не смогли взять баланс с accountInfo/balance: {tb}')

    response5 = get_api_url(session, pages, 'sharing/counters', longtask=True)
    if 'json' in response5.headers.get('content-type'):
        counters = response5.json()['data']['counters']
        # Минуты
        calling = [i for i in counters if i['packageType'] == 'Calling']
        if calling != []:
            unit = {'Second': 60, 'Minute': 1}.get(calling[0]['unitType'], 1)
            nonused = [i['amount'] for i in calling[0]
                       ['parts'] if i['partType'] == 'NonUsed']
            usedbyme = [i['amount'] for i in calling[0]
                        ['parts'] if i['partType'] == 'UsedByMe']
            if nonused != []:
                result['Min'] = int(nonused[0]/unit)
            if usedbyme != []:
                result['SpendMin'] = int(usedbyme[0]/unit)
        # SMS
        messaging = [i for i in counters if i['packageType'] == 'Messaging']
        if messaging != []:
            nonused = [i['amount'] for i in messaging[0]
                       ['parts'] if i['partType'] == 'NonUsed']
            if nonused != []:
                result['SMS'] = int(nonused[0])
        # Интернет
        internet = [i for i in counters if i['packageType'] == 'Internet']
        if internet != []:
            unitMult = settings.UNIT.get(internet[0]['unitType'], 1)
            unitDiv = settings.UNIT.get(interUnit, 1)
            nonused = [i['amount'] for i in internet[0]
                       ['parts'] if i['partType'] == 'NonUsed']
            if nonused != []:
                result['Internet'] = round(nonused[0]*unitMult/unitDiv, 2)

    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module mts')
