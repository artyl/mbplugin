#!/usr/bin/python3
# -*- coding: utf8 -*-
import asyncio, time, re, json, subprocess, logging, shutil, os, sys, traceback
import win32gui, win32process, psutil
import pyppeteer  # PYthon puPPETEER
#import pprint; pp = pprint.PrettyPrinter(indent=4).pprint
import store, settings

# Какой бы ни был режим в mbplugin для всех сторониих модулей отключаем расширенное логирование
# иначе в лог польется все тоннами
[logging.getLogger(name).setLevel(logging.ERROR) for name in logging.root.manager.loggerDict]  # pylint: disable=no-member

# Селекторы и скрипты по умолчанию для формы логона
default_logon_selectors = {
            'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",  # true если мы в личном кабинете
            'chk_login_page_js': "document.querySelector('form input[type=password]') !== null",  # true если мы в окне логина
            'before_login_js': '',  # Команда которую надо выполнить перед вводом логина
            'login_clear_js': "document.querySelector('form input[type=text]').value=''",  # команда для очистки поля логина
            'login_selector': 'form input[type=text]',   # селектор поля ввода логина
            'chk_submit_after_login_js': "",  # проверка нужен ли submit после логина
            'submit_after_login_js': "document.querySelector('form [type=submit]').click()",  # Если после ввода логина нужно нажать submit через js
            'submit_after_login_selector': "",  # или через селектор
            'password_clear_js': "document.querySelector('form input[type=password]').value=''",  # команда на очистку поля пароля
            'password_selector': 'form input[type=password]',  # селектор для поля пароля
            'remember_checker': "",  # "document.querySelector('form input[name=remember]').checked==false",  # Проверка что флаг remember me не выставлен
            'remember_js': "",  # "document.querySelector('form input[name=remember]').click()",  # js для выставления remember me
            'remember_selector': "",  # 'form input[name=remember]',  # селектор для выставления remember me (не указывайте оба сразу а то может кликнуть два раза)
            'captcha_checker': "",  # проверка что на странице капча у MTS - document.querySelector("div[id=captcha-wrapper]")!=null
            'submit_selector': '',  # селектор для нажатия на финальный submit
            'submit_js': "document.querySelector('form [type=submit]').click()",  # js для нажатия на финальный submit
            'captcha_focus': '',  # перевод фокуса на поле капчи
            'pause_press_submit': '1',  # Пауза перед нажатием submit не меньше 1
}


def safe_run_decorator(func):
    'Обертка для функций, выполнение которых не влияет на результат, чтобы при падении они не портили остальное'
    def wrapper(*args, **kwargs):
        # Готовим строку для лога
        default = kwargs.pop('default', None)
        log_string = f'call: {getattr(func,"__name__","")}({", ".join(map(repr,args))}, {", ".join([f"{k}={repr(v)}" for k,v in kwargs.items()])})'
        if str(store.options('log_full_eval_string')) == '0':
            log_string = log_string if len(log_string) < 200 else log_string[:100]+'...'+log_string[-100:]
            if 'password' in log_string:
                log_string = log_string.split('password')[0]+'password ....'
        try:
            res = func(*args, **kwargs)  # pylint: disable=not-callable
            logging.info(f'{log_string} OK')
            return res
        except Exception:
            logging.info(f'{log_string} fail: {"".join(traceback.format_exception(*sys.exc_info()))}')
            return default
    return wrapper    

def safe_run(func, *args, **kwargs):
    'Безопасный запуск функции'
    try:
        res = func(*args, **kwargs)  # CALL
        return res
    except:
        log_string = f'{func.__name__}({", ".join(map(repr,args))}, {", ".join([f"{k}={repr(v)}" for k,v in kwargs.items()])})'
        logging.info(f'call {log_string} fail: {"".join(traceback.format_exception(*sys.exc_info()))}')

