#!/usr/bin/python3
# -*- coding: utf8 -*-
import logging, os, sys, re, traceback
import store, settings
import browsercontroller

icon = '789C75524D4F5341143D84B6A8C0EB2BAD856A4B0BE5E301A508A9F8158DC18498A889896E8C3B638C31F147B83171E34E4388AE5C68E246A3C68D0B5DA82180B5B40A5A94B6F651DA423F012D2DE09D79CF4A207DC949A733F79C39F7CC1D3A37A801FF060912415451058772A09E6FFD04CD18F4DA09C267C214210051FB857EFFC1AFEEB3F3495E2F68DEA35EF396F086F6BCBC46D47E257C2304A1D7045157350DA13A80FA6A1F6AAB7CB4F6AB5A5E08DA71D2F840FC772AEF3B44DD0F1874215A87D1DA34871B57658CDE4F1212B87E2504BBD94F5A01D5938F7B16341F8937CB79C65DBF60DA2DC3E594F1FAE532D64B1BD8DCDCE428D1FAC5B30CDAAD33E483799C2E6B187411E245D124CC63BF18C3DD3BB9326F3B6EDF4A506FB3C49FE5BE99C6DE3D32F6E9636836C671A0631153DEB58AFCC9F155EA4DE951D40579CE8C6B37C5693F895347D388C9EB15F9D148119E1E190D3551F23DC7F366F73A2D4974DA52183E9E831CADCC0F878A38E88AC15C3B4F1A119E5D8B39814EEB125CAD199CF0E4C97FA9227F7CAC809E96382CE4D9489989BA9F7092EF2E7B8A7ACF62D0B58C278F8A15F90F4656D0D29880D5B0C07363EFD6665944B72385012947FC15DCBC56403EB7939BCD6CE0F2852CF193B0352C500F8C1F267EB2CC3FEC5EA10CFFE0D5F39D193C7D5C80BB2DCDEFDBCADFEEFF58FF2A2E9D2FC0F7E9BFC6C45809A74FE62035A778BDE23FCAFD3B28BF0EEB22E597E61E0EF52EE348DF2A2E9EFD8D87236B18BD57C099A13CE596E639B37AF6E66C5E597ECC0B7B7BA97909BDCE0CFA3BB3F074E73906A43CFADA73FC6DBAD4BB597D63DD3C0C35CA0C59049A3D933203926D89DFE3261D779B0217FD67DA2C273667AC9ECDBB323F33F80B823D9864'

login_url = 'https://login.mts.ru/amserver/UI/Login?service=newlk'  # - другая форма логина - там оба поля на одной странице, и можно запомнить сессию
# login_url = 'https://lk.mts.ru/'  # а на этой запомнить сессию нельзя
user_selectors = {
    # Возможно 2 разных формы логина, кроме того при заходе через мобильный МТС форма будет отличаться поэтому в выражении предусмотрены все варианты
    'chk_lk_page_js': "document.querySelector('form input[id^=phone]')==null && document.querySelector('form input[id=password]')==null && document.querySelector('form button[value=Ignore]')==null && document.getElementById('enter-with-phone-form')==null",
    'lk_page_url': 'login/userInfo', # не считаем что зашли в ЛК пока не прогрузим этот url
    # У нас форма из двух последовательных окон (хотя иногда бывает и одно, у МТС две разных формы логона)
    'chk_login_page_js': "document.querySelector('form input[id=phoneInput]')!=null || document.querySelector('form input[id=password]')!=null || document.querySelector('form button[value=Ignore]')!=null || document.getElementById('enter-with-phone-form')!=null",
    # Если мы зашли с интернета МТС то предлагается вариант зайти под номером владельца (есть два варианта этой формы), надо нажать кнопку проигнорить этот вариант
    'before_login_js': """b1=document.querySelector('button[value=Ignore]');
                          if(b1!==null){b1.click()};
                          b2=document.getElementById('enter-with-phone-form');
                          i2=document.getElementById('IDButton');
                          if(b2!==null && i2!==null){i2.value='Ignore';b2.submit.click();}
                        """,
    'login_clear_js': "document.querySelector('form input[id^=phone]').value=''",
    'login_selector': 'form input[id^=phone]', 
    # проверка нужен ли submit после логина (если поле пароля уже есть то не нужен, иначе нужен)
    'chk_submit_after_login_js': "document.querySelector('form input[id=phoneInput]')!=null || document.querySelector('form input[id=password]')==null",  
    'remember_checker': "document.querySelector('form input[name=rememberme]')!=null && document.querySelector('form input[name=rememberme]').checked==false",  # Проверка что флаг remember me не выставлен
    'remember_js': "document.querySelector('form input[name=rememberme]').click()",  # js для выставления remember me
    'captcha_checker': "document.querySelector('div[id=captcha-wrapper]')!=null",
    'captcha_focus': "document.getElementById('password').focus()", 
    }

