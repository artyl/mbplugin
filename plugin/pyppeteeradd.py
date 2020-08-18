#!/usr/bin/python3
# -*- coding: utf8 -*-
import asyncio, time, re, subprocess, logging, shutil, os, traceback
import win32gui, win32process, psutil
import pyppeteer  # PYthon puPPETEER
#import pprint; pp = pprint.PrettyPrinter(indent=4).pprint
import store, settings


def hide_chrome(hide=True):
    'Прячем или показываем окно хрома'
    def enumWindowFunc(hwnd, windowList):
        """ win32gui.EnumWindows() callback """
        text = win32gui.GetWindowText(hwnd)
        className = win32gui.GetClassName(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if text.find("Chrome")>=0 and 'remote-debugging-port' in ''.join(psutil.Process(pid).cmdline()):
            windowList.append((hwnd, text, className))
    myWindows = []
    # enumerate thru all top windows and get windows which are ours
    win32gui.EnumWindows(enumWindowFunc, myWindows)
    for hwnd, text, className in myWindows:
        _, _ = text, className  # dummy pylint
        win32gui.ShowWindow(hwnd, not hide)  # True-Show, False-Hide
        if hide:
            win32gui.MoveWindow(hwnd, -1000, -1000, 0, 0, True) # У скрытого окна бывают доп окна которые вылезают на экран
        else:
            win32gui.MoveWindow(hwnd, 0, 0, 1000, 1000, True) # Возвращаем нормальные координаты

async def launch_browser(storename, response_worker):
    hide_chrome_flag = str(store.options('show_chrome')) == '0' and store.options('logginglevel') != 'DEBUG'
    storefolder = store.options('storefolder')
    user_data_dir = os.path.join(storefolder,'puppeteer')
    profile_directory = storename
    chrome_executable_path = store.options('chrome_executable_path')
    if not os.path.exists(chrome_executable_path):
        chrome_paths = [p for p in settings.chrome_executable_path_alternate if os.path.exists(p)]
        if len(chrome_paths) == 0:
            logging.error('Chrome.exe not found')
            raise RuntimeError(f'Chrome.exe not found')
        chrome_executable_path = chrome_paths[0]
    kill_chrome()  # Превинтивно убиваем все наши хромы, чтобы не появлялось кучи зависших
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
                 '--disable-gpu', 
                 "--window-position=-2000,-2000" if hide_chrome_flag else "--window-position=1,1"],
    })
    if hide_chrome_flag:
        hide_chrome()

    pages = await browser.pages()
    for page in pages[1:]:
        await page.close() # Закрываем остальные страницы, если вдруг открыты
    page = pages[0]  # await browser.newPage()
    page.on("response", response_worker) # вешаем обработчик на страницы        
    return browser, page

def kill_chrome():
    'Киляем дебажный хром если вдруг какой-то висит'
    for p in psutil.process_iter():
        try:
            if p.name()=='chrome.exe' and 'remote-debugging-port' in ''.join(p.cmdline()):
                p.kill()    
        except Exception:
            pass


def clear_cache(storename):
    'Очищаем папку с кэшем профиля чтобы не разрастался'
    #return  # С такой очисткой оказывается связаны наши проблемы с загрузкой
    storefolder = store.options('storefolder')
    profilepath = os.path.abspath(os.path.join(storefolder, 'puppeteer', storename))  
    shutil.rmtree(os.path.join(profilepath, 'Cache'), ignore_errors=True)
    shutil.rmtree(os.path.join(profilepath, 'Code Cache'), ignore_errors=True)

def delete_profile(storename):
    'Удаляем профиль'
    kill_chrome()  # Перед удалением киляем хром
    storefolder = store.options('storefolder')
    profilepath = os.path.abspath(os.path.join(storefolder, 'puppeteer', storename))    
    shutil.rmtree(profilepath)

async def page_evaluate(page, eval_string):
    'Безопасный eval - не падает при ошибке а возвращает None'
    try:
        res = await page.evaluate(eval_string)
        return res
    except Exception:
        if 'password' in eval_string:
            eval_string = eval_string.split('eval_string')[0]+'password ....'
        logging.info(f'eval fail: {eval_string}')
        return None


async def page_reload(page, reason=''):
    logging.info(f'RELOAD {reason}')
    await page.reload()

async def page_goto(page, url):
    logging.info(f'goto {url}')
    try:
        await page.goto(url, {'timeout': 20000})
    except pyppeteer.errors.TimeoutError:
        logging.info(f'page.goto timeout')
    await asyncio.sleep(3)  # Ждем 3 секунды 
    if page_evaluate(page, 'setTimeout(function(){},1)<2'):
        await page_reload(page, 'No timers on page (page_goto)')  # если на странице не появились таймеры - reload
        await asyncio.sleep(3)  # Ждем еще 3 секунды 
    #try:
    #    await page.waitForNavigation({'timeout': 20000})
    #except pyppeteer.errors.TimeoutError:   
    #    logging.info(f'waitForNavigation timeout')


async def do_waitfor(page, waitfor, tokens, wait_and_reload=10, wait_loop=30):
    ''' Ждем пока прогрузятся все интересующие страницы с данными
    wait_and_reload секунд ждем потом перезагружаем страницу
    wait_loop секунд ждем и уходим '''
    waitfor.update(tokens)
    logging.info(f'Start wait {waitfor}')
    for countdown in range(wait_loop):  # TODO подобрать параметр
        if len(waitfor) == 0: break
        logging.debug(f'Wait {waitfor} {countdown}')
        await asyncio.sleep(1) 
        if countdown == wait_and_reload:
            # так и не дождались - пробуем перезагрузить и еще подождать
            await page_reload(page, 'Not all page were received (do_waitfor)')
    logging.info(f'End wait {waitfor}')        