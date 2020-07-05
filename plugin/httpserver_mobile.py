# -*- coding: utf8 -*- 
''' Автор ArtyLa '''
import os, sys, re, time, json, traceback, threading, logging, importlib, configparser, queue
import wsgiref.simple_server, socketserver, socket, requests, urllib.parse
import settings, store, dbengine  # pylint: disable=import-error
try:
    import win32api, win32gui, win32con, winerror
except ModuleNotFoundError:
    print('No win32 installed, no tray icon')

lang='p' # Для плагинов на python преффикс lang всегда 'p'

HTML_NO_REPORT = '''Для того чтобы были доступны отчеты необходимо в mbplugin.ini включить запись результатов в sqlite базу<br>
sqlitestore = 1<br>Также можно настроить импорт из базы BalanceHistory.mdb включив <br>
createhtmlreport = 1<br>
После включения, запустите mbplugin\setup_and_check.bat
'''

def find_ini_up(fn):
    allroot = [os.getcwd().rsplit('\\',i)[0] for i in range(len(os.getcwd().split('\\')))]
    all_ini = [i for i in allroot if os.path.exists(os.path.join(i,fn))]
    if all_ini != []:
        return all_ini[0]
    

def getbalance(method, param_source):
    'fplugin, login, password, date'
    try:
        param = {}
        if method == 'url':
            if len(param_source) != 4:
                return 'text/html', [f'<html>Unknown call - use getbalance/plugin/login/password/date</html>']
            param['fplugin'], param['login'], param['password'], param['date'] = param_source
        elif method == 'get':
            #fplugin,login,password,date = param
            param = param_source
            # все параметры пришли ? 
            if len(set(param.keys()).intersection(set('plugin,login,password,date'.split(',')))) < 4:
                return 'text/html', [f'<html>Unknown call - use get?plugin=PLUGIN&login=LOGIN&password=PASSWORD&date=DATE</html>']
            param = {i:param_source[i][0] for i in param_source} #  в get запросе все параметры - списки
            param['fplugin'] = param['plugin']  # наш параметр plugin на самом деле fplugin
        else:
            logging.error(f'Unknown method {method}')
        logging.info(f"Start {param['fplugin']} {param['login']}")
        #print(f'{fn=} {fn.split("/")=}')
        #print(f'{param['fplugin']=} {param['login']=} {param['password']=} {date=}')
        # Это плагин от python ?
        if param['fplugin'].startswith(f'{lang}_'):
            # get balance
            plugin = param['fplugin'].split('_',1)[1]  # plugin это все что после p_ 
            module = __import__(plugin, globals(), locals(), [], 0)
            importlib.reload(module) # обновляем модуль, на случай если он менялся
            result = module.get_balance(param['login'], param['password'], f"{lang}_{plugin}_{param['login']}")
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
    except Exception:
        exception_text = f'Ошибка: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        return 'text/html', ['<html>ERROR</html>']

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
    options = store.read_ini()['Options']
    db = dbengine.dbengine(options.get('dbfilename', settings.dbfilename))
    #num_format = 0 if len(param)==0 or not param[0].isnumeric() else int(param[0])
    # номера провайдеры и логины из phones.ini
    options_ini = store.read_ini('options.ini') 
    #if inipath is None:return 'text/html', ['phones.ini not found']

    edBalanceLessThen = float(options_ini['Mark']['edBalanceLessThen']) # помечать балансы меньше чем
    edTurnOffLessThen = float(options_ini['Mark']['edTurnOffLessThen']) # помечать когда отключение CalcTurnOff меньше чем
    
    phones_ini = store.read_ini('phones.ini')
    #phones_ini.read_string(re.sub(r'(?usi)\[Phone\] #(\d+)',r'[\1]',open(os.path.join(inipath,'phones.ini')).read())) # replace [Phone] #123 -> [Phone #123]
    phonesdata_numb =  {(re.sub(r' #\d+','',v['Number']),v['Region']):int(k) for k,v in phones_ini.items() if k.isnumeric() and 'Monitor' in v}
    phonesdata_alias = {(re.sub(r' #\d+','',v['Number']),v['Region']):v.get('Alias','') for k,v in phones_ini.items() if k.isnumeric() and 'Monitor' in v}
    phonesdata_descr = {(re.sub(r' #\d+','',v['Number']),v['Region']):v.get('PhoneDescription','') for k,v in phones_ini.items() if k.isnumeric() and 'Monitor' in v}
    
    num_format = '' if len(param)==0 or not param[0].isnumeric() else str(int(param[0]))
    table_format = store.read_ini()['HttpServer'].get('table_format'+num_format,settings.table_format)
    header,data = db.report(table_format.strip().split(','))
    header = ['NN', 'Alias'] + list(header)
    data = [[phonesdata_numb.get(line[0:2],99),phonesdata_alias.get(line[0:2],'???')]+list(line) for line in data]
    data.sort(key=lambda i:(i[0],str(i[1:])))
    # классы для формата заголовка
    header_class = {'Balance': 'p_b', 'RealAverage': 'p_r','BalDelta':'p_r','BalDeltaQuery': 'p_r','NoChangeDays': 'p_r','CalcTurnOff': 'p_r','MinAverage': 'p_r',}
    html_header = ''.join([f'<th id="h{h}" class="{header_class.get(h,"p_n")}">{dbengine.PhonesHText.get(h,h)}</th>' for h in header])
    html_table = []
    for line in data:
        html_line = []
        for he, el in zip(header, line):
            mark = ''  # class="mark"
            if he == 'Balance' and el is not None and el < edBalanceLessThen:
                mark = ' class="mark" '  # Красим когда мало денег
            if he == 'CalcTurnOff' and el is not None and el < edTurnOffLessThen:
                mark = ' class="mark" '  # Красим когда надолго не хватит
            if he == 'PhoneNumber' and el is not None and el.isdigit():
                # форматирование телефонных номеров
                el = re.sub(r'\A(\d{3})(\d{3})(\d{4})\Z', '(\\1) \\2-\\3', el)
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
        options = store.read_ini()['Options']
        if options.get('createhtmlreport','0') == '1':
            _,res = getreport()
            balance_html = options.get('balance_html', settings.balance_html)
            logging.info(f'Создаем {balance_html}')
            open(balance_html,encoding='utf8',mode='w').write('\n'.join(res))
    except Exception:
        logging.error(f'Ошибка генерации {balance_html} {"".join(traceback.format_exception(*sys.exc_info()))}')