class browserengine(browsercontroller.BrowserController):
    def data_collector(self):
        mts_usedbyme = store.options('mts_usedbyme')
        self.do_logon(url=login_url, user_selectors=user_selectors)

        # TODO close banner # document.querySelectorAll('div[class=popup__close]').forEach(s=>s.click())
        if self.login_ori != self.login and self.acc_num.isdigit():  # это финт для захода через другой номер 
            # если заход через другой номер то переключаемся на нужный номер
            # TODO возможно с прошлого раза может сохраниться переключенный но вроде работает и так
            self.page_wait_for(selector="[id=ng-header__account-phone_desktop]")
            self.responses = {}  # Сбрасываем все загруженные данные - там данные по материнскому телефону            
            # Так больше не работает
            # url_redirect = f'https://login.mts.ru/amserver/UI/Login?service=idp2idp&IDButton=switch&IDToken1=id={self.acc_num},ou=user,o=users,ou=services,dc=amroot&org=/users&ForceAuth=true&goto=https://lk.mts.ru'
            # Теперь добываем url так
            url_redirect = self.page_evaluate(f"Array.from(document.querySelectorAll('a.user-block__content')).filter(el => el.querySelector('.user-block__phone').innerText.replace(/\D/g,'').endsWith('{self.acc_num}'))[0].href")
            self.page_goto(url_redirect)
            # !!! Раньше я на каждой странице при таком заходе проверял что номер тот, сейчас проверяю только на старте
            for _ in range(10):
                self.sleep(1)
                numb = self.page_evaluate("document.getElementById('ng-header__account-phone_desktop').innerText")
                if numb is not None and numb !='':
                    break
            else:
                return  # номера на странице так и нет - уходим
            logging.info(f'PHONE {numb}')
            if re.sub(r'(?:\+7|\D)', '', numb) != self.acc_num:
                return  # Если номер не наш - уходим            

        # Для начала только баланс быстрым способом (может запаздывать)
        self.wait_params(params=[
            {'name': 'Balance', 'url_tag': ['api/login/userInfo'], 'jsformula': "parseFloat(data.userProfile.balance).toFixed(2)"},
            # Закрываем банеры (для эстетики)
            {'name': '#banner1', 'url_tag': ['api/login/userInfo'], 'jsformula': "document.querySelectorAll('mts-dialog div[class=popup__close]').forEach(s=>s.click())", 'wait':False},
            ])

        # Потом все остальное
        res1 = self.wait_params(params=[
            {'name': 'TarifPlan', 'url_tag': ['api/login/userInfo'], 'jsformula': "data.userProfile.tariff.replace('(МАСС) (SCP)','')"},
            {'name': 'UserName', 'url_tag': ['api/login/userInfo'], 'jsformula': "data.userProfile.displayName"},
            {'name': 'Balance', 'url_tag': ['for=api/accountInfo/mscpBalance'], 'jsformula': "parseFloat(data.data.amount).toFixed(2)"},
            {'name': 'Balance2', 'url_tag': ['for=api/cashback/account'], 'jsformula': "parseFloat(data.data.balance).toFixed(2)"},
            {'name': '#counters', 'url_tag': ['for=api/sharing/counters'], 'jsformula': "data.data.counters"},
            ])
        if '#counters' in res1 and type(res1['#counters']) == list and len(res1['#counters'])>0:
            counters = res1['#counters']
            # Минуты
            calling = [i for i in counters if i['packageType'] == 'Calling']
            if calling != []:
                unit = {'Second': 60, 'Minute': 1}.get(calling[0]['unitType'], 1)
                nonused = [i['amount'] for i in calling[0] ['parts'] if i['partType'] == 'NonUsed']
                usedbyme = [i['amount'] for i in calling[0] ['parts'] if i['partType'] == 'UsedByMe']
                if nonused != []:
                    self.result['Min'] = int(nonused[0]/unit)
                if usedbyme != []:
                    self.result['SpendMin'] = int(usedbyme[0]/unit)
            # SMS
            messaging = [i for i in counters if i['packageType'] == 'Messaging']
            if messaging != []:
                nonused = [i['amount'] for i in messaging[0] ['parts'] if i['partType'] == 'NonUsed']
                usedbyme = [i['amount'] for i in messaging[0] ['parts'] if i['partType'] == 'UsedByMe']
                if (mts_usedbyme == '0' or self.login not in mts_usedbyme.split(',')) and nonused != []:
                    self.result['SMS'] = int(nonused[0])
                if (mts_usedbyme == '1' or self.login in mts_usedbyme.split(',')) and usedbyme != []:
                    self.result['SMS'] = int(usedbyme[0])
            # Интернет
            internet = [i for i in counters if i['packageType'] == 'Internet']
            if internet != []:
                unitMult = settings.UNIT.get(internet[0]['unitType'], 1)
                unitDiv = settings.UNIT.get(store.options('interUnit'), 1)
                nonused = [i['amount'] for i in internet[0] ['parts'] if i['partType'] == 'NonUsed']
                usedbyme = [i['amount'] for i in internet[0] ['parts'] if i['partType'] == 'UsedByMe']
                if (mts_usedbyme == '0' or self.login not in mts_usedbyme.split(',')) and nonused != []:
                    self.result['Internet'] = round(nonused[0]*unitMult/unitDiv, 2)
                if (mts_usedbyme == '1' or self.login in mts_usedbyme.split(',')) and usedbyme != []:
                    self.result['Internet'] = round(usedbyme[0]*unitMult/unitDiv, 2)
                            
        self.page_goto('https://lk.mts.ru/uslugi/podklyuchennye')
        res2 = self.wait_params(params=[
            {'name': '#services', 'url_tag': ['for=api/services/list/active$'], 'jsformula': "data.data.services.map(s=>[s.name,!!s.subscriptionFee.value?s.subscriptionFee.value:0])"}])
        try:
            services = sorted(res2['#services'], key=lambda i:(-i[1],i[0]))
            free = len([a for a,b in services if b==0 and (a,b)!=('Ежемесячная плата за тариф', 0)])
            paid = len([a for a,b in services if b!=0])
            paid_sum = round(sum([b for a,b in services if b!=0]),2)
            self.result['UslugiOn'] = f'{free}/{paid}({paid_sum})'
            self.result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in services])
        except Exception:
            logging.info(f'Ошибка при получении списка услуг {store.exception_text()}')
        
        # Идем и пытаемся взять инфу со страницы https://lk.mts.ru/obshchiy_paket
        # Но только если телефон в списке в поле mts_usedbyme или для всех телефонов если там 1
        if mts_usedbyme == '1' or self.login in mts_usedbyme.split(',') or self.acc_num.lower().startswith('common'):
            self.page_goto('https://lk.mts.ru/obshchiy_paket')
            # 24.08.2021 иногда возвращается легальная страница, но вместо информации там сообщение об ошибке - тогда перегружаем и повторяем
            for i in range(3):
                res3 = self.wait_params(params=[{'name': '#checktask', 'url_tag': ['for=api/Widgets/GetUserClaims', '/longtask/'], 'jsformula': "data.result"}])
                if 'claim_error' not in str(res3):
                    break
                logging.info(f'mts_usedbyme: GetUserClaims вернул claim_error - reload')
                self.page_reload()
                self.sleep(5)
            else:
                logging.info(f'mts_usedbyme: GetUserClaims за три попытки так и не дал результат. Уходим')
                self.result = {'ErrorMsg': 'Страница общего пакета не возвращает данных (claim_error)'}
                return
            try:
                if 'RoleDonor' in str(res3):  # Просто ищем подстроку во всем json вдруг что-то изменится
                    logging.info(f'mts_usedbyme: RoleDonor')
                    res4 = self.wait_params(params=[{'name': '#donor', 'url_tag': ['for=api/Widgets/AvailableCountersDonor$', '/longtask/'], 'jsformula': "data.result"}])
                    # acceptorsTotalConsumption - иногда возвращается 0 приходится считать самим
                    # data = {i['counterViewUnit']:i['groupConsumption']-i['acceptorsTotalConsumption'] for i in res4['#donor']}
                    data = {i['counterViewUnit']:i['groupConsumption']-sum([j.get('consumption',0) for j in i.get('acceptorsConsumption',[])]) for i in res4['#donor']}
                if 'RoleAcceptor' in str(res3):
                    logging.info(f'mts_usedbyme: RoleAcceptor')
                    res4 = self.wait_params(params=[{'name': '#acceptor', 'url_tag': ['for=api/Widgets/AvailableCountersAcceptor', '/longtask/'], 'jsformula': "data.result.counters"}])
                    data = {i['counterViewUnit']:i['consumption'] for i in res4['#acceptor']}
                if 'RoleDonor' in str(res3) or 'RoleAcceptor' in str(res3):
                    logging.info(f'mts_usedbyme collect: data={data}')
                    if 'MINUTE' in data:
                        self.result['SpendMin'] = data["MINUTE"]
                    if 'ITEM' in data:
                        self.result['SMS'] = data["ITEM"]
                    if 'GBYTE' in data:
                        self.result['Internet'] = data["GBYTE"]
                # Спецверсия для общего пакета, работает только для Donor
                if self.acc_num.lower().startswith('common'): 
                    if 'RoleDonor' in str(res3):
                        # потребление и остаток
                        cdata_charge = {i['counterViewUnit']:i['groupConsumption'] for i in res4['#donor']}
                        сdata_rest = {i['counterViewUnit']:i['counterLimit']-i['groupConsumption'] for i in res4['#donor']}
                        self.result['Min'] = сdata_rest["MINUTE"]  # осталось минут
                        self.result['SpendMin'] = cdata_charge["MINUTE"]  # Потрачено минут
                        if 'rest' in self.acc_num:
                            self.result['SMS'] = сdata_rest["ITEM"]  # остатки по инету и SMS
                            self.result['Internet'] = сdata_rest["GBYTE"]
                        else:
                            self.result['SMS'] = cdata_charge["ITEM"]  # расход по инету и SMS
                            self.result['Internet'] = cdata_charge["GBYTE"]
                        logging.info(f'mts_usedbyme common collect: сdata_rest={сdata_rest} cdata_charge={cdata_charge}')
                    else:  #  Со страницы общего пакета не отдали данные, чистим все, иначе будут кривые графики. ТОЛЬКО для common
                        raise RuntimeError(f'Страница общего пакета не возвращает данных')
            except Exception:
                logging.info(f'Ошибка при получении obshchiy_paket {store.exception_text()}')
                if self.acc_num.lower().startswith('common'): 
                    self.result = {'ErrorMsg': 'Страница общего пакета не возвращает данных'}
                

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    be = browserengine(login, password, storename)
    if str(store.options('show_captcha')) == '1':
        # если включен показ браузера в случае капчи то отключаем headless chrome - в нем видимость браузера не вернуть
        be.launch_config['headless'] = False
    return be.main()

if __name__ == '__main__':
    print('This is module mts on browser (mts)')
