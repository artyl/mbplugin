# -*- coding: utf8 -*-
'Оплата парковки parking.mos.ru'
'(Вход через логин/пароль на login.mos.ru)'
''' Автор ArtyLa '''
import pyppeteeradd as pa

icon = '789C9D53DB2B836118FF297F803FC1A5D2CCA1E44E960BA55D897B17AE28CA36931212CB056EA8D11C4A920B16FAB6B183651726DA2C5BB12D87D5AC1DB2B23944CDFBBCD6D2FA3E93B77EF5F43B3CBDCFFB3D9F42D9580E7E1A19AA182AF22843E5B790D77F1ED9FE206A0E54FF826C2F9F15D4A2A8330D7148E9855E12BAD6BB89C3C74BD44AF5289197312C876CAC874FBC47897CC91E4579B9A0C16AD88126CB08F36AD0E99AE390B39A7A58D82CE491CA4FFB8DD8899CA1E364160FD92472B91C07D5C4ED328D3C627999A0C26D260E856D02B1D7348E623EE802C6420FE248230F798BF3CDD6315CA523E871EBB9DF14F5A2CB358F851B0BFC8C278E34F290B738DF621B87EFE91EBDE72B857CFFC51A9CF100DA1C539C238D3CE4159B3FC2E66CB54FE2E5F31D42D403A573066ACF06BA4F1739471A79A4DE8FEE6A08DB3170B18ED4FB339FF52E9B40E6E38D7306F66DC82395AF376BE14E06A10F5AF99D477DDB1C5413471A797EDB9F06F33096425676CF145C896B0EAA8923EDAFFB47BBD6EED4A1FD58F7EBFE17FEC17FA07AAB0F5FC3BCACE5'

login_url=''
user_selectors={'chk_lk_page_js': "document.querySelector('span[id=balance]') !== null",
    'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
    'login_clear_js': "document.querySelector('form input[name=login]').value=''",
    'login_selector': 'form input[name=login]', 
    'submit_js': "document.querySelector('form button[id=bind]').click()",
    'captcha_checker': "document.querySelector('form [id=sms-code]')!=null",
    'captcha_focus': "document.getElementById('sms-code').focus()", 
    }

class parking_mos_over_puppeteer(pa.balance_over_puppeteer):
    async def async_main(self):
        # Мы должны зайти на страницу личного кабинета, а потом уже перейти на форму логона
        await self.page_goto('https://lk.parking.mos.ru/auth/login')
        await self.page_evaluate("window.location = '/auth/social/sudir?returnTo=/../cabinet'")
        await self.do_logon(url=login_url, user_selectors=user_selectors)
        # Здесь мы берем данные с загружаемой страницы 
        await self.wait_params(params=[{
            'name': 'Balance',
            'jsformula': r"parseFloat(document.querySelector('span[id=balance]').innerText.replace(',', '.'))",
        }])

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return parking_mos_over_puppeteer(login, password, storename).main()


if __name__ == '__main__':
    print('This is module parking_mos')
