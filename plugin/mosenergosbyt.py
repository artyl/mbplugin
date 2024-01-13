#!/usr/bin/python3
# -*- coding: utf8 -*-
import urllib, logging, os, sys
import browsercontroller, store

icon = '789c6d935d48935118c79f77f3462a596ab3ec26e8a68b8292284aadb02231a328d7726bdfefb677ab0d9766769176d177506441901559596494269446a5175a89b577aee92ad30b97d39272098184d0bff3ee9df4e5811fe71ccef33bdf4fde961549142f2b188b18aa041c2d9007d878478acc5401303f412623f548f3685686afd79be6ed7eac3e207e4d2f0b7c31df0c371f6efbe049adeafc6d6a5e244b0efd59cca289f8603fe70c8124f8ee38c925efa0f205fc19a5dd3348082f2677b4824cfe7ce6cf91c52a05c78b6714ae301442080a47e02f3847f027f1e21572f43428ddb18925bbcfbe264dbd92f973e33aef77c45d67f03f57460427f442b1f707d6e80e4028a249c30e1298af527bdf64281d818842e899d6e5ecd2faaced8e21d75c0efb2e824d4730eda4484343d5d2dee109d7fcf277208b28636658c5df7d3bc316c1aa0d2510b29957c0d0ca73d8b727efad6efddcaaf2f422bfba0fe6da3e54dc1e80b6a61f9acbef51796f10758171941fba8453db5623f8e82e5edeb9085f911ae662822b37a54d55268e91318082736ff1301845ff480cf75f0de1c68b8ff0d68de3d8d5568cf63dc7a78110aa9d85a8715a5069590603db4369766a8cbd718cacddc8dc1f44f4db77dc6e8fa02dfc199dd149d8ce34a3f1b407a3ef43187cd385da4a2f4e14acc579ef56b0fb832f7b664ce511dbc81142123be775ff30f6d5f723ffc208824f9a70f3b8015db76ad152731465eb16a2a3fe1ac22d4d38c2af84b18820e4cc6a5797047d9cb3071c1f00b17752ee1946d6ee0a58d62b61dc4ce0f33898586d60f1a60d04eb468abbbc9ef50b4938d91ccd225b609063ff861322c8b154c2c9ce66299631eb126df66e16d696ee4dba7b8b96861c7a9a27fd01b2fa056ecff0640e7f0aae62256c53f1d3602d96d766f3b813f93357c3fe629e81efb2eb9226d8bc0f185758dccf7f5d69ddb8aba5b3f1b4947db5613b6d7216d141878e96683494ccc63bed52dc2e196b62cf562d0d1835e4fa33e5a4dc959ca9be5e4f29c62de472e5ce7a5a9a9df6a534377dccbd2ee599479f5ed278b76a398b9fcd983795f7bf00e40304ec'

