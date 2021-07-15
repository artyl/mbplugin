# -*- coding: utf8 -*-
''' Автор ArtyLa 
для того чтобы не писать утилиты два раза для windows и linux все переносим сюда, а 
непосредственно в bat и sh скриптах оставляем вызов этого скрипта
'''
import os, sys, re, time, subprocess, shutil, glob, traceback, logging, importlib
import click, requests
import rlcompleter, readline

readline.parse_and_bind("tab: complete")
# Т.к. мы меняем текущую папку, то sys.argv[0] будет смотреть не туда, пользоваться можно только
# папка где плагины
PLUGIN_PATH = os.path.abspath(os.path.split(__file__)[0])
# Папка корня standalone версии на 2 уровня вверх (оно же settings.mbplugin_root_path)
ROOT_PATH = os.path.abspath(os.path.join(PLUGIN_PATH, '..', '..'))
STANDALONE_PATH = ROOT_PATH
# папка где embedded python (только в windows)
EMB_PYTHON_PATH = os.path.abspath(os.path.join(PLUGIN_PATH, os.path.join('..', 'python')))
SYS_PATH_ORIGIN = sys.path[:]  # Оригинальное значение sys.path
# TODO пробуем не фиксировать путь и не переходить по папкам
# Fix sys.argv[0]
# sys.argv[0] = os.path.abspath(sys.argv[0])
# Т.к. все остальные ожидают что мы находимся в папке plugin переходим в нее
# os.chdir(PLUGIN_PATH)
try:
    import store
except ModuleNotFoundError:
    click.echo(f'Not found plugin folder use\n  {sys.argv[0]} fix-embedded-python-path')
    sys.path.insert(0, PLUGIN_PATH)
    import store

def http_command(cmd):
    'Посылаем сигнал локальному веб серверу'
    import httpserver_mobile
    port = store.options('port',section='HttpServer')
    try:
        return requests.get(f'http://127.0.0.1:{port}/{cmd}').content.decode('cp1251')
    except Exception:
        pass 

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
@click.argument('name', type=str)
@click.pass_context
def hello(ctx, name):
    'Пока для экспериментов оставил,потом уберу'
    click.echo(f'Hello World! {ctx.obj} {name}')

@cli.command()
@click.argument('expression', type=str, nargs=-1)
@click.pass_context
def set(ctx, expression):
    '''Установка/сброс опции, для флагов используйте 1/0
    если в качестве значения указан default происходит сброс к установкам по умолчанию
    для установки set ini/HttpServer/start_http=1  
    или для сброса set ini/HttpServer/start_http=default       
    '''
    expression_prep = '='.join(expression)
    mbplugin_ini = store.ini()
    mbplugin_ini.read()
    if not re.match(r'^\w+/\w+/\w+=\S+$', expression_prep):
        click.echo(f'Non valid expression {expression_prep}')
        return
    path, value = expression_prep.split('=')
    _, section, key = path.split('/')
    if value.lower() == 'default' and key in mbplugin_ini.ini[section]:
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
def pip_update(ctx):
    '''Обновляем пакеты по requirements.txt или requirements_win.txt '''
    if sys.platform == 'win32':
        os.system(f'"{sys.executable}" -m pip install -r {os.path.join("mbplugin","docker","requirements_win.txt")}')
    else:
        os.system(f'"{sys.executable}" -m pip install -r {os.path.join("mbplugin","docker","requirements.txt")}')
         

