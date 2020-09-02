# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys,io, re, time, json, traceback, threading, logging, importlib, configparser, queue
import wsgiref.simple_server, socketserver, socket, requests, urllib.parse, urllib.request, bs4
import settings, store, dbengine  # pylint: disable=import-error
try:
    import win32api, win32gui, win32con, winerror
except ModuleNotFoundError:
    print('No win32 installed, no tray icon')
try:
    import telegram
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
except ModuleNotFoundError:
    print('No telegram installed, no telegram bot')

lang = 'p'  # Для плагинов на python преффикс lang всегда 'p'

HTML_NO_REPORT = '''Для того чтобы были доступны отчеты необходимо в mbplugin.ini включить запись результатов в sqlite базу<br>
sqlitestore = 1<br>Также можно настроить импорт из базы BalanceHistory.mdb включив <br>
createhtmlreport = 1<br>
После включения, запустите mbplugin\\setup_and_check.bat
'''


def find_ini_up(fn):
    allroot = [os.getcwd().rsplit('\\', i)[0] for i in range(len(os.getcwd().split('\\')))]
    all_ini = [i for i in allroot if os.path.exists(os.path.join(i, fn))]
    if all_ini != []:
        return all_ini[0]


def getbalance_plugin(method, param_source):
    'fplugin, login, password, date'
    param = {}
    if method == 'url':
        if len(param_source) != 4:
            return 'text/html', [f'<html>Unknown call - use getbalance/plugin/login/password/date</html>']
        param['fplugin'], param['login'], param['password'], param['date'] = param_source
    elif method == 'get':
        param = param_source
        # все параметры пришли ?
        if len(set(param.keys()).intersection(set('plugin,login,password,date'.split(',')))) < 4:
            return 'text/html', [f'<html>Unknown call - use get?plugin=PLUGIN&login=LOGIN&password=PASSWORD&date=DATE</html>']
        param = {i: param_source[i][0] for i in param_source}  # в get запросе все параметры - списки
        param['fplugin'] = param['plugin']  # наш параметр plugin на самом деле fplugin
    else:
        logging.error(f'Unknown method {method}')
    logging.info(f'Webserver thread_count={len(threading.enumerate())}')
    logging.info(f"Start {param['fplugin']} {param['login']}")
    # Это плагин от python ?
    if param['fplugin'].startswith(f'{lang}_'):
        # get balance
        plugin = param['fplugin'].split('_', 1)[1]  # plugin это все что после p_
        module = __import__(plugin, globals(), locals(), [], 0)
        importlib.reload(module)  # обновляем модуль, на случай если он менялся
        storename = re.sub(r'\W', '_', f"{lang}_{plugin}_{param['login']}")
        result = module.get_balance(param['login'], param['password'], storename)
        text = store.result_to_html(result)
        # пишем в базу
        dbengine.write_result_to_db(f'{lang}_{plugin}', param['login'], result)
        # обновляем данные из mdb
        dbengine.update_sqlite_from_mdb()
        # генерируем balance_html
        write_report()
        logging.info(f"Complete {param['fplugin']} {param['login']}")
        return 'text/html', text
    logging.error(f"Unknown plugin {param['fplugin']}")
    return 'text/html', [f"<html>Unknown plugin {param['fplugin']}</html>"]


def view_log(param):
    try:
        lines = int(param['lines'][0])
    except Exception:
        lines = 100
    fn = store.options('logginghttpfilename')
    res = open(fn).readlines()[-lines:]
    for num in range(len(res)):
        #.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        if ' ERROR ' in res[num]:
            res[num] = f'<span style="color:red;background-color:white">{res[num]}</span>'
        elif ' WARNING ' in res[num]:
            res[num] = f'<span style="color:yellow;background-color:white">{res[num]}</span>'
    return 'text/html; charset=cp1251', ['<html><head></head><body><pre>']+res+['</pre><script>window.scrollTo(0,document.body.scrollHeight);</script></body></html>']

