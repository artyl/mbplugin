# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging, time
import requests
import browsercontroller, store, settings

icon = '789C85936B48D35118C69F4904164E2552E84B5953D40F5AA4F3830A2A28CB1CE42D25723A6FA5A2A9A890DBD4B979256F24D2655ED25253112CBC864545378DAE504118F6A13E54A0A98498DB7AFA3BB469D1811F07CE799FF3BEE73DCF09914BB7411852E24E1C2C88B06F6DC3B2FFE7282B2BB3222F4F87B0B07AF8F85C82BB7B2B3C3D0D080A6A414646CD96D8CD646555C1C56508212177A81D8693533F6C6D3B211275905E48245DC8CEAEFEA75EA3D12238B8839A7156768B8C9041D24DDA4917F706A052955BE912129A2197B753BFB6AE52E984B5E0E02BF0F6EE81ABEB35B8B919E0EBDB8493276B37DDB7067676AFC90C3C3CEEA3A4C4FA6CB55A87CCCC3A2426362236B609E1E1F5EC4F035253D7CE8988E8619EAFBCF3029C9D7F2020E0EEBAB6A0A016F6F6EF58F75BF2844C903ED2061B9B3E2425D52134F41E6B5A466494090EBBCDD8E96882427955D02B956D8C5D229FC91BF2900C0B7D003A21951A1017F71CDD3D6604C9CCD8B5DF04670F132487E7A05257B2763DEC1DE719BB483E9217E436E9176A70756D63EE693C7D668657A0097BFDA80D320A442A26851A8ECA4721B2F9C9F82FE4F75D1E9021E13D2492CB5024F56264C20C89BF099E478C38144FE28CF08E5842B1BA866F51C91A1618FF9DCC58FA3022D4EFE3D38CD2522D14E9533810484D8C110119ABF03FBD0AAF28238EA78C0935C86463963ECC9269322AF4203676C393B9852D88CF9C842C731601298B38786C1927D26E58FC5001B1F813351FD6F5627107D7B51BDECD6D457ACE75BEBF0EA5655ACE7A2B1F289517E99197D43EE2DBDD64EE7356FB675517A06F588154368FD0C8C788570C22ED542BB273CE233FBF0E4545D5282ED62339B9917FA0EAEF7FA0BC1D670AE7E017422FEC3163FB0E33FFCD0A737EE3FC1ED1D186FFFE418DA6827907E8D129FAF91599A2EFC71113D3CA3B69B7C4FF02FCBF4345'

login_url = 'https://my.novofon.ru/login'
# Личный кабинет переехал с https://my.zadarma.com/ 

user_selectors = {
    'chk_lk_page_js': "document.querySelector('div.bottomMenu') !== null",
    'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
    'login_clear_js': "document.querySelector('form input[name=login]').value=''",
    'login_selector': 'form input[name="login"]',
    'submit_js': "document.querySelector('form [type=submit]').click()",
}

# введите логин demo@saures.ru и пароль demo вручную
class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        # Здесь мы берем данные непосредственно с отрендеренной страницы, поэтому url_tag не указан
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['api.novofon.ru/account'], 'jsformula': "data[0].balance"},
            {'name': 'TurnOffStr', 'url_tag': ['api.novofon.ru/virtual_phone'], 'jsformula': "data[0]?.paid_till ?? '' "},
            {'name': 'UserName', 'url_tag': ['api.novofon.ru/subject'], 'jsformula': "data[0]?.payer_data?.legal_name ?? '' "},
            {'name': 'TarifPlan', 'url_tag': ['/tariff_plan/2'], 'jsformula': "data?.name ?? '' "},
            # virtual_phone
            ])
        if re.match(r'^20\d\d-\d\d-\d\d$', self.result.get('TurnOffStr', '')):
            self.result['TurnOff'] = int((time.mktime(time.strptime(self.result['TurnOffStr'], '%Y-%m-%d')) - time.time()) / 86400)

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module zadarma')
