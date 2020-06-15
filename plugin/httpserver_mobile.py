# -*- coding: utf8 -*- 
''' Автор ArtyLa '''
import os, sys, re, time, json, traceback, threading, logging, importlib,configparser
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler
from socketserver import ThreadingMixIn
sys.path.append('..\\plugin')
import settings, store, dbengine  # pylint: disable=import-error

lang='p' # Для плагинов на python преффикс lang всегда 'p'

def result_to_html(result):
    'Конвертирует словарь результатов в готовый к отдаче вид '
    # Коррекция SMS и Min (должны быть integer)
    if 'SMS' in result:
        result['SMS'] = int(result['SMS'])
    if 'Min' in result:
        result['Min'] = int(result['Min'])
    body = json.dumps(result, ensure_ascii=False)
    return f'<html><meta charset="windows-1251"><p id=response>{body}</p></html>'

def find_ini_up(fn):
    allroot = [os.getcwd().rsplit('\\',i)[0] for i in range(len(os.getcwd().split('\\')))]
    all_ini = [i for i in allroot if os.path.exists(os.path.join(i,fn))]
    if all_ini != []:
        return all_ini[0]
    

def getbalance(param):
    'fplugin, login, password, date'
    try: 
        if len(param) != 4:
            return 'text/html', [f'<html>Unknown call - use getbalance/plugin/login/password/date</html>']
        fplugin,login,password,date = param
        #print(f'{fn=} {fn.split("/")=}')
        #print(f'{fplugin=} {login=} {password=} {date=}')
        # Это плагин от python ?
        if fplugin.startswith(f'{lang}_'):
            # get balance
            plugin = fplugin.split('_',1)[1]  # plugin это все что после p_ 
            module = __import__(plugin, globals(), locals(), [], 0)
            importlib.reload(module) # обновляем модуль, на случай если он менялся
            result = module.get_balance(login, password, f'{lang}_{plugin}_{login}')
            text = result_to_html(result)
            #print(text)
            return 'text/html', text
        return 'text/html', [f'<html>Unknown plugin {fplugin}</html>']
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
    phones_ini = store.read_ini('phones.ini')
    options_ini = store.read_ini('Options.ini')
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
            html_line.append(
                f'<{"th" if he=="NN" else "td"} id="{he}"{mark}>{el}</td>')
        html_table.append(f'<tr id="row" class="n">{"".join(html_line)}</tr>')
    res = template.format(style=style, html_header=html_header, html_table='\n'.join(html_table))
    return 'text/html', [res]


def simple_app(environ, start_response):
    status = '200 OK'
    ct, text = 'text/html',[]
    fn=environ.get('PATH_INFO', None)
    _, cmd, *param = fn.split('/')
    #print(f'{cmd}, {param}')
    if cmd.lower() == 'getbalance':
        ct, text = getbalance(param)  # TODO !!! Но правильно все-таки через POST
    if cmd == '' or cmd == 'report': # report
        ct, text = getreport(param)
        #ct, text = 'text/html', [f'<html>REPORT</html>']
    #th = f'{threading.currentThread().name}:{chr(44).join([t.name for t in threading.enumerate()[1:]])}'
    headers = [('Content-type', ct)]
    start_response(status, headers)
    #print('text',text)
    return [line.encode('cp1251') for line in text]
    

class Handler(WSGIRequestHandler):
    # Disable logging DNS lookups
    def address_string(self):
        return str(self.client_address[0])

    def log_message(self, format, *args):
        logging.info(f"{self.client_address[0]} - - [self.log_date_time_string()] {format % args}\n")


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    pass


def main():
    logging.basicConfig(filename="..\\log\\http.log", level=logging.INFO,
        format = u'[%(asctime)s] %(levelname)s %(funcName)s %(message)s')

    # with make_server('', self.port, self.web_app, handler_class=Handler) as server:
    port = int(store.read_ini()['HttpServer'].get('port', settings.port))
    with make_server('127.0.0.1', port, simple_app, server_class=ThreadingWSGIServer, handler_class=Handler) as httpd:
        print(f'Listening on port {port}....')
        httpd.serve_forever()

if __name__ == '__main__':
    main()
