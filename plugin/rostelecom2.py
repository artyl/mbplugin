#!/usr/bin/python3
# -*- coding: utf8 -*-
import pyppeteeradd as pa

icon = '789CA5D4B171DB401484E1A719050E5D024257A078C7B97BB852B614041ED7B1B16A708012942BA0FF7BA065DAA2259222780310CB77B8EFEEC8AFDF1E3E55BF1EEEABBE70FE7C6C77B5ECC17DFD79DD9D5C97FB5DF67E9A0717492A3F534F8F3FAA16D1068D605969A16D55DC2ED1BFB810B9C8452E729173AB06F9201F7C18E4837C908FEDF85C72937BF418CAE426373997B592AFE42BF94ABE7273255FC93955C8431EF2CC81AF73F03472DEB5916FE41BF946BE916FE4DBB60F9FF9511F8366DA4A0B6DDB690B397EE1177EE1177EE16F365F1217C22FFCC22FFCC2DF53825FF8855FF8855FF885BFA70BBFF00BBFF00BBFF00B7F4F257EE1177EE1177EE117FE9E66FCC22FFCC22FFCC22FFC7309845FF8855FF8855FF8857F5FEFA5D5C6DF6B8FDFF88DBF9706BFF11BBFF11BBFF11B7F2F1B7EE337580332833603330FEF25C56FFCC66FFCC66FFCC6DFCBCD434C47E6CB9E7B10BFF11B7F6F05FCC66FFCC66FFCC66FFCBD4DF01BBFF11BBFF11BBFF1CF2D64FCC66FFCC66FFCC66FFCBD7DF0A7577CB43AF8D3C7B66F2DFCC11FFCC11FFCC11FFCBDEDF0077FF0077FF0077FF0F796C41FFCC11FFCC11FFCC1DFDB157FF0077FF007748085C1F756C61FFCC11FFCC11FFCC1DFDB9C4186818487850E43D1D3F3A1BECF799A135C877ED7E1B09FE6316FCDCF276D3ED3C77D5B276DCEF3BFDF3DD7E6DCD58DB5BFEBE7DCDE52FB523FF7EF92AB6B4FEB679BFF791FA9EF3E9E3F563FF7DA357DBCAABFB28FB3F5B5EFE74BFAF86FFD857DBC597FECE3CDFAE59DFAF14EFDFCCDDD58FBD2C7FC6DDF587BB68F2B6BFFEAE382DA5FA120AA5C'

class rostelecom_over_puppeteer(pa.balance_over_puppeteer):
    async def async_main(self):
        await self.do_logon(
            url='https://lk.rt.ru',
            user_selectors={
                'before_login_js':"document.querySelector('div[data-tab=login]').click()", # Сначала кликаем по Логин
                'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
                'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
                'login_clear_js': "document.querySelector('form input[id=username]').value=''",  # Уточняем поле для логина чтобы не промахнуться
                'login_selector': 'form input[id=username]', 
                'remember_checker': "document.querySelector('form input[name=rememberMe]').checked==false",  # Галка rememberMe почему-то нажимается только через js
                'remember_js': "document.querySelector('form input[name=rememberMe]').click()",
                })
        # Сначала из файла client-api/getAccounts получаем accountId по номеру лицевого счета
        res1 = await self.wait_params(params=[{
            'name': 'accountId',
            'url_tag': ['client-api/getAccounts'],
            'jsformula': f'data.accounts.filter(el => el.number=="{self.acc_num}")[0].accountId',
            #'pformula': f"[el['accountId'] for el in data['accounts'] if el['number']=='{self.acc_num}']"
        }], save_to_result=False)  # Это промежуточные данные их не берем в результат
        accountId = res1['accountId']  # Нам нужен accountId чтобы искать остальные данные

        # Теперь со страницы client-api/getAccountBalanceV2 возьмем Balance (по accountId)
        await self.wait_params(params=[{
            'name': 'Balance',
            'url_tag': ['client-api/getAccountBalanceV2', str(accountId)],
            'jsformula': r"data.balance/100",
        },{  # со страницы client-api/getAccountServicesMainInfo возьмем сумму всех месячных плат и назовем это тарифным планом (тоже по accountId)
            'name': 'TarifPlan',
            'url_tag': ['client-api/getAccountServicesMainInfo', str(accountId)],
            'pformula': r"','.join([i['fee'] for i in data['services'].values()])",
        },{  # и со страницы client-api/getProfile соберем UserName (для него не нужен accountId)
            'name': 'UserName',
            'url_tag': ['client-api/getProfile'],
            'jsformula': 'data.lastName+" "+data.name+" "+data.middleName',
        }])

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return rostelecom_over_puppeteer(login, password, storename).main()


if __name__ == '__main__':
    print('This is module rostelecom on puppeteer')
