#!/usr/bin/python3
# -*- coding: utf8 -*-
import browsercontroller, store

login_url = 'https://lk.uminet.ru/'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[id=LoginForm_password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[id=LoginForm_password]') !== null",
                  'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                  'login_selector': 'form input[type=text]',
                  'submit_js': "document.querySelector('form [type=submit]').click()"}

# введите логин demo@saures.ru и пароль demo вручную
class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        # Здесь мы берет данные непосредственно с отрендеренной страницы, поэтому url_tag не указан
        self.wait_params(params=[{
            'name': 'Balance',
            'jsformula': r"""document.querySelector('.balance-home').innerText.replace(',','.').replace(/\D\./g, '').replace(/[^\d,.-]/g, '')""",
        }, {
            'name': 'BlockStatus', 'wait':False,
            'jsformula': r"""document.querySelector('[data-label="Статус"]').innerText""",
        }, {
            'name': 'TarifPlan', 'wait':False,
            'jsformula': r"""a=document.querySelector('[data-label="Тариф"]');b=document.querySelector('[data-label="Абонентская плата"]'); ((a!==null?a.innerText:"")+" "+(b!==null?b.innerText:"")).replace(/\s/g,' ')""",
        }])


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module uminet')