def tray_icon(cmdqueue):
    'Выставляем для trayicon daemon, чтобы ушел вслед за нами функция нужна для запуска в отдельном thread'
    TrayIcon(cmdqueue).run_forever()

class TrayIcon:
    def __init__(self, cmdqueue):
        self.cmdqueue = cmdqueue
        msg_TaskbarRestart = win32gui.RegisterWindowMessage("TaskbarCreated")
        message_map = {
                msg_TaskbarRestart: self.OnRestart,
                win32con.WM_DESTROY: self.OnDestroy,
                win32con.WM_COMMAND: self.OnCommand,
                win32con.WM_USER+20 : self.OnTaskbarNotify,
        }
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "PythonTaskbarDemo"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32api.LoadCursor( 0, win32con.IDC_ARROW )
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map # could also specify a wndproc.
        try:
            classAtom = win32gui.RegisterClass(wc)
        except win32gui.error as err_info:
            if err_info.winerror!=winerror.ERROR_CLASS_ALREADY_EXISTS:
                raise
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow( wc.lpszClassName, "Taskbar Demo", style, \
                0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, \
                0, 0, hinst, None)
        win32gui.UpdateWindow(self.hwnd)
        self._DoCreateIcons()

    def run_forever(self):
        win32gui.PumpMessages()

    def _DoCreateIcons(self, iconame = 'httpserver.ico'):
        # Try and find a custom icon
        hinst =  win32api.GetModuleHandle(None)
        iconPathName = os.path.join(os.path.split(os.path.abspath(sys.argv[0]))[0], iconame)
        if os.path.isfile(iconPathName):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst, iconPathName, win32con.IMAGE_ICON, 0, 0, icon_flags)
        else:
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER+20, hicon, "Python Demo")
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        except win32gui.error:
            print(f"Failed to add the taskbar icon - is explorer running? {''.join(traceback.format_exception(*sys.exc_info()))}")

    def OnRestart(self, hwnd, msg, wparam, lparam):
        self._DoCreateIcons()

    def OnDestroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0) # Terminate the app.

    def OnTaskbarNotify(self, hwnd, msg, wparam, lparam):
        if lparam==win32con.WM_LBUTTONDBLCLK:
            #print("You double-clicked me - goodbye")
            #win32gui.DestroyWindow(self.hwnd)
            pass
        elif lparam==win32con.WM_RBUTTONUP:
            print("You right clicked me.")
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu( menu, win32con.MF_STRING, 1024, "Open report")
            win32gui.AppendMenu( menu, win32con.MF_STRING, 1025, "Exit program" )
            pos = win32gui.GetCursorPos()
            # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        return 1

    def OnCommand(self, hwnd, msg, wparam, lparam):
        id = win32api.LOWORD(wparam)
        if id == 1024: 
            port = int(store.read_ini()['HttpServer'].get('port', settings.port))
            os.system(f'start http://localhost:{port}/report')
        elif id == 1025:
            print("Goodbye")
            win32gui.DestroyWindow(self.hwnd)          
            self.cmdqueue.put('STOP')
        else:
            print("Unknown command -", id)

