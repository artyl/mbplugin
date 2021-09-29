#!/usr/bin/python3
# -*- coding: utf8 -*-
import browsercontroller

login_url = 'https://lk.uminet.ru/'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[id=bootstrap-password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[id=bootstrap-password]') !== null",
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
            'jsformula': r"""regexp=/Баланс.*?badge.*?>(.*?)<.span/i;
                             html=document.documentElement.outerHTML.replace(/\r|\n/g, "").replace(/>\s+/g, ">");
                             res=regexp.exec(html);
                             parseFloat(res[1].replace(',','.').replace(/\D\./g, '').replace(/[^\d,.-]/g, ''))""",
        }, {
            'name': 'BlockStatus', 'wait':False,
            'jsformula': r"""regexp=/Состояние блокировки.*?badge.*?>(.*?)<.span/i;
                             html=document.documentElement.outerHTML.replace(/\r|\n/g, "").replace(/>\s+/g, ">");
                             res=regexp.exec(html);
                             res[1].trim()""",
        }])


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module uminet')
