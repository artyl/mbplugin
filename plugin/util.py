# -*- coding: utf8 -*-
''' Автор ArtyLa 
для того чтобы не писать утилиты два раза для windows и linux все переносим сюда, а 
непосредственно в bat и sh скриптах оставляем вызов этого скрипта
'''
import os, sys, re, time, subprocess, shutil, glob, traceback, logging
import click, requests
import rlcompleter, readline

readline.parse_and_bind("tab: complete")
# Т.к. мы меняем текущую папку, то sys.argv[0] будет смотреть не туда, пользоваться можно только
PLUGIN_PATH = os.path.split(os.path.abspath(sys.argv[0]))[0]
ROOT_PATH = os.path.abspath(os.path.join(PLUGIN_PATH, '..'))
STANDALONE_PATH = os.path.abspath(os.path.join(ROOT_PATH, '..'))
EMB_PYTHON_PATH = os.path.abspath(os.path.join(PLUGIN_PATH, os.path.join('..', 'python')))
SYS_PATH_ORIGIN = sys.path[:]  # Оригинальное значение sys.path
# Fix sys.argv[0]
sys.argv[0] = os.path.abspath(sys.argv[0])
# Т.к. все остальные ожидают что мы находимся в папке plugin переходим в нее
os.chdir(PLUGIN_PATH)
try:
    import store
except ModuleNotFoundError:
    click.echo(f'Not found plugin folder use\n  {sys.argv[0]} fix-embedded-python-path')
    sys.path.insert(0, PLUGIN_PATH)
    import store

@click.group()
@click.option('-d', '--debug', is_flag=True, help='Debug mode')
@click.option('-v', '--verbose', is_flag=True, help='Verbose mode')
@click.option('--start_http', type=click.Choice(['true', 'false', 'reset', 'nochange'], case_sensitive=False), default='nochange', help='Autostart web server')
@click.pass_context
def cli(ctx, debug, verbose, start_http):
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    ctx.obj['VERBOSE'] = verbose

@cli.command()
@click.pass_context
def hello(ctx):
    'Пока для экспериментов оставил,потом уберу'
    click.echo(f'Hello World! {ctx.obj}')

@cli.command()
@click.argument('expression', type=str)
@click.pass_context
def set(ctx, expression):
    '''Установка/сброс опции, для флагов используйте 1/0
    если в качестве значения указан default происходит сброс к установкам по умолчанию
    для установки set ini/HttpServer/start_http=1  
    или для сброса set ini/HttpServer/start_http=default       
    '''
    mbplugin_ini = store.ini()
    mbplugin_ini.read()
    if not re.match(r'^\w+/\w+/\w+=\S+$', expression):
        click.echo(f'Non valid expression {expression}')
        return
    path, value = expression.split('=')
    _, section, key = path.split('/')
    if value == 'default':
        del mbplugin_ini.ini[section][key]
    else:
        mbplugin_ini.ini[section][key] = value
    mbplugin_ini.write()
    click.echo(f'Set {path} -> {value}')

@cli.command()
@click.pass_context
def fix_embedded_python_path(ctx):
    '''
    Исправляем пути embedded python
    добавляем в sys.path поиск в папке откуда запущен скрипт по умолчанию, в embedded он почему-то выключен
    Только если папка с python есть добавляем в sitecustomize.py путь к текущей папке'''
    name = 'fix_embedded_python_path'
    if PLUGIN_PATH not in SYS_PATH_ORIGIN:
        try:
            click.echo(f'Add current path to sys.path by default')
            txt = '\nimport os, sys\nsys.path.insert(0,os.path.abspath(os.path.split(sys.argv[0])[0]))\n'
            if os.path.isdir(EMB_PYTHON_PATH):
                open(os.path.join(EMB_PYTHON_PATH, 'sitecustomize.py'), 'a').write(txt)
            click.echo(f'OK {name}')
        except Exception:
            click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')                
    else:
        click.echo(f'Not needed {name}')