class Handler(wsgiref.simple_server.WSGIRequestHandler):
    # Disable logging DNS lookups
    def address_string(self):
        return str(self.client_address[0])

    def log_message(self, format, *args):
        # убираем пароль из лога
        args = re.sub('(/.*?/.*?/.*?/)(.*?)(/.*)', r'\1xxxxxxx\3', args[0]), *args[1:]
        args = re.sub('(&password=)(.*?)(&)', r'\1xxxxxxx\3', args[0]), *args[1:]
        logging.info(f"{self.client_address[0]} - - [self.log_date_time_string()] {format % args}\n")


class ThreadingWSGIServer(socketserver.ThreadingMixIn, wsgiref.simple_server.WSGIServer):
    pass


class WebServer():
    def __init__(self):
        self.cmdqueue = queue.Queue()
        httpssec = store.read_ini()['HttpServer']
        options = store.read_ini()['Options']
        logging.basicConfig(filename=options.get('logginghttpfilename', settings.logginghttpfilename), 
                        level=options.get('logginglevel', settings.logginglevel),
                        format=options.get('loggingformat', settings.loggingformat))
        self.port = int(httpssec.get('port', settings.port))
        self.host = '127.0.0.1'
        with socket.socket() as sock:
            sock.settimeout(0.2)  # this prevents a 2 second lag when starting the server
            if sock.connect_ex((self.host, self.port)) == 0:
                logging.error(f"Port {self.host}:{self.port} already in use, try restart.")
                try:
                    requests.Session().get(f'http://{self.host}:{self.port}/exit',timeout=1)
                    time.sleep(1)  # Подождем пока серер остановится
                except Exception:
                    pass
        with wsgiref.simple_server.make_server(self.host, self.port, self.simple_app, server_class=ThreadingWSGIServer, handler_class=Handler) as self.httpd:
            logging.info(f'Listening {self.host}:{self.port}....')
            threading.Thread(target=self.httpd.serve_forever, daemon = True).start()
            if 'win32api' in sys.modules:  # Иконка в трее
                threading.Thread(target=lambda i=self.cmdqueue:tray_icon(i), daemon = True).start()
            # Запустили все остальное демонами и ждем, когда они пришлют сигнал
            self.cmdqueue.get()
            self.httpd.shutdown()
        logging.info(f'Shutdown server {self.host}:{self.port}....')

    def simple_app(self,environ, start_response):
        status = '200 OK'
        ct, text = 'text/html',[]
        fn=environ.get('PATH_INFO', None)
        _, cmd, *param = fn.split('/')
        print(f'{cmd}, {param}')
        if cmd.lower() == 'getbalance':  # старый вариант оставлен поеп для совместимости
            ct, text = getbalance('url', param)  # TODO !!! Но правильно все-таки через POST
        elif cmd.lower() == 'get':  # вариант через get запрос
            param = urllib.parse.parse_qs(environ['QUERY_STRING'])
            ct, text = getbalance('get', param)  
        elif cmd == '' or cmd == 'report': # report
            options = store.read_ini()['Options']
            if options['sqlitestore'] == '1':
                ct, text = getreport(param)
            else:
                ct, text = 'text/html', HTML_NO_REPORT
        elif cmd == 'exit': # exit cmd
            self.cmdqueue.put('STOP')
            text = ['exit']
        headers = [('Content-type', ct)]
        start_response(status, headers)
        return [line.encode('cp1251') for line in text]
        
def main():
    WebServer()

if __name__ == '__main__':
    main()
