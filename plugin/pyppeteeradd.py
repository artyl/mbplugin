#!/usr/bin/python3
# -*- coding: utf8 -*-
import asyncio, time, re, json, subprocess, logging, shutil, os, sys, traceback
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

async def launch_browser(storename, response_worker=None):
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
    if response_worker is not None:
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

async def page_evaluate(page, eval_string, default=None):
    'Безопасный eval - не падает при ошибке а возвращает None'
    try:
        if eval_string == '': 
            return default
        eval_string_log = eval_string if len(eval_string)<200 else eval_string[:100]+'...'+eval_string[-100:]
        if 'password' in eval_string:
            eval_string_log = eval_string.split('password')[0]+'password ....'            
        logging.info(f'page.eval: {repr(eval_string_log)}')            
        res = await page.evaluate(eval_string)
        return res
    except Exception:
        logging.info(f'page.eval fail: {repr(eval_string_log)}')
        exception_text = f'Ошибка page.eval: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.info(exception_text)        
        return default

async def page_reload(page, reason=''):
    logging.info(f'page.reload {reason}')
    await page.reload()

async def page_goto(page, url):
    logging.info(f'page.goto {url}')
    try:
        await page.goto(url, {'timeout': 20000})
    except pyppeteer.errors.TimeoutError:
        logging.info(f'page.goto timeout')
    await asyncio.sleep(3)  # Ждем 3 секунды 
    if await page_evaluate(page, 'setTimeout(function(){},1)<2'):
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
    for countdown in range(wait_loop):  
        if len(waitfor) == 0: break
        logging.debug(f'Wait {waitfor} {countdown}')
        await asyncio.sleep(1) 
        if countdown == wait_and_reload:
            # так и не дождались - пробуем перезагрузить и еще подождать
            await page_reload(page, 'Not all page were received (do_waitfor)')
    logging.info(f'End wait {waitfor}')        


