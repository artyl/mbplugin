# -*- coding: utf8 -*-
''' Автор d1mas
проверка задолженности по услугам ЖКХ РКЦ Наш Дом
https://rkc-m.ru'''

import browsercontroller, store, settings

login_url = 'https://lk.rkc-m.ru/#/login'
user_selectors = {'chk_lk_page_js': "document.querySelector('.menu__link')!=null",
                  'chk_login_page_js': "document.querySelector('.form-box__form')!=null",
                  'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                  'login_selector': 'form input[type=text]',
                  'password_clear_js': "document.querySelector('form input[type=password]').value=''",
                  'password_selector': 'form input[type=password]',
                  'submit_js': "document.querySelector('form button[type=submit]').click()"
                  }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['api.sm-center.ru/vremya/Accounting/Info'], 'jsformula': "data.Data[0].Sum"},
            {'name': 'Balance2', 'url_tag': ['api.sm-center.ru/vremya/Accounting/Info'], 'jsformula': "data.Data[0].Comission"},
            {'name': 'LicSchet', 'url_tag': ['api.sm-center.ru/vremya/Accounting/Info'], 'jsformula': "data.Data[0].Ident"},
            {'name': 'UserName', 'url_tag': ['api.sm-center.ru/vremya/auth/login'], 'jsformula': "data.fio"},
            {'name': 'AnyString', 'url_tag': ['api.sm-center.ru/vremya/Accounting/Info'], 'jsformula': "data.Data[0].Address"},
        ],
        url='https://lk.rkc-m.ru/#/payment')


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module nashdom')