def getreport(param=[]):
    style = '''<style type="text/css">
    table{font-family: Verdana; font-size:85%}
    th {background-color: #D1D1D1}
    td{white-space: nowrap;text-align: right;}
    .hdr  {text-align:left;color:#FFFFFF; font-weight:bold; background-color:#0E3292; padding-left:5}
    .n    {background-color: #FFFFE1}
    .e    {background-color: #FFEBEB}
    .n_us {background-color: #FFFFE1; color: #808080}
    .e_us {background-color: #FFEBEB; color: #808080}
    .mark{color:#FF0000}
    .mark_us{color:#FA6E6E}
    .summ{background-color: lightgreen; color:black}
    .p_n{color:#634276}
    .p_r{color:#006400}
    .p_b{color:#800000}
    #Balance, #SpendBalance {text-align: right; font-weight:bold}
    #Indication, #Alias, #KreditLimit, #PhoneDescr, #UserName, #PhoneNum, #PhoneNumber, #BalExpired, #LicSchet, #TarifPlan, #BlockStatus, #AnyString, #LastQueryTime{text-align: left}
    </style>'''
    template = '''
    <?xml version="1.0" encoding="windows-1251" ?>
    <html>
    <head><title>MobileBalance</title></head>{style}
    <body style="font-family: Verdana; cursor:default">
    <table id="BackgroundTable">
    <tr><td class="hdr">Информация о балансе телефонов - MobileBalance Mbplugin</td></tr>
    <tr><td bgcolor="#808080">
    <table id="InfoTable" border="0" cellpadding="2" cellspacing="1">
        <tr id="header">{html_header}</tr>
        {html_table}
    </table>
    </td></tr>
    </table>
    </body>
    </html>'''
    db = dbengine.dbengine(store.options('dbfilename'))
    # номера провайдеры и логины из phones.ini
    options_ini = store.ini('options.ini').read()

    edBalanceLessThen = float(options_ini['Mark']['edBalanceLessThen'])  # помечать балансы меньше чем
    edTurnOffLessThen = float(options_ini['Mark']['edTurnOffLessThen'])  # помечать когда отключение CalcTurnOff меньше чем

    num_format = '' if len(param) == 0 or not param[0].isnumeric() else str(int(param[0]))
    table_format = store.options('table_format' + num_format, default=store.options('table_format',section='HttpServer'), section='HttpServer')
    table = db.report()
    if 'Alias' not in table_format:
        table_format = 'NN,Alias,' + table_format  # Если старый ini то этих столбцов нет - добавляем
    table = [i for i in table if i['Alias']!='Unknown']  # filter Unknown
    table.sort(key=lambda i:[i['NN'],i['Alias']])  # sort by NN, after by Alias
    header = table_format.strip().split(',')
    # классы для формата заголовка
    header_class = {'Balance': 'p_b', 'RealAverage': 'p_r', 'BalDelta': 'p_r', 'BalDeltaQuery': 'p_r', 'NoChangeDays': 'p_r', 'CalcTurnOff': 'p_r', 'MinAverage': 'p_r', }
    html_header = ''.join([f'<th id="h{h}" class="{header_class.get(h,"p_n")}">{dbengine.PhonesHText.get(h,h)}</th>' for h in header])
    html_table = []
    for line in table:
        html_line = []
        for he in header:
            if he not in line:
                continue
            el = line[he]
            mark = ''  # class="mark"
            if he == 'Balance' and el is not None and el < edBalanceLessThen:
                mark = ' class="mark" '  # Красим когда мало денег
            if he == 'CalcTurnOff' and el is not None and el < edTurnOffLessThen:
                mark = ' class="mark" '  # Красим когда надолго не хватит
            if el is None:
                el = ''
            if he != 'Balance' and (el == 0.0 or el == 0):
                el = ''
            html_line.append(f'<{"th" if he=="NN" else "td"} id="{he}"{mark}>{el}</td>')
        html_table.append(f'<tr id="row" class="n">{"".join(html_line)}</tr>')
    res = template.format(style=style, html_header=html_header, html_table='\n'.join(html_table))
    return 'text/html', [res]


def write_report():
    'сохраняем отчет balance_html если в ini createhtmlreport=1'
    try:
        if store.options('createhtmlreport') == '1':
            _, res = getreport()
            balance_html = store.options('balance_html')
            logging.info(f'Создаем {balance_html}')
            open(balance_html, encoding='utf8', mode='w').write('\n'.join(res))
    except Exception:
        logging.error(f'Ошибка генерации {balance_html} {"".join(traceback.format_exception(*sys.exc_info()))}')


