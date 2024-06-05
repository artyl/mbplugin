# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller, store

icon = '789c73f235636100033320d600620128666450804800e58ff041300cfcffff1fce6e56ce5205e249407c0d887f02f17f20fe01c45780b80f881591f5c130546f3454ed7f3cf81b1087a2eb078a1900f12f34b54f81f802103f441307a9d342d3bf08491ee4067f062400e43b43ed86a9998fa6ff0992dc6c062c00283e1d49cd6334fdff90e47271e8cf4452f3174d3fb2ff1270e84f405637aa7fd0ea8f24423fbef8b72442ff3d2cfa5f03710f1033e2d1ff1788af02b1074c2f005a8a975e'

login_url = 'https://my.ucell.uz'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
                  'login_selector': 'form input[name=phone_number]',
                  'login_clear_js': "document.querySelector('form input[name=phone_number]').value=''",
                  'before_login_js': "Array.from(document.querySelectorAll('.radio-inline_')).filter(el=>el.innerText=='По постоянному паролю').forEach(el=>el.click())",
                  'submit_js': "document.querySelector('button[name=btn_login]').click();setTimeout(()=>document.querySelectorAll('button[name=btn_login]').forEach(el=>el.click()),3000)"
                  }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.sleep(5)        
        self.result['Balance'] = 0
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['GetSbsData'], 'jsformula': "parseFloat(data.data.bcore.replace(' ','')).toFixed(2)"},
            {'name': 'UserName', 'url_tag': ['GetSbsData'], 'jsformula': "data.data.fullname"},
            {'name': 'TarifPlan', 'wait': False, 'url_tag': ['GetSbsData'], 'jsformula': "data.data.tariff"},
            {'name': 'Min', 'wait': False, 'url_tag': ['GetSbsData'], 'jsformula': "data.data.bsec.replace(' ','')"},
            {'name': 'SMS', 'wait': False, 'url_tag': ['GetSbsData'], 'jsformula': "data.data.bsms.replace(' ','')"},
            {'name': 'Internet', 'wait': False, 'url_tag': ['GetSbsData'], 'jsformula': "data.data.btoct.replace(' ','')"},
        ])

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module ucelluz')
