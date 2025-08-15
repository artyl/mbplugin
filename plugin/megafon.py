# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, io, re, logging, collections
import requests
import store, settings, browsercontroller

interUnit = 'GB'
icon = '789C73F235636100033320D600620128666450804840E591C1FFFFFFB1E237DF1F32CCBF91C7B0F66E13C3D3AFD771AA43C63FFE7C6688D8C5CC10B69381E1FCEB6D601A19171ED1C0A9F7CCAB4D286AB1E987E15B1F8EA1E9FF87A1069F7E10FEF7FF2F5C7FDC5E1E9CFA41F265C7F4C1EA57DDA963C838280516CB3C2803D78FCD7C64FDFD1743C1F4D9D79B196A4E5AC0F5806850D8E2D38F0F5F7EBB8761F59D7AAC725B1FF4E1751F084FBF92C8B0FDD124BC76E0D33FE95214C3B73F1F71EA8BDDC385573FC88FB8E441E2317B38F0EA87F96FF2A56892DD0F731BA130C225F7EFFF1F14FDBFFE7E235AFFA5B7BB71E683C5378B71EA8FD9C389926E09E10B6F7680E9EBEF0FE1540300F7C7D83E'

login_url = 'https://lk.megafon.ru/'
login_checkers = ['public/rwlk/runtime', '/public/rwlk/vendors', '/public/rwlk/app']
login_url_old_lk = 'https://lk.megafon.ru/'
login_checkers_old_lk = ['<input[^>]*name="CSRF"[^>]*', '<input[^>]*name="j_username"[^>]*', '<input[^>]*name="j_password"[^>]*', '<input[^>]*type="submit"[^>]*']
user_selectors = {'chk_lk_page_js': "document.querySelector('.login-tile input.phone-input__field') == null",
                  'chk_login_page_js': "document.querySelector('.login-tile input.phone-input__field') !== null",
                  'before_login_js': 'document.querySelectorAll("button").forEach(el=>el.innerText.toLowerCase().endsWith("по паролю")?el.click():0)',
                  'login_clear_js': "[document.querySelector('input.phone-input__field').setAttribute('value',''),document.querySelector('input.phone-input__field').value='']",
                  'login_selector': 'input.phone-input__field',
                  'password_clear_js': "[document.querySelector('input[type=password]').setAttribute('value',''),document.querySelector('input[type=password]').value='']",
                  'password_selector': 'input[type=password]',
                  'submit_js': "document.querySelectorAll('.login-tile button').forEach(el=>el.innerText=='Войти'?el.click():1)",
                  }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.page_goto('https://lk.megafon.ru/options')
        self.page_wait_for(loadstate=True)
        self.sleep(1)
        self.page_screenshot()
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['api/main/balance'], 'jsformula': "parseFloat(data.balance).toFixed(2)"},
            {'name': 'KreditLimit', 'url_tag': ['api/main/balance'], 'jsformula': "parseFloat(data.balanceWithLimit).toFixed(2)"},
            {'name': 'UserName', 'url_tag': ['/api/auth/sessionCheck'], 'jsformula': """data.name.replace('"','').replace("'",'').replace('&quot;','').replace('&nbsp;',' ').replace('&mdash;','-')"""},
            {'name': 'TarifPlan', 'url_tag': ['api/tariff/2019-3/current'], 'jsformula': """data.name.replace('"','').replace("'",'').replace('&quot;','').replace('&nbsp;',' ').replace('&mdash;','-')"""},
            {'name': 'Min', 'url_tag': ['remainders/mini'], 'jsformula': "(data.remainders ?? []).filter(el => el.remainderType=='VOICE'&&('availableValue' in el)).map(el => el.availableValue.value).reduce((a,b)=>a+b,0)"},
            {'name': 'SMS', 'url_tag': ['remainders/mini'], 'jsformula': "(data.remainders ?? []).filter(el => el.remainderType=='MESSAGE'&&('availableValue' in el)).map(el => el.availableValue.value).reduce((a,b)=>a+b,0)"},
            {'name': 'Internet', 'url_tag': ['remainders/mini'], 'jsformula': "(data.remainders ?? []).filter(el => el.remainderType=='INTERNET'&&('availableValue' in el)).map(el => [el.availableValue.value,el.availableValue.unit]).map(([v,u])=>v*{'KB':1,'МБ':2**10,'ГБ':2**20,'ТБ':2**30}[u]).reduce((a,b)=>a+b,0)"},
        ])
        try: 
            if len(str(self.result.get('Min', 0))) > 9:  # unlimit recalculate to 30000-spend
                self.result['Min'] = 30000-(1000000500-int(self.result['Min']))
        except Exception:
            logging.error(f'Unlimit Min recalculate fail:{store.exception_text()}')
        try:
            # recalculate self.result['Internet'] in KB to interUnit (default GB)
            self.result['Internet'] = self.result.get('Internet', 0) / settings.UNIT.get(store.options('interUnit'), settings.UNIT['GB'])
        except Exception:
            logging.error(f'Internet calculation fail:{store.exception_text()}')
            del self.result['Internet']
        try:
            self.page_goto('https://lk.megafon.ru/options/connected/paid')  # ??? https://lk.megafon.ru/options
            self.sleep(5)
            a_tariff, a_services, a_reports = {}, {}, {}
            resps = [v for k, v in self.responses.items() if 'api/tariff/2019-3/current' in k]
            if len(resps) > 0:
                a_tariff = resps[-1]            
            resps = [v for k, v in self.responses.items() if 'api/services/currentServices/list' in k]
            if len(resps) > 0:
                a_services = resps[-1]
            resps = [v for k, v in self.responses.items() if 'api/reports/expenses' in k]
            if len(resps) > 0:
                a_reports = resps[-1]
            if len(a_services) > 0:
                calc_uslugi(self.result, a_tariff, a_services, a_reports)
            else:
                logging.error(f'Not found response api/services/currentServices/list')
        except Exception:
            exception_text = f'Ошибка обработки списка услуг {store.exception_text()}'
            logging.error(exception_text)
        return


