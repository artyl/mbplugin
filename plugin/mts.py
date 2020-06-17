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


def get_api_json(session, pages, token, longtask=False):
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
        url = f'https://lk.mts.ru/api/longtask/check/{CountersKey}?for=api/{token}'
    for _ in range(10):  # 10 попыток TODO вынести в settings
        time.sleep(2)
        logging.info(f'{url}')
        response2 = session.get(url)
        logging.info(f'{response2.status_code}')
        if store.read_ini()['Options']['logginglevel'] == 'DEBUG':
            open(os.path.join('..\\log',time.strftime('%Y%m%d%H%M%S.html',time.localtime())),'wb').write(response2.content)
        if response2.status_code >= 400:
            # Вернули ошибку, продолжать нет смысла
            return {}            
        if response2.status_code != 200:
            # Надо чуть подождать (бывает что и 6 секунд можно прождать)
            continue
        if 'json' in response2.headers.get('content-type'):
            # если у json есть 'loginStatus'=='InProgress' уходим на дополнительный круг
            if response2.json().get('loginStatus', '') != 'InProgress':
                return response2.json()  # результат есть выходим из цикла
        else:
            logging.info(f"Not json:{response2.headers.get('content-type')}")
            # ответ есть и это не json - выходим
            return {}
    else:
        logging.info(f'Limit retry for {url}')
    return {}


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
    
    response_json = get_api_json(session, pages, 'login/userInfo', longtask=False)
    if 'userProfile' not in response_json:
        # Отдали не json, попробуем перелогиниться 1 раз
        logging.info('userInfo not return json try relogon, relogin')
        response_json = get_api_json(session, pages, 'userInfo', longtask=False)
        if 'userProfile' not in response_json:
            # снова не json - тогда в другой раз заново
            store.drop_session(storename)
            raise RuntimeError(f'login/userInfo not return json')
    profile = response_json['userProfile']
    # Это баланс с login/userInfo (он не всегда обновляется, так что может отстать от реальности)
    # Берем его, на случай если другого не дадут
    result['Balance'] = round(profile.get('balance', 0), 2)
    result['TarifPlan'] = profile.get('tariff', '')
    result['UserName'] = profile.get('displayName', '')

    response_json = get_api_json(session, pages, 'accountInfo/balance', longtask=True)
    data = response_json.get('data', {})
    if 'amount' in data:
        result['Balance'] = round(data['amount'], 2)
    else:
        logging.info(f'не смогли взять баланс с accountInfo/balance')

    response_json = get_api_json(session, pages, 'services/list/active', longtask=True)
    data = response_json.get('data', {})
    if 'services' in data:
        services = [(i['name'], i.get('subscriptionFees', [{}])[0].get('value', 0)) for i in data['services']]
        services.sort(key=lambda i:(-i[1],i[0]))
        free = len([a for a,b in services if b==0 and (a,b)!=('Ежемесячная плата за тариф', 0)])
        paid = len([a for a,b in services if b!=0])
        paid_sum = round(sum([b for a,b in services if b!=0]),2)
        result['UslugiOn']=f'{free}/{paid}({paid_sum})'
        result['UslugiList']='\n'.join([f'{a}\t{b}' for a,b in services])

    response_json = get_api_json(session, pages, 'sharing/counters', longtask=True)
    data = response_json.get('data', {})
    if 'counters' in data:
        counters = data['counters']
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
    else:
        logging.info(f'не смогли взять counters из sharing/counters')                

    store.save_session(storename, session)
    return result


if __name__ == '__main__':
    print('This is module mts')
