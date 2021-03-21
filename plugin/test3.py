#!/usr/bin/python3
# -*- coding: utf8 -*-
import pyppeteeradd as pa

login_url = 'https://lk.saures.ru/dashboard'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
                  'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                  'login_selector': 'form input[type=text]', }

# введите логин demo@saures.ru и пароль demo вручную
class test4_over_puppeteer(pa.balance_over_puppeteer):
    async def async_main(self):
        await self.do_logon(url=login_url, user_selectors=user_selectors)
        # Здесь мы берет данные непосредственно с отрендеренной страницы, поэтому url_tag не указан
        await self.wait_params(params=[{
            'name': 'Balance',
            'jsformula': r"parseFloat(document.querySelector('.sensor-5 .d-inline').innerText.replace(/[^\d,.]/g, '').replace(',','.'))",
        }, {
            'name': 'BlockStatus',
            'jsformula': r"document.querySelector('.sensor-9 .d-inline').innerText",
        }])


def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return test4_over_puppeteer(login, password, storename).main()


if __name__ == '__main__':
    print('This is module test4 for test chrome on puppeteer with class balance_over_puppeteer')
