# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller, store

icon = '789C73F235636100033320D600620128666450804840E591C1FFFFFFB1E237DF1F32CCBF91C7B0F66E13C3D3AFD771AA43C63FFE7C6688D8C5CC10B69381E1FCEB6D601A19171ED1C0A9F7CCAB4D286AB1E987E15B1F8EA1E9FF87A1069F7E10FEF7FF2F5C7FDC5E1E9CFA41F265C7F4C1EA57DDA963C838280516CB3C2803D78FCD7C64FDFD1743C1F4D9D79B196A4E5AC0F5806850D8E2D38F0F5F7EBB8761F59D7AAC725B1FF4E1751F084FBF92C8B0FDD124BC76E0D33FE95214C3B73F1F71EA8BDDC385573FC88FB8E441E2317B38F0EA87F96FF2A56892DD0F731BA130C225F7EFFF1F14FDBFFE7E235AFFA5B7BB71E683C5378B71EA8FD9C389926E09E10B6F7680E9EBEF0FE1540300F7C7D83E'

login_url = 'https://b2blk.megafon.ru/dashboard'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
                  'login_clear_js': "document.querySelector('form input[name=username]').value=''",
                  'login_selector': 'form input[name=username]',
                  'submit_js': "document.querySelector('button[type=submit]').click()",
                  'pause_press_submit': '5',
                  }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        self.sleep(10)
        self.result['Balance'] = 0
        self.wait_params(params=[
            {'name': 'Balance', 'wait': False, 'url_tag': ['accounts/balance'], 'jsformula': "parseFloat(data.data.totalBalance).toFixed(2)"},
            # {'name': 'TarifPlan', 'wait': False, 'url_tag': ['widget/subscribers'], 'jsformula': "data.data.tariffs[0].name"},
            {'name': 'TarifPlan', 'wait': False, 'url_tag': ['/info/tariff?'], 'jsformula': "data.data.ratePlan.name"},
            {'name': 'Min', 'wait': False, 'url_tag': ['/info/tariff?'], 'jsformula': "data.data.discounts.filter(el=>el.label=='Минуты по тарифу').map(el=>parseInt(el.value)).reduce((x,y)=>x+y,0)"},
            {'name': 'SMS', 'wait': False, 'url_tag': ['/info/tariff?'], 'jsformula': "data.data.discounts.filter(el=>el.label=='SMS и MMS').map(el=>parseInt(el.value)).reduce((x,y)=>x+y,0)"},
            {'name': 'Internet', 'wait': False, 'url_tag': ['/info/tariff?'], 'jsformula': "data.data.discounts.filter(el=>el.label=='Интернет на любые сервисы').map(el=>parseFloat(el.value)).reduce((x,y)=>x+y,0)"},
        ])

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()

if __name__ == '__main__':
    print('This is module megafonb2b')
