# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller, store

icon = '789C7D93CB6B135114C6BF79C4BC66924993D0269926D3247DD8579A5A92D61A5B84B6282816AC8FADB890BAB3E24E37EE15D48505F11FD045C54AC577B1540AC5A255B1B4A2958AF85AE9C23E92F8CD344A15F4901FDF9D7BE79C09E7BB67C7EE8C0C2B32A48E68250418EB07A5F3FF45454505CACBCBE1F3F9204912445182D7EB4520184490FC2B3C5E0F227A04A220941021992A8A10A842692F180C4051953F72BD9A86B2AA66A8B12628B14628C63AEEAA46A8550D50889AA026EAE149D6A38C6BD5ABFDCE8F1C3D0F5C2F02770BC03875823A459D26B3E42599E7DE5BEA12799F8776E6A295AB376D012E7F07AEFD004696811B2BC02D726F15784026F2C063324D9EB2C67332CFF5B365045ADA103A3E0CDCE4F31D729F678F587FB2F4ED19F2827BAFA8AFC922F9403E93AF79F8CF0DA332D50E776D3BD41A6A5D164EE2DA9C85BB210BA521034F6316BEE60E78531D50F9AE92CEC0D5DA0E676B16C18616C8A20C4114D86BD1EAAF60F94DB8762B2AC2E13092890489731DB27A2F0A1264D31F7A63936DD6B359E39777FCC1ED70221AD5D19A4E23B77D1B72B91CD22D2984F5305C7607BFCB7C4940B47B2F94ADFBA012676E006EE2EC1A40B0E720D20347D03B7812FD43A7D07FE2347A8E0D2175E830427B0EC0BE6B3FFCDD7D080F5D0246D9E7DB66FFA8E3D4C95548336B48CEADA16BB180BEA53C7AD9B7EE8F45843E156037FBF7A580E0D96118CD6DC0956FC0557A364246C9D88A55273E9547E76C013BE75863BE884E7A1059A01F0BE6BD584679BACDBA0389C10BF49FDE8F9977883C5CF7D0F1A48824BD6BE1FB29DE9D38FD93DFF1EC4D1E81D2FD3143E3ACE891045C6521B87CC41F81C35F014F4847D848C048D6C0A8AE41C888C3138EC2AFC7E0D1B48D23004DF3A2BAB6D69A1769C30CC9928C4DECB7CD66A75F326246CC9AB57F85611888C562F42ECA1C1B6459E27F8B40AFD42DFE8E9F8F93C73F'

login_url = 'https://beeline.uz/ru'
user_selectors = {
    'chk_login_page_js': "Array.from(document.querySelectorAll('button.auth__action')).filter(el=>el.innerText.startsWith('Войти')).length>0",
    'chk_lk_page_js': "Array.from(document.querySelectorAll('a.auth__action')).filter(el=>el.innerText.toLowerCase().startsWith('личный кабинет')).length>0",
    'before_login_js': "Array.from(document.querySelectorAll('button.auth__action')).filter(el=>el.innerText.toLowerCase()=='войти')[0].click();setTimeout(()=>document.querySelectorAll('button').forEach(el=>el.innerText.toLowerCase()=='вход по паролю'?el.click():0),1000)",
    'login_clear_js': """document.querySelector('form[style=""] input[type=tel]').value=''""",
    'login_selector': """form[style=""] input[type=tel]""",
    'password_clear_js': """document.querySelector('form[style=""] input[type=password]').value=''""",
    'password_selector': """form[style=""] input[type=password]""",
    'remember_checker': "true",  # все проверяем в remember_js
    'remember_js': "",
    'submit_js': "document.querySelectorAll('button').forEach(el=>el.innerText.toLowerCase()=='вход'?el.click():0)",
}

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.force = 2  # сайт тормозной - увеличиваем тайминги
        self.page_goto(login_url, wait_until='commit')
        self.page_wait_for(expression="document.querySelectorAll('.auth__action').length>0")
        self.sleep(1)
        self.do_logon(url=None, user_selectors=user_selectors)
        #self.page_evaluate("document.querySelectorAll('button').forEach(el=>el.innerText.startsWith('+998')?el.click():0)")  # удалить, этого вроде не нужно уже?
        self.page_evaluate("Array.from(document.querySelectorAll('a')).filter(el=>el.innerText.toLowerCase().startsWith('личный кабинет')).forEach(el=>el.click())")
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['/lk-api/user/dashboard'], 'jsformula': "parseFloat(data.core_balance).toFixed(2)"},
            {'name': 'TarifPlan', 'url_tag': ['/lk-api/user/dashboard'], 'jsformula': "data.plan.name"},
            {'name': 'UserName', 'url_tag': ['/lk-api/user/dashboard'], 'jsformula': "data.customer_info.first_name + ' ' + data.customer_info.last_name"},
            {'name': 'Internet', 'url_tag': ['/lk-api/user/dashboard'], 'jsformula': r"data.balances.filter(el=>el.unit=='kb' && !el.name.startsWith('Бонусный')).map(v => /(\d+(\.\d+)?)\s*(GB|MB)/.exec(v.value)).filter(x=>x).map(el=>el[3]=='MB'?el[1]/1024:el[1]/1).reduce((x,y)=>x+y,0).toFixed(2)"},
            {'name': 'SMS', 'url_tag': ['/lk-api/user/dashboard'], 'jsformula': r"data.balances.filter(el=>el.unit=='unit').map(el=>el.value.replace(/\D/g, '')*1).reduce((x,y)=>x+y,0).toFixed(0)"},
            {'name': 'Min', 'url_tag': ['/lk-api/user/dashboard'], 'jsformula': r"data.balances.filter(el=>el.unit=='min').map(el=>el.value.replace(/\D/g, '')*1).reduce((x,y)=>x+y,0).toFixed(0)"},
            {'name': 'LicSchet', 'url_tag': ['/lk-api/user?'], 'jsformula': "data.id"},
            {'name': 'BlockStatus', 'url_tag': ['/lk-api/user?'], 'jsformula': "data.status"},
            #{'name': 'UslugiOn', 'url_tag': ['/dashboard-updated$'], 'jsformula': "data.services.filter(el => el.accordeons).length"},
            #{'name': 'UslugiList', 'url_tag': ['/dashboard-updated$'], 'jsformula': r"data.services.filter(el => el.accordeons).map(el => el.name.ru).join('\n')"},
        ])

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module beeline Uzbegistan')
