#!/usr/bin/python3
# -*- coding: utf8 -*-
''' пример плагина почти на чистом puppeteer без упрощенной логики '''
import time, re, json, logging, os
import pyppeteeradd

def main(login, password, storename=None):
    result = {} 
    pyppeteeradd.clear_cache(storename)

    pa = pyppeteeradd.BalanceOverPyppeteer(login, password, storename)
    pa.browser_launch()
    # Нажмите кнопку "Демо-доступ" или введите логин demo@saures.ru и пароль demo вручную. 
    pa.page_goto('https://lk.saures.ru/dashboard')

    if pa.page_evaluate("document.getElementById('main-wrapper')!=null"):
        logging.info(f'Already login')
    else:
        for cnt in range(20):  # Почему-то иногда с первого раза логон не проскакивает
            if pa.page_evaluate("document.querySelector('form input[type=password]') !== null"):
                logging.info(f'Login')
                pa.page_type("#email", login, {'delay': 10})
                pa.page_type("#password", password, {'delay': 10})
                pa.sleep(1)
                # await page.click("form button[type=submit]") # почему-то так не заработало
                pa.page_evaluate("document.querySelector('form button[type=submit]').click()")
            elif pa.page_evaluate("document.getElementById('main-wrapper')!=null"):
                logging.info(f'Logoned')
                break 
            pa.sleep(1)
            if cnt==10:
                pa.page_reload('unclear: logged in or not')
        else:
            logging.error(f'Unknown state')
            raise RuntimeError(f'Unknown state')

    # Ждем появления информации
    for cnt in range(20):
        pa.sleep(1)
        if pa.page_evaluate("document.querySelector('.sensor-5 .d-inline')!=null"):
            break
    else:
        logging.error(f'Not found BALANCE')
        raise RuntimeError(f'Not found BALANCE')
    
    baltext = pa.page_evaluate("document.querySelector('.sensor-5 .d-inline').innerText")
    baltext = re.sub(r'[^\d|,|.-]','',baltext).replace(',', '.')
    result['Balance'] = float(baltext)

    block_status = pa.page_evaluate("document.querySelector('.sensor-9 .d-inline').innerText")
    if block_status is not None:
        result['BlockStatus'] = block_status
    else:
        logging.info(f'Not found BlockStatus')

    logging.debug(f'Data ready {result.keys()}')
    pa.browser_close()
    pyppeteeradd.clear_cache(storename)
    return result


def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    result = {}
    result = main(login, password, storename)
    return result    


if __name__ == '__main__':
    print('This is module test3 for test chrome on puppeteer')
