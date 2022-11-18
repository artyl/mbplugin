# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller, store

icon = '789c73f235636100033320d600620128666450804800e58ff041300cfcffff1f37dee5f59f20a6a77e5c62c35d3fb9614b2ca6461ce21327643e3e75a4e81fcaf653224f41fc02005a870287'

login_url = 'https://debet.east.ru/lk'
user_selectors = {
    'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
    'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
    'login_clear_js': "document.querySelector('form input[formcontrolname=login]').value=''",
    'login_selector': 'form input[formcontrolname=login]',
    'submit_js': "document.querySelector('form [type=button]').click()",
}

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['State', 'index.pl'], 'jsformula': "data.data.user.balance.toFixed(2)"},
            {'name': 'TarifPlan', 'url_tag': ['State', 'index.pl'], 'jsformula': "data.data.tariff[0].cTariffName + data.data.tariff[0].cTariffCost"},
            {'name': 'LicSchet', 'url_tag': ['State', 'index.pl'], 'jsformula': "data.data.user.login"},
            {'name': 'UserName', 'url_tag': ['State', 'index.pl'], 'jsformula': "data.data.user.FullName"},
            {'name': 'BlockStatus', 'url_tag': ['State', 'index.pl'], 'jsformula': "data.data.user.blocked==0?'Active':'Blocked'"},
            {'name': 'TurnOff', 'url_tag': ['State', 'index.pl'], 'jsformula': "data.data.user.dremain"},
            ])


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module east telecom')
