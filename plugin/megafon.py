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
                  'before_login_js': 'document.querySelectorAll("button").forEach(el=>el.innerText=="По паролю"?el.click():0)',
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
            {'name': 'TarifPlan', 'url_tag': ['api/tariff'], 'jsformula': """data.name.replace('"','').replace("'",'').replace('&quot;','').replace('&nbsp;',' ').replace('&mdash;','-')"""},
            {'name': 'Min', 'url_tag': ['remainders/mini'], 'jsformula': "data.remainders.filter(el => el.remainderType=='VOICE'&&('availableValue' in el)).map(el => el.availableValue.value).reduce((a,b)=>a+b,0)"},
            {'name': 'Sms', 'url_tag': ['remainders/mini'], 'jsformula': "data.remainders.filter(el => el.remainderType=='MESSAGE'&&('availableValue' in el)).map(el => el.availableValue.value).reduce((a,b)=>a+b,0)"},
            {'name': 'Internet', 'url_tag': ['remainders/mini'], 'jsformula': "data.remainders.filter(el => el.remainderType=='INTERNET'&&('availableValue' in el)).map(el => el.availableValue.value*1024).reduce((a,b)=>a+b,0)"},  # FIXME el.availableValue.unit
        ])
        try:
            self.result['Internet'] = self.result.get('Internet', 0) * (settings.UNIT['KB'] / settings.UNIT.get(store.options('interUnit'), settings.UNIT['KB']))
        except Exception:
            logging.error(f'Internet calculation fail:{store.exception_text()}')
            del self.result['Internet']
        try:
            url_tag = 'api/options/list/current'
            resps = [v for k, v in self.responses.items() if url_tag in k]
            if len(resps) > 0:
                o_list = resps[-1]
                services = [(i['optionName'], i['monthRate'] * (1 if i['monthly'] else 30)) for i in o_list.get('paid', [])]
                services += [(i['optionName'], i['monthRate'] * (1 if i['monthly'] else 30)) for i in o_list.get('free', [])]
                services.sort(key=lambda i: (-i[1], i[0]))
                free = len([a for a, b in services if b == 0])  # бесплатные
                paid = len([a for a, b in services if b != 0])  # платные
                paid_sum = round(sum([b for a, b in services]), 2)
                self.result['UslugiOn'] = f'{free}/{paid}({paid_sum})'
                self.result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in services])
            else:
                logging.error(f'Not found response {url_tag}')
        except Exception:
            exception_text = f'Ошибка обработки api/options/list/current {store.exception_text()}'
            logging.error(exception_text)

        return


def get_balance_browser(login, password, storename=None, **kwargs):
    ''' Работаем через Browser На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__).main()

def get_balance_api(login, password, storename=None, **kwargs):
    result = {}
    session = store.Session(storename)
    response3 = session.get('https://old.lk.megafon.ru/api/lk/main/atourexpense')
    if 'json' in response3.headers.get('content-type') and 'balance' in response3.text:
        logging.info('Old session is ok')
    else:  # Нет, логинимся
        logging.info('Old session is bad, relogin')
        session.drop_and_create()
        response1 = session.get('https://old.lk.megafon.ru/login/')
        if response1.status_code != 200:
            raise RuntimeError(f'GET Login page error: status_code {response1.status_code}!=200')
        csrf = re.search('(?usi)name="CSRF" value="([^\"]+)"', response1.text)
        data = {'CSRF': csrf, 'j_username': f'+7{login}', 'j_password': password}
        response2 = session.post('https://old.lk.megafon.ru/dologin/', data=data)
        if response2.status_code != 200:
            raise RuntimeError(f'POST Login page error: status_code {response2.status_code}!=200')
        response3 = session.get('https://old.lk.megafon.ru/api/lk/main/atourexpense')
        if response3.status_code != 200 or 'json' not in response3.headers.get('content-type'):
            raise RuntimeError(f'Get Balance page not return json: status_code={response2.status_code} {response3.headers.get("content-type")}')
        if 'balance' not in response3.text:
            raise RuntimeError(f'Get Balance page not return balance: status_code={response2.status_code} {response3.text}')

    result['Balance'] = response3.json().get('balance', 0)
    result['KreditLimit'] = response3.json().get('limit', 0)

    try:
        response4 = session.get('https://old.lk.megafon.ru/api/profile/name')
        if response4.status_code == 200 and 'json' in response4.headers.get('content-type'):
            result['UserName'] = response4.json()['name'].replace('"', '').replace("'", '').replace('&quot;', '')

        response5_new = session.get('https://old.lk.megafon.ru/api/tariff/2019-3/current')
        response5 = session.get('https://old.lk.megafon.ru/api/tariff/current')
        if response5.status_code != 200:
            response5 = response5_new
        if response5.status_code == 200 and 'json' in response5.headers.get('content-type'):
            result['TarifPlan'] = response5.json().get('name', '').replace('&nbsp;', ' ').replace('&mdash;', '-')
    except Exception:
        exception_text = f'Ошибка при получении дополнительных данных {store.exception_text()}'
        logging.error(exception_text)

    # Старый вариант без получения стоимости платных услуг
    # response6 = session.get('https://old.lk.megafon.ru/api/lk/mini/options')
    # if response6.status_code == 200 and 'json' in response6.headers.get('content-type'):
    #    servicesDto = response6.json().get('servicesDto', {})
    #    result['UslugiOn'] = f"{servicesDto.get('free','')}/{servicesDto.get('paid','')}"
    try:
        response6 = session.get('https://old.lk.megafon.ru/api/options/list/current')
        if response6.status_code == 200 and 'json' in response6.headers.get('content-type'):
            oList = response6.json()
            services = [(i['optionName'], i['monthRate'] * (1 if i['monthly'] else 30)) for i in oList.get('paid', [])]
            services += [(i['optionName'], i['monthRate'] * (1 if i['monthly'] else 30)) for i in oList.get('free', [])]
            services.sort(key=lambda i: (-i[1], i[0]))
            free = len([a for a, b in services if b == 0])  # бесплатные
            paid = len([a for a, b in services if b != 0])  # платные
            paid_sum = round(sum([b for a, b in services]), 2)
            result['UslugiOn'] = f'{free}/{paid}({paid_sum})'
            result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in services])
    except Exception:
        exception_text = f'Ошибка обработки api/options/list/current {store.exception_text()}'
        logging.error(exception_text)

    try:
        response7 = session.get('https://old.lk.megafon.ru/api/options/remaindersMini')
        if response7.status_code == 200 and 'json' in response7.headers.get('content-type'):
            r7_remainders = response7.json().get('remainders', [])  # {.., remainders: [{remainders:[{...},{...}], ...]...},  ...}
            remainders = sum([i.get('remainders', []) for i in r7_remainders if 'в крыму' not in i.get('name', '').lower()], [])
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
    pkey = store.get_pkey(login, plugin_name=__name__)
    if store.options('plugin_mode', pkey=pkey).upper() == 'WEB_DEBUG':
        return get_balance_browser(login, password, storename)
    return get_balance_api(login, password, storename)

if __name__ == '__main__':
    print('This is module megafon')