@cli.command()
@click.pass_context
def clear_browser_cache(ctx):
    '''Очищаем кэш браузера'''
    name = 'clear_browser_cache'
    try:
        [os.remove(fn) for fn in glob.glob(os.path.join(ROOT_PATH, 'mbplugin', 'store', 'p_*'))]
        shutil.rmtree(os.path.join(ROOT_PATH, 'mbplugin', 'store', 'puppeteer'), ignore_errors=True)
        shutil.rmtree(os.path.join(ROOT_PATH, 'mbplugin', 'store', 'headless'), ignore_errors=True)
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
            #os.system(f"{os.path.join(ROOT_PATH, 'mbplugin', 'dllsource', 'compile_all_p.bat')}")
            for fn in glob.glob('mbplugin\\plugin\\*.py'):
                pluginname = f'p_{os.path.splitext(os.path.split(fn)[1])[0]}'
                src = os.path.join(ROOT_PATH, 'mbplugin', 'dllsource', pluginname + '.dll')
                dst = os.path.join(ROOT_PATH, 'mbplugin', 'dllplugin', pluginname + '.dll')
                compile_bat = os.path.join(ROOT_PATH, 'mbplugin', 'dllsource', 'compile.bat')
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
    name = 'check-import'
    try:
        import telegram, requests, PIL, bs4, readline, psutil, playwright, schedule
        if sys.platform == 'win32':
            import win32api, win32gui, win32con, pyodbc, pystray
    except ModuleNotFoundError:
        click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')
        return
    click.echo(f'OK {name}')

@cli.command()
@click.pass_context
def web_control(ctx):
    'Открываем страницу управления mbplugin (если запущен веб сервер)'
    name = 'web-control'
    if sys.platform == 'win32':
        start_cmd = 'start'
    elif sys.platform == 'linux':
        start_cmd = 'xdg-open'
    elif sys.platform == 'darwin':
        start_cmd = 'open'        
    else:
        click.echo(f'Unknown platform {sys.platform}')
    os.system(f'{start_cmd} http://localhost:{store.options("port", section="HttpServer")}/main')
    click.echo(f'OK {name}')

@cli.command()
@click.argument('turn', type=click.Choice(['on', 'off'], case_sensitive=False), default='on')
@click.pass_context
def autostart_web_server(ctx, turn):
    '''Автозапуск web сервера (только windows) и только если разрешен в ini
    on - Создаем lnk на run_webserver.bat и помещаем его в автозапуск и запускаем
    off - убираем из автозапуска
    для отключения в ini дайте команду mbp set ini\HttpServer\start_http=0
    '''
    name = 'autostart-web-server'
    if sys.platform == 'win32':
        try:
            import win32com.client
            shell = win32com.client.Dispatch('WScript.Shell')
            lnk_path = os.path.join(ROOT_PATH, 'mbplugin', 'run_webserver.lnk')
            lnk_startup_path = f"{os.environ['APPDATA']}\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
            lnk_startup_full_name = f"{os.environ['APPDATA']}\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\run_webserver.lnk"
            shortcut = shell.CreateShortCut(lnk_path)
            shortcut.Targetpath = os.path.abspath(os.path.join(ROOT_PATH, 'mbplugin', 'run_webserver.bat'))
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
    name = 'run-web-server'
    try:
        if sys.platform == 'win32':
            lnk_path = os.path.join(ROOT_PATH, 'mbplugin', 'run_webserver.bat')
            os.system(f'"{lnk_path}"')
            click.echo(f'OK {name}')
        else:
            import httpserver_mobile
            httpserver_mobile.WebServer()
            time.sleep(4)
            click.echo(f'OK {name}')
    except Exception:
        click.echo(f'Fail {name}: {"".join(traceback.format_exception(*sys.exc_info()))}')                

@cli.command()
@click.pass_context
def restart_web_server(ctx):
    'Останавливает web сервер'
    name = 'restart-web-server'
    http_command(cmd='restart')
    click.echo(f'OK {name}')

@cli.command()
@click.pass_context
def stop_web_server(ctx):
    'Останавливает web сервер'
    name = 'stop-web-server'
    http_command(cmd='exit')
    click.echo(f'OK {name}')