class balance_over_puppeteer():
    '''Основная часть общих действий вынесена сюда см mosenergosbyt для примера использования '''
    def __init__(self,  login, password, storename=None, wait_loop=30, wait_and_reload=10):
        self.wait_loop = wait_loop  # TODO подобрать параметр
        self.wait_and_reload = wait_and_reload
        self.password = password
        self.login_ori, self.acc_num = login, ''
        self.login = login
        self.storename = storename
        if '/' in login:
            self.login, self.acc_num = self.login_ori.split('/')
            # !!! в storename уже преобразован поэтому чтобы выкинуть из него ненужную часть нужно по ним тоже регуляркой пройтись
            self.storename = self.storename.replace(re.sub(r'\W', '_', self.login_ori), re.sub(r'\W', '_', self.login))  # исправляем storename
        clear_cache(self.storename)
        self.result = {}
        self.responses = {}

    # потом наверно перенесем их совсем сюда, а отдельные прибьем
    async def page_evaluate(self, eval_string, default=None):
        ''' переносим вызов в класс для того чтобы каждый раз не указывать page'''
        return (await page_evaluate(self.page, eval_string, default=None))

    async def page_goto(self, url):
        ''' переносим вызов в класс для того чтобы каждый раз не указывать page'''
        return (await page_goto(self.page, url))

    async def page_reload(self, reason=''):
        ''' переносим вызов в класс для того чтобы каждый раз не указывать page'''
        return (await page_reload(self.page, reason=''))

    async def page_type(self, selector, text, *args, **kwargs):
        'Безопасный type - не падает при ошибке а возвращает None'
        logging.info(f'page.type: {repr(selector)}')
        try:
            if selector != '' and text != '': 
                await self.page.type(selector, text, *args, **kwargs)
        except Exception:
            logging.info(f'page.type fail: {repr(selector)}')

    async def page_click(self, selector, *args, **kwargs):
        'Безопасный click - не падает при ошибке а возвращает None'
        logging.info(f'page.click: {repr(selector)}')
        try:
            if selector != '': 
                await self.page.click(selector, *args, **kwargs)
        except Exception:
            logging.info(f'page.click fail: {repr(selector)}')

    async def page_waitForNavigation(self, *args, **kwargs):
        'Безопасный waitForNavigation - не падает при ошибке а возвращает None'
        logging.info(f'page.waitForNavigation')
        try:
            return await self.page.waitForNavigation({'timeout': 10000})
        except pyppeteer.errors.TimeoutError:   
            logging.info(f'page.waitForNavigation timeout')

    # !!! TODO есть page.waitForSelector - покопать в эту сторону
    async def page_waitForSelector(self, selector, *args, **kwargs):
        'Безопасный type - не падает при ошибке а возвращает None'
        logging.info(f'page.waitForSelector: {repr(selector)}')
        try:
            if selector != '': 
                await self.page.waitForSelector(selector, *args, **kwargs)
        except Exception:
            logging.info(f'page.waitForSelector fail: {repr(selector)}')  

    async def worker(self, response):
        'Worker вызывается на каждый url который открывается при загрузке страницы (т.е. список тот же что на вкладке сеть в хроме)'
        'Проходящие запросы, которые json сохраняем в responses'
        if response.status == 200:
            try:
                data = await response.json()  # Берем только json
            except Exception:
                return
            try:
                post = ''
                if response.request.method == 'POST' and response.request.postData is not None:
                    post = response.request.postData
                self.responses[f'{response.request.method}:{post} URL:{response.request.url}'] = data
            except:
                exception_text = f'Ошибка: {"".join(traceback.format_exception(*sys.exc_info()))}'
                logging.debug(exception_text)

    async def do_logon(self, url,user_selectors={}):
        'Делаем заход в личный кабинет/ проверяем не залогинены ли уже'
        'На вход передаем словарь селекторов и скриптов который перекроет действия по умолчанию'
        'Если какой-то из шагов по умолчанию хотим пропустить, передаем пустую строку'
        # Селекторы и скрипты по умолчанию
        selectors = {'before_login_js': '',
                    'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",
                    'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",
                    'login_clear_js': "document.querySelector('form input[type=text]').value=''",
                    'login_selector': 'form input[type=text]',
                    'password_clear_js': "document.querySelector('form input[type=password]').value=''",
                    'password_selector': 'form input[type=password]',
                    'remember_checker': "document.querySelector('form input[name=remember]').checked==false",
                    'remember_js': "", #document.querySelector('form input[name=remember]').click()",
                    'remember_selector': 'form input[name=remember]',
                    'submit_selector': '',
                    'submit_js': "document.querySelector('form [type=submit]').click()"
        }
        selectors.update(user_selectors)
        await self.page_goto(url)
        # Logon form
        if await self.page_evaluate(selectors['chk_lk_page_js']):
            logging.info(f'Already login')
        else:
            for cnt in range(20):  # Почему-то иногда с первого раза логон не проскакивает
                if await self.page_evaluate(selectors['chk_login_page_js']):
                    logging.info(f'Login')
                    await self.page_evaluate(selectors['before_login_js'])
                    await self.page_evaluate(selectors['login_clear_js'])
                    await self.page_evaluate(selectors['password_clear_js'])
                    await self.page_type(selectors['login_selector'], self.login, {'delay': 10})
                    await self.page_type(selectors['password_selector'], self.password, {'delay': 10})
                    if await self.page_evaluate(selectors['remember_checker'], default=False):
                        await self.page_evaluate(selectors['remember_js'])
                        await self.page_click(selectors['remember_selector'], {'delay': 10})
                    await asyncio.sleep(1)
                    await self.page_click(selectors['submit_selector']) # почему-то так не заработало
                    await self.page_evaluate(selectors['submit_js'])
                elif await self.page_evaluate(selectors['chk_lk_page_js']):
                    logging.info(f'Logoned')
                    break 
                await asyncio.sleep(1)
                if cnt==10:
                    await self.page_reload('unclear: logged in or not')
            else:
                logging.error(f'Unknown state')
                raise RuntimeError(f'Unknown state')

    async def wait_params(self, params, url='', save_to_result=True):
        ''' Переходим по url и ждем параметры
        ---
        url если url пустой то не переходим а просто производим действия на текущей странице
        --- 
        params - список словарей вида 
        {'name':'text', 'url_tag':['text1','text2'], 'pformula':'text'} - ожидается приход json с урлом содержащим все строки из  url_tag из этого json через python eval возьмем tag_pformula
        либо 
        {'name':'text', 'url_tag':['text'], 'jsformula':'text'} - ожидается приход json с урлом содержащим url_tag из этого json через js eval возьмем tag_jformula
        либо
        {'name':'text', 'url_tag':[], 'jsformula':'text'} - url_tag - пустой список или не указан, на странице выполняется js из jsformula
        результат во всех случаях записывается с именем name в результирующий словарь 
        ---
        save_to_result=True то записываем их в итоговый словарь результатов (self.result)
        и также результаты возвращаем в словаре (return result) 
        ВАЖНО
        Из того что уже вылезло - если возникают проблемы со сложным eval надо завернуть его в ()=>{...;return ...}
        '''
        result = {}
        if len([i for i in params if 'name' not in i])>0:
            error_msg = f'Not all params have name param: {params}'
            logging.error(error_msg)
            raise RuntimeError(error_msg)
        if url != '':  # Если указан url то сначала переходим на него
            await self.page_goto(url)
            await self.page_waitForNavigation()
        for countdown in range(self.wait_loop): 
            await asyncio.sleep(1)
            for param in params:
                if param.get('url_tag', []) != []:  # Ищем в загруженных страницах
                    response_result_ = [v for k,v in self.responses.items() if [i for i in param['url_tag'] if i not in k]==[]]
                    if len(response_result_)>0:
                        response_result = response_result_[0]
                        if param.get('pformula','') != '':
                            result[param['name']] = eval(param['pformula'], {'data':response_result})
                        if param.get('jsformula', '') != '':
                            result[param['name']] = await self.page_evaluate(f"()=>{{data={json.dumps(response_result)};return {param['jsformula']};}}")
                else:  # Ищем на самой странице - запускаем js 
                    result[param['name']] = await self.page_evaluate(param['jsformula'])
            if {i['name'] for i in params} == set(result):
                break  # выходим если проверять все получили
            if countdown == self.wait_and_reload:
                # так и не дождались - пробуем перезагрузить и еще подождать
                await self.page_reload('Data not received')        
        else:  # время вышло а получено не все - больше не ждем 
            no_receved_keys = {i['name'] for i in params} - set(result)
            logging.error(f'Not found all param on {url}: {",".join(no_receved_keys)}')
        if save_to_result:
            self.result.update(result)
        return result

    async def _async_main(self):
        self.browser, self.page = await launch_browser(self.storename, self.worker)
        await self.async_main()  # !!! CALL async_main
        logging.debug(f'Data ready {self.result.keys()}')
        await self.browser.close()
        clear_cache(self.storename)
        return self.result

    async def async_main(self):
        pass

    def main(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop().run_until_complete(self._async_main())
        return self.result   
