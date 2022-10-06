# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging, collections
import requests
import store, settings
import browsercontroller

icon = '789CAD532DA8C250143E0F5E31080B83D581618F056141EBE00583F0C06235D9865530894D64C13010C12C68B50D8345C3FA82C16A90051141C7E6DF39CF5DAE6F4E1EBCF7C11776EE77CE3DDF39BB9F5FF97720E46FFCB851B8F30DE4EF83FB398FCBE5F267FABE0F994C060A85029CCF678AD56A358ABDE2683422EDE170A05E645966F9BAAEC79BFD01CBB2487B3C1EE95B5114963F180CC0300CEAA35AAD42A5528172B90CB95C0E5455A5BB86C361623E72329940B3D9846EB70BBD5E0F1CC7A1386A4EA713D326E5E35C70263C168B456C7E49F948BC07FBE7B15C2E1F346118422A95225FCFF68335F91A8220D0CCF16C3C1E93CF76BB4D1E77BB1DF3C6F78231DE4BBD5EA7F833341A0D9A99A669502A95C81F6AB7DB2DF519017B984EA7D0E974683FD96C96CE716FA669329DE779AC0FFEBF705D37E613678E75715711B01ECE68BD5E8324492F771131080210459169E7F379CCE766B379F92E56AB15A4D369D2CE66B387DC56ABF5ABB7B5DFEFA1DFEF9357DC6FB15804DBB6FFE5DD22AF62AEE146'
api_url = 'https://api.tele2.ru/api/subscribers/'
login_url = 'https://msk.tele2.ru/lk'
api_headers = {'Tele2-User-Agent': 'mytele2-app/6.09.0', 'User-Agent': 'okhttp/6.2.3'}

class browserengine(browsercontroller.BrowserController):

    def data_collector(self):

        def prepare_login(login):
            return re.sub(r'(\d\d\d)(\d\d\d)(\d\d)(\d\d)', '+7 \\1 \\2-\\3-\\4', login)

        def get_state():
            res = self.page_evaluate('''[
                document.querySelector('input[id="keycloakAuth.phone"]') != null,
                document.querySelector('input[id="keycloakAuth.password"]') != null,
                (a => a == null ? '' : a.innerText)(document.querySelector('button.keycloak-login-form__button')),
                document.querySelector('input[id="header-navbar-login"]') != null
                ]''')
            if type(res) == list and len(res) == 4:
                kc_phone, kc_password, kc_button, hnr = res
                return States(kc_phone, kc_password, kc_button, hnr)

        self.baseurl = 'https://tele2.ru/lk'
        States = collections.namedtuple('States', 'kc_phone, kc_password, kc_button, hnr')
        self.page_goto(self.baseurl)
        self.sleep(1)
        states, state = set(), None
        # Проверка текущего состояния и логин пр инеобходимости
        while True:
            # Ждем изменения состояния
            if len(states) > 0:
                for _ in range(10):
                    if state == get_state():
                        self.sleep(1)
            state = get_state()
            logging.info(f'{__name__}:Login phase {state}')
            if state in states:
                logging.info(f'{__name__}:Login phase Dublicate state {state}')
                break  # В каждом состоянии можем побывать не более одного раза иначе на выход чтобы не забанили
            states.add(state)
            if state.kc_phone and not state.kc_password and state.kc_button == 'Далее' and not state.hnr:  # Хочет номер для sms входа
                # Похоже tele2 передумал и можно сразу заходить по паролю
                # self.page_fill("input[id='keycloakAuth.phone']", prepare_login(self.options('tele2_sms_num')))
                # self.sleep(3)
                # self.page_screenshot()
                # self.page_click('button.keycloak-login-form__button')
                self.page_evaluate("document.querySelectorAll('.filled-tabs button').forEach(el=>el.innerText=='По паролю'?el.click():0)")
            elif not state.kc_phone and not state.kc_password and state.kc_button == 'Вход по паролю' and not state.hnr:  # Прислал SMS просит код
                self.page_screenshot()
                self.page_click('button.keycloak-login-form__button')
            elif state.kc_phone and state.kc_phone and state.kc_button == 'Войти' and not state.hnr:  # Добрались до входа с логином паролем - входим
                self.page_press("input[id='keycloakAuth.phone']", "Control+a")
                self.page_fill("input[id='keycloakAuth.phone']", prepare_login(self.login))
                self.page_fill("input[id='keycloakAuth.password']", prepare_login(self.password))
                self.sleep(3)
                self.page_screenshot()
                self.page_click('button.keycloak-login-form__button')
            elif state.kc_phone is False and state.kc_password is False and state.kc_button == '' and state.hnr is False:
                if len(states) == 1:
                    logging.info(f'Already login')
                break
            self.sleep(1)
        if not (state.kc_phone is False and state.kc_password is False and state.kc_button == '' and state.hnr is False):
            self.page_screenshot()
            logging.error(f'Not entered to lk')
            raise RuntimeError('You have not logged into your personal account')
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['/balance$'], 'jsformula': "parseFloat(data.data.value).toFixed(2)"},
            {'name': 'TarifPlan', 'url_tag': ['/tariff$'], 'jsformula': "data.data.frontName"},
            {'name': 'UserName', 'url_tag': ['/profile$'], 'jsformula': "data.data.fullName"},
        ])
        self.page_screenshot()
        self.page_goto(self.baseurl + '/../../lk/remains')
        for _ in range(10):
            if 'connected$' not in str(self.responses.keys()):
                self.sleep(1)
        self.page_screenshot()
        self.page_goto(self.baseurl + '/../../lk/services')
        for _ in range(100):
            if 'subscription$' not in str(self.responses.keys()):
                self.sleep(1)
        self.page_screenshot()
        try:
            response_t = [v for k, v in self.responses.items() if k.endswith('tariff$')][0]
            response_с = [v for k, v in self.responses.items() if k.endswith('connected$')][0]
            response_s = [v for k, v in self.responses.items() if k.endswith('subscription$')][0]
            response_r = [v for k, v in self.responses.items() if k.endswith('rests$')][0]
            self.result = calculate_dop(self.result, response_t, response_с, response_s, response_r)
        except Exception:
            exception_text = f'Ошибка при получении дополнительных данных {store.exception_text()}'
            logging.error(exception_text)


