#!/usr/bin/python3
# -*- coding: utf8 -*-
import asyncio, time, re, subprocess, logging, shutil, os, traceback
import win32gui, win32process, psutil
import pyppeteer  # PYthon puPPETEER
#import pprint; pp = pprint.PrettyPrinter(indent=4).pprint
import store, settings
import pyppeteeradd as pa

interUnit = 'GB'  # В каких единицах идет выдача по интернету

icon = '789C75524D4F5341143D84B6A8C0EB2BAD856A4B0BE5E301A508A9F8158DC18498A889896E8C3B638C31F147B83171E34E4388AE5C68E246A3C68D0B5DA82180B5B40A5A94B6F651DA423F012D2DE09D79CF4A207DC949A733F79C39F7CC1D3A37A801FF060912415451058772A09E6FFD04CD18F4DA09C267C214210051FB857EFFC1AFEEB3F3495E2F68DEA35EF396F086F6BCBC46D47E257C2304A1D7045157350DA13A80FA6A1F6AAB7CB4F6AB5A5E08DA71D2F840FC772AEF3B44DD0F1874215A87D1DA34871B57658CDE4F1212B87E2504BBD94F5A01D5938F7B16341F8937CB79C65DBF60DA2DC3E594F1FAE532D64B1BD8DCDCE428D1FAC5B30CDAAD33E483799C2E6B187411E245D124CC63BF18C3DD3BB9326F3B6EDF4A506FB3C49FE5BE99C6DE3D32F6E9636836C671A0631153DEB58AFCC9F155EA4DE951D40579CE8C6B37C5693F895347D388C9EB15F9D148119E1E190D3551F23DC7F366F73A2D4974DA52183E9E831CADCC0F878A38E88AC15C3B4F1A119E5D8B39814EEB125CAD199CF0E4C97FA9227F7CAC809E96382CE4D9489989BA9F7092EF2E7B8A7ACF62D0B58C278F8A15F90F4656D0D29880D5B0C07363EFD6665944B72385012947FC15DCBC56403EB7939BCD6CE0F2852CF193B0352C500F8C1F267EB2CC3FEC5EA10CFFE0D5F39D193C7D5C80BB2DCDEFDBCADFEEFF58FF2A2E9D2FC0F7E9BFC6C45809A74FE62035A778BDE23FCAFD3B28BF0EEB22E597E61E0EF52EE348DF2A2E9EFD8D87236B18BD57C099A13CE596E639B37AF6E66C5E597ECC0B7B7BA97909BDCE0CFA3BB3F074E73906A43CFADA73FC6DBAD4BB597D63DD3C0C35CA0C59049A3D933203926D89DFE3261D779B0217FD67DA2C273667AC9ECDBB323F33F80B823D9864'

