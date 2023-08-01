# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, time, logging
import store, settings, browsercontroller

icon = '789C7D93CB6B135114C6BF79C4BC66924993D0269926D3247DD8579A5A92D61A5B84B6282816AC8FADB890BAB3E24E37EE15D48505F11FD045C54AC577B1540AC5A255B1B4A2958AF85AE9C23E92F8CD344A15F4901FDF9D7BE79C09E7BB67C7EE8C0C2B32A48E68250418EB07A5F3FF45454505CACBCBE1F3F9204912445182D7EB4520184490FC2B3C5E0F227A04A220941021992A8A10A842692F180C4051953F72BD9A86B2AA66A8B12628B14628C63AEEAA46A8550D50889AA026EAE149D6A38C6BD5ABFDCE8F1C3D0F5C2F02770BC03875823A459D26B3E42599E7DE5BEA12799F8776E6A295AB376D012E7F07AEFD004696811B2BC02D726F15784026F2C063324D9EB2C67332CFF5B365045ADA103A3E0CDCE4F31D729F678F587FB2F4ED19F2827BAFA8AFC922F9403E93AF79F8CF0DA332D50E776D3BD41A6A5D164EE2DA9C85BB210BA521034F6316BEE60E78531D50F9AE92CEC0D5DA0E676B16C18616C8A20C4114D86BD1EAAF60F94DB8762B2AC2E13092890489731DB27A2F0A1264D31F7A63936DD6B359E39777FCC1ED70221AD5D19A4E23B77D1B72B91CD22D2984F5305C7607BFCB7C4940B47B2F94ADFBA012676E006EE2EC1A40B0E720D20347D03B7812FD43A7D07FE2347A8E0D2175E830427B0EC0BE6B3FFCDD7D080F5D0246D9E7DB66FFA8E3D4C95548336B48CEADA16BB180BEA53C7AD9B7EE8F45843E156037FBF7A580E0D96118CD6DC0956FC0557A364246C9D88A55273E9547E76C013BE75863BE884E7A1059A01F0BE6BD584679BACDBA0389C10BF49FDE8F9977883C5CF7D0F1A48824BD6BE1FB29DE9D38FD93DFF1EC4D1E81D2FD3143E3ACE891045C6521B87CC41F81C35F014F4847D848C048D6C0A8AE41C888C3138EC2AFC7E0D1B48D23004DF3A2BAB6D69A1769C30CC9928C4DECB7CD66A75F326246CC9AB57F85611888C562F42ECA1C1B6459E27F8B40AFD42DFE8E9F8F93C73F'
login_url = 'https://my.beeline.ru'
# если залогинены, то попадем сразу в ЛК, иначе попадем ХЗ куда
direct_lk_url = 'https://beeline.ru/customers/products/elk/tab/mobile-connection'
profile_url = 'https://beeline.ru/customers/products/mobile/profile/'
user_selectors = {'chk_lk_page_js': "document.querySelector('div.initial-form')==null && document.querySelector('form input[type=password]')== null",
                  'chk_login_page_js': "!(document.querySelector('div.initial-form')==null && document.querySelector('form input[type=password]')== null)",
                  'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                  'login_selector': 'form input[type=text]',
                  'password_clear_js': "document.querySelector('form input[type=password][role=textbox]').value=''",
                  'password_selector': 'form input[type=password][role=textbox]',
                  'submit_js': "document.querySelector('form [type=button]').click()",
                 }