def filter_balance(table, filter='FULL', params={}):
    ''' Фильтруем данные для отчета
    filter = FULL - Все телефоны, LASTCHANGE - Изменивниеся за день, LASTCHANGE - Изменившиеся в последнем запросе
    params['include'] = None - все, либо список через запятую псевдонимы или логины или какая-то их уникальная часть для включения в результат
    params['exclude'] = None - все, либо список через запятую псевдонимы или логины или какая-то их уникальная часть для включения в результат'''
    # фильтр по filter_include
    if 'include' in params:
        filter_include = [re.sub(r'\W', '', el) for el in params['include'].split(',')]
        table = [line for line in table if len([1 for i in filter_include if i in re.sub(r'\W', '', '_'.join(map(str,line.values())))])>0]
    # фильтр по filter_exclude
    if 'exclude' in params:
        filter_exclude = [re.sub(r'\W', '', el) for el in params['exclude'].split(',')]
        table = [line for line in table if len([1 for i in filter_exclude if i in re.sub(r'\W', '', '_'.join(map(str,line.values())))])==0]
    if filter == 'LASTCHANGE': # TODO сделать настройку в ini на счет line['Balance']
        table = [line for line in table if line['BalDeltaQuery'] != 0 and line['Balance'] !=0]
        table = [line for line in table if line['BalDeltaQuery'] != '' and line['Balance'] !='']
    elif filter == 'LASTDAYCHANGE':
        table = [line for line in table if line['BalDelta'] != 0 and line['Balance'] !=0]
        table = [line for line in table if line['BalDelta'] != '' and line['Balance'] !='']
    return table


def prepare_balance_mobilebalance(filter='FULL', params={}):
    """Формируем текст для отправки в telegram из html файла полученного из web сервера mobilebalance
    """
    url = store.options('mobilebalance_http', section='Telegram', mainparams=params)
    tgmb_format = store.options('tgmb_format', section='Telegram', mainparams=params)
    response1_text = requests.get(url).content.decode('cp1251')
    # нет таблицы
    if 'Введите пароль' in response1_text or '<table' not in response1_text:
        res = 'Неправильный пароль для страницы баланса в ini, проверьте параметр mobilebalance_http'
        return res
    soup = bs4.BeautifulSoup(response1_text, 'html.parser')
    headers = [''.join(el.get('id')[1:]) for el in soup.find(id='header').findAll('th')]
    if filter == 'LASTCHANGE' and 'BalDeltaQuery' not in headers:  # нет колонки Delta (запрос)
        res = 'Включите показ колонки Delta (запрос) в настройках mobilebalance'
        return res
    elif filter == 'LASTDAYCHANGE' and 'BalDelta' not in headers:  # нет колонки Delta (день)
        res = 'Включите показ колонки Delta (день) в настройках mobilebalance'
        return res
    data = [[''.join(el.contents) for el in line.findAll(['th', 'td'])] for line in soup.findAll(id='row')]
    table = [dict(zip(headers, line)) for line in data]
    table = filter_balance(table, filter, params)
    res = [tgmb_format.format(**line) for line in table]
    return '\n'.join(res)


def prepare_balance_sqlite(filter='FULL', params={}):
    'Готовим данные для отчета из sqlite базы'
    db = dbengine.dbengine(store.options('dbfilename', mainparams=params))
    table_format = store.options('tg_format', section='Telegram', mainparams=params).replace('\\t','\t').replace('\\n','\n')
    # table_format = 'Alias,PhoneNumber,Operator,Balance'
    # Если формат задан как перечисление полей через запятую - переделываем под формат
    if re.match(r'^(\w+(?:,|\Z))*$', table_format.strip()):
        table_format = ' '.join([f'{{{i}}}' for i in table_format.strip().split(',')])
    table = db.report()
    table = [i for i in table if i['Alias']!='Unknown']  # filter Unknown
    table.sort(key=lambda i:[i['NN'],i['Alias']])  # sort by NN, after by Alias
    table = filter_balance(table, filter, params)
    res = [table_format.format(**line) for line in table]
    return '\n'.join(res)


def prepare_balance(filter='FULL', params={}):
    """Prepare balance for TG."""
    try:
        baltxt = ''
        if store.options('tg_from', section='Telegram', mainparams=params) == 'sqlite':
            baltxt = prepare_balance_sqlite(filter, params)
        else:
            baltxt = prepare_balance_mobilebalance(filter, params)
        if baltxt == '' and str(store.options('send_empty', section='Telegram', mainparams=params))=='1':
            baltxt = 'No changes'
        return baltxt
    except Exception:
        exception_text = f'Ошибка: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        return 'error'


