#!/usr/bin/python3
# -*- coding: utf8 -*-
import asyncio, time, subprocess, logging, shutil, os, traceback
import pyppeteer  # PYthon puPPETEER
#import pprint; pp = pprint.PrettyPrinter(indent=4).pprint
import store, settings

interUnit = 'GB'  # В каких единицах идет выдача по интернету

icon = '789C75524D4F5341143D84B6A8C0EB2BAD856A4B0BE5E301A508A9F8158DC18498A889896E8C3B638C31F147B83171E34E4388AE5C68E246A3C68D0B5DA82180B5B40A5A94B6F651DA423F012D2DE09D79CF4A207DC949A733F79C39F7CC1D3A37A801FF060912415451058772A09E6FFD04CD18F4DA09C267C214210051FB857EFFC1AFEEB3F3495E2F68DEA35EF396F086F6BCBC46D47E257C2304A1D7045157350DA13A80FA6A1F6AAB7CB4F6AB5A5E08DA71D2F840FC772AEF3B44DD0F1874215A87D1DA34871B57658CDE4F1212B87E2504BBD94F5A01D5938F7B16341F8937CB79C65DBF60DA2DC3E594F1FAE532D64B1BD8DCDCE428D1FAC5B30CDAAD33E483799C2E6B187411E245D124CC63BF18C3DD3BB9326F3B6EDF4A506FB3C49FE5BE99C6DE3D32F6E9636836C671A0631153DEB58AFCC9F155EA4DE951D40579CE8C6B37C5693F895347D388C9EB15F9D148119E1E190D3551F23DC7F366F73A2D4974DA52183E9E831CADCC0F878A38E88AC15C3B4F1A119E5D8B39814EEB125CAD199CF0E4C97FA9227F7CAC809E96382CE4D9489989BA9F7092EF2E7B8A7ACF62D0B58C278F8A15F90F4656D0D29880D5B0C07363EFD6665944B72385012947FC15DCBC56403EB7939BCD6CE0F2852CF193B0352C500F8C1F267EB2CC3FEC5EA10CFFE0D5F39D193C7D5C80BB2DCDEFDBCADFEEFF58FF2A2E9D2FC0F7E9BFC6C45809A74FE62035A778BDE23FCAFD3B28BF0EEB22E597E61E0EF52EE348DF2A2E9EFD8D87236B18BD57C099A13CE596E639B37AF6E66C5E597ECC0B7B7BA97909BDCE0CFA3BB3F074E73906A43CFADA73FC6DBAD4BB597D63DD3C0C35CA0C59049A3D933203926D89DFE3261D779B0217FD67DA2C273667AC9ECDBB323F33F80B823D9864'

