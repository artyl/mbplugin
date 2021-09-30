# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, time, logging
import store, settings, browsercontroller

icon = '789C7D93CB6B135114C6BF79C4BC66924993D0269926D3247DD8579A5A92D61A5B84B6282816AC8FADB890BAB3E24E37EE15D48505F11FD045C54AC577B1540AC5A255B1B4A2958AF85AE9C23E92F8CD344A15F4901FDF9D7BE79C09E7BB67C7EE8C0C2B32A48E68250418EB07A5F3FF45454505CACBCBE1F3F9204912445182D7EB4520184490FC2B3C5E0F227A04A220941021992A8A10A842692F180C4051953F72BD9A86B2AA66A8B12628B14628C63AEEAA46A8550D50889AA026EAE149D6A38C6BD5ABFDCE8F1C3D0F5C2F02770BC03875823A459D26B3E42599E7DE5BEA12799F8776E6A295AB376D012E7F07AEFD004696811B2BC02D726F15784026F2C063324D9EB2C67332CFF5B365045ADA103A3E0CDCE4F31D729F678F587FB2F4ED19F2827BAFA8AFC922F9403E93AF79F8CF0DA332D50E776D3BD41A6A5D164EE2DA9C85BB210BA521034F6316BEE60E78531D50F9AE92CEC0D5DA0E676B16C18616C8A20C4114D86BD1EAAF60F94DB8762B2AC2E13092890489731DB27A2F0A1264D31F7A63936DD6B359E39777FCC1ED70221AD5D19A4E23B77D1B72B91CD22D2984F5305C7607BFCB7C4940B47B2F94ADFBA012676E006EE2EC1A40B0E720D20347D03B7812FD43A7D07FE2347A8E0D2175E830427B0EC0BE6B3FFCDD7D080F5D0246D9E7DB66FFA8E3D4C95548336B48CEADA16BB180BEA53C7AD9B7EE8F45843E156037FBF7A580E0D96118CD6DC0956FC0557A364246C9D88A55273E9547E76C013BE75863BE884E7A1059A01F0BE6BD584679BACDBA0389C10BF49FDE8F9977883C5CF7D0F1A48824BD6BE1FB29DE9D38FD93DFF1EC4D1E81D2FD3143E3ACE891045C6521B87CC41F81C35F014F4847D848C048D6C0A8AE41C888C3138EC2AFC7E0D1B48D23004DF3A2BAB6D69A1769C30CC9928C4DECB7CD66A75F326246CC9AB57F85611888C562F42ECA1C1B6459E27F8B40AFD42DFE8E9F8F93C73F'

login_url = 'https://my.beeline.ru'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[type=password][role=textbox]') == null",
                'chk_login_page_js': "document.querySelector('form input[type=password][role=textbox]') !== null",
                'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                'login_selector': 'form input[type=text]', 
                'password_clear_js': "document.querySelector('form input[type=password][role=textbox]').value=''",  
                'password_selector': 'form input[type=password][role=textbox]',
                'submit_js': "document.querySelector('form [type=button]').click()",
                }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['api/profile/userinfo/data'], 'jsformula': "parseFloat(data.balance.data.balance).toFixed(2)"},
            #{'name': 'Internet', 'url_tag': ['api/profile/userinfo/data'], 'jsformula': "parseFloat(data.balance.data.balance).toFixed(2)"},
            #{'name': 'UserName', 'url_tag': ['api/user/info'], 'jsformula': "data.data.company"},
            #{'name': 'TurnOff', 'url_tag': ['api/user/info'], 'jsformula': "data.data.days_to_off"},
            #{'name': 'LicSchet', 'url_tag': ['api/user/info'], 'jsformula': "data.data.login"},
            #{'name': 'TarifPlan', 'url_tag': ['api/user/info'], 'jsformula': "data.data.tariff_name"},
            #{'name': 'BlockStatus', 'url_tag': ['api/user/info'], 'jsformula': "data.status"},
            ])          

