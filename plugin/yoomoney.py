#!/usr/bin/python3
# -*- coding: utf8 -*-
import pyppeteeradd as pa, store, asyncio

icon = '789c9593cb4a42511486f74169d4c5a0410545a3081a449368dcbc17c87a81a049d02c6854d00344efd030088388e842415a1622055d250cd1b4222f1d2ffbef5f1e053d7a9416fc70f6deebdbeb72f69a999d72abb24d516394a722438d58073c3febb66437000b5480fa85b3c9d925e5ade10c6a9d2ab5e0ec26be1b1576ee1f9cdde6a9ebea4253be0cb0f5096c8b5254924a702f0eec705dd4757c90ca57175fccaa3f02a85009eadc84f217a1e8a11841f9811e7e7f14ea78b37691223ff046df07ea2a0fb5ff03e5a34e72501705f4053512f53cecfc6094ec331bc33b8cb086714af680771c65d0e737dbf3efe45fc83e5a77a83bc9bd00759c6dcb7fb337c331fab3070673705d26618458c78d2ef3bd81d67c9afc10fbaca407cca36b69159d2b9b70df039e8b1c466ff348b5e0e5d7aca519376adde1f2c7e0da0b63f215889a1af182866ec44cfbc62e5fe978a50ee9e574c431a4fcfb60b303e9e532df4bc713301141b3b862f2f6e69d2b020eb3c0227be250b6bc7d99019905c7f9d168882fbe327346cd1c7a61cd66bbf995195fa8727f7496860e'

login_url = 'https://yoomoney.ru/actions'
js_check_balance_str = "document.querySelector('div[class=balance-widget__amount]')!=null"
user_selectors = {}

class yoomoney_over_puppeteer(pa.balance_over_puppeteer):
    async def async_main(self):
        #await self.do_logon(url=login_url, user_selectors=user_selectors)
        # По простому если не видим баланса - показываем капчу
        await self.page_goto(login_url)
        await self.page_waitForNavigation()
        if str(store.options('show_captcha')) == '1':
            if not await self.page_evaluate(js_check_balance_str, default=False):
                pa.hide_chrome(hide=False, foreground=True)
                for cnt2 in range(int(store.options('max_wait_captcha'))):
                    _ = cnt2
                    if await self.page_evaluate(js_check_balance_str, default=False):
                        break
                    await asyncio.sleep(1)                
        await self.wait_params(params=[{
            'name': 'Balance',
            'jsformula': r"parseFloat(document.querySelector('div[class=balance-widget__amount]').innerText.replace(/[^\d\.,-]/g,'').replace(',','.'))",
        },], 
        url='https://yoomoney.ru/actions')

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return yoomoney_over_puppeteer(login, password, storename).main()


if __name__ == '__main__':
    print('This is module vscale on puppeteer')