@cli.command()
@click.pass_context
def install_chromium(ctx):
    '''Устанавливаем движок chromium, только если включена опция use_builtin_browser'''
    name = 'install_chromium'
    if str(store.options('use_builtin_browser')) != '1':
        click.echo(f'Not needed {name}')
        return
    try:
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])
        click.echo(f'OK {name}')
    except Exception:
        click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')          

@cli.command()
@click.pass_context
def clear_browser_cache(ctx):
    '''Очищаем кэш браузера'''
    name = 'clear_browser_cache'
    try:
        [os.remove(fn) for fn in glob.glob(os.path.join(ROOT_PATH, 'store', 'p_*'))]
        shutil.rmtree(os.path.join(ROOT_PATH, 'store', 'puppeteer'), ignore_errors=True)
        shutil.rmtree(os.path.join(ROOT_PATH, 'store', 'headless'), ignore_errors=True)
        click.echo(f'OK {name}')
    except Exception:
        click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')         

@cli.command()
@click.pass_context
def recompile_dll(ctx):
    'Пересобираем DLL плагины (только windows)'
    name = 'recompile_dll'
    if sys.platform == 'win32':
        try:
            #os.system(f"{os.path.join(ROOT_PATH, 'dllsource', 'compile_all_p.bat')}")
            for fn in glob.glob('..\\plugin\\*.py'):
                pluginname = f'p_{os.path.splitext(os.path.split(fn)[1])[0]}'
                src = os.path.join(ROOT_PATH,'dllsource',pluginname+'.dll')
                dst = os.path.join(ROOT_PATH,'dllplugin',pluginname+'.dll')
                compile_bat = os.path.join(ROOT_PATH,'dllsource','compile.bat')
                if 'def get_balance(' in open(fn,encoding='utf8').read():
                    os.system(f'{compile_bat} {pluginname}')
                    shutil.move(src, dst)
                if ctx.obj['VERBOSE']:
                    click.echo(f'Move {pluginname}.dll -> dllplugin\\')
            click.echo(f'OK {name}')
        except Exception:
            click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')                
    else:
        click.echo('On windows platform only')

@cli.command()
@click.pass_context
def recompile_jsmblh(ctx):
    'Пересобираем JSMB LH plugin'
    name = 'recompile_jsmblh'
    import compile_all_jsmblh
    try:
        compile_all_jsmblh.recompile(PLUGIN_PATH, verbose=ctx.obj['VERBOSE'])
        click.echo(f'OK {name}')
    except Exception:
        click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')

@cli.command()
@click.pass_context
def check_import(ctx):
    'Проверяем что все модули импортируются'
    name = 'check_import'
    try:
        import telegram, requests, PIL, bs4, pyreadline, psutil, pystray, playwright, schedule
        if sys.platform == 'win32':
            import win32api, win32gui, win32con, pyodbc    
    except ModuleNotFoundError:
        click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')
        return
    click.echo(f'OK {name}')

@cli.command()
@click.argument('turn', type=click.Choice(['on', 'off'], case_sensitive=False), default='on')
@click.pass_context
def autostart_web_server(ctx, turn):
    'Автозапуск web сервера (только windows)'
    'Создаем lnk на run_webserver.bat и помещаем его в автозапуск и запускаем'
    name = 'autostart_web_server'
    if sys.platform == 'win32':
        try:
            import win32com.client
            shell = win32com.client.Dispatch('WScript.Shell')
            lnk_path = os.path.join(ROOT_PATH, 'run_webserver.lnk')
            lnk_startup_path = f"{os.environ['APPDATA']}\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
            lnk_startup_full_name = f"{os.environ['APPDATA']}\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\run_webserver.lnk"
            shortcut = shell.CreateShortCut(lnk_path)
            shortcut.Targetpath = os.path.abspath(os.path.join(ROOT_PATH, 'run_webserver.bat'))
            shortcut.save()
            if turn == 'on':
                if str(store.options('start_http', section='HttpServer')) == '1':
                    # %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
                    shutil.copy(lnk_path, lnk_startup_path)
                    os.system(f'"{lnk_startup_full_name}"')
                else:
                    click.echo(f'Start http server disabled in mbplugin.ini (start_http=0)')
            if turn == 'off':
                if os.path.exists(lnk_startup_full_name):
                    os.remove(lnk_startup_full_name)
            time.sleep(4)
            click.echo(f'OK {name}')
        except Exception:
            click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')                
    else:
        click.echo('On windows platform only')