@safe_run_decorator
def hide_chrome(hide=True, foreground=False):
    'Прячем или показываем окно хрома'
    def enumWindowFunc(hwnd, windowList):
        """ win32gui.EnumWindows() callback """
        text = win32gui.GetWindowText(hwnd).lower()
        className = win32gui.GetClassName(hwnd).lower()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:  #  ??? text.lower().find('chrome')>=0
            if (text != '' and 'remote-debugging-port' in ''.join(psutil.Process(pid).cmdline())
            and not text.startswith('msct') and not text.startswith('default') and 'восстановить' not in text):
                windowList.append((hwnd, text, className))
                logging.debug(f'enumWindowFunc:{text=}, {className=}')
        except Exception:
            pass
    myWindows = []
    # enumerate thru all top windows and get windows which are ours
    win32gui.EnumWindows(enumWindowFunc, myWindows)
    for hwnd, text, className in myWindows:
        _, _ = text, className  # dummy pylint
        win32gui.ShowWindow(hwnd, not hide)  # True-Show, False-Hide
        if hide:
            safe_run(win32gui.MoveWindow, hwnd, -1000, -1000, -100, -200, True) # У скрытого окна бывают доп окна которые вылезают на экран
        else:
            safe_run(win32gui.MoveWindow, hwnd, 80, 80, 980, 880, True) # Возвращаем нормальные координаты
            if foreground:
                safe_run(win32gui.SetForegroundWindow, hwnd)

@safe_run_decorator
def kill_chrome():
    '''Киляем дебажный хром если вдруг какой-то висит, т.к. народ умудряется запускать не только хром, то имя exe возьмем из пути '''
    chrome_executable_path = store.options('chrome_executable_path')
    pname = os.path.split(chrome_executable_path)[-1].lower()
    for p in psutil.process_iter():
        try:
            if p.name().lower()==pname and 'remote-debugging-port' in ''.join(p.cmdline()):
                p.kill()    
        except Exception:
            pass

@safe_run_decorator
def fix_crash_banner(storename):
    'Исправляем Preferences чтобы убрать баннер Работа Chrome была завершена некорректно'
    storefolder = store.options('storefolder')
    fn_pref = os.path.abspath(os.path.join(storefolder, 'puppeteer', storename, 'Preferences'))
    with open(fn_pref, encoding='utf8') as f:
        data = f.read()
    data1 = data.replace('"exit_type":"Crashed"','"exit_type":"Normal"').replace('"exited_cleanly":false','"exited_cleanly":true')
    if data != data1:
        logging.info(f'Fix chrome crash banner')
        open(fn_pref, encoding='utf8', mode='w').write(data1)        

@safe_run_decorator
def clear_cache(storename):
    'Очищаем папку с кэшем профиля чтобы не разрастался'
    #return  # С такой очисткой оказывается связаны наши проблемы с загрузкой
    storefolder = store.options('storefolder')
    profilepath = os.path.abspath(os.path.join(storefolder, 'puppeteer', storename))  
    shutil.rmtree(os.path.join(profilepath, 'Cache'), ignore_errors=True)
    shutil.rmtree(os.path.join(profilepath, 'Code Cache'), ignore_errors=True)
    shutil.rmtree(os.path.join(profilepath, 'Service Worker', 'CacheStorage'), ignore_errors=True)

@safe_run_decorator
def delete_profile(storename):
    'Удаляем профиль'
    kill_chrome()  # Перед удалением киляем хром
    storefolder = store.options('storefolder')
    profilepath = os.path.abspath(os.path.join(storefolder, 'puppeteer', storename))    
    shutil.rmtree(profilepath)

