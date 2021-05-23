#!/usr/bin/python3
# -*- coding: utf8 -*-
import browsercontroller

icon = '789c73f235636600033320d600620128666490804800e58ff041300cfc270b6cdc7868ca94ddab56edbe73e7fe9b376fbe7dfbf6ffffbfffffffe050feb7b0f0a4b0f00d46c663f6f6b3d7ae5d76e8e0be1933d6a4a71f6e6db9f8f1e3574c0d9b363fd0d179cec7f7c9d0f0cea74f3f7ffefc9e9aba8681e1aab4f4e5f7efbf61aa7ffbf68bb3f3556dedff7c7c5f8d8ceeb9b9df97963ec3c0f03839f921d861589c545171c5d4ec9b98d87f2eeeb79c5c4f98989f31333f5ebaf439d0b28f1f3ffefefd1b4dc3b66d0fcccc9ec8c9ff4f4a7ed3da7a9895f59c84e4e3a74fbfb7b6362b28286cddba154dfdebd79f6c6d2fe8e9ffb7b27e1f11b18299e58e97d7a37ffffe6766663033332f5bb60c5b285d56d7fc262bff5944643913f393cecee740d1c2c2422121a1952b5762fa61cb9687d2324fb474fe494bbfe3e37f72f0e0cbe7cf9f151515aaa8a8ac59b30653fdbb779f7574af2a2aff5756fd6f6cf2ece1c31701017e76b6b67676766bd7aec51a4a25a55784843f2928fdacaa7afefdfb97acac2c3737773f3f7f1ceaff7ffaf463dfbe77376e7cf9f1039418debe7d5b5e5eeee7e7b77af56aacea31c1cd9b3767cf9e7dedda3522d5530800550a6598'

login_url = 'https://my.a1.by/work.html'
user_selectors = {'chk_lk_page_js': "document.getElementById('ext-gen2') != null",
                'before_login_js': 'document.querySelector("#pwd_choose").click()',
                'chk_login_page_js': "document.querySelector('form input[type=password]') != null",
                'login_clear_js': "document.querySelector('form input[id=itelephone_new]').value=''",
                'login_selector': 'form input[id=itelephone_new]', 
                'remember_checker': '',
                }

class browserengine(browsercontroller.get_browser_engine_class()):
    def data_collector(self):
        self.login = self.login[-9:]
        self.do_logon(url=login_url, user_selectors=user_selectors)
        # Кликаем на '_root/PERSONAL_INFO' или на '_root/USER_INFO' т.е. '_root/...._INFO'
        self.page_evaluate( '''document.querySelector('span[id^="_root/"][id$=INFO]').click()''')
        self.page_waitForNavigation()
        self.wait_params(params=[{
            'name': 'Balance',
            'jsformula': r'''()=>
            {
                b1 = document.getElementById('balance')
                b2 = document.getElementById('BALANCE')
                baltxt = (b1!=null?b1:b2).innerText.replace('\u2012','-').replace('коп.','').replace(',','.').replace(/[^\d\.,-]/g, '')
                return parseFloat(baltxt)
            }''',},{
            'name': 'TarifPlan',
            'jsformula': '''()=>{
                t1=document.getElementById('TRPL')
                t2=document.getElementById('TPLAN')
                return (t1!=null?t1:t2).innerText
            }'''
            },{
            'name': 'BlockStatus',
            'jsformula': '''()=>{
                s1=document.getElementById('STATUS')
                s2=document.getElementById('CUR_STATUS')
                return (s1!=null?s1:s2).innerText
            }'''
            },
            {'name': 'UserName','jsformula': "document.all.NAME==null?'':document.all.NAME.innerText"},
            {'name': 'Expired', 'jsformula': "document.all.DEN==null?'':document.all.DEN.innerText", 'wait': False},
            ])

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename).main()


if __name__ == '__main__':
    print('This is module a1by on browser')
