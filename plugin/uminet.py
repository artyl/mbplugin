#!/usr/bin/python3
# -*- coding: utf8 -*-
import browsercontroller, store

icon = '789c3d93fb4fdb6514c667e2cfc63fc11f75f44a4be9a037ca147023c1658325fbc10bd36ccb748be22d243361730c286d29145a5a2e5bc476dd040b4c371c17875b608a90ccc82463863b01b98ce924baf6e36901dfe4c9fb3de7bccf39e77bdee7b5e71b9edd955c06c18b82e7b7f1ccae17b60212ffe1b92dec2c5dc08a56a0f1cbde60415d9bc96eb78197aa0555067657a59192840165a51185c388d29581ca6342556b21b5d146aa70353e335aaf99f4da97b17bf279c55d409ef300b9ce02b29dfb48abb60b3f134565bae430a0901c0ab705adf0b57e0b3a9f8d7d8d859c6afd948a3617f5611ffe70006fa8818a964a4ed79790ef2a425f69913ce9281d19289d265213bd375ac86b394445a49aee6faf313c7c97b1915146864618be3dc4773d3d7c158950d3eae1485d31ba0aa9eb3061acc992fa56327cb91c6ffa80cbed11c646c758595de5b7a909a283d788f677d1d37793ce6817df7476e3bde227c77950f8564c35b9a81bcdecad7f8df71d9f10fe22c4eccc1c4b1bcbb40e853872e96d8a2f9ec075d94b73530bddd14efaeef452ec3f89aaca84c19995ec7dbfbf90cfeacae8686f67617e91817b831435bd81a23a1d7dad4d7a3b4db039c88d9eebfc327e8f0f2f96a211bed165472db33bdc56cc97d7c38c8e8d323b3f4fdbc01572bc05289c7be43e2dbc1bfe98de813e7e1dbfcfe4c3df290d9591eab491599387ca6fe268c77bfc3831c2fada1acbcb2b5cea0d932bffa472ef415367e34ccf056616e778b4bec1d4d4346722e74873dbc9a8cb21c59fc9b1ee121e2c4f0271d657d769eb8d90e73b8452b4a4abcfa2fc96873ffffd9bf8d33833d3d39cbb5a4e5a8ddc7b9d15a5d47fa7ab84f1e50962f1181b6bab84fa851f388c4af4a4f709ff7b378f37ff22f634c6ecdc14e7bfae40e7b593e2b5a1f69938de59c2fdc507c46271fe79b249f4a7a8e8a11085e859e7b70bdfc393cd4de2f1380bab0b5cb8e142df908da641f87e3347a3a7b83bf5334b8fffe0e1ca34bee1566ccdfb653656e1efa5acaf8af9478b2c6c2cd13f799b63d112f15bd1cbec35010baf860e52da7b96f23b1e3ebaf9390742af27e31ad1963668a7e8ea5b9c1f7471f69683373b4e620ce66ce93e81800d9de4d0c959b5d8ea40e24d59b7e359a26f1b9aa0d449dad6a4de77b889dada6dffffe7e55bb713175b9f4020e1cf4ee648f07581c46e411f34f31f3b798d90'

login_url = 'https://lk.uminet.ru/'
user_selectors = {'chk_lk_page_js': "document.querySelector('form input[id=LoginForm_password]') == null",
                  'chk_login_page_js': "document.querySelector('form input[id=LoginForm_password]') !== null",
                  'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                  'login_selector': 'form input[type=text]',
                  'submit_js': "document.querySelector('form [type=submit]').click()"}

# введите логин demo@saures.ru и пароль demo вручную
class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        # Здесь мы берет данные непосредственно с отрендеренной страницы, поэтому url_tag не указан
        self.wait_params(params=[{
            'name': 'Balance',
            'jsformula': r"""document.querySelector('.balance-home').innerText.replace(',','.').replace(/\D\./g, '').replace(/[^\d,.-]/g, '')""",
        }, {
            'name': 'BlockStatus', 'wait':False,
            'jsformula': r"""document.querySelector('[data-label="Статус"]').innerText""",
        }, {
            'name': 'TarifPlan', 'wait':False,
            'jsformula': r"""a=document.querySelector('[data-label="Тариф"]');b=document.querySelector('[data-label="Абонентская плата"]'); ((a!==null?a.innerText:"")+" "+(b!==null?b.innerText:"")).replace(/\s/g,' ')""",
        }])


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    return browserengine(login, password, storename, plugin_name=__name__).main()


if __name__ == '__main__':
    print('This is module uminet')
