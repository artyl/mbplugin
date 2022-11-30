#!/usr/bin/python3
# -*- coding: utf8 -*-
import browsercontroller, store

icon = '789c73f235636600033320d600620128666490804800e58ff041300cfc270b6cdc7868ca94ddab56edbe73e7fe9b376fbe7dfbf6ffffbfffffffe050feb7b0f0a4b0f00d46c663f6f6b3d7ae5d76e8e0be1933d6a4a71f6e6db9f8f1e3574c0d9b363fd0d179cec7f7c9d0f0cea74f3f7ffefc9e9aba8681e1aab4f4e5f7efbf61aa7ffbf68bb3f3556dedff7c7c5f8d8ceeb9b9df97963ec3c0f03839f921d861589c545171c5d4ec9b98d87f2eeeb79c5c4f98989f31333f5ebaf439d0b28f1f3ffefefd1b4dc3b66d0fcccc9ec8c9ff4f4a7ed3da7a9895f59c84e4e3a74fbfb7b6362b28286cddba154dfdebd79f6c6d2fe8e9ffb7b27e1f11b18299e58e97d7a37ffffe6766663033332f5bb60c5b285d56d7fc262bff5944643913f393cecee740d1c2c2422121a1952b5762fa61cb9687d2324fb474fe494bbfe3e37f72f0e0cbe7cf9f151515aaa8a8ac59b30653fdbb779f7574af2a2aff5756fd6f6cf2ece1c31701017e76b6b67676766bd7aec51a4a25a55784843f2928fdacaa7afefdfb97acac2c3737773f3f7f1ceaff7ffaf463dfbe77376e7cf9f1039418debe7d5b5e5eeee7e7b77af56aacea31c1cd9b3767cf9e7dedda3522d5530800550a6598'

login_url = 'https://my.a1.by/work.html'
user_selectors = {
    'chk_lk_page_js': "document.getElementById('ext-gen2') != null",
    'before_login_js': 'document.querySelector("#pwd_choose").click()',
    'chk_login_page_js': "document.querySelector('form input[type=password]') != null",
    'login_clear_js': "document.querySelector('form input[id=itelephone_new]').value=''",
    'login_selector': 'form input[id=itelephone_new]',
    'remember_checker': '',
}

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        # self.login = self.login[-9:]
        self.do_logon(url=login_url, user_selectors=user_selectors)

        #кликаем "старая версия" f.user_input_3.value='1'; jumpTo('_next')
        self.page_evaluate( '''f.user_input_3.value='1'; jumpTo('_next');''')
        self.sleep(2)

        # Кликаем на '_root/PERSONAL_INFO' или на '_root/USER_INFO' т.е. '_root/...._INFO'
        self.page_evaluate('''document.querySelector('span[id^="_root/"][id$=INFO]').click()''')
        self.page_wait_for(loadstate=True)
        self.sleep(2)

        self.wait_params(params=[
            {'name': 'Balance', 'jsformula': r"parseFloat(document.querySelector('#balance, #BALANCE').innerText.replace('\u2012','-').replace(/[^\d\.,-]/g, '').replace(',','.'))"},
            {'name': 'TarifPlan', 'jsformula': "document.querySelector('#TRPL, #TPLAN').innerText"},
            {'name': 'BlockStatus', 'jsformula': "document.querySelector('#STATUS, #CUR_STATUS').innerText"},
            {'name': 'UserName', 'jsformula': "document.all.NAME==null?'':document.all.NAME.innerText"},
            {'name': 'Expired', 'jsformula': "document.all.DEN==null?'':document.all.DEN.innerText", 'wait': False},
            {'name': 'SMS', 'jsformula': r"d1=document.querySelector('#DISCOUNT'); d2=(d1!==null)?d1.innerText.match(/\d+\.?\d* SMS/):null; d3=(d2!==null)?parseFloat(d2[0]):'' "},
            {'name': 'Min', 'jsformula': r"d1=document.querySelector('#DISCOUNT'); d2=(d1!==null)?d1.innerText.match(/\d+\.?\d* мин/):null; d3=(d2!==null)?parseFloat(d2[0]):'' "},
            {'name': 'Internet', 'jsformula': r"d1=document.querySelector('#DISCOUNT'); d2=(d1!==null)?d1.innerText.match(/\d+\.?\d* МБ/):null; d3=(d2!==null)?parseFloat(d2[0]):'' "},
        ])
        if self.result['Min'] == '':
            del self.result['Min']
        if self.result['SMS'] == '':
            del self.result['SMS']
        if self.result['Internet'] == '':
            del self.result['Internet']

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module a1by on browser')