async def async_main(login, password, storename=None):
    result = {}
    waitfor = set()
    options = store.read_ini()['Options']
    # спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный
    mts_usedbyme = options.get('mts_usedbyme', settings.mts_usedbyme)
    storefolder = options.get('storefolder', settings.storefolder)
    user_data_dir = os.path.join(storefolder,'puppeteer')
    profile_directory = storename
    chrome_executable_path = options.get('chrome_executable_path', settings.chrome_executable_path)
    if not os.path.exists(chrome_executable_path):
        chrome_paths = [p for p in settings.chrome_executable_path_alternate if os.path.exists(p)]
        if len(chrome_paths) == 0:
            logging.error('Chrome.exe not found')
            raise RuntimeError(f'Chrome.exe not found')
        chrome_executable_path = chrome_paths[0]
    logging.info(f'Launch chrome from {chrome_executable_path}')
    browser = await pyppeteer.launch({
        'headless': False,
        'ignoreHTTPSErrors': True,
        'defaultViewport': None,
        'handleSIGINT':False,  # need for threading (https://stackoverflow.com/questions/53679905)
        'handleSIGTERM':False,  
        'handleSIGHUP':False,
        # TODO хранить параметр в ini
        'executablePath': chrome_executable_path,
        'args': [f"--user-data-dir={user_data_dir}", f"--profile-directory={profile_directory}",
                 '--wm-window-animations-disabled',
                 '--no-sandbox',
                 '--disable-setuid-sandbox',
                 '--disable-dev-shm-usage',
                 '--disable-accelerated-2d-canvas',
                 '--no-first-run',
                 '--no-zygote',
                 '--log-level=3', # no logging                 
                 #'--single-process', # <- this one doesn't works in Windows
                 '--disable-gpu', ],
    })

    async def worker(response):
        if response.status != 200:
            return        
        if response.request.url.endswith('api/login/userInfo'):
            waitfor.difference_update({'api/login/userInfo'}) # этот элемент больше не ждем
            logging.info(f'await {response.request.url}')
            data = await response.json()
            profile = data['userProfile']
            result['Balance'] = round(profile.get('balance', 0), 2)
            result['TarifPlan'] = profile.get('tariff', '')
            result['UserName'] = profile.get('displayName', '')                    
        if response.request.url.endswith('for=api/accountInfo/balance'):
            waitfor.difference_update({'for=api/accountInfo/balance'}) # этот элемент больше не ждем
            logging.info(f'await {response.request.url}')
            response_json = await response.json()
            data = response_json.get('data', {})
            result['Balance'] = round(data['amount'], 2)
        if response.request.url.endswith('for=api/services/list/active'):
            #if len(await response.text())==0: return
            waitfor.difference_update({'for=api/services/list/active'}) # этот элемент больше не ждем
            logging.info(f"{response.request.url=} {response.request.url.endswith('for=api/services/list/active')} {response.status}")
            response_json = await response.json()
            data = response_json.get('data', {})
            if 'services' in data:
                services = [(i['name'], i.get('subscriptionFees', [{}])[0].get('value', 0)) for i in data['services']]
                services.sort(key=lambda i:(-i[1],i[0]))
                free = len([a for a,b in services if b==0 and (a,b)!=('Ежемесячная плата за тариф', 0)])
                paid = len([a for a,b in services if b!=0])
                paid_sum = round(sum([b for a,b in services if b!=0]),2)
                result['UslugiOn']=f'{free}/{paid}({paid_sum})'
                result['UslugiList']='\n'.join([f'{a}\t{b}' for a,b in services])
        if response.request.url.endswith('for=api/sharing/counters'):
            waitfor.difference_update({'for=api/sharing/counters'}) # этот элемент больше не ждем
            logging.info(f"{response.request.url=} {response.request.url.endswith('for=api/services/list/active')} {response.status}")
            response_json = await response.json()
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

    async def do_waitfor(tokens):
        'Ждем пока прогрузятся все интересующие страницы с данными'
        waitfor.update(tokens)
        logging.info(f'Start wait {waitfor}')
        for countdown in range(10):  # TODO подобрать параметр
            if len(waitfor) == 0: break
            logging.debug(f'Wait {waitfor} {countdown}')
            await asyncio.sleep(1) 
        else:  # так и не дождались - пробуем перезагрузить и еще подождать
            logging.info(f'RELOAD')
            await page.reload()
            for countdown in range(20):  # TODO подобрать параметр
                if len(waitfor) == 0: break
                logging.debug(f'Wait {waitfor} {countdown}')
        logging.info(f'End wait {waitfor}')

    pages = await browser.pages()
    for page in pages[1:]:
        await page.close() # Закрываем остальные страницы, если вдруг открыты
    page = pages[0]  # await browser.newPage()
    page.on("response", worker) # вешаем обработчик на страницы
    logging.info(f'goto https://lk.mts.ru')
    try:
        await page.goto('https://lk.mts.ru', {'timeout': 20000})
    except pyppeteer.errors.TimeoutError:
        logging.info(f'page.goto timeout')
    logging.info(f'waitForNavigation')
    # почему-то иногда застревает 
    await page.reload()
    try:
        await page.waitForNavigation({'timeout': 20000})
    except pyppeteer.errors.TimeoutError:   
        logging.info(f'waitForNavigation timeout')
    #await page.screenshot({ 'path': 'image2.jpg', type: 'jpeg' });

    if await page.evaluate("document.getElementById('password') !== null"):
        logging.info(f'Login')
        await page.type("#phone", login, {'delay': 10})
        await page.type("#password", password, {'delay': 10})
        await page.evaluate("document.getElementsByClassName('checkbox__input')[0].checked=true")
        await asyncio.sleep(1)
        await page.evaluate("document.getElementsByClassName('btn btn_large btn_wide')[0].click()")
    else:
        logging.info(f'Already login')
    #await asyncio.sleep(1000)
    # почему-то иногда застревает явно идем в https://lk.mts.ru
    await page.goto('https://lk.mts.ru', {'timeout': 20000})
    await do_waitfor({'api/login/userInfo', 'for=api/accountInfo/balance', 'for=api/sharing/counters'})

    await page.goto('https://lk.mts.ru/uslugi/podklyuchennye', {'timeout': 20000})
    await do_waitfor({'for=api/services/list/active'})
    logging.info(f'Data ready')
    await browser.close()
    clear_cache(user_data_dir, profile_directory)
    return result

def clear_cache(user_data_dir, profile_directory):
    profilepath = os.path.abspath(os.path.join(user_data_dir, profile_directory))
    shutil.rmtree(os.path.join(profilepath, 'Cache'), ignore_errors=True)
    shutil.rmtree(os.path.join(profilepath, 'Code Cache'), ignore_errors=True)

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    result = {}
    # спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный
    options = store.read_ini()['Options']
    mts_usedbyme = options.get('mts_usedbyme', settings.mts_usedbyme)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = asyncio.get_event_loop().run_until_complete(async_main(login, password, storename))
    # TODO !!! kill chrome    
    return result    


if __name__ == '__main__':
    print('This is module mts on puppeteer (mts2)')