@cli.command()
@click.pass_context
def reload_schedule(ctx):
    'Перечитывает расписание запросов баланса'
    name = 'reload-schedule'
    res = http_command(cmd='reload_schedule')
    click.echo(f'OK {name}\n{res}')

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
    path = os.path.join(ROOT_PATH, 'mbplugin', 'jsmblhplugin', 'p_test1_localweb.jsmb')
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
    name = 'check-dll'
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
    name = 'check-playwright'
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
def init(ctx):
    '''Инициализация можно втором параметром указать noweb тогда вебсервер не будет запускаться и помещаться в автозапуск
    Если в mbplugin.ini пути не правильные то прописывает абсолютные пути к тем файлам, которые лежат в текущей папке 
    '''
    name = 'init'
    try:
        if not os.path.exists(os.path.join(STANDALONE_PATH, 'phones.ini')):
            click.echo(f'The folder {STANDALONE_PATH} must contain a file phones.ini')
            return
        ini=store.ini()
        ini.read()
        # TODO пока для совместимости НЕ Убираем устаревшую секцию MobileBalance - она больше не используется
        # ini.ini.remove_section('MobileBalance')
        # Если лежит mobilebalance - отрабатываем обычный, а не автономный конфиг
        if not os.path.exists(os.path.join(STANDALONE_PATH, 'MobileBalance.exe')):
            #click.echo(f'The folder {STANDALONE_PATH} must not contain a file mobilebalance.exe')
            # Запись SQLITE, создание report и работу с phone.ini из скриптов точно включаем если рядом нет mobilebalance.exe, иначе это остается на выбор пользователя
            ini.ini['Options']['sqlitestore'] = '1'
            ini.ini['Options']['createhtmlreport'] = '1'
            ini.ini['Options']['phone_ini_save'] = '1'
        # TODO пока для совместимости ini со старой версией оставляем путь как есть если если он абсолютный и файл по нему есть
        if not(os.path.abspath(ini.ini['Options']['dbfilename']) == os.path.abspath('BalanceHistory.sqlite') and os.path.exists(ini.ini['Options']['dbfilename'])):
            ini.ini['Options']['dbfilename'] = 'BalanceHistory.sqlite'
        if not (os.path.abspath(ini.ini['Options']['balance_html']) == os.path.abspath('balance.html') and os.path.exists(ini.ini['Options']['balance_html'])):
            ini.ini['Options']['balance_html'] = 'balance.html'
        ini.write()
        click.echo(f'OK {name}')
    except Exception:
        click.echo(f'Fail {name}:\n{"".join(traceback.format_exception(*sys.exc_info()))}')    

@cli.command()
@click.option('--only_failed', is_flag=True, help='Запросить балансы, по которым были ошибки')
@click.argument('filter', nargs=-1)
@click.pass_context
def get_balance(ctx, only_failed, filter):
    'Получение балансов, можно указать only_failed, тогда будут запрошены только те где последняя попытка была неудачной'
    name = 'get-balance'
    import httpserver_mobile
    #breakpoint()
    res = httpserver_mobile.getbalance_standalone(filter=filter,only_failed=only_failed)
    click.echo(f'OK {name}\n{res}')

@cli.command()
@click.pass_context
def refresh_balance_html(ctx):
    'Обновить balance.html'
    name = 'refresh-balance-html'
    import httpserver_mobile
    res = httpserver_mobile.write_report()
    click.echo(f'OK {name}\n{res}')

@cli.command()
@click.pass_context
def copy_all_from_mdb(ctx):
    'копировать все данные из mdb'
    name = 'copy-all-from-mdb'
    import dbengine
    store.turn_logging(logginglevel=logging.DEBUG)
    res = dbengine.update_sqlite_from_mdb(deep=10000)
    click.echo(f'OK {name}\n{res}')

@cli.command()
@click.pass_context
def send_tgbalance(ctx):
    'Отправка баланса TG через API веб сервера'
    name = 'send-tgbalance'
    # Sendtgbalance
    res1 = http_command(cmd='sendtgbalance')
    # Subscription
    res2 = http_command(cmd='sendtgsubscriptions')
    click.echo(f'OK {name}\nSendtgbalance: {res1}\nSubscription: {res2}')