profile_tag = 'api/profile/userinfo/data/?noTimeout'
accumulators2_tag = 'api/uni-profile-mobile/blocks'
services_tag = '/api/uni-profile-mobile/services/'
subscribtions_tag = '/api/uni-profile-mobile/subscriptions/'

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        logging.info(f'Before call self.page_goto({direct_lk_url})')
        self.page_goto(direct_lk_url)
        # оптимистичный сценарий если залогинены стараемся побыстрому все забрать
        for _ in range(10):
            self.sleep(1)
            logging.info(f'Wait page {accumulators2_tag} and {services_tag}')
            # Ждем пока появтся accumulators2_tag и services_tag
            if len([v for k, v in self.responses.items() if accumulators2_tag in k and 'accumulators' in v or services_tag in k]) >= 2:
                break
        # Если не попали внутрь ЛК (попали на новую форму логина) - тогда пытаемся логиниться
        if self.page_evaluate(user_selectors['chk_login_page_js']):
            self.do_logon(url=login_url, user_selectors=user_selectors)
            self.page_goto(direct_lk_url)
            self.sleep(10)
        logging.info(f'Before call self.page_goto({profile_url})')
        self.page_goto(profile_url)
        # TODO костыль - сайт очень медленно открывается тупо долго ждем
        for _ in range(0, 180, 5):
            logging.info(f'Wait page {profile_tag} {len(self.responses)}')
            if any([k for k, v in self.responses.items() if profile_tag in k and 'balance' in v]):
                break
            self.sleep(5)
        else:
            raise RuntimeError(f'Так и не получили страницу с балансом {profile_tag}')
        # Приходится сначала долго ждать страницу, а затем когда она пришла получить ее точный url чтобы отфильтроваться от остальных запросов с похожим url
        bal_data_url, bal_data = [[k, v] for k, v in self.responses.items() if profile_tag in k and 'balance' in v][-1]
        self.result['Balance'] = bal_data.get('balance', {}).get('data', {})['balance']
        self.result['TarifPlan'] = bal_data.get('profileSummary', {}).get('data', {}).get('tariffName', '')
        # ??? self.result['Internet'] = ??? {'name': 'Internet', 'url_tag': [bal_data_url], 'jsformula': "Math.max.apply(null,data.accumulators.data.list.concat(data.accumulators.data.listForYoung).map(el => (el!=undefined&&el.unit=='KBYTE'?el.rest:0)))"},
        # ??? self.result['Min'] = ??? {'name': 'Min', 'url_tag': [bal_data_url], 'jsformula': "Math.max.apply(null,data.accumulators.data.list.concat(data.accumulators.data.listForYoung).map(el => (el!=undefined&&el.unit=='SECONDS'?el.rest/60:0))).toFixed(0)"},
        # ??? self.result['SMS'] = {'name': 'SMS', 'url_tag': [bal_data_url], 'jsformula': "Math.max.apply(null,data.accumulators.data.list.concat(data.accumulators.data.listForYoung).map(el => (el!=undefined&&el.unit=='SMS'?el.rest:0)))"},
        self.result['BlockStatus'] = bal_data.get('status', {}).get('data', {}).get('status', '')
        self.result['LicSchet'] = bal_data.get('profileSummary', {}).get('data', {}).get('ctn', '')
        # аккумуляторы тарифа Простой ?
        try:
            # все страницы попадающие под описание
            accumulators2_all = [v for k, v in self.responses.items() if accumulators2_tag in k and 'accumulators' in v]
            if len(accumulators2_all) > 0:  # Нашли что нибудь?
                acc2_list = accumulators2_all[-1].get('accumulators', {}).get('items', [])  # Из последнего подходящего списка берем список items
                acc2_dict = {el.get('unit'): el.get('rest', 0) for el in acc2_list}
                self.result['Internet'] = self.result.get('Internet', 0) + acc2_dict.get('KBYTE', 0)
                self.result['Internet'] = round(self.result.get('Internet', 0) * (settings.UNIT['KB'] / settings.UNIT.get(store.options('interUnit'), settings.UNIT['KB'])), 3)
                self.result['Min'] = self.result.get('Min', 0) + acc2_dict.get('SECONDS', 0)
                self.result['SMS'] = self.result.get('SMS', 0) + acc2_dict.get('SMS', 0)
        except Exception:
            exception_text = f'Ошибка при получении accumulators2 {store.exception_text()}'
            logging.error(exception_text)
        try:
            services = [v for k, v in self.responses.items() if services_tag in k][0]
            subscribtions = [v for k, v in self.responses.items() if subscribtions_tag in k][0]
            uslugi = [[ln.get('title', 'xxx'), ln.get('rcRate', 0) * (1 if ln.get('rcRatePeriod') == 'Mounthly' else 1)] for ln in services]
            # у меня этого нет - строчка ниже написана в слепую
            uslugi.extend([[ln.get('title', 'xxx'), ln.get('rcRate', 0) * (1 if ln.get('rcRatePeriod') == 'Mounthly' else 1)] for ln in subscribtions])
            # дополнительно добавляем алерт про услуги
            if len(subscribtions) > 0:
                uslugi.append(['Unwanted Нежелательная подписка (проверьте)', 0])
            profile = [v for k, v in self.responses.items() if profile_tag in k and 'balance' in v][0]['profileSummary']['data']
            # Цена тарифа только в виде '250 ₽ в месяц' - придется парсить
            tariff_rate = int(re.sub(r'\D', '', profile['tariffRcRateText']))
            paid_sum = tariff_rate * (30 if 'день' in profile.get('tariffRcRateText') else 1)
            free = len([a for a, b in uslugi if b == 0])  # бесплатные
            subscr = len(subscribtions)
            paid = len([a for a, b in uslugi if b != 0])  # платные
            paid_sum = paid_sum + round(sum([b for a, b in uslugi if b != 0]), 2)
            self.result['UslugiOn'] = f'{free}/{subscr}/{paid}({paid_sum})'
            self.result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in uslugi])
        except Exception:
            exception_text = f'Ошибка при получении списка услуг и подписок {store.exception_text()}'
            logging.error(exception_text)


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
    session = store.Session(storename, headers={'User-Agent': 'tiehttp', })
    uri = 'https://my.beeline.ru/api/1.0/auth/auth?login=' + \
        login + '&password=' + password
    response1 = session.get(uri)
    if response1.status_code != 200:
        raise RuntimeError(f'Login error: status_code {response1.status_code}!=200')

    if 'json' not in response1.headers.get('content-type') or response1.json().get('meta', {}).get('status', '') != 'OK':
        raise RuntimeError(f'Login error: .meta.status!=OK {response1.text}')
    token = response1.json()['token']

    jsonBalance = beeline_api(session, token, login, 'info/prepaidBalance')
    if jsonBalance.get('meta', {}).get('status', '') == 'ERROR' and jsonBalance.get('meta', {}).get('code', 0) == 49999:
        jsonBalance = beeline_api(session, token, login, 'info/postpaidBalance')
    if jsonBalance.get('meta', {}).get('status', '') == 'OK':
        result['Balance'] = round(jsonBalance['balance'], 2)
    else:
        raise RuntimeError(f'Balance not found in {jsonBalance}')

    try:
        jsonTariff = beeline_api(session, token, login, 'info/pricePlan')
        if jsonTariff.get('meta', {}).get('status', '') == 'OK':
            result['TarifPlan'] = jsonTariff['pricePlanInfo']['entityName']

        # список услуг
        jsonSubscr = beeline_api(session, token, login, 'info/subscriptions')
        subscr = len(jsonSubscr.get('subscriptions', []))
        jsonServices = beeline_api(session, token, login, 'info/serviceList')
        paid_sum = 0
        ppi = jsonTariff['pricePlanInfo']
        kperiod = 1
        if ppi.get('rcRate', None) is not None and ppi.get('rcRatePeriod', None) is not None:
            kperiod = 30 if jsonTariff['pricePlanInfo']['rcRatePeriod'].split('.')[-1] == 'dayly' else 1
            paid_sum = ppi['rcRate'] * kperiod
        services = []
        for el in jsonServices['services']:
            if el.get('rcRate', None) is not None and el.get('rcRatePeriod', None) is not None:
                kperiod = 30 if el['rcRatePeriod'].split('.')[-1] == 'dayly' else 1
                fee = el['rcRate'] * kperiod
            else:
                fee = 0
            services.append((el['entityName'], fee))
        free = len([a for a, b in services if b == 0])  # бесплатные
        paid = len([a for a, b in services if b != 0])  # платные
        paid_sum = paid_sum + round(sum([b for a, b in services if b != 0]), 2)
        result['UslugiOn'] = f'{free}/{subscr}/{paid}({paid_sum})'
        result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in services])

        jsonStatus = beeline_api(session, token, login, 'info/status')
        if jsonStatus.get('meta', {}).get('status', '') == 'OK':
            result['BlockStatus'] = jsonStatus['status']

        jsonRests = beeline_api(session, token, login, 'info/rests')
        if jsonRests.get('meta', {}).get('status', '') == 'OK' and 'rests' in jsonRests:
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
        if jsonAcc.get('meta', {}).get('status', '') == 'OK' and 'accumulators' in jsonAcc:
            result['Min'] = result.get('Min', 0)
            result['Internet'] = result.get('Internet', 0)
            result['SMS'] = result.get('SMS', 0)
            for elem in jsonAcc['accumulators']:
                if elem.get('unit', '') == 'SECONDS':
                    result['Min'] += elem.get('rest', 0) // 60
                if elem.get('unit', '') == 'KBYTE' and elem.get('accName', '') != 'в роуминге':
                    result['Internet'] += elem.get('rest', 0) * (settings.UNIT['KB'] / settings.UNIT.get(store.options('interUnit'), settings.UNIT['KB']))
                if elem.get('unit', '') == 'SMS':
                    result['SMS'] += elem.get('rest', 0)
    except Exception:
        exception_text = f'Ошибка при получении дополнительных данных {store.exception_text()}'
        logging.error(exception_text)

    session.save_session()
    return result


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    pkey = store.get_pkey(login, plugin_name=__name__)
    if store.options('plugin_mode', pkey=pkey).upper() == 'WEB':
        return get_balance_browser(login, password, storename)
    return get_balance_api(login, password, storename)


if __name__ == '__main__':
    print('This is module beeline')
