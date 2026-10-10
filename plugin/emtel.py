# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller, store

icon = '789c73f235636100033320d600620128666450804800e58ff041300cfcffff1f37dee5f59f20a6a77e5c62c35d3fb9614b2ca6461ce21327643e3e75a4e81fcaf653224f41fc02005a870287'

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
