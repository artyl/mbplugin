# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import browsercontroller

icon = '789c8d90dd4b53611cc75db36ded2d9b83d80b7412f71211dec4bca828b2a288a0022b2970b5c9e8562abaf33fe8aadca82eca20c2a13799292d7676f6727674b51d75ad2ccb98b3bb9aa35969876fcfd956196ccb2f7c38cf737ecfe79cdfef3978c2d1d8508a8360273455903450e502a947b4656a451d855d1905a766706deb3854860494ea103c2a0e9c3606476db39ce6088c72069fe411088a1066096fc87e45c108050d03ebff7c319b83a08cc30b03e6a145984a641f6b5858d6e38a318fe5759ae7df239ac0329a9ee6a17b92e77581a2693dae328c3645589890b3802c04a89e7d83c1bf00cbed97d3566f6c4fddbec3d8a2a0c9bc1c20a709c49731e25a80f9d13c2cb7d8c5366fac661f6a7af5943c5efe6fc9af207e433bba04eb5d1e762fdb53cdb50ca4db8d831f3fc822557cb2578f17d1ea4bc0ea9bcc510f5e1df9230212038bbdbad1fc9cc99fc546a68edfcfc1762709fdc897ac3e8ee320ae9b87f94c0acca1d0d72bcd43b97bd228d048ff8b94f89bc68a68f1bd80f56674787fb070f9ec1458d73476f4f561c3d50c3412d24a0b87dddb39619922774f45ffb22d06b4867ec0e17fb7d2fe70f6b07856743a07215d7b074e5eb8ef9903dcaf814b3304be0259bbc8bb9ef78093c7883873b53bece6d1e14aa3f3420ae776c591b42500db24b0338eb75d499c176bdd291cade5ff4e6f0efa8ee0527a1f9d87c801ba30efc980aae7accdc5195c3f9df8896381cf254e4eacc239851bebf59d4978c8bc5ee2f48bb833a5676fb5be7f01fc3192aa'


login_url = 'https://chailand.ru/balance'

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.page_goto(login_url)
        self.sleep(1)
        self.page_wait_for(selector='input.cardnumber')
        self.page_fill('input.cardnumber', self.login)
        self.page_click('button.checkbalance')
        # Здесь мы берем данные с загружаемой страницы api.vscale.io/v1/billing/balance (то что мы видем в отладчике на странице Network)
        # {"balance":123, "unpaid":0,"user_id":12345} 
        # данные страницы json представленные в переменной data соответственно формула получения data.balance
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['chailand/getbalance'], 'jsformula': 'data.success.Cash_Balance+data.success.Cash_Bonus_Balance',},
            {'name': 'Balance2', 'url_tag': ['chailand/getbalance'], 'jsformula': 'data.success.Token_Balance',},
            {'name': 'TarifPlan', 'url_tag': ['chailand/getbalance'], 'jsformula': '"Карта "+data.success.Account+" Баланс "+data.success.Cash_Balance+" Бонус "+data.success.Cash_Bonus_Balance+" Жетоны "+(data.success.Token_Balance+data.success.Token_Bonus_Balance)',},
            {'name': 'UslugiOn', 'url_tag': ['chailand/getbalance'], 'jsformula': '""+(data.success.Cash_Balance+data.success.Cash_Bonus_Balance)+"/"+(data.success.Token_Balance+data.success.Token_Bonus_Balance)',},
            
            ],)

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module chailand')