def get_balance_browser(login, password, storename=None, **kwargs):
    ''' Работаем через Browser На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__).main()


def calculate_dop(result, response_t, response_с, response_s, response_r):
    '''Считаем допы, для обоих вариантов WEB и API
    response_t - tariff response_с - connected, response_s - subscription, response_r - rests'''
    def get_data(response):
        if type(response) == dict:
            return response.get('data', {})
        return response.json().get('data', {}) if response.status_code == 200 else ''

    # Тарифный план у tele2 за услугу не считается, так что просто прибавляем его цену
    tarif_fee = get_data(response_t).get('currentAbonentFee', {}).get('amount', 0)
    tarif_period = get_data(response_t).get('period')
    paid_tarif = tarif_fee * settings.UNIT.get(tarif_period, 1)
    services = []
    for el in get_data(response_с):
        name = el.get('name', '')
        abonentFee = el.get('abonentFee', {})
        fee = abonentFee.get('amount', 0)
        fee = 0 if fee is None else fee
        kperiod = settings.UNIT.get(abonentFee.get('period', ''), 1)
        services.append((name, fee * kperiod))
    for el in get_data(response_s):
        name = el.get('name', '') + ' ' + el.get('description', '')
        cost = el.get('cost', None)
        cost = 0 if cost is None else float(str(cost).replace(',', '.'))
        kperiod = settings.UNIT.get(el.get('period', ''), 1)
        services.append((name, cost * kperiod))
    free = len([a for a, b in services if b == 0])  # бесплатные
    paid = len([a for a, b in services if b != 0])  # платные
    paid_sum = paid_tarif + round(sum([b for a, b in services if b != 0]), 2)
    result['UslugiOn'] = f'{free}/{paid}({paid_sum})'
    services.append(['Tarif:' + result['TarifPlan'], paid_tarif])  # Добавляем тарифный план как бы как услугу (но после того как все посчитали)
    result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in services])

    # остатки
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
                result['Internet'] += rest['remain'] * (settings.UNIT['MB'] / settings.UNIT.get(store.options('interUnit'), settings.UNIT['MB']))
            if rest['uom'] == 'pcs':
                result['SMS'] += rest['remain']
            if 'billingServiceStatus' in rest.get('service', {}):
                result['BlockStatus'] = rest['service']['billingServiceStatus']
    return result

def get_balance_api(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    def check_or_get_bearer():
        '''Проверяем если сессия отдает баланс, то ок, если нет, то логинимся заново'''
        session = store.Session(storename, headers=api_headers)
        if 'Authorization' in session.get_headers():
            response1 = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/balance')
            if response1.status_code == 200:
                logging.info('Old session bearer ok')
                store.feedback.text(f'Старая сессия сохранилась', append=True)
                return session
        # Логинимся заново
        store.feedback.text(f'Старая сессия не сохранилась, логинимся заново', append=True)
        session.drop_and_create()  # TODO непонятно как лучше рубить концы или нет
        response2 = session.post(f'https://sso.tele2.ru/auth/realms/tele2-b2c/protocol/openid-connect/token?msisdn=7{login}&action=auth&authType=pass', data=data)
        if response2.status_code == 200:
            logging.info('New bearer is ok')
            bearer = response2.json()['access_token']
            session.update_headers({'Authorization': 'Bearer ' + bearer})
            return session
        logging.error(
            f'Bearer get error {response2.status_code} for login {login}')
        raise RuntimeError(f'Bearer get error {response2.status_code}')

    def get_data(response):
        return response.json().get('data', {}) if response.status_code == 200 else ''

    result = {}
    data = {
        'username': '7' + login,
        'password': password,
        'grant_type': 'password', 'client_id': 'android-app', 'password_type': 'password'
    }
    store.feedback.text(f'Авторизация', append=True)
    session = check_or_get_bearer()

    store.feedback.text(f'Забираем данные из личного кабинета', append=True)
    response_b = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/balance')
    result['Balance'] = get_data(response_b).get('value')  # баланс
    response_t = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/tariff')
    result['TarifPlan'] = get_data(response_t).get('frontName', '')  # тариф
    response_p = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/profile')
    result['UserName'] = get_data(response_p).get('fullName', '')  # ФИО владельца
    siteId = get_data(response_p).get('siteId', '')  # регион
    # список услуг
    response_с = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/{siteId}/services?status=connected')
    # подписки (мошенники из Теле2 стыдливо прячут их и стараются не показывать) прибавим их как услуги
    response_s = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/subscription')
    # остатки
    response_r = session.get(f'https://api.tele2.ru/api/subscribers/7{login}/rests')
    result = calculate_dop(result, response_t, response_с, response_s, response_r)

    session.save_session()
    return result


def get_balance(login, password, storename=None, **kwargs):
    pkey = store.get_pkey(login, plugin_name=__name__)
    if store.options('plugin_mode', pkey=pkey).upper() == 'WEB':
        return get_balance_browser(login, password, storename)
    return get_balance_api(login, password, storename)


if __name__ == '__main__':
    print('This is module tele2')
