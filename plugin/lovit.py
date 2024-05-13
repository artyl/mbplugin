# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller, store

icon = '789c73f235636100033320d600620128666450804800e58ff041302940c0e17982a0c3d30f020e4f0c48d309d2fb3440d0e1d97f08c66f06480ea8ee00b21aa0dd0a40b10708339e5dc0adf7e907a89a07020ef705d0cc85e9ff2fe4f0b481807e909a05c8f2203d48663cc0ee86e70ec8f6a0bae1be00aa1cf67000f90fa1e669009adc0184dcf3046cfa91dd89ee4f909ff0850135f4a3ba9134f753127e94c61faa7e503a454f3f286663f53b349d3d404dbf60775f40b61bd96c428094fc83db0c58fe458d0f1000008689ed5a'

login_url = 'https://lk.lovit.ru/login'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
                  'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                  'login_selector': 'form input[type=text]',
                  }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['api/user/info'], 'jsformula': "parseFloat(data.data.balance).toFixed(2)"},
            {'name': 'UserName', 'url_tag': ['api/user/info'], 'jsformula': "data.data.company"},
            {'name': 'TurnOff', 'url_tag': ['api/user/info'], 'jsformula': "data.data.days_to_off"},
            {'name': 'Expired', 'url_tag': ['api/user/info'], 'jsformula': "data.data.days_to_off"},  # Некоторые хотят чтобы было в этом поле
            {'name': 'LicSchet', 'url_tag': ['api/user/info'], 'jsformula': "data.data.login"},
            {'name': 'TarifPlan', 'url_tag': ['api/user/info'], 'jsformula': "data.data.tariff_name"},
            {'name': 'BlockStatus', 'url_tag': ['api/user/info'], 'jsformula': "data.status"},
            ])

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module lovit')