def send_telegram_over_requests(text=None, auth_id=None, filter='FULL', params={}):
    """Отправка сообщения в телеграм через requests без задействия python-telegram-bot
    Может пригодится при каких-то проблемах с ботом или в ситуации когда на одной машине у нас крутится бот, 
    а с другой в этого бота мы еще хотим засылать инфу
    text - сообщение, если не указано, то это баланс для телефонов у которых он изменился
    auth_id - список id через запятую на которые слать, если не указано, то берется список из mbplugin.ini 
    """
    if text is None:
        text = prepare_balance(filter, param)
    api_token = store.options('api_token', section='Telegram', mainparams=params).strip()
    if len(api_token) == 0:
        logging.info('Telegtam api_token not found')
        return
    if auth_id is None:
        auth_id = list(map(int, store.options('auth_id', section='Telegram', mainparams=params).strip().split(',')))
    else:
        auth_id = list(map(int,str(auth_id).strip().split(',')))
    r=[requests.post(f'https://api.telegram.org/bot{api_token}/sendMessage',data={'chat_id':chat_id,'text':text,'parse_mode':'HTML'}) for chat_id in auth_id if text!='']
    return [repr(i) for i in r]


def tray_icon(cmdqueue):
    'Выставляем для trayicon daemon, чтобы ушел вслед за нами функция нужна для запуска в отдельном thread'
    if str(store.options('show_tray_icon')) == '1':
        TrayIcon(cmdqueue).run_forever()


class TrayIcon:
    def __init__(self, cmdqueue):
        self.cmdqueue = cmdqueue
        msg_TaskbarRestart = win32gui.RegisterWindowMessage("TaskbarCreated")
        message_map = {
            msg_TaskbarRestart: self.OnRestart,
            win32con.WM_DESTROY: self.OnDestroy,
            win32con.WM_COMMAND: self.OnCommand,
            win32con.WM_USER + 20: self.OnTaskbarNotify,
        }
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "PythonTaskbarDemo"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32api.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map  # could also specify a wndproc.
        try:
            classAtom = win32gui.RegisterClass(wc)
            _ = classAtom  # dummy pylint
        except win32gui.error as err_info:
            if err_info.winerror != winerror.ERROR_CLASS_ALREADY_EXISTS:
                raise
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(wc.lpszClassName, "Taskbar Demo",
                                          style, 0, 0, win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT, 0, 0, hinst,
                                          None)
        win32gui.UpdateWindow(self.hwnd)
        self._DoCreateIcons()

    def run_forever(self):
        win32gui.PumpMessages()

    def _DoCreateIcons(self, iconame='httpserver.ico'):
        # Try and find a custom icon
        hinst = win32api.GetModuleHandle(None)
        iconPathName = os.path.join(os.path.split(os.path.abspath(sys.argv[0]))[0], iconame)
        if os.path.isfile(iconPathName):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst, iconPathName, win32con.IMAGE_ICON, 0, 0, icon_flags)
        else:
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "Python Demo")
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        except win32gui.error:
            print(f"Failed to add the taskbar icon - is explorer running? {''.join(traceback.format_exception(*sys.exc_info()))}")

    def OnRestart(self, hwnd, msg, wparam, lparam):
        self._DoCreateIcons()

    def OnDestroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # Terminate the app.

    def OnTaskbarNotify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_LBUTTONDBLCLK:
            # print("You double-clicked me - goodbye")
            # win32gui.DestroyWindow(self.hwnd)
            pass
        elif lparam == win32con.WM_RBUTTONUP:
            print("You right clicked me.")
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1024, "Open report")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1025, "View log")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1026, "Exit program")
            pos = win32gui.GetCursorPos()
            # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        return 1

    def OnCommand(self, hwnd, msg, wparam, lparam):
        id = win32api.LOWORD(wparam)
        port = int(store.options('port', section='HttpServer'))
        if id == 1024:
            os.system(f'start http://localhost:{port}/report')
        if id == 1025:
            os.system(f'start http://localhost:{port}/log?lines=40')
        elif id == 1026:
            print("Goodbye")
            win32gui.DestroyWindow(self.hwnd)
            self.cmdqueue.put('STOP')
        else:
            print("Unknown command -", id)


