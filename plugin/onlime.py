# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller

icon = '789C73F235636100033320D600620128666450804840E5A905989999F1CAB359A833B0DBEB90AC9F595A88817F423283D895490C5C31F644EB67E46065E0CEF264103DD3CB20B2AF9924FDEC2EFA0CC23B1B1844CFF531F0E4FB3230097013AD9F7F6A1A582DFF943406663911885BD85888D62F7AAC8381B72E9C81919111A2174833B2B1E2D40F5387AC9FA7D08F4150408841008841348FA0205C3F0F0F2F032F2F1F0307072703171737033FBF2056FD1CEC1C0C6C6CEC0C3CDCBC0C2C9C1C70FDDCDC3C0CEC40391066656503D3C8FA450EB63288EC6D6260773744B811C9FF30F7E2F23FB38C3003FFC414B07A8179B90C2CAA5224851F0CB0596930086DAA6610BB38011C9EA4EA0703166606AE782706D1135DE4E9870226113E06BE966806CE683BB2F4C300232BEE4C4B8C7EBC6603E305008A3A3F17'

login_url = 'https://my.rt.ru/'
user_selectors = {'chk_lk_page_js': "document.querySelector('div.lk-login input[type=password]') == null",
                  'chk_login_page_js': "document.querySelector('div.lk-login input[type=password]') !== null",
                  'login_clear_js': "document.querySelector('div.lk-login input[name=auth_login]').value=''",
                  'password_clear_js': "document.querySelector('div.lk-login input[type=password]').value=''",
                  'login_selector': 'div.lk-login input[name=auth_login]',
                  'password_selector': 'div.lk-login input[type=password]',
                  'submit_js': 'document.querySelector("div.lk-login input[type=submit]").click()',
                  }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        # Здесь мы берем данные с загружаемой страницы 
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['api/lk/cabinet'], 'jsformula': "data.accountInfo.balance"},
            {'name': 'Balance2', 'url_tag': ['api/lk/cabinet'], 'jsformula': "data.bonusAccount.points"},
            {'name': 'LicSchet', 'url_tag': ['api/lk/cabinet'], 'jsformula': "data.accountInfo.AccountID"},
            {'name': 'TurnOff', 'url_tag': ['api/lk/cabinet'], 'jsformula': "data.accountInfo.daysToLock"},
            {'name': 'TurnOffStr', 'url_tag': ['api/lk/cabinet'], 'jsformula': "data.accountInfo.dateToLock"},
            {'name': 'Expired', 'url_tag': ['api/lk/cabinet'], 'jsformula': "data.accountInfo.dateToLock"},
            {'name': 'AnyString', 'url_tag': ['api/lk/cabinet'], 'jsformula': "data.bonusAccount.tier"},
            ])


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module onlime')
