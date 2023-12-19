#!/usr/bin/python3
# -*- coding: utf8 -*-
import browsercontroller, store

icon = '789c73f235636600033320d600620128666490804800e58ff041300cfc270b6cdc7868ca94ddab56edbe73e7fe9b376fbe7dfbf6ffffbfffffffe050feb7b0f0a4b0f00d46c663f6f6b3d7ae5d76e8e0be1933d6a4a71f6e6db9f8f1e3574c0d9b363fd0d179cec7f7c9d0f0cea74f3f7ffefc9e9aba8681e1aab4f4e5f7efbf61aa7ffbf68bb3f3556dedff7c7c5f8d8ceeb9b9df97963ec3c0f03839f921d861589c545171c5d4ec9b98d87f2eeeb79c5c4f98989f31333f5ebaf439d0b28f1f3ffefefd1b4dc3b66d0fcccc9ec8c9ff4f4a7ed3da7a9895f59c84e4e3a74fbfb7b6362b28286cddba154dfdebd79f6c6d2fe8e9ffb7b27e1f11b18299e58e97d7a37ffffe6766663033332f5bb60c5b285d56d7fc262bff5944643913f393cecee740d1c2c2422121a1952b5762fa61cb9687d2324fb474fe494bbfe3e37f72f0e0cbe7cf9f151515aaa8a8ac59b30653fdbb779f7574af2a2aff5756fd6f6cf2ece1c31701017e76b6b67676766bd7aec51a4a25a55784843f2928fdacaa7afefdfb97acac2c3737773f3f7f1ceaff7ffaf463dfbe77376e7cf9f1039418debe7d5b5e5eeee7e7b77af56aacea31c1cd9b3767cf9e7dedda3522d5530800550a6598'

login_url = 'https://myaccount.a1.by/tariff'
user_selectors = {
    'chk_lk_page_js': """document.querySelector('form input[type=tel][value*="375"]') == null""",
    'chk_login_page_js': """document.querySelector('form input[type=tel][value*="375"]') != null""",
    'before_login_js': "Array.from(document.querySelectorAll('button[type=button]')).filter(el=>el.innerText=='Пароль').forEach(el=>el.click()) ",
    'login_clear_js': """document.querySelector('form input[type=tel][value*="375"]').value=''""",
    'login_selector': """form input[type=tel][value*="375"]""",
    'submit_js': "document.querySelector('form [type=submit]').click()",
    'remember_checker': '',
}

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.login = self.login.strip()[-9:]
        self.do_logon(url=login_url, user_selectors=user_selectors)

        # Кликаем на Абонент
        self.page_evaluate("Array.from(document.querySelectorAll('h6')).filter(el=>el.innerText=='Абонент').forEach(el=>el.click())")
        self.sleep(2)

        self.page_wait_for(response_url='v1new_prod/billing-accounts')

        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['v1new_prod/billing-accounts'], 'jsformula': "parseFloat(data.primaryBalance.moneyAmount).toFixed(2)"},
            {'name': 'TarifPlan', 'url_tag': ['include=primaryBillingAccount'], 'jsformula': "data[0].tariff.name"},
            {'name': 'Min', 'url_tag': ['v1new_prod/profile?include=customer,subscriptions'], 'jsformula': "data.subscriptions[0].units.filter(el=>el.unitType=='minutes').map(el=>el.amountRemaining).reduce((x,y)=>x+y,0)"},
            {'name': 'Internet', 'url_tag': ['v1new_prod/profile?include=customer,subscriptions'], 'jsformula': "data.subscriptions[0].units.filter(el=>el.unitType=='bytes').map(el=>el.amountRemaining/1024/1024).reduce((x,y)=>x+y,0)"},
            # {'name': 'SMS', ... unitType=='numeric' or =='messages' ?
            {'name': 'UslugiOn', 'url_tag': ['v1new_prod/profile?include=customer,subscriptions'], 'jsformula': "data.subscriptions[0].addons.length + '/' + data.subscriptions[0].addons.map(el=>parseFloat(el.prices.filter(e=>e.type=='recurring')[0].value)).filter(el=>el>0).length + '/' + data.subscriptions[0].addons.map(el=>parseFloat(el.prices.filter(e=>e.type=='recurring')[0].value)).filter(el=>el>0).reduce((x,y)=>x+y,0)"},
            {'name': 'UslugiList', 'url_tag': ['v1new_prod/profile?include=customer,subscriptions'], 'jsformula': r"data.subscriptions[0].addons.map(el => el.name+'\t'+el.prices.filter(e=>e.type=='recurring')[0].value).join('\n')"},
            {'name': 'BlockStatus', 'url_tag': ['v1new_prod/billing-accounts'], 'jsformula': "data.state"},
            {'name': 'UserName', 'url_tag': ['v1new_prod/profile?include=customer,subscriptions'], 'jsformula': "data.name"},
            # {'name': 'Expired', ???
        ])

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module a1by on browser')