def get_balance_browser(login, password, storename=None, **kwargs):
    ''' Работаем через Browser На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__).main()

def get_balance_api(login, password, storename=None, **kwargs):
    ''' Работаем через API На вход логин и пароль, на выходе словарь с результатами '''
    def beeline_api(session, token, login, item):
        apiURL = 'https://my.beeline.ru/api/1.0/' + item + '?ctn=' + login + '&token=' + token
        response = session.get(apiURL)
        if response.status_code != 200:
            raise RuntimeError(f'api get {item} error status_code {response.status_code}!=200')
        if 'json' not in response.headers.get('content-type'):
            raise RuntimeError(f'api {item} not return json {response.text}')
        return response.json()
    result = {}
    # Загружаем или создаем сессию
    session = store.Session(storename, headers = {'User-Agent': 'tiehttp', })
    uri = 'https://my.beeline.ru/api/1.0/auth/auth?login=' + \
        login + '&password=' + password
    response1 = session.get(uri)
    if response1.status_code != 200:
        raise RuntimeError(f'Login error: status_code {response1.status_code}!=200')

    if 'json' not in response1.headers.get('content-type') or response1.json()['meta']['status'] != 'OK':
        raise RuntimeError(f'Login error: .meta.status!=OK {response1.text}')
    token = response1.json()['token']

    jsonBalance = beeline_api(session, token, login, 'info/prepaidBalance')
    if jsonBalance['meta']['status'] == 'ERROR' and jsonBalance['meta']['code'] == 49999:
        jsonBalance = beeline_api(session, token, login, 'info/postpaidBalance')
    if jsonBalance['meta']['status'] == 'OK':
        result['Balance'] = round(jsonBalance['balance'], 2)
    else:
        raise RuntimeError(f'Balance not found in {jsonBalance}')

    jsonTariff = beeline_api(session, token, login, 'info/pricePlan')
    if jsonTariff['meta']['status'] == 'OK':
        result['TarifPlan'] = jsonTariff['pricePlanInfo']['entityName']

    # список услуг
    jsonSubscr = beeline_api(session, token, login, 'info/subscriptions')
    subscr = len(jsonSubscr.get('subscriptions',[]))
    jsonServices = beeline_api(session, token, login, 'info/serviceList')
    paid_sum = 0
    ppi = jsonTariff['pricePlanInfo']
    kperiod = 1
    if ppi.get('rcRate', None) != None and ppi.get('rcRatePeriod', None) != None:
        kperiod = 30 if jsonTariff['pricePlanInfo']['rcRatePeriod'].split('.')[-1]=='dayly' else 1
        paid_sum = ppi['rcRate'] * kperiod
    services = []
    for el in jsonServices['services']:
        if el.get('rcRate', None) != None and el.get('rcRatePeriod', None) != None:
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

    jsonStatus = beeline_api(session, token, login, 'info/status')
    if jsonStatus['meta']['status'] == 'OK':
        result['BlockStatus'] = jsonStatus['status']
    
    jsonRests = beeline_api(session, token, login, 'info/rests')
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

    # похоже теперь у билайна не rests а accumulators, данных мало так что пробуем так
    # и не понятно как определить про что аккумулятор, так что пока ориентируемся на поле unit, у интернета он 'unit': 'KBYTE'
    jsonAcc = beeline_api(session, token, login, 'info/accumulators')
    if jsonAcc['meta']['status'] == 'OK' and 'accumulators' in jsonAcc:
        result['Min'] = result.get('Min', 0)
        result['Internet'] = result.get('Internet', 0)
        result['SMS'] = result.get('SMS', 0)
        for elem in jsonAcc['accumulators']:
            if elem['unit'] == 'SECONDS':
                result['Min'] += elem['rest']//60
            if elem['unit'] == 'KBYTE':
                result['Internet'] += elem['rest']*(settings.UNIT['KB']/settings.UNIT.get(store.options('interUnit'), settings.UNIT['KB']))
            if elem['unit'] == 'SMS':
                result['SMS'] += elem['rest']

    session.save_session()
    return result


def get_balance(login, password, storename=None, **kwargs):
    lang = 'p'
    if store.options('plugin_mode', pkey=kwargs.get('pkey','')).upper() == 'WEB':
        return get_balance_browser(login, password, storename)        
    return get_balance_api(login, password, storename)


if __name__ == '__main__':
    print('This is module beeline')
