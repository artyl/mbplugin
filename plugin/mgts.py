# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import logging
import browsercontroller, store

icon = '789c73f235636100033320d600620128666450804800e58ff041300c9c6c669801c49f80f8d7a956d6ff08ccf2ff540b330483d8487220b5503dd380f80b10ff47c72075677b84c018a41f9b1aec7a19ff5f5b64fffff5a545ffbf3c3b03c4a7ffbfbeb8f0ffb5857660391ce6c0f1cde55eff7f7e7af21f1dfcfcf8f8ff8d659e78f59eed16fcffe9c1010cbd30f0f1c1feff67ba0570eabfb6c0e6ff9f1f1f70ea07c95d5d608d53ffed35a1fffffffb8b53ffbf7f7f806a4270eabfb53a08a8fd376efd7f7ffdbfb52a00a7feabf3ccfffffefe0ea7fedfdfdefebf32c70477f8f508fffff2f4144efd5f9e9e04a7077c71f0f8402d4efd203942f17f618af2ff6fafae60e805895d9caa42503f08df591701f4eb1b147f83c488d10b4efbc03c737b6dd8ff4f0f0f82d313880d12c3a1fe1b7671c6ff67baf8c0188f5da0fc3307887f10eb36347b6701002142d1fc'

# Для тестов выносим параметры наружу, чтобы их можно было взять тестами
login_url = 'https://auth.mgts.ru/login/b2c'
# login_url = 'http://localhost:9000/'  # for debug
user_selectors={
                'chk_lk_page_js': "document.getElementById('loginform-username')==null && document.getElementById('loginform-password')==null",
                'chk_login_page_js': "document.getElementById('loginform-username')!=null || document.getElementById('loginform-password')!=null",
                'chk_submit_after_login_js': "document.getElementById('loginform-username')!=null && document.getElementById('loginform-password')==null",
                'submit_after_login_js': "document.getElementById('submit').click()", # js для нажатия на далее после логона
                'login_clear_js': "document.getElementById('loginform-username').value",
                'login_selector': '#loginform-username',
                }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.sleep(3*self.force)
        balance  = self.page_evaluate("document.querySelector('.account-info_balance_value').innerText.replace(/[^0-9,\.-]/g,'').replace(',','.')")
        self.result['Balance'] = float(balance)
        self.responses[f'GET URL:{self.page.url}$'] = self.page.content()  # т.к. мы парсим страницу, то для лога интересно ее содержимое
        try:
            self.result['UserName'] = self.page_evaluate("document.querySelector('.account-info_title').innerText.replace(/\s/g,' ')")
            self.result['TarifPlan'] = self.page_evaluate("Array.from(document.querySelectorAll('.text-link')).map(e => e.innerText).join(' ')")
            self.result['LicSchet'] = self.page_evaluate("Array.from(document.querySelectorAll('.account-info_item_value')).filter(e => e.parentElement.innerText.includes('Лицевой')).map(e => e.innerText).join(' ')")
        except Exception:
            logging.info(f'Ошибка при получении доп информации {store.exception_text()}')

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module yota')
