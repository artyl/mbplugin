# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller, store

icon = '789c73f235636100033320d600620128666450804800e58ff041300cfcffff1fce6e56ce5205e249407c0d887f02f17f20fe01c45780b80f881591f5c130546f3454ed7f3cf81b1087a2eb078a1900f12f34b54f81f802103f441307a9d342d3bf08491ee4067f062400e43b43ed86a9998fa6ff0992dc6c062c00283e1d49cd6334fdff90e47271e8cf4452f3174d3fb2ff1270e84f405637aa7fd0ea8f24423fbef8b72442ff3d2cfa5f03710f1033e2d1ff1788af02b1074c2f005a8a975e'

login_url = 'https://lk.ucell.uz/login'
user_selectors = {'chk_lk_page_js': "document.querySelectorAll('div.flex').length>10",
                  'chk_login_page_js': """document.querySelectorAll('input[placeholder="(__) ___-__-__"]').length>0""",
                  'login_selector': 'input[placeholder="(__) ___-__-__"]',
                  'login_clear_js': """document.querySelectorAll('input[placeholder="(__) ___-__-__"]').value=''""",
                  'before_login_js': "Array.from(document.querySelectorAll('div')).filter(el=>['Parol orqali','По паролю','Via password'].includes(el.innerText)).map(el=>el.click())",
                  'submit_js': "Array.from(document.querySelectorAll('button')).filter(el=>['Kirish','Войти','Login'].includes(el.innerText.trim())).map(el=>el.click())"
                  }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.sleep(5)        
        self.result['Balance'] = 0
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['api/v2/app/mainscreen'], 'jsformula': "(parseFloat(data.balance.balance)/100).toFixed(2)"},
            {'name': 'UserName', 'url_tag': ['api/v2/user/settings'], 'jsformula': "data.name"},
            {'name': 'TarifPlan', 'wait': False, 'url_tag': ['api/v2/app/mainscreen'], 'jsformula': "data.tariff.name"},
            #{'name': 'Min', 'wait': False, 'url_tag': ['GetSbsData'], 'jsformula': "data.data.bsec.replace(' ','')"},
            #{'name': 'SMS', 'wait': False, 'url_tag': ['GetSbsData'], 'jsformula': "data.data.bsms.replace(' ','')"},
            #{'name': 'Internet', 'wait': False, 'url_tag': ['GetSbsData'], 'jsformula': "data.data.btoct.replace(' ','')"},
        ])

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module ucelluz')
