#!/usr/bin/python3
# -*- coding: utf8 -*-
import asyncio, time, re, json, subprocess, logging, shutil, os, traceback
import win32gui, win32process, psutil
import pyppeteer  # PYthon puPPETEER
#import pprint; pp = pprint.PrettyPrinter(indent=4).pprint
import store, settings
import pyppeteeradd as pa

icon = '789CA5D4B171DB401484E1A719050E5D024257A078C7B97BB852B614041ED7B1B16A708012942BA0FF7BA065DAA2259222780310CB77B8EFEEC8AFDF1E3E55BF1EEEABBE70FE7C6C77B5ECC17DFD79DD9D5C97FB5DF67E9A0717492A3F534F8F3FAA16D1068D605969A16D55DC2ED1BFB810B9C8452E729173AB06F9201F7C18E4837C908FEDF85C72937BF418CAE426373997B592AFE42BF94ABE7273255FC93955C8431EF2CC81AF73F03472DEB5916FE41BF946BE916FE4DBB60F9FF9511F8366DA4A0B6DDB690B397EE1177EE1177EE16F365F1217C22FFCC22FFCC2DF53825FF8855FF8855FF885BFA70BBFF00BBFF00BBFF00B7F4F257EE1177EE1177EE117FE9E66FCC22FFCC22FFCC22FFC7309845FF8855FF8855FF8857F5FEFA5D5C6DF6B8FDFF88DBF9706BFF11BBFF11BBFF11B7F2F1B7EE337580332833603330FEF25C56FFCC66FFCC66FFCC6DFCBCD434C47E6CB9E7B10BFF11B7F6F05FCC66FFCC66FFCC66FFCBD4DF01BBFF11BBFF11BBFF1CF2D64FCC66FFCC66FFCC66FFCBD7DF0A7577CB43AF8D3C7B66F2DFCC11FFCC11FFCC11FFCBDEDF0077FF0077FF0077FF0F796C41FFCC11FFCC11FFCC1DFDB157FF0077FF007748085C1F756C61FFCC11FFCC11FFCC1DFDB9C4186818487850E43D1D3F3A1BECF799A135C877ED7E1B09FE6316FCDCF276D3ED3C77D5B276DCEF3BFDF3DD7E6DCD58DB5BFEBE7DCDE52FB523FF7EF92AB6B4FEB679BFF791FA9EF3E9E3F563FF7DA357DBCAABFB28FB3F5B5EFE74BFAF86FFD857DBC597FECE3CDFAE59DFAF14EFDFCCDDD58FBD2C7FC6DDF587BB68F2B6BFFEAE382DA5FA120AA5C'

async def async_main(login, password, storename=None):
    result = {} 
    login_ori, acc_num = login, ''
    if '/' in login:
        login, acc_num = login_ori.split('/')
        storename =  storename.replace(re.sub(r'\W', '_', login_ori), re.sub(r'\W', '_', login))  # исправляем storename
    accounts = {}  # словарь хранения данных по аккауттам accounts[accountId]={}
    waitfor = set()
    browser = await pa.launch_browser(storename)

    async def worker(response):
        'Worker вызывается на каждый url который открывается при загрузке страницы (т.е. список тот же что на вкладке сеть в хроме)'
        if response.status != 200:
            return
        # Список окончаний url которые мы будем смотреть, остальные игнорируем
        catch_elements = ['client-api/getProfile', 'client-api/getAccounts', 'client-api/getAccountServicesMainInfo', 'client-api/getAccountBalanceV2']
        for elem in catch_elements:
            if response.request.url.endswith(elem):
                waitfor.difference_update({elem}) # каждый элемент должен пройти хотя бы раз
                logging.info(f'await {response.request.url}')
                try: data = await response.json()
                except: return
        # Если счетов несколько то можем придти несколько раз
        if response.request.url.endswith('client-api/getProfile'):  # # # # # ФИО
            result['UserName'] = f'{data.get("lastName","")} {data.get("name","")} {data.get("middleName","")}'
        if response.request.url.endswith('client-api/getAccounts'):  # # # # # ЛС и accountId
            for elem in data['accounts']:
                accountId = elem['accountId']
                accounts[accountId] = accounts.get(accountId, {})      
                accounts[accountId]['number'] = elem['number']  #  ЛС
        if response.request.url.endswith('client-api/getAccountServicesMainInfo'):  # # # # # fee or TarifPlan
            accountId = json.loads(response.request.postData)['accountId']
            accounts[accountId] = accounts.get(accountId, {})
            accounts[accountId]['TarifPlan'] = ','.join([i['fee'] for i in data['services'].values()])
        if response.request.url.endswith('client-api/getAccountBalanceV2'):  # # # # # Баланс
            accountId = json.loads(response.request.postData)['accountId']
            accounts[accountId] = accounts.get(accountId, {})
            accounts[accountId]['Balance'] = data['balance']/100

    pages = await browser.pages()
    for page in pages[1:]:
        await page.close() # Закрываем остальные страницы, если вдруг открыты
    page = pages[0]  # await browser.newPage()
    page.on("response", worker) # вешаем обработчик на страницы
    await pa.page_goto(page, 'https://lk.rt.ru')

    if await pa.page_evaluate(page, "document.getElementById('root')!=null"):
        logging.info(f'Already login')
    else:
        for cnt in range(20):  # Почему-то иногда с первого раза логон не проскакивает
            if await pa.page_evaluate(page, "document.getElementById('password') !== null"):
                logging.info(f'Login')
                await page.evaluate("document.getElementById('username').value=''")
                await page.type("#username", login, {'delay': 10})
                await page.type("#password", password, {'delay': 10})
                await page.evaluate("document.getElementById('rememberMe').checked=true")
                await asyncio.sleep(1)
                await page.click("#kc-login")
            elif await pa.page_evaluate(page, "document.getElementById('root')!=null"):
                logging.info(f'Logoned')
                break 
            # TODO надо бы еще капчу проверять
            await asyncio.sleep(1)
            if cnt==10:
                await page.reload()
        else:
            logging.error(f'Unknown state')
            raise RuntimeError(f'Unknown state')
    # почему-то иногда застревает явно идем в https://lk.mts.ru/ 
    #await pa.page_goto(page, 'https://lk.mts.ru')
    await pa.do_waitfor(page, waitfor, {'client-api/getProfile', 'client-api/getAccounts', 'client-api/getAccountServicesMainInfo', 'client-api/getAccountBalanceV2'})
    await asyncio.sleep(3)
    logging.info(f'{accounts=}')
    for elem in accounts.values():
        if acc_num == elem.get('number','') or acc_num == '':
            result['Balance'] = elem['Balance']
            if 'TarifPlan' in elem:
                result['TarifPlan'] = elem['TarifPlan'].replace('\u20bd','p')
    logging.info(f'Data ready {result.keys()}')
    await browser.close()
    pa.clear_cache(storename)
    return result


def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    result = {}
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = asyncio.get_event_loop().run_until_complete(async_main(login, password, storename))
    return result    


if __name__ == '__main__':
    print('This is module rostelecom on puppeteer')