class TelegramBot():
    def auth_decorator(func):  # pylint: disable=no-self-argument
        def wrapper(self, update, context):
            if update.message.chat_id in self.auth_id():
                res = func(self, update, context)  # pylint: disable=not-callable
                return res
            else:
                logging.info(f'TG:{update.message.chat_id} unautorized get /balance')
        return wrapper

    def auth_id(self):
        auth_id = store.options('auth_id', section='Telegram').strip()
        if not re.match(r'(\d+,?)', auth_id):
            logging.error(f'incorrect auth_id in ini: {auth_id}')
        return map(int, auth_id.split(','))

    def get_id(self, update, context):
        """Echo chat id."""
        logging.info(f'TG:{update.message.chat_id} /id')
        update.message.reply_text(update.message.chat_id)

    @auth_decorator
    def get_balancetext(self, update, context):
        """Send balance only auth user."""
        logging.info(f'TG:{update.message.chat_id} /balance')
        baltxt = prepare_balance('FULL')
        update.message.reply_text(baltxt, parse_mode=telegram.ParseMode.HTML)

    @auth_decorator
    def get_balancefile(self, update, context):
        """Send balance html file only auth user."""
        logging.info(f'TG:{update.message.chat_id} /balancefile')
        _, res = getreport()
        for id in self.auth_id():
            self.updater.bot.send_document(chat_id=id, filename='balance.htm', document=io.BytesIO('\n'.join(res).strip().encode('cp1251')))

    def send_message(self, text, parse_mode='HTML', ids=None):
        if self.updater is None or text == '':
            return
        if ids is None:
            lst = self.auth_id()
        else:
            lst = ids
        for id in lst:
            self.updater.bot.sendMessage(chat_id=id, text=text, parse_mode=parse_mode)

    def send_balance(self):
        'Отправляем баланс'
        if self.updater is None or str(store.options('send_balance_changes', section='Telegram')) == '0':
            return
        baltxt = prepare_balance('LASTCHANGE')
        self.send_message(text=baltxt, parse_mode=telegram.ParseMode.HTML)

    def send_subsribtions(self):
        'Отправляем подписки - это строки из ini вида:'
        'subscribtionXXX = id:123456 include:1111,2222 exclude:6666'
        if self.updater is None:
            return
        subscribtions = store.options('subscribtion', section='Telegram', listparam=True)
        for subscr in subscribtions:
            # id:123456 include:1111,2222 -> {'id':'123456','include':'1111,2222'}
            params = {k: v.strip() for k, v in [i.split(':', 1) for i in subscr.split(' ')]}
            baltxt = prepare_balance('LASTCHANGE', params)
            ids = [int(i) for i in params.get('id', '').split(',') if i.isdigit()]
            self.send_message(text=baltxt, parse_mode=telegram.ParseMode.HTML, ids=ids)

    def stop(self):
        '''Stop bot'''
        if self.updater is not None:
            self.updater.stop()

    def __init__(self):
        api_token = store.options('api_token', section='Telegram').strip()
        request_kwargs = {}
        tg_proxy = store.options('tg_proxy', section='Telegram').strip()
        if tg_proxy.lower() == 'auto':
            request_kwargs['proxy_url'] = urllib.request.getproxies().get('https', '')
        elif tg_proxy != '' and tg_proxy.lower() != 'auto':
            request_kwargs['proxy_url'] = tg_proxy
            # ??? Надо или не надо ?
            # request_kwargs['urllib3_proxy_kwargs'] = {'assert_hostname': 'False', 'cert_reqs': 'CERT_NONE'}
        self.updater = None
        if api_token != '' and str(store.options('start_tgbot', section='Telegram')) == '1' and 'telegram' in sys.modules:
            try:
                logging.info(f'Module telegram starting for id={self.auth_id()}')
                self.updater = Updater(api_token, use_context=True, request_kwargs=request_kwargs)
                logging.info(f'{self.updater}')
                dp = self.updater.dispatcher
                dp.add_handler(CommandHandler("id", self.get_id))
                dp.add_handler(CommandHandler("balance", self.get_balancetext))
                dp.add_handler(CommandHandler("balancefile", self.get_balancefile))
                self.updater.start_polling()  # Start the Bot
                if str(store.options('send_empty', section='Telegram'))=='1':
                    self.send_message(text='Hey there!')
            except Exception:
                exception_text = f'Ошибка запуска telegram bot {"".join(traceback.format_exception(*sys.exc_info()))}'
                logging.error(exception_text)
        elif 'telegram' not in sys.modules:
            logging.info('Module telegram not found')
        elif api_token == '':
            logging.info('Telegtam api_token not found')
        elif str(store.options('start_tgbot', section='Telegram')) != '1':
            logging.info('Telegtam bot start is disabled in mbplugin.ini (start_tgbot=0)')


