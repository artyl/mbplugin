# -*- coding: utf8 -*-
''' Автор ArtyLa
Огромная благодарность pasha за его плагин МТС_Pasha_wR used internet, который сильно ускорил процесс '''
import os, sys, re, time, logging, traceback
import requests
import store, settings

interUnit = 'GB'  # В каких единицах идет выдача по интернету

icon = '789C75524D4F5341143D84B6A8C0EB2BAD856A4B0BE5E301A508A9F8158DC18498A889896E8C3B638C31F147B83171E34E4388AE5C68E246A3C68D0B5DA82180B5B40A5A94B6F651DA423F012D2DE09D79CF4A207DC949A733F79C39F7CC1D3A37A801FF060912415451058772A09E6FFD04CD18F4DA09C267C214210051FB857EFFC1AFEEB3F3495E2F68DEA35EF396F086F6BCBC46D47E257C2304A1D7045157350DA13A80FA6A1F6AAB7CB4F6AB5A5E08DA71D2F840FC772AEF3B44DD0F1874215A87D1DA34871B57658CDE4F1212B87E2504BBD94F5A01D5938F7B16341F8937CB79C65DBF60DA2DC3E594F1FAE532D64B1BD8DCDCE428D1FAC5B30CDAAD33E483799C2E6B187411E245D124CC63BF18C3DD3BB9326F3B6EDF4A506FB3C49FE5BE99C6DE3D32F6E9636836C671A0631153DEB58AFCC9F155EA4DE951D40579CE8C6B37C5693F895347D388C9EB15F9D148119E1E190D3551F23DC7F366F73A2D4974DA52183E9E831CADCC0F878A38E88AC15C3B4F1A119E5D8B39814EEB125CAD199CF0E4C97FA9227F7CAC809E96382CE4D9489989BA9F7092EF2E7B8A7ACF62D0B58C278F8A15F90F4656D0D29880D5B0C07363EFD6665944B72385012947FC15DCBC56403EB7939BCD6CE0F2852CF193B0352C500F8C1F267EB2CC3FEC5EA10CFFE0D5F39D193C7D5C80BB2DCDEFDBCADFEEFF58FF2A2E9D2FC0F7E9BFC6C45809A74FE62035A778BDE23FCAFD3B28BF0EEB22E597E61E0EF52EE348DF2A2E9EFD8D87236B18BD57C099A13CE596E639B37AF6E66C5E597ECC0B7B7BA97909BDCE0CFA3BB3F074E73906A43CFADA73FC6DBAD4BB597D63DD3C0C35CA0C59049A3D933203926D89DFE3261D779B0217FD67DA2C273667AC9ECDBB323F33F80B823D9864'

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
    response2 = session.post('https://login.mts.ru/amserver/UI/Login', data=data)
    pages.append(response2.text)
    if response2.status_code != 200:
        raise RuntimeError(f'POST Login page error: status_code {response2.status_code}!=200')


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
    pages = ['']
    # !!! Без этого ругается на несовместимый браузер
    headers = {'Accept-Language': 'ru', }
    # Загружаем или создаем сессию
    session = store.load_or_create_session(storename, headers = headers)

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
        session = store.drop_and_create_session(storename, headers = headers)
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