@cli.command()
@click.pass_context
def send_tgbalance_over_requests(ctx):
    name = 'send_tgbalance_over_requests'
    'Отправка баланса TG чистым requests без использования web сервера'
    # Balanse over requests
    import httpserver_mobile
    httpserver_mobile.send_telegram_over_requests()
    click.echo(f'OK {name}')

@cli.command()
@click.argument('action', type=click.Choice(['hide', 'show'], case_sensitive=False), default='hide')
@click.pass_context
def show_chrome(ctx, action):
    'Показывает спрятанный crome. Работает только на windows, и только при headless_chrome = 0, если chrome запущен в режиме headless то его показать нельзя'
    name = 'show-chrome'
    import browsercontroller
    if sys.platform == 'win32':
        browsercontroller.hide_chrome(hide=(action == 'hide'))
        click.echo(f'OK {name}')
    else:
        click.echo(f'{name}:On windows platform only')    

@cli.command()
@click.pass_context
def check_ini(ctx):
    'Проверка INI на корректность'
    name = 'check-ini'
    # Проверку сделаю позже, пока ее нет
    try:
        ini=store.ini()
        ini.read()
        click.echo(f'OK {name} mbplugin.ini')
        ini=store.ini('phones.ini')
        ini.read()
        click.echo(f'OK {name} phones.ini')
    except Exception:
        click.echo(f'Fail {name}:\n{"".join(traceback.format_exception(*sys.exc_info()))}')

@cli.command()
@click.option('-b', '--bpoint', type=int)
@click.argument('plugin', type=str)
@click.argument('login', type=str)
@click.argument('password', type=str)
@click.pass_context
def check_plugin(ctx, bpoint, plugin, login, password):
    'Проверка работы плагина по заданному логину и паролю'
    name = 'check-plugin'
    store.turn_logging() 
    click.echo(f'{plugin} {login} {password}')
    import httpserver_mobile
    if bpoint:
        import pdb
        pdbpdb = pdb.Pdb()
        lang = 'p'
        plugin = plugin.split('_', 1)[1]  # plugin это все что после p_
        module = __import__(plugin, globals(), locals(), [], 0)
        importlib.reload(module)  # обновляем модуль, на случай если он менялся
        storename = re.sub(r'\W', '_', f"{lang}_{plugin}_{login}")
        pdbpdb.set_break(module.__file__, bpoint)
        #module.get_balance(login,  password, storename)
        _ = login,  password, storename  # dummy linter - use in pdbpdb.run
        res = pdbpdb.run("module.get_balance(login,  password, storename)", globals(), locals())
        #res = exec("httpserver_mobile.getbalance_plugin('url', [plugin, login, password, '123'])", globals(), locals())
        #breakpoint()
    else:
        res = httpserver_mobile.getbalance_plugin('url', [plugin, login, password, '123'])
    click.echo(f'{name}:\n{res}')