class Handler(wsgiref.simple_server.WSGIRequestHandler):
    # Disable logging DNS lookups
    def address_string(self):
        return str(self.client_address[0])

    def log_message(self, format, *args):
        # убираем пароль из лога
        args = re.sub('(/.*?/.*?/.*?/)(.*?)(/.*)', r'\1xxxxxxx\3', args[0]), *args[1:]
        args = re.sub('(&password=)(.*?)(&)', r'\1xxxxxxx\3', args[0]), *args[1:]
        # а если это показ лога вообще в лог не пишем, а то фигня получается
        if 'GET /log' not in args[0] and 'GET /favicon.ico' not in args[0]:
            logging.info(f"{self.client_address[0]} - - [self.log_date_time_string()] {format % args}\n")


class ThreadingWSGIServer(socketserver.ThreadingMixIn, wsgiref.simple_server.WSGIServer):
    pass


class WebServer():
    def __init__(self):
        self.cmdqueue = queue.Queue()
        logging.basicConfig(filename=store.options('logginghttpfilename'),
                            level=store.options('logginglevel' ),
                            format=store.options('loggingformat'))
        self.port = int(store.options('port', section='HttpServer'))
        self.host = store.options('host', section='HttpServer')
        with socket.socket() as sock:
            sock.settimeout(0.2)  # this prevents a 2 second lag when starting the server
            if sock.connect_ex((self.host, self.port)) == 0:
                logging.info(f"Port {self.host}:{self.port} already in use, try restart.")
                try:
                    requests.Session().get(f'http://{self.host}:{self.port}/exit', timeout=1)
                    time.sleep(3)  # Подождем пока сервер остановится
                except Exception:
                    pass
        if str(store.options('start_http', section='HttpServer')) != '1':
            logging.info(f'Start http server disabled in mbplugin.ini (start_http=0)')
            return
        with wsgiref.simple_server.make_server(self.host, self.port, self.simple_app, server_class=ThreadingWSGIServer, handler_class=Handler) as self.httpd:
            logging.info(f'Listening {self.host}:{self.port}....')
            threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
            if 'win32api' in sys.modules:  # Иконка в трее
                threading.Thread(target=lambda i=self.cmdqueue: tray_icon(i), daemon=True).start()
            if 'telegram' in sys.modules:  # telegram bot (он сам все запустит в threading)
                self.telegram_bot = TelegramBot()
            # Запустили все остальное демонами и ждем, когда они пришлют сигнал
            self.cmdqueue.get()
            self.telegram_bot.stop()
            self.httpd.shutdown()
        logging.info(f'Shutdown server {self.host}:{self.port}....')

    def simple_app(self, environ, start_response):
        try:
            status = '200 OK'
            ct, text = 'text/html', []
            fn = environ.get('PATH_INFO', None)
            _, cmd, *param = fn.split('/')
            print(f'{cmd}, {param}')
            if cmd.lower() == 'getbalance':  # старый вариант оставлен пока для совместимости
                ct, text = getbalance_plugin('url', param)  # TODO !!! Но правильно все-таки через POST
            elif cmd.lower() == 'sendtgbalance':
                self.telegram_bot.send_balance()
            elif cmd.lower() == 'sendtgsubscriptions':
                self.telegram_bot.send_subsribtions()
            elif cmd.lower() == 'get':  # вариант через get запрос
                param = urllib.parse.parse_qs(environ['QUERY_STRING'])
                ct, text = getbalance_plugin('get', param)
            elif cmd.lower() == 'log': # просмотр лога
                param = urllib.parse.parse_qs(environ['QUERY_STRING'])
                ct, text = view_log(param)
            elif cmd == '' or cmd == 'report':  # report
                if store.options('sqlitestore') == '1':
                    ct, text = getreport(param)
                else:
                    ct, text = 'text/html', HTML_NO_REPORT
            elif cmd == 'exit':  # exit cmd
                self.cmdqueue.put('STOP')
                text = ['exit']
            headers = [('Content-type', ct)]
            start_response(status, headers)
            return [line.encode('cp1251', errors='ignore') for line in text]
        except Exception:
            exception_text = f'Ошибка: {"".join(traceback.format_exception(*sys.exc_info()))}'
            logging.error(exception_text)
            headers = [('Content-type', 'text/html')]
            return ['<html>ERROR</html>'.encode('cp1251')]


def main():
    try:
        WebServer()
    except Exception:
        exception_text = f'Ошибка запуска WebServer: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)


if __name__ == '__main__':
    main()