def get_balance_browser(login, password, storename=None, **kwargs):
    ''' Работаем через Browser На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__).main()

def calc_uslugi(result, a_tariff, a_services, a_reports):
    ''' Внимание result меняется внутри функции
    Общее место расчета услуг и для api и для web
    a_tariff - JSON из api/tariff/2019-3/current
    a_services - JSON из api/services/currentServices/list
    a_reports - txt из api/reports/expenses
    '''
    paid_tarif = float(a_tariff.get('ratePlanCharges', {}).get('price', {}).get('value', '0').replace(',', '.'))
    # paid_sum = float(a_tariff.get('ratePlanCharges', {}).get('totalMonthlyPrice', {}).get('value', '0').replace(',', '.'))
    services = [(f"Тариф {result.get('TarifPlan', '')}", paid_tarif)]
    # 'title': '200 ₽ за 30 дней' ->(r'^\d*')-> '200' -> 200
    services += [(i['optionName'], int('0' + re.search(r'^\d*', i.get('previewImportantInformation',[{}])[0].get('title', '')).group())) for i in a_services.get('paid', [])]
    services += [(i['optionName'], 0) for i in a_services.get('free', [])]
    if re.search(r'(?usi)Абонентская\W+плата\W+за\W+Сохранение\W+номера', str(a_reports)):
        services += [('Абонентская плата за Сохранение номера нежелательная', 5)]
    services.sort(key=lambda i: (-i[1], i[0]))
    free = len([a for a, b in services if b == 0])  # бесплатные
    paid = len([a for a, b in services if b != 0])  # платные
    paid_sum = sum([b for a, b in services if b != 0]) # общая сумма
    result['UslugiOn'] = f'{free}/{paid}({paid_sum})'
    result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in services])

def get_balance_api(login, password, storename=None, **kwargs):
    result = {}
    session = store.Session(storename)
    api_url = 'https://api.megafon.ru/mlk/'
    logging.info('Use api {api_url}')
    add_headers = {'User-Agent': 'MLK Android Phone 4.28.10'}
    session.update_headers(add_headers)
    response1 = session.post(api_url + 'login', data={'login': f'7{login}', 'password': password})
    if 'json' not in response1.headers.get('content-type') or 'name' not in response1.json():
        session.drop_and_create()
        raise RuntimeError(f'Authentication failed: status_code={response1.status_code} {response1.text}')
    response2 = session.get(api_url + 'auth/check')
    if 'json' not in response2.headers.get('content-type') or response2.json().get('authenticated') is False:
        session.drop_and_create()
        raise RuntimeError(f'Authentication failed: status_code={response2.status_code} {response2.text}')
    response3 = session.get(api_url + 'api/main/balance')

    result['Balance'] = response3.json().get('balance', 0)
    result['KreditLimit'] = response3.json().get('limit', 0)

    a_profile, a_tariff, a_services = {}, {}, {}

    try:
        response4 = session.get(api_url + 'api/profile/name')
        if response4.status_code == 200 and 'json' in response4.headers.get('content-type'):
            a_profile = response4.json()
            result['UserName'] = a_profile.get('name', '').replace('"', '').replace("'", '').replace('&quot;', '').replace('&nbsp;',' ').replace('&mdash;','-')
    except Exception:
        exception_text = f'Ошибка обработки api/profile/name {store.exception_text()}'
        logging.error(exception_text)

    try:
        response5 = session.get(api_url + 'api/tariff/2019-3/current')
        if response5.status_code == 200 and 'json' in response5.headers.get('content-type'):
            a_tariff = response5.json()
            result['TarifPlan'] = a_tariff.get('name', '').replace('"', '').replace("'", '').replace('&quot;', '').replace('&nbsp;',' ').replace('&mdash;','-')
    except Exception:
        exception_text = f'Ошибка обработки api/tariff/2019-3/current {store.exception_text()}'
        logging.error(exception_text)

    try:
        response6 = session.get(api_url + 'api/reports/expenses')
        if response6.status_code == 200 and 'json' in response6.headers.get('content-type'):
            a_reports = response6.json()
    except Exception:
        exception_text = f'Ошибка обработки api/reports/expenses {store.exception_text()}'
        logging.error(exception_text)

    try:
        response7 = session.get(api_url + 'api/services/currentServices/list')
        if response7.status_code == 200 and 'json' in response7.headers.get('content-type'):
            a_services = response7.json()
            calc_uslugi(result, a_tariff, a_services, a_reports)
    except Exception:
        exception_text = f'Ошибка обработки api/services/currentServices/list {store.exception_text()}'
        logging.error(exception_text)

    try:
        response8 = session.get(api_url + 'api/options/remaindersMini')
        if response8.status_code == 200 and 'json' in response8.headers.get('content-type'):
            r8_remainders = response8.json().get('remainders', [])  # {.., remainders: [{remainders:[{...},{...}], ...]...},  ...}
            remainders = sum([i.get('remainders', []) for i in r8_remainders if 'в крыму' not in i.get('name', '').lower()], [])
            minutes = [i['availableValue'] for i in remainders if i.get('unit', '').startswith('мин') or i.get('groupId', '') == 'voice']
            if len(minutes) > 0:
                result['Min'] = sum([i['value'] for i in minutes if i['value'] < 10000])
            internet = [i['availableValue'] for i in remainders if i.get('unit', '').endswith('Б') or i.get('groupId', '') == 'internet']
            unitDiv = settings.UNIT.get(interUnit, 1)
            if len(internet) > 0:
                result['Internet'] = sum([round(i['value'] * settings.UNIT.get(i.get('unit', ''), 1) / unitDiv, 3) for i in internet])
            sms = [i['availableValue'] for i in remainders if i.get('unit', '').startswith('шту') or i.get('groupId', '') == 'message']
            if len(sms) > 0:
                result['SMS'] = sum([i['value'] for i in sms])
    except Exception:
        exception_text = f'Ошибка обработки api/options/remaindersMini {store.exception_text()}'
        logging.error(exception_text)

    session.save_session()
    return result

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    pkey = store.get_pkey(login, plugin_name=__name__)
    if store.options('plugin_mode', pkey=pkey).upper() == 'API':
        return get_balance_api(login, password, storename)
    return get_balance_browser(login, password, storename)

if __name__ == '__main__':
    print('This is module megafon')