@cli.command()
@click.option('-f', '--force', is_flag=True, help='С заменой измененых файлов')
@click.argument('branch', nargs=-1)
@click.pass_context
def git_update(ctx, force, branch):
    '''Обновление mbplugin из https://github.com/artyl/mbplugin если репозиторий не установлен устанавливаем
    При желании можно явно указать комит/тэг/ветку на которую переключаемся'''
    name = 'git-update'
    # TODO проверить наличие git в системе
    if os.system('git --version') > 0:
        click.echo('git not found')
        return
    if len(branch) > 2:
        click.echo('Use not more 1 phrases for branch')
        return
    branch_name = 'dev_playwright'  # TODO после переключения в master поменять на master и закомитить последнюю версию с master в ветку dev_playwright
    if len(branch) == 1:
        branch_name = branch[0]
    if re.match('\A0\.99.(\d+)\.?\d?\Z', branch_name) and int(re.search('\A0\.99.(\d+)\.?\d*\Z', branch_name).groups()[0])>32:
        # В старые версии где еще нет mbp переключаться нельзя обратно уже тем же путем будет не вернуться
        click.echo('Switch to this version broke mbp')
        return
    if os.path.isdir('mbplugin') and not os.path.isdir(os.path.join('mbplugin', '.git')):
        os.system(f'git clone --bare https://github.com/artyl/mbplugin.git mbplugin/.git')
        os.system(f'git -C mbplugin config remote.origin.fetch +refs/heads/*:refs/remotes/origin/*')
        os.system(f'git -C mbplugin branch -D dev_playwright')
        os.system(f'git -C mbplugin branch -D master')
        os.system(f'git -C mbplugin branch -D dev')
        os.system(f'git -C mbplugin config --local --bool core.bare false')
    if not os.path.isdir(os.path.join('mbplugin', '.git')):
        click.echo(f"{os.path.join('mbplugin', '.git')} is not folder")
        return
    os.system(f'git -C mbplugin fetch --all --prune')
    os.system(f'git -C mbplugin stash')
    os.system(f'git -C mbplugin pull')
    os.system(f'git -C mbplugin checkout {"-f" if force else ""} {branch_name}')
    click.echo(f'OK {name}')

@cli.command()
@click.pass_context
def list_phone(ctx):
    phones = store.ini('phones.ini')
    phones.read()
    for sec in phones.ini.sections():
        if phones.ini[sec].get('Monitor', 'FALSE') == 'TRUE':
            print(f'{sec:3} {phones.ini[sec]["Alias"]:20} {phones.ini[sec]["Region"]:20} {phones.ini[sec]["Number"]:20}')

@cli.command()
@click.option('-n', '--num', type=int, default=-1)
@click.option('-d', '--delete', is_flag=True)
@click.option('-pl', '--plugin', type=str, default='')
@click.option('-m', '--monitor', type=click.Choice(['true', 'false', ''], case_sensitive=False), default='')
@click.option('-a', '--alias', type=str, default='')
@click.option('-l', '--login', type=str, default='')
@click.option('-p', '--password', type=str, default='')
@click.pass_context
def change_phone(ctx, num, delete, plugin, monitor, alias, login, password):
    'Добавить или изменить или удалить номер в phones.ini'
    name = 'change-phone'
    if str(store.options('phone_ini_save')) == '0':
        click.echo('Work with phone.ini from mbp not allowed (turn phone_ini_save=1 in mbplugin.ini)')
        return
    cmd = "DELETE" if delete else ("CHANGE" if num>0 else "CREATE")
    click.echo(f'{cmd}')
    click.echo(f'num:{num} alias:{alias}, plugin:{plugin}, monitor:{monitor}, login:{login}, password:{password}')
    phones = store.ini('phones.ini')
    phones.read()
    if delete:
        if str(num) in phones.ini.sections():
            click.echo(f'Delete {list(phones.ini[str(num)].items())}')
            del phones.ini[str(num)]
        else: 
            for sec in phones.ini.sections():
                if ((phones.ini[sec]['Region'] == plugin or plugin == '') and 
                    (phones.ini[sec]['Number'] == login or login == '') and 
                    (phones.ini[sec]['Alias'] == alias or alias == '')):
                    click.echo(f'Delete {list(phones.ini[sec].items())}')
                    del phones.ini[sec]
    if not delete and num < 0:
        if plugin == '' or login == '' or password =='':
            click.echo('For new phone plugin login and password must be specified')
            return
        exists = [sec for sec in phones.ini.sections()
                  if phones.ini[sec]['Region'] == plugin and phones.ini[sec]['Number'] == login]
        if len(exists) > 0:
            click.echo(f'Already exists {exists[0]} {phones.ini[exists[0]]}')
            return
        sec = str(max([int(i) for i in phones.ini.sections()])+1)
        phones.ini[sec] = {
            'Region': plugin,
            'Monitor': str(monitor!='false').upper(),
            'Alias': (login if alias == '' else alias),
            'Number': login,
            'Password2': password
        }
        click.echo(f'Create {list(phones.ini[sec].items())}')
    if not delete and str(num) in phones.ini.sections():
        if plugin !='':
            phones.ini[str(num)]['Region'] = plugin
        if monitor != '':
            phones.ini[str(num)]['Monitor'] = monitor.upper()
        if alias != '':
            phones.ini[str(num)]['Alias'] = alias
        if login != '':
            phones.ini[str(num)]['Number'] = login
        if password != '':
            phones.ini[str(num)]['Password2'] = password
        click.echo(f'Change {list(phones.ini[str(num)].items())}')
    phones.write()
    click.echo(f'OK {name} {cmd}')

