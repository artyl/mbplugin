# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import sys
import playwright.sync_api

icon = '789C9593CB2B44511CC7BF1E49918429C98285A2C9D6C64E91CD142B0B0BB3B555FC0962E71FC0828D479E83A99944C32499143316081393CC9DFB987BE7DE3BF7EDB81E79D4BDD7AF3E9BF3EB7BCEF77C7FE7F404BACA615717A19D50FB41095ADE1B1FFDEF6559D67FF95DF6BAF2B209434EC3327528540C1A7F65AFAB4C0C3A7FEEA857A52CE82D1FE4D40498CB29306B656036AAA07209E4F63A209C041CF59A4C830DF9205D8C221B1B06BB061B29BD0866B70585D34117FF0639C70F2ED281E27318B9703BF8E33E889910E8F54A4857E3AEF7E76FE76CDFF9836E141F1720DECC800E3581DDAE87215EBBEA4D53433E354D7268F8F2CF45FC24D7A8A7FC3F51F93B6496ABC11DF6C2D404CFF3FB4457043C2ED5803D1AF8D7FCDF30141A7C7212D46A05C9BD15C5A715F21E544F7A5548931974920C4B918FB681DD6904BB5E06E12C08CB505CF5ECC908793395901F66611A05E285021D0FDA7B28996547BDAEE6EDF3C4F3E00FAF862E81D96986981872D42B8567305B759093637FF2CAEDB6818FF73BFB277F46BE9F87C626FEE8A5F42A346ADFF3FC3CF0A35E019A97F6FE'

# Для тестов выносим параметры наружу, чтобы их можно было взять тестами
login_url = 'https://my.yota.ru/selfcare/devices'


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    def response_worker(response):
        if response.status == 200 and 'finance/getBalance' in response.url:
            data['balance'] = response.json()  # Берем только json

    data = {}
    with playwright.sync_api.sync_playwright() as pcm:
        browser = pcm.chromium.launch(
            headless=False,
            executable_path="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        )
        context = browser.new_context()
        page = context.new_page()
        page.on("response", response_worker)
        page.goto("https://my.yota.ru/selfcare/devices")
        # WAIT page.goto("https://my.yota.ru/login?returnUrl=%2Fdevices")
        page.wait_for_load_state()
        page.wait_for_timeout(3000)
        if page.query_selector("input[type='password']"): # Log in
            page.wait_for_selector("input[type='password']")
            print('login+password',
                  page.query_selector("input[type='password']"))
            page.fill("input", login)
            page.fill("input[type=\"password\"]", password)
            page.wait_for_timeout(1000)
            page.click("text=Войти")
            page.wait_for_load_state()
            page.wait_for_selector("input[type='password']", state='detached')
        page.query_selector("text=Счет:")
        page.wait_for_selector("text=Счет:", state='attached')
        for _ in range(30):
            page.wait_for_timeout(1000)
            if 'balance' in data:
                break
        result = {'Balance': data['balance']['amount']}
    return result


if __name__ == '__main__':
    print('This is module yota')
    print(get_balance(login=sys.argv[1], password=sys.argv[2]))
