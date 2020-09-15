#!/usr/bin/python3
# -*- coding: utf8 -*-
import asyncio, time, re, json, subprocess, logging, shutil, os, traceback
import win32gui, win32process, psutil
import pyppeteer  # PYthon puPPETEER
#import pprint; pp = pprint.PrettyPrinter(indent=4).pprint
import store, settings
import pyppeteeradd as pa

icon = '789c73f235636600033320d600620128666490804800e58ff041300cfc270b6cdc7868ca94ddab56edbe73e7fe9b376fbe7dfbf6ffffbfffffffe050feb7b0f0a4b0f00d46c663f6f6b3d7ae5d76e8e0be1933d6a4a71f6e6db9f8f1e3574c0d9b363fd0d179cec7f7c9d0f0cea74f3f7ffefc9e9aba8681e1aab4f4e5f7efbf61aa7ffbf68bb3f3556dedff7c7c5f8d8ceeb9b9df97963ec3c0f03839f921d861589c545171c5d4ec9b98d87f2eeeb79c5c4f98989f31333f5ebaf439d0b28f1f3ffefefd1b4dc3b66d0fcccc9ec8c9ff4f4a7ed3da7a9895f59c84e4e3a74fbfb7b6362b28286cddba154dfdebd79f6c6d2fe8e9ffb7b27e1f11b18299e58e97d7a37ffffe6766663033332f5bb60c5b285d56d7fc262bff5944643913f393cecee740d1c2c2422121a1952b5762fa61cb9687d2324fb474fe494bbfe3e37f72f0e0cbe7cf9f151515aaa8a8ac59b30653fdbb779f7574af2a2aff5756fd6f6cf2ece1c31701017e76b6b67676766bd7aec51a4a25a55784843f2928fdacaa7afefdfb97acac2c3737773f3f7f1ceaff7ffaf463dfbe77376e7cf9f1039418debe7d5b5e5eeee7e7b77af56aacea31c1cd9b3767cf9e7dedda3522d5530800550a6598'

async def async_main(login, password, storename=None):
    result = {} 
    pa.clear_cache(storename)

    async def worker(response):
        return

    browser, page = await pa.launch_browser(storename, worker)
    await pa.page_goto(page, 'https://my.a1.by/work.html')

    if await pa.page_evaluate(page, "document.getElementById('ext-gen2')!=null"):
        logging.info(f'Already login')
    else:
        for cnt in range(20):  # Почему-то иногда с первого раза логон не проскакивает
            if await pa.page_evaluate(page, "document.querySelector('form input[type=password]') !== null"):
                logging.info(f'Login')
                await page.evaluate("document.getElementById('itelephone_new').value=''")
                await page.type("#itelephone_new", login[-9:], {'delay': 10})
                await page.type("#ipassword", password, {'delay': 10})
                await asyncio.sleep(1)
                # await page.click("form button[type=submit]") # почему-то так не заработало
                await pa.page_evaluate(page, "document.querySelector('form button[type=submit]').click()")
            elif await pa.page_evaluate(page, "document.getElementById('ext-gen2')!=null"):
                logging.info(f'Logoned')
                break 
            await asyncio.sleep(1)
            if cnt==10:
                await pa.page_reload(page, 'unclear: logged in or not')
        else:
            logging.error(f'Unknown state')
            raise RuntimeError(f'Unknown state')

    # Кликаем на Персональная информация
    for cnt in range(20):
        await asyncio.sleep(1)
        if await pa.page_evaluate(page, "document.getElementById('_root/USER_INFO')!=null"):
            # await page.click('#_root/USER_INFO') # почему-то так не заработало
            await pa.page_evaluate(page, "document.getElementById('_root/USER_INFO').click()")
            break
        else:
            if await pa.page_evaluate(page, "document.getElementById('_root/PERSONAL_INFO')!=null"):
               await pa.page_evaluate(page, "document.getElementById('_root/PERSONAL_INFO').click()")
               break

            else:
                logging.error(f'Not found _root/USER_INFO||PERSONAL_INFO')
                raise RuntimeError(f'Not found _root/USER_INFO||PERSONAL_INFO')
                break

    # Ждем появления информации
    for cnt in range(20):
        await asyncio.sleep(1)
        if await pa.page_evaluate(page, "document.getElementById('BALANCE')!=null"):
            break
        if await pa.page_evaluate(page, "document.getElementById('Balance')!=null"):
            break
    else:
        logging.error(f'Not found BALANCE')
        raise RuntimeError(f'Not found BALANCE')
    
    baltext = await pa.page_evaluate(page, "document.getElementById('BALANCE').innerText")
    if (baltext is None):
        baltext = await pa.page_evaluate(page, "document.getElementById('Balance').innerText")


    baltext = baltext.replace('\u2012','-').replace('коп.','')
    baltext = re.sub('[^\d|,|.-]','',baltext).replace(',','.')
    result['Balance'] = float(baltext)


    Tariff1 = "";
    Tariff2 = "";

    try:
        Tariff1 = await pa.page_evaluate(page, "document.getElementById('TRPL').innerText")
        Tariff2 = await pa.page_evaluate(page, "document.getElementById('TPLAN').innerText")
    except:
        logging.info(f'Not found TarifPlan')

    logging.info(f'%s', Tariff1)
    logging.info(f'%s', Tariff2)

    if (Tariff1 is not None):
        result['TarifPlan'] = Tariff1;
    elif (Tariff2 is not None):
        result['TarifPlan'] = Tariff2;
    else: 
        logging.info(f'Not found TarifPlan');
    


    BlockStatus1 = "";
    BlockStatus2 = "";

    try:
        BlockStatus1 = await pa.page_evaluate(page, "document.getElementById('STATUS').innerText")
        BlockStatus2 = await pa.page_evaluate(page, "document.getElementById('CUR_STATUS').innerText")
    except:
        logging.info(f'Not found BlockStatus')

    if (BlockStatus1 is not None):
        result['BlockStatus'] = BlockStatus1;
    elif (BlockStatus2 is not None):
        result['BlockStatus'] = BlockStatus2;
    else: 
        logging.info(f'Not found BlockStatus2');
    

    try:
        result['UserName'] = await pa.page_evaluate(page, "document.getElementById('NAME').innerText")
    except:
        logging.info(f'Not found UserName')

    try:
        result['Expired'] = await pa.page_evaluate(page, "document.getElementById('DEN').innerText")
    except:
        logging.info(f'Not found Expired')


    logging.debug(f'Data ready {result.keys()}')
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