async def async_main(login, password, storename=None):
    result = {}
    waitfor = set()
    # можно зайти в lk через другой номер тогда логин номер_для_баланса/номер_для_входа
    # тогда пароль указывается от номера для входа
    main_login = login_ori = login
    if '/' in login:
        login, main_login = login_ori.split('/')
        storename = storename.replace(re.sub(r'\W', '_',login_ori) ,re.sub(r'\W', '_',main_login))  # исправляем storename
    # спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный
    mts_usedbyme = store.options('mts_usedbyme')

    async def worker(response):
        'Worker вызывается на каждый url который открывается при загрузке страницы (т.е. список тот же что на вкладке сеть в хроме)'
        if response.status != 200:
            return
        # Список окончаний url которые мы будем смотреть, остальные игнорируем
        catch_elements = ['api/login/userInfo', 'for=api/accountInfo/balance', 'for=api/services/list/active', 'for=api/sharing/counters']
        for elem in catch_elements:
            if response.request.url.endswith(elem):
                # Если это сложный заход, то проверяем что смотрим на нужный телефон
                if '/' in login_ori:
                    numb = await pa.page_evaluate(page, "document.getElementsByClassName('mts16-other-sites__phone')[0].innerText")
                    if numb is None:
                        return  # номера на странице нет - уходим
                    logging.info(f'PHONE {numb}')
                    if re.sub(r'(?:\+7|\D)', '', numb) != login:
                        return  # Если номер не наш - уходим
                waitfor.difference_update({elem}) # этот элемент больше не ждем
                logging.info(f'await {response.request.url}')
                response_json = await response.json()
                break
        else:  # Если url не из списка - уходим
            return
        if response.request.url.endswith('api/login/userInfo'):  # # # # # Баланс и еще
            data = response_json
            profile = data['userProfile']
            result['Balance'] = round(profile.get('balance', 0), 2)
            result['TarifPlan'] = profile.get('tariff', '')
            result['UserName'] = profile.get('displayName', '')                    
        if response.request.url.endswith('for=api/accountInfo/balance'):  # # # # # Баланс поточнее
            data = response_json.get('data', {})
            result['Balance'] = round(data['amount'], 2)
        if response.request.url.endswith('for=api/services/list/active'):  # # # # # Услуги
            data = response_json.get('data', {})
            if 'services' in data:
                services = [(i['name'], i.get('subscriptionFees', [{}])[0].get('value', 0)) for i in data['services']]
                services.sort(key=lambda i:(-i[1],i[0]))
                free = len([a for a,b in services if b==0 and (a,b)!=('Ежемесячная плата за тариф', 0)])
                paid = len([a for a,b in services if b!=0])
                paid_sum = round(sum([b for a,b in services if b!=0]),2)
                result['UslugiOn']=f'{free}/{paid}({paid_sum})'
                result['UslugiList']='\n'.join([f'{a}\t{b}' for a,b in services])
        if response.request.url.endswith('for=api/sharing/counters'):  # # # # # Остатки пакетов
            data = response_json.get('data', {})
            if 'counters' in data:
                counters = data['counters']
                # Минуты
                calling = [i for i in counters if i['packageType'] == 'Calling']
                if calling != []:
                    unit = {'Second': 60, 'Minute': 1}.get(calling[0]['unitType'], 1)
                    nonused = [i['amount'] for i in calling[0] ['parts'] if i['partType'] == 'NonUsed']
                    usedbyme = [i['amount'] for i in calling[0] ['parts'] if i['partType'] == 'UsedByMe']
                    if nonused != []:
                        result['Min'] = int(nonused[0]/unit)
                    if usedbyme != []:
                        result['SpendMin'] = int(usedbyme[0]/unit)
                # SMS
                messaging = [i for i in counters if i['packageType'] == 'Messaging']
                if messaging != []:
                    nonused = [i['amount'] for i in messaging[0] ['parts'] if i['partType'] == 'NonUsed']
                    usedbyme = [i['amount'] for i in messaging[0] ['parts'] if i['partType'] == 'UsedByMe']
                    if (mts_usedbyme == '0' or login not in mts_usedbyme.split(',')) and nonused != []:
                        result['SMS'] = int(nonused[0])
                    if (mts_usedbyme == '1' or login in mts_usedbyme.split(',')) and usedbyme != []:
                        result['SMS'] = int(usedbyme[0])
                # Интернет
                internet = [i for i in counters if i['packageType'] == 'Internet']
                if internet != []:
                    unitMult = settings.UNIT.get(internet[0]['unitType'], 1)
                    unitDiv = settings.UNIT.get(interUnit, 1)
                    nonused = [i['amount'] for i in internet[0] ['parts'] if i['partType'] == 'NonUsed']
                    usedbyme = [i['amount'] for i in internet[0] ['parts'] if i['partType'] == 'UsedByMe']
                    if (mts_usedbyme == '0' or login not in mts_usedbyme.split(',')) and nonused != []:
                        result['Internet'] = round(nonused[0]*unitMult/unitDiv, 2)
                    if (mts_usedbyme == '1' or login in mts_usedbyme.split(',')) and usedbyme != []:
                        result['Internet'] = round(usedbyme[0]*unitMult/unitDiv, 2)

    pa.clear_cache(storename)
    browser, page = await pa.launch_browser(storename, worker)  
    await pa.page_goto(page, 'https://lk.mts.ru/')

    if await pa.page_evaluate(page, "document.getElementById('balance') !== null"):
        logging.info(f'Already login')
    else:
        for cnt in range(20):  # Почему-то иногда с первого раза логон не проскакивает
            if await pa.page_evaluate(page, '''document.getElementById('password') !== null 
                    && document.getElementById('phone') !== null 
                    && document.getElementsByClassName('btn btn_large btn_wide')[0] !== undefined '''):
                logging.info(f'Login')
                await pa.page_evaluate(page, f"document.getElementById('phone').value='{main_login}'")
                await pa.page_evaluate(page, f"document.getElementById('password').value='{password}'")
                await pa.page_evaluate(page, "document.getElementsByClassName('checkbox__input')[0].checked=true") 
                await asyncio.sleep(1)
                await pa.page_evaluate(page, "document.getElementsByClassName('btn btn_large btn_wide')[0].click()") 
            elif await pa.page_evaluate(page, "document.getElementById('balance') !== null"):
                logging.info(f'Logoned')
                break 
            elif await pa.page_evaluate(page, "document.body.innerText.search('Your support ID is:')>0"):
                # Капча - эту капчу вводить бесполезно
                logging.info(f'Captcha')
                #logging.info(f'Delete profile')
                #pa.delete_profile(storename)
                raise RuntimeError(f'Captca Your support ID is')                
                break
            elif await pa.page_evaluate(page, "document.getElementById('captcha-wrapper') !== null"):
                # Капча
                # TODO включить проверку флага:
                if str(store.options('show_captcha')) == '1':
                    pa.hide_chrome(hide=False) # Покажем хром и подождем вдруг кто-нибудь введет
                    logging.info(f'Captcha, wait human')
                    for _ in range(90):
                        if await pa.page_evaluate(page, "document.getElementById('captcha-wrapper') !== null"):
                            break
                        await asyncio.sleep(1)
                    else:
                        logging.error('No more wait for a human')
                        raise RuntimeError(f'Captcha not solve')
                else:
                    logging.error('No wait for a human')
                    raise RuntimeError(f'Captcha not solve')
            await asyncio.sleep(1)
            if cnt==10:
                await page.reload()
        else:
            logging.error(f'Unknown state')
            raise RuntimeError(f'Unknown state')
    # почему-то иногда застревает явно идем в https://lk.mts.ru/ 
    await pa.page_goto(page, 'https://lk.mts.ru')
    if main_login != login:  # это финт для захода через другой номер
        # если заход через другой номер то переключаемся на нужный номер
        # TODO возможно с прошлого раза может сохраниться переключенный но вроде работает и так
        for i in range(20):
            if await pa.page_evaluate(page, "document.getElementsByClassName('mts16-other-sites__phone').length") > 0:
                break
            logging.info(f'wait mts16-other-sites__phone')
            await asyncio.sleep(1)
        url_redirect = f'https://login.mts.ru/amserver/UI/Login?service=idp2idp&IDButton=switch&IDToken1=id%3D{login}%2Cou%3Duser%2Co%3Dusers%2Cou%3Dservices%2Cdc%3Damroot&org=%2Fusers&ForceAuth=true&goto=https%3A%2F%2Flk.mts.ru'
        await pa.page_goto(page, url_redirect)

    await pa.do_waitfor(page, waitfor, {'api/login/userInfo', 'for=api/accountInfo/balance', 'for=api/sharing/counters'})

    await pa.page_goto(page, 'https://lk.mts.ru/uslugi/podklyuchennye')
    await pa.do_waitfor(page, waitfor, {'for=api/services/list/active'})
    logging.info(f'Data ready {result.keys()}')
    await browser.close()
    pa.clear_cache(storename)
    return result


def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    result = {}
    # спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = asyncio.get_event_loop().run_until_complete(async_main(login, password, storename))
    return result    


if __name__ == '__main__':
    print('This is module mts on puppeteer (mts2)')