class balance_over_puppeteer():
    '''Основная часть общих действий вынесена сюда см mosenergosbyt для примера использования '''

    def async_check_browser_opened_decorator(func):  # pylint: disable=no-self-argument
        'Проверка на закрытый браузер, если браузера нет пишем в лог и падаем'
        async def wrapper(self, *args, **kwargs):
            if self.browser_open:
                res = await func(self, *args, **kwargs)  # pylint: disable=not-callable
                return res
            else:
                logging.error(f'Browser was not open')
                raise RuntimeError(f'Browser was not open')
        return wrapper

    def async_safe_run_with_log_decorator(func):  # pylint: disable=no-self-argument
        '''await Декоратор для безопасного запуска функции не падает в случае ошибки, а пишет в лог и возвращяет Null
        параметры предназначенные декоратору, и не передаются в вызываемую функцию:
        default: возвращаемое в случае ошибки значение'''
        async def wrapper(self, *args, **kwargs):
            default = kwargs.pop('default', None)
            if len(args) > 0 and args[0] == '':
                return default            
            # Готовим строку для лога
            log_string = f'call: {getattr(func,"__name__","")}({", ".join(map(repr,args))}, {", ".join([f"{k}={repr(v)}" for k,v in kwargs.items()])})'
            if str(store.options('log_full_eval_string')) == '0':
                log_string = log_string if len(log_string) < 200 else log_string[:100]+'...'+log_string[-100:]
                if 'password' in log_string:
                    log_string = log_string.split('password')[0]+'password ....'
            log_string = log_string.encode('cp1251', errors='ignore').decode('cp1251', errors='ignore')  # Убираем всякую хрень
            try:
                res = await func(self, *args, **kwargs)  # pylint: disable=not-callable
                logging.info(f'{log_string} OK')
                return res
            except Exception:
                logging.info(f'{log_string} fail: {"".join(traceback.format_exception(*sys.exc_info()))}')
                return default
        return wrapper

    def __init__(self,  login, password, storename=None, wait_loop=30, wait_and_reload=10, login_attempt=1, login_url=None, user_selectors=None):
        'Передаем стандартно login, password, storename'
        'Дополнительно'
        'wait_loop=30 - Сколько секунд ждать появления информации на странице'
        'wait_and_reload=10 - Сколько секунд ждать, после чего перезагрузить страницу'
        'login_attempt=1 - Количество попыток логона' 
        'login_url, user_selectors - можно передать параметры для логона при создании класса'
        self.browser, self.page = None, None  # откроем браузер - заполним
        self.browser_open = True  # флаг что браузер работает
        self.wait_loop = wait_loop  # TODO подобрать параметр
        self.login_attempt = login_attempt
        self.wait_and_reload = wait_and_reload
        self.password = password
        self.login_ori, self.acc_num = login, ''
        self.login = login
        self.storename = storename
        self.login_url = login_url
        self.user_selectors = user_selectors
        if '/' in login:
            self.login, self.acc_num = self.login_ori.split('/')
            # !!! в storename уже преобразован поэтому чтобы выкинуть из него ненужную часть нужно по ним тоже регуляркой пройтись
            self.storename = self.storename.replace(re.sub(r'\W', '_', self.login_ori), re.sub(r'\W', '_', self.login))  # исправляем storename
        kill_chrome()  # Превинтивно убиваем все наши хромы, чтобы не появлялось кучи зависших
        clear_cache(self.storename)
        self.result = {}
        self.responses = {}

    async def response_worker(self, response):
        'Response Worker вызывается на каждый url который открывается при загрузке страницы (т.е. список тот же что на вкладке сеть в хроме)'
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
                self.responses[f'{response.request.method}:{post} URL:{response.request.url}$'] = data
                # TODO Сделать какой-нибудь механизм для поиска по загруженным страницам
                # txt = await response.text()
                # if '2336' in txt:
                #    logging.info(f'2336 in {response.request.url}')
            except:
                exception_text = f'Ошибка: {"".join(traceback.format_exception(*sys.exc_info()))}'
                logging.debug(exception_text)

    async def disconnected_worker(self):
        'disconnected_worker вызывается когда закрыли браузер'
        logging.info(f'Browser was closed')
        self.browser_open = False  # выставляем флаг

    async def launch_browser(self):
        hide_chrome_flag = str(store.options('show_chrome')) == '0' and store.options('logginglevel') != 'DEBUG'
        storefolder = store.options('storefolder')
        user_data_dir = os.path.join(storefolder,'puppeteer')
        profile_directory = self.storename
        chrome_executable_path = store.options('chrome_executable_path')
        if not os.path.exists(chrome_executable_path):
            chrome_paths = [p for p in settings.chrome_executable_path_alternate if os.path.exists(p)]
            if len(chrome_paths) == 0:
                logging.error('Chrome.exe not found')
                raise RuntimeError(f'Chrome.exe not found')
            chrome_executable_path = chrome_paths[0]
        logging.info(f'Launch chrome from {chrome_executable_path}')
        launch_config = {
            'headless': False,
            'ignoreHTTPSErrors': True,
            'defaultViewport': None,
            'handleSIGINT':False,  # need for threading (https://stackoverflow.com/questions/53679905)
            'handleSIGTERM':False,  
            'handleSIGHUP':False,
            # TODO хранить параметр в ini
            'executablePath': chrome_executable_path,
            'args': [f"--user-data-dir={os.path.abspath(user_data_dir)}", f"--profile-directory={profile_directory}",
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
                    "--window-position=-2000,-2000" if hide_chrome_flag else "--window-position=80,80",
                    "--window-size=800,900"],
        }
        if store.options('proxy_server').strip() != '':
            launch_config['args'].append(f'--proxy-server={store.options("proxy_server").strip()}')
        fix_crash_banner(self.storename)
        self.browser = await pyppeteer.launch(launch_config)
        if hide_chrome_flag:
            hide_chrome()
        pages = await self.browser.pages()
        for pg in pages[1:]:
            await pg.close() # Закрываем остальные страницы, если вдруг открыты
        self.page = pages[0]  # await browser.newPage()
        if self.response_worker is not None:
            self.page.on("response", self.response_worker) # вешаем обработчик на страницы
        if self.disconnected_worker is not None:
            self.browser.on("disconnected", self.disconnected_worker) # вешаем обработчик закрытие браузера

    @async_check_browser_opened_decorator
    @async_safe_run_with_log_decorator
    async def page_evaluate(self, eval_string, default=None):
        ''' переносим вызов evaluate в класс для того чтобы каждый раз не указывать page и обернуть декораторами'''
        return await self.page.evaluate(eval_string)

    @async_check_browser_opened_decorator
    @async_safe_run_with_log_decorator
    async def page_goto(self, url):
        ''' переносим вызов goto в класс для того чтобы каждый раз не указывать page и обернуть декораторами'''
        try:
            return await self.page.goto(url, {'timeout': 10000})
        except pyppeteer.errors.TimeoutError:
            logging.info(f'goto timeout')        

    @async_check_browser_opened_decorator
    @async_safe_run_with_log_decorator
    async def page_reload(self, reason=''):
        ''' переносим вызов reload в класс для того чтобы каждый раз не указывать page'''
        return await self.page.reload()

    @async_check_browser_opened_decorator
    @async_safe_run_with_log_decorator
    async def page_type(self, selector, text, *args, **kwargs):
        ''' переносим вызов type в класс для того чтобы каждый раз не указывать page'''
        if selector != '' and text != '': 
            return await self.page.type(selector, text, *args, **kwargs)

    @async_check_browser_opened_decorator
    @async_safe_run_with_log_decorator    
    async def page_click(self, selector, *args, **kwargs):
        ''' переносим вызов click в класс для того чтобы каждый раз не указывать page'''
        return await self.page.click(selector, *args, **kwargs)

    @async_check_browser_opened_decorator
    @async_safe_run_with_log_decorator
    async def page_waitForNavigation(self):
        ''' переносим вызов waitForNavigation в класс для того чтобы каждый раз не указывать page'''
        try:
            return await self.page.waitForNavigation({'timeout': 10000})
        except pyppeteer.errors.TimeoutError:
            logging.info(f'waitForNavigation timeout')

    # !!! TODO есть page.waitForSelector - покопать в эту сторону
    @async_check_browser_opened_decorator
    @async_safe_run_with_log_decorator
    async def page_waitForSelector(self, selector, *args, **kwargs):
        ''' переносим вызов waitForSelector в класс для того чтобы каждый раз не указывать page'''
        return await self.page.waitForSelector(selector, {'timeout': 10000})

    @async_check_browser_opened_decorator
    async def check_logon_selectors(self):
        selectors = default_logon_selectors.copy()
        login_url = self.login_url
        user_selectors = self.user_selectors
        assert set(user_selectors)-set(selectors) == set(), f'Не все ключи из user_selectors есть в selectors. Возможна опечатка, проверьте {set(user_selectors)-set(selectors)}'
        selectors.update(user_selectors)
        # TODO fix for submit_js -> chk_submit_js
        selectors['chk_submit_js'] = selectors['submit_js'].replace('.click()','!== null')
        print(f'{login_url=}')
        if login_url != '':
            await self.page_goto(login_url)
        await self.page_waitForNavigation()
        await asyncio.sleep(1)
        for sel in ['chk_login_page_js', 'login_clear_js', 'password_clear_js', 'chk_submit_js']:
            if selectors[sel] !='':
                print(f'Check {selectors[sel]}')
                eval_res = await self.page_evaluate(selectors[sel])
                if sel.startswith('chk_'):
                    assert eval_res == True , f'Bad result for js:{sel}:{selectors[sel]}'
                else:
                    assert eval_res == '' , f'Bad result for js:{sel}:{selectors[sel]}'
        for sel in ['login_selector', 'password_selector', 'submit_selector']:
            if selectors[sel] !='':
                print(f'Check {selectors[sel]}')
                assert await self.page_evaluate(f"document.querySelector('{selectors['login_selector']}') !== null")==True, f'Not found on page:{sel}:{selectors[sel]}'

    @async_check_browser_opened_decorator
    async def do_logon(self, url=None, user_selectors=None):
        'Делаем заход в личный кабинет/ проверяем не залогинены ли уже'
        'На вход передаем словарь селекторов и скриптов который перекроет действия по умолчанию'
        'Если какой-то из шагов по умолчанию хотим пропустить, передаем пустую строку'
        'Смотрите актуальное описание напротив параметров в коментариях'
        'Чтобы избежать ошибок - копируйте названия параметров'
        selectors = default_logon_selectors.copy()
        if url is None:
            url = self.login_url
        if user_selectors is None:
            user_selectors = self.user_selectors if user_selectors is not None else {}
        # проверяем что все поля из user_selectors есть в селектор (если не так то скорее всего опечатка и надо сигналить)
        if set(user_selectors)-set(selectors) != set():
            logging.error(f'Не все ключи из user_selectors есть в selectors. Возможна опечатка, проверьте {set(user_selectors)-set(selectors)}')
        selectors.update(user_selectors)
        if url is not None:  # Иногда мы должны сложным путем попасть на страницу - тогда указываем пустой url
            await self.page_goto(url)
        await self.page_waitForNavigation()
        await asyncio.sleep(1)
        if not await self.page_evaluate(selectors['chk_lk_page_js']) and not await self.page_evaluate(selectors['chk_login_page_js']):
            # Мы не в личном кабинете и не на странице логона - попробуем обновить страницу
            await self.page_reload('Not open login page')
            await asyncio.sleep(10)
        # Logon form
        if await self.page_evaluate(selectors['chk_lk_page_js']):
            logging.info(f'Already login')
        else:
            # Почему-то иногда с первого раза логон не проскакивает, тогда можно задать несколько login_attempt
            for cnt in range(self.login_attempt):
                if await self.page_evaluate(selectors['chk_login_page_js']):
                    logging.info(f'Login')
                    await self.page_evaluate(selectors['before_login_js'])  # Если задано какое-то действие перед логином - выполняем
                    await self.page_waitForSelector(selectors['login_selector'])  # Ожидаем наличия поля логина
                    await self.page_evaluate(selectors['login_clear_js'])  # очищаем поле логина
                    await self.page_type(selectors['login_selector'], self.login, {'delay': 10})  # вводим логин
                    if (await self.page_evaluate(selectors['chk_submit_after_login_js'], default=False)):  # Если нужно после логина нажать submit
                        await self.page_click(selectors['submit_after_login_selector']) # либо click
                        await self.page_evaluate(selectors['submit_after_login_js'])  # либо через js
                        await self.page_waitForSelector(selectors['password_selector'])  # и ждем появления поля с паролем
                        await asyncio.sleep(1)
                    await self.page_evaluate(selectors['password_clear_js'])  # очищаем поле пароля           
                    await self.page_type(selectors['password_selector'], self.password, {'delay': 10})  # вводим пароль
                    if await self.page_evaluate(selectors['remember_checker'], default=False):  # Если есть невыставленный check remember me
                        await self.page_evaluate(selectors['remember_js'])  # выставляем его
                        await self.page_click(selectors['remember_selector'], {'delay': 10})
                    await asyncio.sleep(int(selectors['pause_press_submit']))
                    await self.page_click(selectors['submit_selector']) #  нажимаем на submit form
                    await self.page_evaluate(selectors['submit_js'])  # либо через js (на некоторых сайтах один из вариантов не срабатывает)
                    await self.page_waitForNavigation()  # ждем отработки нажатия
                    await asyncio.sleep(1)
                if await self.page_evaluate(selectors['chk_lk_page_js']):
                    logging.info(f'Logged on')
                    break 
                await asyncio.sleep(1)
                if cnt==10:  # На 10 попытку перезагружаем страницу
                    await self.page_reload('unclear: logged in or not')
            else:
                # Проверяем - это не капча ?
                if await self.page_evaluate(selectors['captcha_checker'], False):
                    # Если стоит флаг показывать капчу то включаем видимость хрома и ждем заданное время
                    if str(store.options('show_captcha')) == '1':
                        logging.info('Show captcha')
                        hide_chrome(hide=False, foreground=True)
                        await self.page_evaluate(selectors['captcha_focus'])
                        for cnt2 in range(int(store.options('max_wait_captcha'))):
                            _ = cnt2
                            if not await self.page_evaluate(selectors['captcha_checker'], False):
                                break
                            await asyncio.sleep(1)
                        else:  # Капчу так никто и не ввел
                            logging.error(f'Show captcha timeout. A captcha appeared, but no one entered it')        
                            raise RuntimeError(f'A captcha appeared, but no one entered it')
                    else:  # Показ капчи не зададан выдаем ошибку и завершаем
                        logging.error(f'Captcha appeared')        
                        raise RuntimeError(f'Captcha appeared')
                else:
                    # Никуда не попали и это не капча
                    logging.error(f'Unknown state')
                    raise RuntimeError(f'Unknown state')

    @async_check_browser_opened_decorator
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
        Если нужно указать что в url_tag url заканчивается этим текстом, то поставьте после него знак $
        результат во всех случаях записывается с именем name в результирующий словарь
        Если параметр необязательный (т.е. его может и не быть) то чтобы его не ждать можно добавить в словарь по данному параметру 'wait':False
        #param если параметр не нужен а просто нужно выполнить действие, то в начале такого параметра ставим # 
        ---
        save_to_result=True то записываем их в итоговый словарь результатов (все, которые не начинаются с решетки) (self.result) 
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
                            logging.info(f'pformula on {param["url_tag"]}:{param["pformula"]}')
                            # Для скрипта на python делаем 
                            try:
                                res = eval(param['pformula'], {'data':response_result})
                                if res is not None:
                                    result[param['name']] = res
                            except Exception:
                                exception_text = f'Ошибка в pformula:{param["pformula"]} :{"".join(traceback.format_exception(*sys.exc_info()))}'
                                logging.info(exception_text)    
                        if param.get('jsformula', '') != '':
                            logging.info(f'jsformula on {param["url_tag"]}:{param["jsformula"]}')
                            res = await self.page_evaluate(f"()=>{{data={json.dumps(response_result,ensure_ascii=False)};return {param['jsformula']};}}")
                            if res is not None:
                                result[param['name']] = res
                else:  # Ищем на самой странице - запускаем js
                    logging.info(f'jsformula on url {self.page.url}:{param["jsformula"]}')
                    content = await self.page.content()
                    self.responses[f'CONTENT URL:{self.page.url}$'] = content
                    res = await self.page_evaluate(param['jsformula'])
                    if res is not None:
                        result[param['name']] = res
            # Если все обязательные уже получили
            if {i['name'] for i in params if i.get('wait',True)} - set(result) == set():
                break  # выходим если все получили
            if countdown == self.wait_and_reload:
                # так и не дождались - пробуем перезагрузить и еще подождать
                await self.page_reload('Data not received')        
        else:  # время вышло а получено не все - больше не ждем 
            no_receved_keys = {i['name'] for i in params} - set(result)
            logging.error(f'Not found all param on {url}: {",".join(no_receved_keys)}')
        if save_to_result:
            self.result.update({k:v for k,v in result.items() if not k.startswith('#')})  # Не переносим те что с решеткой в начале
        return result

    async def _async_main(self, run):
        await self.launch_browser()
        if run == 'normal':
            await self.async_main()  # !!! CALL async_main
        elif run == 'check_logon':
            await self.async_check_logon_selectors_prepare()
            await self.check_logon_selectors()
        logging.debug(f'Data ready {self.result.keys()}')
        if str(store.options('log_responses')) == '1' or store.options('logginglevel') == 'DEBUG':
            import pprint
            text = '\n\n'.join([f'{k}\n{v if k.startswith("CONTENT") else pprint.PrettyPrinter(indent=4).pformat(v) }'
                                for k, v in self.responses.items() if 'GetAdElementsLS' not in k and 'mc.yandex.ru' not in k])
            with open(os.path.join(store.options('loggingfolder'), self.storename + '.log'), 'w', encoding='utf8', errors='ignore') as f:
                f.write(text)
        await self.browser.close()
        kill_chrome()  # Добиваем  все наши незакрытые хромы, чтобы не появлялось кучи зависших
        clear_cache(self.storename)
        return self.result

    async def async_check_logon_selectors_prepare(self):
        pass

    async def async_main(self):
        pass

    def main(self, run='normal'):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop().run_until_complete(self._async_main(run))
        return self.result   