@cli.command()
@click.pass_context
def version_download(ctx):
    name = 'version-download'
    store.download_file('https://github.com/artyl/mbplugin/archive/refs/heads/dev_playwright.zip', os.path.join('mbplugin','pack','new.zip'))
    click.echo(f'OK {name}')

@cli.command()
@click.pass_context
def version_check(ctx):
    name = 'version-check'
    res = store.version_check(os.path.join('mbplugin','pack','new.zip'))
    click.echo(f'{"OK" if len(res)==0 else "FAIL"} {name}')
    click.echo('\n'.join(res))

@cli.command()
@click.option('-f', '--force', is_flag=True, help='С заменой измененых файлов')
@click.pass_context
def version_update(ctx, force):
    name = 'version-update'
    current_zipname = os.path.join('mbplugin','pack','current.zip')
    new_zipname = os.path.join('mbplugin','pack','new.zip')
    if not force:
        diff = version_check(current_zipname)
        if len(diff) > 0:
            print(f'The current files differ frome the release (use -f )')
            print('\n'.join())
            return
    store.version_update(new_zipname)
    click.echo(f'OK {name}')

@cli.command()
@click.pass_context
def db_tables(ctx):
    'Запуск запроса к БД SQLite'
    name = 'db-tables'
    if store.options('sqlitestore') == '1':
        import dbengine
        db = dbengine.dbengine(store.options('dbfilename'))
        query1 = "SELECT name FROM sqlite_master WHERE type='table'"
        dbdata = db.cur.execute(query1).fetchall()
        for line in dbdata:
            tbl = line[0]
            cnt = db.cur.execute(f"select count(*) from {tbl}").fetchall()[0][0]
            print(f'{tbl} {cnt}') 

@cli.command()
@click.argument('query', nargs=1)
@click.pass_context
def db_query(ctx, query):
    'Запуск запроса к БД SQLite'
    name = 'db-query'
    if store.options('sqlitestore') == '1':
        import dbengine

        dbfilename = store.options('dbfilename')
        db = dbengine.dbengine(dbfilename)
        cur = db.cur.execute(query)
        if cur.description is not None:
            description = cur.description
            dbheaders = list(zip(*cur.description))[0]
            dbdata = cur.fetchall()
            res = [list(dbheaders)] + [i for i in dbdata]
            for line in res:
                print('\t'.join(map(str,line)))
        if cur.rowcount >= 0:
            print(f'{cur.rowcount} line affected')
        db.conn.commit()
    click.echo(f'OK {name}')

@cli.command()
@click.argument('args', nargs=-1)
@click.pass_context
def bash(ctx, args):
    'Запуск консоли с окружением для mbplugin - удобно в docker и venv'
    name = 'bash'
    if sys.platform == 'win32':
        os.system(f'cmd {" ".join(args)}')
    else:
        os.system(f'bash {" ".join(args)}')
    click.echo(f'OK {name}')

if __name__ == '__main__':
    cli(obj={})