login_url = 'https://my.mosenergosbyt.ru/auth'
user_selectors = {
    # Сначала закрываем infomessage
    'before_login_js': "document.querySelectorAll('button[testid=skip]').forEach(s=>s.click())",
    # Признак того что залогинились (на сложных страница лучше не оставлять по паролю а искать специфичный тэг)
    'chk_lk_page_js': "document.querySelector('#authPage')!=null",
    'remember_checker': "document.querySelector('form input[name=remember]').checked==false",
    # 'remember_js': "document.querySelector('form input[name=remember]').click()",
    'remember_selector': "form input[name=remember]",
}

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        self.do_logon(url=login_url, user_selectors=user_selectors)
        # Выключаем банеры если есть
        self.page_click("button:has-text('Отключить на странице')")  # Skip
        self.page_click("div[role='document'] path")  # Нажимаем на крестик
        # Сначала из файла gate_lkcomu?action=sql&query=LSList& получаем id_service по номеру лицевого счета
        res1 = self.wait_params(params=[{
            'name': '#id_services',
            'url_tag': ['gate_lkcomu?action=sql&query=LSList&'],
            'jsformula': f'data.data.map(s=>[s.nn_ls,s.id_service])',
        }, {
            'name': '#vl_providers',
            'url_tag': ['gate_lkcomu?action=sql&query=LSList&'],
            'jsformula': f'data.data.map(s=>[s.nn_ls,s.vl_provider])',
        }])  # Это промежуточные данные их не берем в результат (они начинаются с #)
        id_services = dict(res1['#id_services'])  # Нам нужен id_service
        vl_providers = dict(res1['#vl_providers'])  # и vl_provider чтобы искать остальные данные
        if self.acc_num != '' and (self.acc_num not in id_services or self.acc_num not in vl_providers):
            logging.error(f'Не найден лицевой счет')
            raise RuntimeError(f'Не найден лицевой счет')
        # Теперь получаем данные по лицевому счету если указан либо по первому с балансом
        for nn_ls in id_services:
            if self.acc_num != '' and self.acc_num != nn_ls:
                continue  # Если он был указан то получаем по нему
            id_service = id_services[nn_ls]
            vl_provider = vl_providers[nn_ls]
            try:
                nm_indication_variants = dict([map(str.strip, i.split(':')) for i in store.options('mosenergosbyt_nm_indication_variants').strip().split(',')])
                nm_indication_take = nm_indication_variants.get(str(store.options('mosenergosbyt_nm_indication_take').strip()), '')
            except Exception:
                logging.error(f'Неправильные настройки для nm_indication в mbplugin.ini: {store.exception_text()}')
                nm_indication_take = ''
            res1 = self.wait_params(params=[{
                'name': 'Balance',  # Баланс в зависимости от вида ЛК может придти либо так
                'url_tag': ['gate_lkcomu?action=sql&query=smorodinaTransProxy&', 'AbonentCurrentBalance', urllib.parse.quote(vl_provider)],
                'jsformula': f'data.data.map(s => s.sm_balance).reduce((a,b)=>a+b)',
            }, {
                'name': 'Balance',  # Либо так (у dimon_s2020) эта версия работает 23.10.20
                'url_tag': ['gate_lkcomu?action=sql&query=bytProxy&', 'proxyquery=CurrentBalance', urllib.parse.quote(vl_provider)],
                'jsformula': f'data.data.map(s => s.vl_balance).reduce((a,b)=>a+b)',
            }, {
                'name': 'Balance2',  # Показания электросчетчика втарифе T1, берем максимальные, они скорее всего будут правильные
                'url_tag': ['gate_lkcomu?action=sql&query=bytProxy&', 'proxyquery=Indications', urllib.parse.quote(vl_provider)],
                'jsformula': f'Math.max(...data.data.filter(s=>s.nm_indication_take=="{nm_indication_take}"||"{nm_indication_take}"=="").map(s=>s.vl_t1))', 'wait':True,  # FIXME пока поставил обязательное ожидание, посмотрим будет ли получать. у некоторых этого параметра может и не быть
            }, {
                'name': 'UserName',  # Username
                'url_tag': ['gate_lkcomu?action=sql&query=GetProfileAttributesValues&'],
                'jsformula': f'data.data[0].attributes[0].vl_attribute+" "+data.data[0].attributes[1].vl_attribute+" "+data.data[0].attributes[2].vl_attribute',
            }], url=f'https://my.mosenergosbyt.ru/accounts/{id_service}',  # Соберем после захода на эту страницу
            )
            # if 'Balance' in res1:  # FIXME ждем до таймаута
            #    break
        else:
            if 'Balance' not in res1:
                logging.error(f'Не найден баланс')
                # raise RuntimeError(f'Не найден баланс')

        # import pprint
        # text = '\n\n'.join([f'{k}\n{pprint.PrettyPrinter(indent=4, width=160).pformat(v)}' for k,v in self.responses.items() if 'GetAdElementsLS' not in k and 'mc.yandex.ru' not in k])
        # open('..\\log\\mosenergosbyt.log','w').write(text)


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return browserengine(login, password, storename, plugin_name=__name__, wait_loop=5, wait_and_reload=-1).main()


if __name__ == '__main__':
    print(store.options('mosenergosbyt_nm_indication_variants'))
    print(dict([map(str.strip, i.split(':', 1)) for i in store.options('mosenergosbyt_nm_indication_variants').strip().split(',')]))  # type: ignore
    print('This is module mosenergosbyt on browser')