@cli.command()
@click.pass_context
def run_web_server(ctx):
    'Запуск web сервера'
    name = 'run_web_server'
    try:
        import httpserver_mobile
        httpserver_mobile.WebServer()
        time.sleep(4)
        click.echo(f'OK {name}')
    except Exception:
        click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')                

@cli.command()
@click.pass_context
def reload_schedule(ctx):
    'Перечитывает расписание запросов баланса'
    name = 'reload_schedule'
    import httpserver_mobile
    port = store.options('port',section='HttpServer')
    res = requests.get(f'http://127.0.0.1:{port}/reload_schedule').content.decode('cp1251')
    click.echo(res)

@cli.command()
@click.argument('plugin', type=click.Choice(['simple', 'chrome'], case_sensitive=False), default='simple')
@click.pass_context
def check_jsmblh(ctx, plugin):
    'Проверяем что все работает JSMB LH PLUGIN простой плагин'
    name = 'check_jsmblh'
    if str(store.options('start_http', section='HttpServer')) != '1':
        click.echo(f'Start http server disabled in mbplugin.ini (start_http=0)')
        return
    import re,requests
    # Здесь не важно какой плагин мы берем, нам нужен только адрес с портом, а он у всех одинаковый
    # Можно было бы взять из ini, но мы заодно проверяем что в плагинах правильный url
    path = os.path.join(ROOT_PATH, 'jsmblhplugin', 'p_test1_localweb.jsmb')
    url = re.findall(r'(?usi)(http://127.0.0.1:.*?/)',open(path).read())[0]
    try:
        if plugin == 'simple':
            res = requests.session().get(url+f'getbalance/p_test1/123/456/789').content.decode('cp1251')
        else:
            res = requests.session().get(url+'getbalance/p_test3/demo@saures.ru/demo/789').content.decode('cp1251')
        click.echo(f'OK {name} {plugin}')
        if ctx.obj['VERBOSE']:
            click.echo(f'{res}')
    except Exception:
        click.echo(f'Fail {name} {plugin}:\n{"".join(traceback.format_exception(*sys.exc_info()))}')

@cli.command()
@click.pass_context
def check_dll(ctx):
    'Проверяем что все работает DLL PLUGIN'
    name = 'check_dll'
    #call plugin\test_mbplugin_dll_call.bat p_test1 123 456 
    if sys.platform == 'win32':
        try:
            import dll_call_test
            #echo INFO:
            res = dll_call_test.dll_call('p_test1', 'Info', '123', '456')
            if ctx.obj['VERBOSE']:
                click.echo(f'Info:{res}')
            #echo EXECUTE:
            res = dll_call_test.dll_call('p_test1', 'Execute', '123', '456')
            if ctx.obj['VERBOSE']:
                click.echo(f'Execute:{res}')
            click.echo(f'OK {name}')
        except Exception:
            click.echo(f'Fail {name}:\n{"".join(traceback.format_exception(*sys.exc_info()))}')
    else:
        click.echo('On windows platform only')    

@cli.command()
@click.pass_context
def check_playwright(ctx):
    'Проверяем что playwright работает'
    name = 'check_playwright'
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("https://wikipedia.org/")
            if len(page.content()):
                click.echo(f'OK {name} {len(page.content())}')
            browser.close()
    except Exception:
        click.echo(f'Fail {name}:\n{"".join(traceback.format_exception(*sys.exc_info()))}')

