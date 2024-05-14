#!/usr/bin/python3
# -*- coding: utf8 -*-
import logging
import browsercontroller, store

icon = '789CA5D4B171DB401484E1A719050E5D024257A078C7B97BB852B614041ED7B1B16A708012942BA0FF7BA065DAA2259222780310CB77B8EFEEC8AFDF1E3E55BF1EEEABBE70FE7C6C77B5ECC17DFD79DD9D5C97FB5DF67E9A0717492A3F534F8F3FAA16D1068D605969A16D55DC2ED1BFB810B9C8452E729173AB06F9201F7C18E4837C908FEDF85C72937BF418CAE426373997B592AFE42BF94ABE7273255FC93955C8431EF2CC81AF73F03472DEB5916FE41BF946BE916FE4DBB60F9FF9511F8366DA4A0B6DDB690B397EE1177EE1177EE16F365F1217C22FFCC22FFCC2DF53825FF8855FF8855FF885BFA70BBFF00BBFF00BBFF00B7F4F257EE1177EE1177EE117FE9E66FCC22FFCC22FFCC22FFC7309845FF8855FF8855FF8857F5FEFA5D5C6DF6B8FDFF88DBF9706BFF11BBFF11BBFF11B7F2F1B7EE337580332833603330FEF25C56FFCC66FFCC66FFCC6DFCBCD434C47E6CB9E7B10BFF11B7F6F05FCC66FFCC66FFCC66FFCBD4DF01BBFF11BBFF11BBFF1CF2D64FCC66FFCC66FFCC66FFCBD7DF0A7577CB43AF8D3C7B66F2DFCC11FFCC11FFCC11FFCBDEDF0077FF0077FF0077FF0F796C41FFCC11FFCC11FFCC1DFDB157FF0077FF007748085C1F756C61FFCC11FFCC11FFCC1DFDB9C4186818487850E43D1D3F3A1BECF799A135C877ED7E1B09FE6316FCDCF276D3ED3C77D5B276DCEF3BFDF3DD7E6DCD58DB5BFEBE7DCDE52FB523FF7EF92AB6B4FEB679BFF791FA9EF3E9E3F563FF7DA357DBCAABFB28FB3F5B5EFE74BFAF86FFD857DBC597FECE3CDFAE59DFAF14EFDFCCDDD58FBD2C7FC6DDF587BB68F2B6BFFEAE382DA5FA120AA5C'

login_url = 'https://lk.rt.ru'
user_selectors = {
    'before_login_js': "document.querySelectorAll('button[name=standard_auth_btn]').forEach(e => e.click());document.querySelectorAll('div#t-btn-tab-login').forEach(e => e.click())",  # Сначала кликаем по Логин
    'chk_lk_page_js': "document.querySelector('#root')!=null",  # true если мы в личном кабинете
    # 'lk_page_url': 'client-api/getAccounts',  # не считаем что зашли в ЛК пока не прогрузим этот url
    'chk_login_page_js': "document.getElementById('standard_auth_btn')!== null || document.getElementById('otp_get_code')!== null || document.querySelector('form input[type=password]') !== null ",  # true если мы в окне логина
    'login_clear_js': "document.querySelector('form input[id=username]').value=''",  # Уточняем поле для логина чтобы не промахнуться
    'login_selector': 'form input[id=username]',
    'submit_js': "document.querySelector('form [type=submit][id=kc-login]').click()",
    'remember_checker': "document.querySelector('form input[name=rememberMe]').checked==false",  # Галка rememberMe почему-то нажимается только через js
    'remember_js': "document.querySelector('form input[name=rememberMe]').click()",
}


class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        accountId = 0
        logging.info(f'Use /start/accounts')
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['/start/accounts'], 'jsformula': f"data.data.filter(el=>el['id']=='{self.acc_num}'||'{self.acc_num}'=='')[0].balance.amount/100"},
            {'name': 'UserName', 'url_tag': ['/start/accounts'], 'jsformula': f"((e=data.data.filter(el=>el['id']=='{self.acc_num}'||'{self.acc_num}'=='')[0].client)=>''+e.last_name+' '+e.first_name+' '+e.middle_name)().replace('undefined', '').trim()"},
            {'name': 'BlockStatus', 'url_tag': ['/start/accounts'], 'jsformula': f"data.data.filter(el=>el['id']=='{self.acc_num}'||'{self.acc_num}'=='')[0].status.id"},
            {'name': 'LicSchet', 'url_tag': ['/start/accounts'], 'jsformula': f"data.data.filter(el=>el['id']=='{self.acc_num}'||'{self.acc_num}'=='')[0].id"},
        ])
        logging.info(f'Use /bonuses')
        self.wait_params(params=[
            {'name': 'Balance2', 'url_tag': ['/bonuses'], 'jsformula': f"data.data.balance"},
        ])


class browserengine_qiwi(browsercontroller.BrowserController):
    def data_collector(self):
        self.page_goto('https://platiuslugi.ru/oplata/rostelecom/')
        self.sleep(3)
        self.page_screenshot()
        self.page_evaluate("document.querySelector('input.form-control').click()")
        acc_num = self.acc_num if self.acc_num.isdigit() else self.login
        self.page_fill('input.form-control', acc_num)
        self.page_click('button.submit')
        for num in range(10):
            self.sleep(1)
            if self.page_evaluate('''document.querySelector('input.form-control[name*="BALANCE"]')''') is not None:
                break
        else:
            self.page_screenshot()
            return
        self.page_screenshot()
        # pp list(self.responses.values())[-1]['elements'][0]['value']
        self.result['Balance'] = self.page_evaluate('''document.querySelector('input.form-control[name*="BALANCE"]').value''').replace(',', '.')


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    pkey = store.get_pkey(login, plugin_name=__name__)
    if store.options('plugin_mode', pkey=pkey).upper() in ('QIWI', 'PLATIUSLUGI'):
        return browserengine_qiwi(login, password, storename, plugin_name=__name__).main()
    else:
        return browserengine(login, password, storename, plugin_name=__name__, headless=browsercontroller.NOT_IN_CHROME).main()  # ростелеком в headless не работает


if __name__ == '__main__':
    print('This is module rostelecom on browser')
