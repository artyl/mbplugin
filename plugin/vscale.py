#!/usr/bin/python3
# -*- coding: utf8 -*-
import browsercontroller, store

icon = '789C5DD2A192D4401485E1DE2AA80243E1C646F204AB4FE1D16BF328E70990E8080ACB2B1C11452D12C756B55ABD6A0C22FC7D330B934DE65672FBCC4CFA4BF7C74FB7AF5B1DB7AF5AFBC0F5FDA56EDA9B3DB8696D7DB7D7F1707D9ABD5FC6C94D9296DF694F3FBEB536899A298269A142F5D6186E9A286E442E72918B5CE40CB5997C269F6966F2997C269FFBE5B9E426F75C73682637B9C9B96D0BF942BE902FE40B830BF942CEA5853CE421CF98F832264F91F3699DBC9377F24EDEC93B79EFFBF4DB448D73A64C2D54A8BED32672FCC22FFCC22FFCC25F6CBE246E845FF8855FF885BF5E097EE1177EE1177EE117FE7A5DF8855FF8855FF8855FF8EB55E2177EE1177EE1177EE1AFD78C5FF8855FF8855FF8857F2C81F00BBFF00BBFF00BBFF0EFEB3D95DAF86BEDF11BBFF1D7D2E0377EE3377EE3377EE3AF65C36FFC066B4066D26662E6E1B5A4F88DDFF88DDFF88DDFF86BB97988F923F3658F3D88DFF88DBFB6027EE3377EE3377EE337FEDA26F88DDFF88DDFF88DDFF8C716327EE3377EE3377EE337FEDA3EF8532B3E973AF85367DFB716FEE00FFEE00FFEE00FFEDA76F8833FF8833FF8833FF86B4BE20FFEE00FFEE00FFEE0AFED8A3FF8833FF8033AC0C2E46B2BE30FFEE00FFEE00FFEE0AF6DCE24C344C2C3C21F861F3DFDD9DAD7F19EC60B6E5B7DDAB6ED97718EA1D16FDBE397BBD3E9F47D7B3ED6D3A1DDD69F87765BD7CFD72DFDFAF645BF9E5FF4F7E7637F3D50FDFAEB7CECFF0FACCF0397FEFED23F5CFAC763BB6D0FC7B606AE5B06FEB57F01674F2A6B'

login_url = 'https://vds.selectel.ru/panel/login/'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
                  'login_clear_js': "document.querySelector('form input[name=email_or_login]').value=''",
                  'login_selector': 'form input[name=email_or_login]',
                  }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        # Здесь мы берем данные с загружаемой страницы api.vscale.io/v1/billing/balance (то что мы видем в отладчике на странице Network)
        # {"balance":123, "unpaid":0,"user_id":12345}
        # данные страницы json представленные в переменной data соответственно формула получения data.balance
        self.wait_params(params=[{
            'name': 'Balance',
            'url_tag': ['api.vscale.io/v1/billing/balance'],
            'jsformula': 'data.balance',
        },],
        url='https://vscale.io/panel/scalets/')

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module vscale')