@cli.command()
@click.pass_context
def standalone_init(ctx):
    'Инициализация можно втором параметром указать noweb тогда вебсервер не будет запускаться и помещаться в автозапуск'
    name = 'standalone_init'
    try:
        # Если лежит mobilebalance - не работаем, а то только запутаем всех
        if os.path.exists(os.path.join(STANDALONE_PATH, 'MobileBalance.exe')):
            click.echo(f'The folder {STANDALONE_PATH} must not contain a file mobilebalance.exe')
            return
        if not os.path.exists(os.path.join(STANDALONE_PATH, 'phones.ini')):
            click.echo(f'The folder {STANDALONE_PATH} must contain a file phones.ini')
            return
        ini=store.ini()
        ini.read()
        ini.ini['Options']['sqlitestore'] = '1'
        ini.ini['Options']['createhtmlreport'] = '1'
        ini.ini['Options']['balance_html'] = os.path.abspath(os.path.join('..','..','balance.html'))
        ini.write()
        click.echo(f'OK {name}')
    except Exception:
        click.echo(f'Fail {name}:\n{"".join(traceback.format_exception(*sys.exc_info()))}')    

@cli.command()
@click.option('--only_failed', is_flag=True, help='Запросить балансы, по которым были ошибки')
@click.argument('filter', nargs=-1)
@click.pass_context
def standalone_get_balance(ctx, only_failed, filter):
    'Получение балансов, можно указать only_failed, тогда будут запрошены только те где последняя попытка была неудачной'
    import httpserver_mobile
    #breakpoint()
    httpserver_mobile.detbalance_standalone(filter=filter,only_failed=only_failed)

@cli.command()
@click.pass_context
def refresh_balance_html(ctx):
    'Обновить balance.html'
    import httpserver_mobile
    httpserver_mobile.write_report()

@cli.command()
@click.pass_context
def copy_all_from_mdb(ctx):
    'копировать все данные из mdb'
    import dbengine
    store.turn_logging(logginglevel=logging.DEBUG)
    dbengine.update_sqlite_from_mdb(deep=10000)


@cli.command()
@click.pass_context
def send_tgbalance(ctx):
    'Отправка баланса TG через API веб сервера'
    import httpserver_mobile
    port = store.options('port',section='HttpServer')
    # Sendtgbalance
    res = requests.get(f'http://127.0.0.1:{port}/sendtgbalance').content.decode('cp1251')
    click.echo(res)
    # Subscription
    res = requests.get(f'http://127.0.0.1:{port}/sendtgsubscriptions').content.decode('cp1251')
    click.echo(res)

@cli.command()
@click.pass_context
def send_tgbalance_over_requests(ctx):
    'Отправка баланса TG чистым requests без использования web сервера'
    # Balanse over requests
    import httpserver_mobile
    httpserver_mobile.send_telegram_over_requests()


@cli.command()
@click.argument('action', type=click.Choice(['hide', 'show'], case_sensitive=False), default='hide')
@click.pass_context
def show_chrome(ctx, action):
    'Показывает спрятанный crome. Работает только на windows, и только при headless_chrome = 0, если chrome запущен в режиме headless то его показать нельзя'
    import browsercontroller
    if sys.platform == 'win32':
        browsercontroller.hide_chrome(hide=(action == 'hide'))
    else:
        click.echo('On windows platform only')    

@cli.command()
@click.pass_context
def check_mbplugin_ini(ctx):
    'Проверка INI на корректность'
    name = 'check_mbplugin_ini'
    # Проверку сделаю позже, пока ее нет
    try:
        ini=store.ini()
        ini=store.ini('phones.ini')
        click.echo(f'OK {name}')
    except Exception:
        click.echo(f'Fail {name}:\n{"".join(traceback.format_exception(*sys.exc_info()))}')



if __name__ == '__main__':
    cli(obj={})
