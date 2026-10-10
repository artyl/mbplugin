# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller, store

icon = '789c6550cb71c230107d5a49d6d722172881d082afccc02d1d90361877406a2055f8ec6b3a80265c824f8eb482e4c09b79a37dfb5fed3fce028c73e62ef3ed41015b0339fe932aff63c0b22cf83c9dd0751da669c2fb768b554af8ba5cb059af713c1c300c03fabec7fd76c3388e98e719dfd72b44460cd2369abc6028c2035215a9f1079d1dae185636ec20d1f21b455ab127d662979bf962845a6d8cf25c29cb25d290f1244c6954b449ce87c0ba91b5bda296f375a89b3893781245d6ed739e173cb091f587e4ebbe42b9a724552f6c495b2b432cf62f95cc1e1e'

login_url = 'https://lk.em-tel.ru/'
user_selectors = {
    'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
    'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
    'login_clear_js': "document.querySelector('form input[name=login]').value=''",
    'login_selector': 'form input[name=login]',
    'submit_js': "document.querySelector('form [type=submit]').click()",
}

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['api/user'], 'jsformula': "data.data.balance.toFixed(2)"},
            {'name': 'TarifPlan', 'url_tag': ['api/user'], 'jsformula': "data.data.subs[0].desc + ' ' +data.data.subs[0].tarif_speed +' Мбит/сек '+ data.data.subs[0].tarif_price + ' Р/мес'"},
            {'name': 'LicSchet', 'url_tag': ['api/user'], 'jsformula': "data.data.login"},
            {'name': 'UserName', 'url_tag': ['api/user'], 'jsformula': "data.data.company"},
            {'name': 'BlockStatus', 'url_tag': ['api/user'], 'jsformula': "data.data.blocked?'Blocked':'Active'"},
            {'name': 'TurnOff', 'url_tag': ['api/user'], 'jsformula': "Math.round(data.data.balance.toFixed(2)/data.data.subs[0].tarif_price*30)"},
            # {'name': 'TurnOff', 'url_tag': ['api/user'], 'jsformula': "data.data.days_to_off"},
            ])


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module east telecom')
