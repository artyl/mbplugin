#!/usr/bin/python3
# -*- coding: utf8 -*-
import browsercontroller

login_url = 'https://lk.saures.ru/dashboard'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
                  'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                  'login_selector': 'form input[type=text]', }

# введите логин demo@saures.ru и пароль demo вручную
class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        # Здесь мы берет данные непосредственно с отрендеренной страницы, поэтому url_tag не указан
        self.wait_params(params=[{
            'name': 'Balance',
            'url_tag': ['object/meters'], 
            'jsformula': "data.data.sensors[0].meters.length",
            #'jsformula': r"parseFloat(document.querySelector('div.card-body div.counter__row').innerText.replace(/[^\d,.-]/g, '').replace(',','.'))",
        }])


def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename).main()


if __name__ == '__main__':
    print('This is module test3 for test chrome on browser')
