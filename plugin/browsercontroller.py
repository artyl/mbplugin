''' Чтобы не делать кашу из синхронных и асинхронных решено оставить здесь только синхронный вариант
pyppiteradd останется для совместимости со старыми плагинами через async
'''
import glob, json, logging, os, re, shutil, subprocess, sys, time, traceback
from playwright.sync_api import sync_playwright
import playwright
if sys.platform == 'win32':
    try:
        import win32gui, win32process
    except Exception:
        print('No win32 installed, no fake-headless mode')
import psutil
#import pprint; pp = pprint.PrettyPrinter(indent=4).pprint
import store, settings

# Какой бы ни был режим в mbplugin для всех сторонних модулей отключаем расширенное логирование
# иначе в лог польется все тоннами
[logging.getLogger(name).setLevel(logging.ERROR) for name in logging.root.manager.loggerDict]  # pylint: disable=no-member

# Селекторы и скрипты по умолчанию для формы логона
# Проверять попадание в ЛК по отсутствию поля пароля - универсальный, простой, но ненадежный путь - 
# в процессе загрузки страницы логона поля не будет, но это не означает что мы на нужной странице
# Ходовые варианты проверки 
# по url: window.location.href=="https://...."
# по селектору: document.querySelector('span[id=balance]') !== null
default_logon_selectors = {
            'chk_lk_page_js': "document.querySelector('form input[type=password]') == null",  # true если мы в личном кабинете
            'lk_page_url': '', # Если задан то появление в списке self.responces этого url или его части будет означать что мы залогинились
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

# Константы для отключения headless mode в хроме (не на всех сайтах работает), если в опциях персонально не поменяно - просто отключаем
NOT_IN_CHROME = 'NOT_IN_CHROME'


def safe_run_decorator(func):
    def wrapper(*args, **kwargs):
        'decorator:Обертка для функций, выполнение которых не влияет на результат, чтобы при падении они не портили остальное'
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
            logging.info(f'{log_string} fail: {store.exception_text()}')
            return default
    wrapper.__doc__ = f'wrapper:{wrapper.__doc__}\n{func.__doc__}'
    return wrapper

def safe_run(func, *args, **kwargs):
    'Безопасный запуск функции'
    try:
        res = func(*args, **kwargs)  # CALL
        return res
    except Exception:
        log_string = f'{func.__name__}({", ".join(map(repr,args))}, {", ".join([f"{k}={repr(v)}" for k,v in kwargs.items()])})'
        logging.info(f'call {log_string} fail: {store.exception_text()}')

@safe_run_decorator
def hide_chrome(hide=True, foreground=False):
    'Прячем или показываем окно хрома, только в windows в linux и macOS не умеем'
    # TODO 
    def enumWindowFunc(hwnd, windowList):
        """ win32gui.EnumWindows() callback """
        text = win32gui.GetWindowText(hwnd).lower()
        className = win32gui.GetClassName(hwnd).lower()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:  #  ??? text.lower().find('chrome')>=0  remote-debugging-port or remote-debugging-pipe
            if (text != '' and 
            ('remote-debugging-p' in ''.join(psutil.Process(pid).cmdline()) or 'ms-playwright\\firefox' in ''.join(psutil.Process(pid).cmdline()))
            and not text.startswith('msct') and not text.startswith('default') and 'восстановить' not in text):
                windowList.append((hwnd, text, className))
                logging.debug(f'enumWindowFunc:text={text}, className={className}')
        except Exception:
            pass
    if 'win32gui' not in sys.modules:
        logging.info(f"No win32 modules, can't hide chrome windows")
        return
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
    '''Киляем бажный хром если вдруг какой-то висит, т.к. народ умудряется запускать не только хром, то имя exe возьмем из пути '''
    # TODO получилось как-то сложно пока убиваем то что начинается на chrome и имеет remote-debugging-port в cmdline
    pname = 'chrome'  # chrome or chrome.exe # os.path.split(chrome_executable_path)[-1].lower()
    # TODO в сложном случае когда мы запускаем встроенный у нас может получиться что имя exe которое мы берем из chrome_executable_path
    # не совпадет с тем что мы реально запускаем, тогда мы можем не достать запущенные хромы
    # с другой стороны playwright вроде все корректно прибивает
    # но по правильному имя браузера мы должны взять из self.sync_pw.chromium.executable_path
    for p in psutil.process_iter():
        try:
            if p.name().lower().startswith(pname) and 'remote-debugging-port' in ''.join(p.cmdline()):
                p.kill()    
        except Exception:
            pass

@safe_run_decorator
def fix_crash_banner(storefolder, storename):
    'Исправляем Preferences чтобы убрать баннер Работа Chrome была завершена некорректно'
    fn_pref = store.abspath_join(storefolder, 'headless', storename,'Default', 'Preferences')
    if not os.path.exists(fn_pref):
        return  # Нет Preferences - выходим
    with open(fn_pref, encoding='utf8') as f:
        data = f.read()
    data1 = data.replace('"exit_type":"Crashed"','"exit_type":"Normal"').replace('"exited_cleanly":false','"exited_cleanly":true')
    if data != data1:
        logging.info(f'Fix chrome crash banner')
        open(fn_pref, encoding='utf8', mode='w').write(data1)        

@safe_run_decorator
def clear_cache(storefolder, storename):
    'Очищаем папку с кэшем профиля чтобы не разрастался'
    #return  # С такой очисткой оказывается связаны наши проблемы с загрузкой
    profilepath = store.abspath_join(storefolder, 'headless', storename)
    shutil.rmtree(store.abspath_join(profilepath, 'BrowserMetrics'), ignore_errors=True)
    shutil.rmtree(store.abspath_join(profilepath, 'cache2'), ignore_errors=True)
    shutil.rmtree(store.abspath_join(profilepath, 'startupCache'), ignore_errors=True)
    shutil.rmtree(store.abspath_join(profilepath, 'Crashpad'), ignore_errors=True)
    shutil.rmtree(store.abspath_join(profilepath, 'Default', 'Cache'), ignore_errors=True)
    shutil.rmtree(store.abspath_join(profilepath, 'Default', 'Code Cache'), ignore_errors=True)
    shutil.rmtree(store.abspath_join(profilepath, 'Default', 'Service Worker', 'CacheStorage'), ignore_errors=True)

@safe_run_decorator
def delete_profile(storefolder, storename):
    'Удаляем профиль'
    kill_chrome()  # Перед удалением киляем хром
    profilepath = store.abspath_join(storefolder, 'headless', storename)
    shutil.rmtree(profilepath)


class BalanceOverPlaywright():
    '''Общая часть класса управления браузером '''

    def check_browser_opened_decorator(func):  # pylint: disable=no-self-argument
        def wrapper(self, *args, **kwargs):
            'decorator Проверка на закрытый браузер, если браузера нет пишем в лог и падаем'
            if self.browser_open:
                res = func(self, *args, **kwargs)  # pylint: disable=not-callable
                return res
            else:
                logging.error(f'Browser was not open')
                raise RuntimeError(f'Browser was not open')
        wrapper.__doc__ = f'wrapper:{wrapper.__doc__}\n{func.__doc__}'
        return wrapper

    def safe_run_with_log_decorator(func):  # pylint: disable=no-self-argument
        def wrapper(self, *args, **kwargs):
            '''decorator для безопасного запуска функции не падает в случае ошибки, а пишет в лог и возвращает default=None
            параметры предназначенные декоратору, и не передаются в вызываемую функцию:
            default: возвращаемое в случае ошибки значение'''
            default = kwargs.pop('default', None)
            if len(args) > 0 and (args[0] == '' or args[0] == None):
                return default            
            # Готовим строку для лога
            log_string = f'call: {getattr(func,"__name__","")}({", ".join(map(repr,args))}, {", ".join([f"{k}={repr(v)}" for k,v in kwargs.items()])})'
            if str(self.options('log_full_eval_string')) == '0':
                log_string = log_string if len(log_string) < 200 else log_string[:100]+'...'+log_string[-100:]
                if 'password' in log_string:
                    log_string = log_string.split('password')[0]+'password ....'
            log_string = log_string.encode('cp1251', errors='ignore').decode('cp1251', errors='ignore')  # Убираем всякую хрень
            try:
                res = func(self, *args, **kwargs)  # pylint: disable=not-callable
                logging.info(f'{log_string} OK')
                return res
            except Exception:
                logging.info(f'{log_string} fail: {exception_text()}')
                return default
        wrapper.__doc__ = f'wrapper:{wrapper.__doc__}\n{func.__doc__}'
        return wrapper

    def options(self, param):
        ''' Обертка вокруг store.options чтобы передать в нее пару (номер, плагин) для вытаскивания индивидуальных параметров'''
        lang = 'p'
        return store.options(param, pkey=(self.login, f'{lang}_{self.plugin_name}'))

    def __init__(self,  login, password, storename=None, wait_loop=30, wait_and_reload=10, max_timeout=15, login_url=None, user_selectors=None, headless=None, force=1, plugin_name=''):
        '''Передаем стандартно login, password, storename'
        Дополнительно
        wait_loop=30 - Сколько секунд ждать появления информации на странице
        wait_and_reload=10 - Сколько секунд ждать, после чего перезагрузить страницу
        max_timeout=15 - сколько секунд ждать прогрузки страниц, появления форм и т.п.
        login_url, user_selectors - можно передать параметры для логона при создании класса
        headless можно указать явно, иначе будет взято из настроек, но работать будет только в playwright
        force - коэффициент, на который будет умножено страховочное ожидание 0 - ускориться, 2 - замедлиться
        если все проверки заданы качественно - можно указать force=0
        plugin_name - нужен для поиска индивидуальных параметров в phones.ini'''
        self.browser, self.page = None, None  # откроем браузер - заполним
        self.browser_open = True  # флаг что браузер работает
        self.wait_loop = wait_loop  # TODO подобрать параметр
        self.max_timeout = max_timeout
        self.force = force
        self.plugin_name = plugin_name
        self.wait_and_reload = wait_and_reload
        self.password = password
        self.login_ori, self.acc_num = login, ''
        self.login = login
        self.storefolder = self.options('storefolder')
        self.storename = storename
        self.login_url = login_url
        self.user_selectors = user_selectors
        self.ss_counter = 0  # Счетчик скриншотов
        # Удаляем скриншоты с прошлых разов
        for fn in glob.glob(store.abspath_join(self.options('loggingfolder'), self.storename + '*.png')):
            os.remove(fn)
        # headless ТОЛЬКО в PLAYWRIGHT и ТОЛЬКО если отключен показ капчи, и ТОЛЬКО если не стоит show_chrome=0
        # иначе мы видимость браузера из headless уже не вернем и капчу показать не сможем
        if type(headless) == bool:
            self.headless = headless
        elif headless == NOT_IN_CHROME:
            # Если указано что в хроме headless не работает и настройками это не поменяли, то выключаем чтобы хоть как-то отработало
            if str(self.options('headless_chrome')) == '1' and self.options('browsertype') == 'chromium':
                self.headless = False
            else:
                self.headless = True
        else:  #if headless is None:
            if(str(self.options('show_captcha')) == '0' and str(self.options('show_chrome')) == '0'):
                self.headless = str(self.options('headless_chrome')) == '1'
            else:
                self.headless = False
        if '/' in login:
            self.login, self.acc_num = self.login_ori.split('/')
            # !!! в storename уже преобразован поэтому чтобы выкинуть из него ненужную часть нужно по ним тоже регуляркой пройтись
            self.storename = self.storename.replace(re.sub(r'\W', '_', self.login_ori), re.sub(r'\W', '_', self.login))  # исправляем storename
        kill_chrome()  # Превентивно убиваем все наши хромы, чтобы не появлялось кучи зависших
        clear_cache(self.storefolder, self.storename)
        self.result = {}
        self.responses = {}
        self.hide_chrome_flag = str(self.options('show_chrome')) == '0' and self.options('logginglevel') != 'DEBUG'
        self.profile_directory = self.storename
        self.launch_config_args = [
            '--log-level=3', # no logging
            "--window-position=-2000,-2000" if self.hide_chrome_flag else "--window-position=80,80",
            "--window-size=800,900"]
        # if self.headless:
        # В Headless chrome не работают профили, в Firefox их вообще нет, так что многопрофильность не используем
        self.user_data_dir = store.abspath_join(self.storefolder, 'headless', self.profile_directory)
        self.launch_config = {
            'headless': self.headless,
        }
        fix_crash_banner(self.storefolder, self.storename)            

    def response_worker(self, response):
        'Response Worker вызывается на каждый url который открывается при загрузке страницы (т.е. список тот же что на вкладке сеть в хроме)'
        'Проходящие запросы, которые json сохраняем в responses'
        if response.status == 200:
            try:
                data = response.json()  # Берем только json
            except Exception:
                # TODO добавить взятие и текста страниц для парсинга
                return
            try:
                post = ''
                if response.request.method == 'POST' and response.request.post_data is not None:
                    post = response.request.post_data
                self.responses[f'{response.request.method}:{post} URL:{response.request.url}$'] = data
                # TODO Сделать какой-нибудь механизм для поиска по загруженным страницам
                # txt = response.text()
                # if '2336' in txt:
                #    logging.info(f'2336 in {response.request.url}')
            except Exception:
                exception_text = f'Ошибка: {store.exception_text()}'
                logging.debug(exception_text)

    def on_route_worker(self, route):
        'Обработчик обращений браузера, здесь можно их прервать, чтобы лишние данные не грузить'
        # TODO вынести константы наверх
        stop_url = ['google-analytics', '.yandex.ru/', 'dynamicyield.com/', 'googletagmanager.com/', 'yastatic.net/', 'cloudflare.com/', 'facebook.net/', 'vk.com/']
        if route.request.resource_type in ('image', 'font', 'manifest') or len([u for u in stop_url if u in route.request.url])>0:
            #print(f'Abort {route.request.method}:{route.request.url}')
            try:
                logging.debug(f'Abort: {route.request.resource_type}:{route.request.url}')
                route.abort()
            except Exception:
                print('NO ABORT')
        else:
            #print(route.request.resource_type)
            try:
                route.continue_()
            except Exception:
                print('NO CONTINUE')  

    def disconnected_worker(self):
        'disconnected_worker вызывается когда закрыли браузер'
        logging.info(f'Browser was closed')
        self.browser_open = False  # выставляем флаг

    def sleep(self, delay):
        'Специальный sleep, т.к. вокруг все асинхронное должны спать через asyncio.sleep в секундах'
        #logging.info(f'sleep {delay}')
        return self.page.wait_for_timeout(delay*1000)

    @check_browser_opened_decorator
    @safe_run_with_log_decorator
    def page_evaluate(self, eval_string, default=None, args=[]):
        ''' переносим вызов evaluate в класс для того чтобы каждый раз не указывать page и обернуть декораторами
        Проверка на пустой eval_string и default значение - сделано в декораторе'''
        try:
            return self.page.evaluate(eval_string, args)
        except Exception:
            exception_text = f'Ошибка в page_evaluate:{store.exception_text()}'
            if 'Execution context was destroyed' not in exception_text:
                logging.info(exception_text)
                raise


    def page_check_response_url(self, response_url):
        ''' проверяем наличие response_url в загруженных url, если не задан или пустой то возвращаем True '''
        if response_url == None or response_url == '':
            return True
        if len([i for i in self.responses.keys() if response_url in i]) > 0:
            logging.info(f'Found an "{response_url}" in responses')
            return True
        else:
            return False

    @check_browser_opened_decorator
    @safe_run_with_log_decorator
    def page_goto(self, url):
        ''' переносим вызов goto в класс для того чтобы каждый раз не указывать page и обернуть декораторами'''
        try:
            if url != None and url != '':
                return self.page.goto(url)
        except Exception:
            logging.info(f'goto timeout')

    @check_browser_opened_decorator
    @safe_run_with_log_decorator
    def page_reload(self, reason=''):
        ''' переносим вызов reload в класс для того чтобы каждый раз не указывать page'''
        if reason != '':
            logging.info(f'page.reload {reason}')
        return self.page.reload()

    def page_content(self):
        ''' переносим вызов content в класс для того чтобы каждый раз не указывать page'''
        return self.page.content()

    def page_screenshot(self, path='', number=-1, suffix=''):
        if str(self.options('log_responses')) != '1' and self.options('logginglevel') != 'DEBUG':
            return
        if number == -1 and suffix == '':
            suffix = self.ss_counter
            self.ss_counter += 1
        if path == '':
            path = store.abspath_join(self.options('loggingfolder'), f'{self.storename}_{suffix}.png')
        self.page.screenshot(path=path)

    @check_browser_opened_decorator
    @safe_run_with_log_decorator
    def page_wait_for(self, expression=None, selector=None, loadstate=None, response_url=None, location_href_url=None, **kwargs):
        ''' Ожидаем одно или несколько событий:
        наступления eval(expression)==True
        появления selector 
        loadstate=True - окончания загрузки страницы (в playwright нужно осторожно, его поведение не всегда предсказуемо)
        location_href_url - ожидание url в адресной строке (glob, regex or predicate)
        response_url - появления в self.responses указанного url
        '''
        if loadstate != None and loadstate == True:
            try:
                self.page.wait_for_load_state("networkidle", timeout=self.max_timeout*1000)
            except Exception:
                logging.info(f'wait_for_load_state timeout')
        if location_href_url != None and location_href_url != '':
            self.page.wait_for_url(location_href_url, **kwargs)
        if  selector != None and selector != '':
            self.page.wait_for_selector(selector)
        if  expression != None and expression != '':
            # TODO почему то с self.page.wait_for_function возникли проблемы - переделал на eval
            res = None
            for cnt in range(self.max_timeout):
                try:
                    # в процессе выполнения можем грохнуться т.к. страница может перезагрузиться, такие даже не пишем в лог
                    res = self.page.evaluate(expression, **kwargs)
                except Exception:
                    exception_text = f'Ошибка в page_wait_for:{store.exception_text()}'
                    if 'Execution context was destroyed' not in exception_text:
                        logging.info(exception_text)   
                if res:
                    break
                self.sleep(1)
        if response_url != None and response_url != '':
            for cnt in range(self.max_timeout):
                if self.page_check_response_url(response_url):
                    break
                self.sleep(1)

    @check_browser_opened_decorator
    @safe_run_with_log_decorator
    def page_type(self, selector, text, *args, **kwargs):
        ''' переносим вызов type в класс для того чтобы каждый раз не указывать page'''
        if selector != '' and text != '': 
            return self.page.type(selector, text, *args, **kwargs)

    @check_browser_opened_decorator
    @safe_run_with_log_decorator
    def page_fill(self, selector, text, *args, **kwargs):
        ''' переносим вызов type в класс для того чтобы каждый раз не указывать page'''
        if selector != '' and text != '': 
            return self.page.fill(selector, text, *args, **kwargs)

    @check_browser_opened_decorator
    @safe_run_with_log_decorator    
    def page_click(self, selector, *args, **kwargs):
        ''' переносим вызов click в класс для того чтобы каждый раз не указывать page
        Кликаем только если элемент есть'''
        if selector != '' and self.page.query_selector(selector):
            return self.page.click(selector, *args, **kwargs)            

    def launch_browser(self, launch_func):
        self.launch_config.update({
            'user_data_dir': self.user_data_dir,
            'ignore_https_errors': True,
            'args': self.launch_config_args,
            })
        if self.options('use_builtin_browser').strip() == '0':
            self.chrome_executable_path = self.options('chrome_executable_path')
            if not os.path.exists(self.chrome_executable_path):
                chrome_paths = [p for p in settings.chrome_executable_path_alternate if os.path.exists(p)]
                if len(chrome_paths) == 0:
                    logging.error('Chrome.exe not found')
                    raise RuntimeError(f'Chrome.exe not found')
                self.chrome_executable_path = chrome_paths[0]
            self.launch_config.update({'executable_path': self.chrome_executable_path,})
        else:
            self.chrome_executable_path = self.browsertype.executable_path
        logging.info(f'Launch chrome from {self.chrome_executable_path}')
        if self.options('proxy_server').strip() != '':
            self.launch_config['args'].append(f'--proxy-server={self.options("proxy_server").strip()}') 
        # playwright: launch_func = self.sync_pw.chromium.launch_persistent_context
        self.browser = launch_func(**self.launch_config) # sync_pw.chromium.launch_persistent_context
        if self.hide_chrome_flag:
            hide_chrome()
        self.page = self.browser.pages[0]
        [p.close() for p in self.browser.pages[1:]]
        self.page.on("response", self.response_worker)
        if str(self.options('intercept_request')) == '1' and str(self.options('show_captcha')) == '0':            
            # Если включено показывать капчу - то придется грузить все чтобы загрузить картинки
            self.page.route("*", self.on_route_worker)        
        self.browser.on("disconnected", self.disconnected_worker) # вешаем обработчик закрытие браузера

    def browser_close(self):
        self.browser.close()

    @check_browser_opened_decorator
    def check_logon_selectors(self):
        ''' Этот метод для тестирования, поэтому здесь можно assert
        Проверяем что селекторы на долго не выполняются - это максимум того что мы можем проверить без ввода логина и пароля
        '''
        selectors = default_logon_selectors.copy()
        login_url = self.login_url
        user_selectors = self.user_selectors
        assert set(user_selectors)-set(selectors) == set(), f'Не все ключи из user_selectors есть в selectors. Возможна опечатка, проверьте {set(user_selectors)-set(selectors)}'
        selectors.update(user_selectors)
        # TODO fix for submit_js -> chk_submit_js
        selectors['chk_submit_js'] = selectors['submit_js'].replace('.click()','!== null')
        print(f'login_url={login_url}')
        if login_url != '':
            self.page_goto(login_url)
        self.page_wait_for(loadstate=True)
        self.sleep(1)
        self.page_wait_for(expression=selectors['chk_login_page_js'])
        for sel in ['chk_login_page_js', 'login_clear_js', 'password_clear_js', 'chk_submit_js']:
            if selectors[sel] !='':
                print(f'Check {selectors[sel]}')
                eval_res = self.page_evaluate(selectors[sel])
                if sel.startswith('chk_'):
                    assert eval_res == True , f'Bad result for js:{sel}:{selectors[sel]}'
                else:
                    assert eval_res == '' , f'Bad result for js:{sel}:{selectors[sel]}'
        for sel in ['login_selector', 'password_selector', 'submit_selector']:
            if selectors[sel] !='':
                print(f'Check {selectors[sel]}')
                assert self.page_evaluate(f"document.querySelector('{selectors['login_selector']}') !== null")==True, f'Not found on page:{sel}:{selectors[sel]}'

    @check_browser_opened_decorator
    def do_logon(self, url=None, user_selectors=None):
        '''Делаем заход в личный кабинет/ проверяем не залогинены ли уже
        На вход передаем словарь селекторов и скриптов который перекроет действия по умолчанию
        Если какой-то из шагов по умолчанию хотим пропустить, передаем пустую строку
        Смотрите актуальное описание напротив параметров в коментариях
        Чтобы избежать ошибок - копируйте названия параметров'''
        breakpoint() if os.path.exists('breakpoint_logon') else None
        selectors = default_logon_selectors.copy()
        if url is None:
            url = self.login_url
        if user_selectors is None:
            user_selectors = self.user_selectors if user_selectors is not None else {}
        # проверяем что все поля из user_selectors есть в селектор (если не так то скорее всего опечатка и надо сигналить)
        if set(user_selectors)-set(selectors) != set():
            logging.error(f'Не все ключи из user_selectors есть в selectors. Возможна опечатка, проверьте {set(user_selectors)-set(selectors)}')
        selectors.update(user_selectors)
        # Если проверка на нахождение в личном кабинете на отсутствие элемента - дополнительно ожидаем чтобы страница гарантированно загрузилась
        is_bad_chk_lk_page_js = ' == null' in selectors['chk_lk_page_js'] or '=== null' in selectors['chk_lk_page_js']
        if url is not None:  # Иногда мы должны сложным путем попасть на страницу - тогда указываем url=None
            self.page_goto(url)
            # Появилось слишком много сайтов на которых медленно открывается страница логона и мы успеваем подумать что пароля на странице нет
            self.sleep(1*self.force if not is_bad_chk_lk_page_js else 5)
            self.page_wait_for(loadstate=True)
        self.page_screenshot()
        for countdown in range(self.wait_loop): 
            if self.page_evaluate(selectors['chk_lk_page_js'], default=True) and self.page_check_response_url(selectors['lk_page_url']):
                logging.info(f'Already login')
                break # ВЫХОДИМ ИЗ ЦИКЛА - уже залогинины
            if self.page_evaluate(selectors['chk_login_page_js']):
                logging.info(f'Login')
                if selectors['before_login_js'] != '':
                    self.page_evaluate(selectors['before_login_js'])  # Если задано какое-то действие перед логином - выполняем
                    self.sleep(1*self.force)
                self.page_wait_for(selector=selectors['login_selector'])  # Ожидаем наличия поля логина
                self.page_evaluate(selectors['login_clear_js'])  # очищаем поле логина
                self.page_fill(selectors['login_selector'], self.login)  # вводим логин
                if (self.page_evaluate(selectors['chk_submit_after_login_js'], default=False)):  # Если нужно после логина нажать submit
                    self.page_click(selectors['submit_after_login_selector']) # либо click
                    self.page_evaluate(selectors['submit_after_login_js'])  # либо через js
                    self.page_wait_for(selector=selectors['password_selector'])  # и ждем появления поля с паролем
                    self.sleep(1*self.force)
                self.page_evaluate(selectors['password_clear_js'])  # очищаем поле пароля
                self.page_fill(selectors['password_selector'], self.password)  # вводим пароль
                if self.page_evaluate(selectors['remember_checker'], default=False):  # Если есть невыставленный check remember me
                    self.page_evaluate(selectors['remember_js'])  # выставляем его
                    self.page_click(selectors['remember_selector'])
                self.sleep(1*self.force + int(selectors['pause_press_submit']))
                self.page_click(selectors['submit_selector']) #  нажимаем на submit form
                self.page_evaluate(selectors['submit_js'])  # либо через js (на некоторых сайтах один из вариантов не срабатывает)
                self.page_wait_for(loadstate=True)  # ждем отработки нажатия
                # ждем появления личного кабинета, или проваливаемся по таймауту
                self.page_wait_for(expression=selectors['chk_lk_page_js'], response_url=selectors['lk_page_url'])
                self.sleep(1*self.force if not is_bad_chk_lk_page_js else self.max_timeout)
                if self.page_evaluate(selectors['chk_lk_page_js'], default=True) and self.page_check_response_url(selectors['lk_page_url']):
                    logging.info(f'Logged on')
                    break  # ВЫХОДИМ ИЗ ЦИКЛА - залогинились
                self.sleep(1*self.force)
                # Проверяем - это не капча ?
                if self.page_evaluate(selectors['captcha_checker'], False):
                    # Если стоит флаг показывать капчу то включаем видимость хрома и ждем заданное время
                    if str(self.options('show_captcha')) == '1':
                        logging.info('Show captcha')
                        hide_chrome(hide=False, foreground=True)
                        self.page_evaluate(selectors['captcha_focus'])
                        for cnt2 in range(int(self.options('max_wait_captcha'))):
                            _ = cnt2
                            if not self.page_evaluate(selectors['captcha_checker'], False):
                                break  # ВЫХОДИМ ИЗ ЦИКЛА - капчи на странице больше нет
                            self.sleep(1)
                        else:  # Капчу так никто и не ввел
                            self.page_screenshot(suffix='captcha')
                            logging.error(f'Show captcha timeout. A captcha appeared, but no one entered it')        
                            raise RuntimeError(f'A captcha appeared, but no one entered it')
                    else:  # Показ капчи не зададан выдаем ошибку и завершаем
                        logging.error(f'Captcha appeared')
                        self.page_screenshot(suffix='captcha')       
                        raise RuntimeError(f'Captcha appeared')
                else:
                    # Никуда не попали и это не капча
                    self.page_screenshot(suffix='unknown')
                    logging.error(f'Unknown state')
                    raise RuntimeError(f'Unknown state')
                break  # ВЫХОДИМ ИЗ ЦИКЛА
            if countdown == self.wait_and_reload:
                # так и не дождались - пробуем перезагрузить и еще подождать
                self.page_reload('Unknown page try reload') 
            self.sleep(1)
        self.page_screenshot()

    def calculate_param(self, url_tag=[], jsformula='', pformula=''):
        'Вычисляет js выражение jsformula над json co страницы с url_tag, !!! url_tag - список тэгов'
        # TODO self.page.evaluate(f"(data) => {jsformula}", json_data)
        #return self.page_evaluate(f"()=>{{data={json.dumps(json_data,ensure_ascii=False)};return {jsformula};}}")
        if url_tag != []:  # Ищем в загруженных страницах
            response_result_ = [v for k,v in self.responses.items() if [i for i in url_tag if i not in k]==[]]
            if len(response_result_)>0:
                response_result = response_result_[-1]  # если ответов несколько - берем последний, так правильнее
                if pformula != '':
                    logging.info(f'pformula on {url_tag}:{pformula}')
                    # Для скрипта на python делаем 
                    try:
                        res = eval(pformula, {'data':response_result})
                        return res
                    except Exception:
                        exception_text = f'Ошибка в pformula:{pformula} :{store.exception_text()}'
                        logging.info(exception_text)    
                if jsformula != '':
                    logging.info(f'jsformula on {url_tag}:{jsformula}')
                    # !!! TODO Было: 
                    res = self.page_evaluate(f"()=>{{data={json.dumps(response_result,ensure_ascii=False)};return {jsformula};}}")
                    # Стало: в playwright автоматом подставится переменная response_result из кода, теперь можно так:
                    # TODO как-то не стало :-) надо разобраться
                    # res = self.page_evaluate(f"(data) => {jsformula}", args=[response_result])
                    return res
        else:  # Ищем на самой странице - запускаем js
            logging.info(f'jsformula on url {self.page.url}:{jsformula}')
            content = self.page_content()
            self.responses[f'CONTENT URL:{self.page.url}$'] = content
            res = self.page_evaluate(jsformula)
            return res

    @check_browser_opened_decorator
    def wait_params(self, params, url='', save_to_result=True):
        ''' Переходим по url и ждем параметры
        ---
        url если url пустой то не переходим а просто производим действия на текущей странице
        --- 
        params - список словарей вида 
        {'name':'text', 'url_tag':['text1','text2'], 'pformula':'text'} - ожидается приход json с url содержащим все строки из  url_tag из этого json через python eval возьмем tag_pformula
        либо 
        {'name':'text', 'url_tag':['text'], 'jsformula':'text'} - ожидается приход json с url содержащим url_tag из этого json через js eval возьмем tag_jsformula
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
            self.page_goto(url)
            self.page_wait_for(loadstate=True)
        for countdown in range(self.wait_loop):
            self.sleep(1)
            breakpoint() if os.path.exists('breakpoint_wait') else None
            for param in params:
                res = self.calculate_param(param.get('url_tag',''), param.get('jsformula',''), param.get('pformula',''))
                if res is not None:
                    result[param['name']] = res
            # Если все обязательные уже получили
            if {i['name'] for i in params if i.get('wait',True)} - set(result) == set():
                break  # выходим если все получили
            if countdown == self.wait_and_reload:
                # так и не дождались - пробуем перезагрузить и еще подождать
                self.page_reload('Data not received')        
        else:  # время вышло а получено не все - больше не ждем 
            no_received_keys = {i['name'] for i in params} - set(result)
            logging.error(f'Not found all param on {url}: {",".join(no_received_keys)}')
        if save_to_result:
            self.result.update({k:v for k,v in result.items() if not k.startswith('#')})  # Не переносим те что с решеткой в начале
        self.page_screenshot()
        return result

    def check_logon_selectors_prepare(self):
        'Метод для подготовки к тестированию'
        pass

    def data_collector(self):
        'Переопределите для своего плагина'
        pass

    @safe_run_decorator
    def main(self, run='normal'):
        logging.info(f"browserengine=Playwright")
        if sys.platform != 'win32' and not self.launch_config.get('headless', True) and str(self.options('xvfb')) == '1':
            os.system('pgrep Xvfb || Xvfb :99 -screen 0 1920x1080x24 &')            
            os.system('export DISPLAY=:99')  # On linux and headless:False use Xvfb
            os.environ['DISPLAY']=':99'
        with sync_playwright() as self.sync_pw:
            browsertype_text = self.options('browsertype')
            self.browsertype : playwright.sync_api._generated.BrowserType = getattr(self.sync_pw, browsertype_text)
            self.launch_browser(self.browsertype.launch_persistent_context)  # self.sync_pw.chromium.launch_persistent_context
            if run == 'normal':
                self.data_collector()
            elif run == 'check_logon':
                self.check_logon_selectors_prepare()
                self.check_logon_selectors()
            logging.debug(f'Data ready {self.result.keys()}')
            if str(self.options('log_responses')) == '1' or self.options('logginglevel') == 'DEBUG':
                import pprint
                text = '\n\n'.join([f'{k}\n{v if k.startswith("CONTENT") else pprint.PrettyPrinter(indent=4).pformat(v) }'
                                    for k, v in self.responses.items() if 'GetAdElementsLS' not in k and 'mc.yandex.ru' not in k])
                with open(store.abspath_join(self.options('loggingfolder'), self.storename + '.log'), 'w', encoding='utf8', errors='ignore') as f:
                    f.write(text)
            self.browser_close()
        kill_chrome()  # Добиваем все наши незакрытые хромы, чтобы не появлялось кучи зависших
        clear_cache(self.storefolder, self.storename)
        time.sleep(2)  # Даем время закрыться
        return self.result   

class BrowserController(BalanceOverPlaywright):
    pass

