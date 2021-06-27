# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys,io, re, time, json, traceback, threading, logging, importlib, configparser, queue, argparse, subprocess, psutil
import wsgiref.simple_server, socketserver, socket, requests, urllib.parse, urllib.request, bs4, uuid
import settings, store, dbengine, compile_all_jsmblh  # pylint: disable=import-error
try:
    import schedule
except ModuleNotFoundError:
    print('No schedule installed')
try:
    import pystray, PIL.Image
except Exception:
    print('No pystray installed or other error, no tray icon')
try:
    import telegram
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
except ModuleNotFoundError:
    print('No telegram installed, no telegram bot')

lang = 'p'  # Для плагинов на python преффикс lang всегда 'p'

HTML_NO_REPORT = '''Для того чтобы были доступны отчеты необходимо в mbplugin.ini включить запись результатов в sqlite базу<br>
sqlitestore = 1<br>Также можно настроить импорт из базы BalanceHistory.mdb включив <br>
createhtmlreport = 1<br>
После включения, запустите mbplugin\\setup_and_check.bat
'''

TRAY_MENU = (
    {'text':"Main page", 'cmd':lambda:os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/main'), 'show':True, 'default':True},
    {'text':"View report", 'cmd':lambda:os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/report'), 'show':True},
    {'text':"Edit config", 'cmd':lambda:os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/editcfg'), 'show':store.options('HttpConfigEdit') == '1'},
    {'text':"View log", 'cmd':lambda:os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/log?lines=40'), 'show':True},
    {'text':"Flush log", 'cmd':lambda:store.logging_restart(), 'show':True},
    {'text':"Recompile jsmblh plugin",'cmd':lambda:compile_all_jsmblh.recompile(), 'show':True},
    {'text':"Restart server", 'cmd':lambda:restart_program(reason='tray icon command'), 'show':True},
    {'text':"Exit program", 'cmd':lambda:restart_program(reason='Tray icon exit', exit_only=True), 'show':True}
)

def turn_logging():
    logging.basicConfig(filename=store.options('logginghttpfilename'),
                        level=store.options('logginglevel'),
                        format=store.options('loggingformat'))    


def detbalance_standalone(filter=[], only_failed=False, feedback=None) :
    ''' Получаем балансы самостоятельно без mobilebalance 
    Если filter пустой то по всем номерам из phones.ini
    Если не пустой - то логин/алиас/оператор или его часть
    для автономной версии в поле Password2 находится незашифрованный пароль
    ВНИМАНИЕ! при редактировании файла phones.ini через MobileBalance строки с паролями будут удалены
    для совместного использования с MobileBalance храните пароли password2 и другие специфичные опции
    для Standalone версии в файле phones_add.ini
    only_failed=True - делать запросы только по тем номерам, по которым прошлый запрос был неудачный
    feedback - если не None - то это функция, которая умеет выдавать статус на экран
    '''
    turn_logging()  # Т.к. сюда можем придти извне, то включаем логирование здесь
    logging.info(f'detbalance_standalone: filter={filter}')
    phones = store.ini('phones.ini').phones()
    queue_balance = []  # Очередь телефонов на получение баланса
    for val in phones.values():
        keypair = f"{val['Region']}_{val['Number']}"
        # Проверяем все у кого задан плагин, логин и пароль пароль
        if val['Number'] != '' and val['Region'] != '' and val['Password2'] != '':
            if len(filter) == 0 or [1 for i in filter if i.lower() in f"__{keypair}__{val['Alias']}".lower()] != []:
                if not only_failed or only_failed and str(dbengine.flags('get',keypair)).startswith('error'):
                    # Формируем очередь на получение балансов и размечаем балансы из очереди в таблице flags чтобы красить их по другому
                    queue_balance.append(val)
                    logging.info(f'detbalance_standalone queued: {keypair}')
                    dbengine.flags('set',f'{keypair}','queue')  # выставляем флаг о постановке в очередь
    if feedback is not None:
        feedback(f'Queued {len(queue_balance)} numbers')
    for val in queue_balance:
        # TODO пока дергаем метод от вебсервера там уже все есть, потом может вынесем отдельно
        try:
            if feedback is not None:
                feedback(f"Receive {val['Alias']}:{val['Region']}_{val['Number']}")
            getbalance_plugin('get',{'plugin':[val['Region']],'login':[val['Number']],'password':[val['Password2']],'date':['date']})
        except:
            logging.error(f"Unsuccessful check {val['Region']} {val['Number']} {''.join(traceback.format_exception(*sys.exc_info()))}")

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
        dbengine.flags('set',f"{lang}_{plugin}_{param['login']}",'start')  # выставляем флаг о начале запроса
        try:
            result = module.get_balance(param['login'], param['password'], storename)
            text = store.result_to_html(result)
            if 'Balance' not in result:
                raise RuntimeError(f'В result отсутствует баланс')
        except:
            logging.info(f'{plugin} fail: {"".join(traceback.format_exception(*sys.exc_info()))}')
            dbengine.flags('set',f"{lang}_{plugin}_{param['login']}",'error call')  # выставляем флаг о ошибке вызова
            return 'text/html', [f"<html>Error call {param['fplugin']}</html>"]
        dbengine.flags('delete',f"{lang}_{plugin}_{param['login']}",'start')  # запрос завершился успешно - сбрасываем флаг
        try:    
            # пишем в базу
            dbengine.write_result_to_db(f'{lang}_{plugin}', param['login'], result)
            # обновляем данные из mdb
            dbengine.update_sqlite_from_mdb()
        except Exception:    
            exception_text = f'Ошибка при подготовке работе с БД: {"".join(traceback.format_exception(*sys.exc_info()))}'
            logging.error(exception_text)   
        try:
            # генерируем balance_html
            write_report()
        except Exception:    
            exception_text = f'Ошибка при подготовке report: {"".join(traceback.format_exception(*sys.exc_info()))}'
            logging.error(exception_text)        
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
    'Делает html отчет balance.html'
    def pp_field(pkey, he, el, hover):
        'форматирует поле, красит, выкидывает None и нули в полях баланса - возвращает готовый тэг th или tr'
        'he - header'
        'el - element'
        'pkey - пара (номер,оператор)'
        mark = ''  # class="mark"
        if he == 'Balance' and el is not None and el < float(phones[pkey]['BalanceLessThen']):
            mark = ' class="mark" '  # Красим когда мало денег
        if he == 'CalcTurnOff' and el is not None and el < int(phones[pkey]['TurnOffLessThen']):
            mark = ' class="mark" '  # Красим когда надолго не хватит
        if he == 'NoChangeDays' and el is not None and pkey in phones and int(el) > int(phones[pkey]['BalanceNotChangedMoreThen']):
            mark = ' class="mark" '  # Красим когда давно не изменялся
        if he == 'NoChangeDays' and el is not None and pkey in phones and int(el) < int(phones[pkey]['BalanceChangedLessThen']):
            mark = ' class="mark" '  # Красим недавно поменялся а не должен был
        if el is None:
            el = ''
        if he != 'Balance' and (el == 0.0 or el == 0) and mark == '':
            el = ''
        if type(el) == float:
            el = f'{el:.2f}'  #round(el,2)
        if hover != '':
            el = f'<div class="item">{el}<div class="hoverHistory">{hover}</div></div>'
        return f'<{"th" if he=="NN" else "td"} id="{he}"{mark}>{el}</td>'

    style = '''<style type="text/css">
    .BackgroundTable, .InfoTable {font-family: Verdana; font-size:85%}
    .HistoryBgTable, .HistoryTable {font-family: Verdana; font-size:100%}
    th {background-color: #D1D1D1}
    td{white-space: nowrap;text-align: right;}
    tr:hover {background-color: #ffff99;}
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
    .hoverHistory {display: none;}
    .item:hover .hoverHistory {{HoverCss}}
    #Balance, #SpendBalance {text-align: right; font-weight:bold}
    #Indication, #Alias, #KreditLimit, #PhoneDescr, #UserName, #PhoneNum, #PhoneNumber, #BalExpired, #LicSchet, #TarifPlan, #BlockStatus, #AnyString, #LastQueryTime{text-align: left}
    </style>'''
    template_page = '''
     <html>
    <head><title>MobileBalance</title><meta http-equiv="content-type" content="text/html; charset=windows-1251"></head>{style}
    <body style="font-family: Verdana; cursor:default">
    <table class="BackgroundTable">
    <tr><td class="hdr">Информация о балансе телефонов - MobileBalance Mbplugin</td></tr>
    <tr><td bgcolor="#808080">
    <table class="InfoTable" border="0" cellpadding="2" cellspacing="1">
        <tr class="header">{html_header}</tr>
        {html_table}
    </table>
    </td></tr>
    </table>
    </body>
    </html>'''
    template_history = '''
    <table class="HistoryBgTable">
    <tr><td class="hdr">{h_header}</td></tr>
    <tr><td bgcolor="#808080">
    <table class="HistoryTable" border="0" cellpadding="2" cellspacing="1">
        <tr class="header">{html_header}</tr>
        {html_table}
    </table>
    </td></tr>
    </table>
    '''    
    db = dbengine.dbengine(store.options('dbfilename'))
    flags = dbengine.flags('getall')  # берем все флаги словарем
    responses = dbengine.responses()  # все ответы по запросам
    # номера провайдеры и логины из phones.ini
    num_format = '' if len(param) == 0 or not param[0].isnumeric() else str(int(param[0]))
    table_format = store.options('table_format' + num_format, default=store.options('table_format',section='HttpServer'), section='HttpServer')
    table = db.report()
    phones = store.ini('phones.ini').phones()
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
        pkey = (line['PhoneNumber'],line['Operator'])
        for he in header:
            if he not in line:
                continue
            hover = ''
            if he == 'UslugiOn':  # На услуги вешаем hover со списоком услуг
                uslugi = json.loads(responses.get(f"{line['Operator']}_{line['PhoneNumber']}",'{}')).get('UslugiList','')
                if uslugi !='':
                    h_html_header = f'<th id="hUsluga" class="p_n">Услуга</th><th id="hPrice" class="p_n">р/мес</th>'
                    h_html_table = []
                    for h_line in [l.split('\t',1) for l in sorted(uslugi.split('\n')) if '\t' in l]:
                        txt = h_line[0].replace("  "," &nbsp;")
                        bal = f'{float(h_line[1]):.2f}' if re.match(r'^ *-?\d+(?:\.\d+)? *$', h_line[1]) else h_line[1]
                        h_html_line = f'<td id="Alias">{txt}</td><td id="Balance">{bal}</td>'
                        h_html_table.append(f'<tr id="row" class="n">{h_html_line}</tr>')
                    hover = template_history.format(h_header=f"Список услуг по {line['Alias']}", html_header=h_html_header, html_table='\n'.join(h_html_table))
            if he == 'Balance':  # На баланс вешаем hover с историей
                history = db.history(line['PhoneNumber'], line['Operator'], int(store.options('RealAverageDays')), int(store.options('ShowOnlyLastPerDay')))
                if history != []:
                    h_html_header = ''.join([f'<th id="h{h}" class="{header_class.get(h,"p_n")}">{dbengine.PhonesHText.get(h,h)}</th>' for h in history[0].keys()])
                    h_html_table = []
                    for h_line in history:
                        h_html_line = ''.join([pp_field(pkey, h, v, '') for h,v in h_line.items()])
                        h_html_table.append(f'<tr id="row" class="n">{h_html_line}</tr>')
                    hover = template_history.format(h_header=f"История запросов по {line['Alias']}", html_header=h_html_header, html_table='\n'.join(h_html_table))
            html_line.append(pp_field(pkey, he, line[he], hover))  # append <td>...</td>
        classflag = 'n'  # красим строки - с ошибкой красным, еще в очереди - серым и т.д.
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}",'').startswith('error'):  
            classflag = 'e_us'
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}",'').startswith('start'):
            classflag = 'n_us'
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}",'').startswith('queue'):
            classflag = 'n_us'
        html_table.append(f'<tr id="row" class="{classflag}">{"".join(html_line)}</tr>')
    style = style.replace('{HoverCss}',store.options('HoverCss'))
    res = template_page.format(style=style, html_header=html_header, html_table='\n'.join(html_table))
    return 'text/html', [res]


def write_report():
    'сохраняем отчет balance_html если в ini createhtmlreport=1'
    try:
        if store.options('createhtmlreport') == '1':
            _, res = getreport()
            balance_html = store.options('balance_html')
            logging.info(f'Создаем {balance_html}')
            open(balance_html, encoding='cp1251', mode='w').write('\n'.join(res))
    except Exception:
        logging.error(f'Ошибка генерации balance_html {"".join(traceback.format_exception(*sys.exc_info()))}')

def filter_balance(table, filter='FULL', params={}):
    ''' Фильтруем данные для отчета
    filter = FULL - Все телефоны, LASTCHANGE - Изменивниеся за день, LASTCHANGE - Изменившиеся в последнем запросе
    params['include'] = None - все, либо список через запятую псевдонимы или логины или какая-то их уникальная часть для включения в результат
    params['exclude'] = None - все, либо список через запятую псевдонимы или логины или какая-то их уникальная часть для исключения из результата'''
    flags = dbengine.flags('getall')
    # фильтр по filter_include - оставляем только строчки попавшие в фильтр
    if params.get('include', None) is not None:
        filter_include = [re.sub(r'\W', '', el).lower() for el in params['include'].split(',')]
        table = [line for line in table if len([1 for i in filter_include if i in re.sub(r'\W', '', ('_'.join(map(str,line.values()))+'__'+line.get('Operator','')+'_'+line.get('PhoneNumber','')+'__').lower())])>0]
    # фильтр по filter_exclude - выкидываем строчки попавшие в фильтр
    if params.get('exclude', None) is not None:
        filter_exclude = [re.sub(r'\W', '', el).lower() for el in params['exclude'].split(',')]
        table = [line for line in table if len([1 for i in filter_exclude if i in re.sub(r'\W', '', '_'.join(map(str,line.values())).lower())])==0]
    if filter == 'LASTCHANGE':  # TODO сделать настройку в ini на счет line['Balance']
        # Balance==0 Это скорее всего глюк проверки, соответственно его исключаем
        # Также исключаем BalDeltaQuery==Balance - это возврат обратно с кривого нуля
        # BUG: line['Operator'] и line['PhoneNumber']в случае получения отчета через MobileBalance будет давать KeyError: 
        # Так что делаем костыль с .get который приведет к тому что это условие мы не зацепим
        table = [line for line in table
                 if line['BalDeltaQuery'] != 0 and line['Balance'] != 0 and line['BalDeltaQuery'] != line['Balance']
                 and line['BalDeltaQuery'] != '' and line['Balance'] != ''
                 or flags.get(f"{line.get('Operator','')}_{line.get('PhoneNumber','')}", '').startswith('error')
                 ]
    elif filter == 'LASTDAYCHANGE':
        table = [line for line in table if line['BalDelta'] != 0 and line['Balance'] !=0]
        table = [line for line in table if line['BalDelta'] != '' and line['Balance'] !='']
    return table


def prepare_balance_mobilebalance(filter='FULL', params={}):
    """Формируем текст для отправки в telegram из html файла полученного из web сервера mobilebalance
    """
    phones = store.ini('phones.ini').phones()
    phones_by_num = {v['NN']:v for v in phones.values()}
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
    table = [dict(zip(headers, line)) for line in data]  # Берем данные из html
    for line in table:  # Добавляем Region/Operator и  из phones.ini - нужен для фильтра
        line['Operator'] = line['Region'] = phones_by_num.get(int(line['NN']),'')['Region']
        line['PhoneNumber'] = phones_by_num.get(int(line['NN']),'')['Number'].split(' #')[0]  # Также отрезаем хвост <space>#num
    table = filter_balance(table, filter, params)
    res = [tgmb_format.format(**line) for line in table]
    return '\n'.join(res)


def prepare_balance_sqlite(filter='FULL', params={}):
    'Готовим данные для отчета из sqlite базы'
    db = dbengine.dbengine(store.options('dbfilename', mainparams=params))
    table_format = store.options('tg_format', section='Telegram', mainparams=params).replace('\\t','\t').replace('\\n','\n')
    phones = store.ini('phones.ini').phones()
    flags = dbengine.flags('getall')
    def alert_suffix(line):
        pkey = (line['PhoneNumber'],line['Operator'])
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}",'').startswith('error'):
            return '<b> ! последняя попытка получить баланс завершилась ошибкой !</b>'
        if line['Balance'] is not None and line['Balance'] < float(phones[pkey]['BalanceLessThen']):
            return '<b> ! достигнут порог баланса !</b>'
        if line['CalcTurnOff'] is not None and line['CalcTurnOff'] < int(phones[pkey]['TurnOffLessThen']):
            return '<b> ! возможно скорое отключение !</b>'
        if line['NoChangeDays'] is not None and pkey in phones and line['NoChangeDays'] > int(phones[pkey]['BalanceNotChangedMoreThen']):
            return f'<b> ! баланс не изменялся более {phones[pkey]["BalanceNotChangedMoreThen"]} дней !</b>'
        if line['NoChangeDays'] is not None and pkey in phones and line['NoChangeDays'] > int(phones[pkey]['BalanceNotChangedMoreThen']):
            return f'<b> ! баланс изменился менее {phones[pkey]["BalanceChangedLessThen"]} дней назад!</b>'
        return ''
    # table_format = 'Alias,PhoneNumber,Operator,Balance'
    # Если формат задан как перечисление полей через запятую - переделываем под формат
    if re.match(r'^(\w+(?:,|\Z))*$', table_format.strip()):
        table_format = ' '.join([f'{{{i}}}' for i in table_format.strip().split(',')])
    table = db.report()
    table = [i for i in table if i['Alias']!='Unknown']  # filter Unknown
    table.sort(key=lambda i:[i['NN'],i['Alias']])  # sort by NN, after by Alias
    table = filter_balance(table, filter, params)
    res = [table_format.format(**line)+alert_suffix(line) for line in table]
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
    turn_logging()  # Т.к. сюда можем придти извне, то включаем логирование здесь
    if text is None:
        text = prepare_balance(filter, params)
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

def restart_program(reason='', exit_only=False):
    cmd = subprocess.list2cmdline(psutil.Process().cmdline())
    logging.info(f'Restart by {reason} with cmd:{cmd}')
    TrayIcon().stop()
    if not exit_only:
        os.system('call start "" ' + cmd)
    psutil.Process().kill()

class TrayIcon:
    'Создаем переменную класса, и при повторных вызовах не создаем новый а обращаемся к уже созданному'
    icon = None

    def __init__(self):
        if str(store.options('show_tray_icon')) != '1' or 'pystray' not in sys.modules:
            return
        if TrayIcon.icon is None:
            print('pystray traymeny')
            threading.Thread(target=self._create, name='TrayIcon',  daemon=True).start()
            logging.info('Tray icon started')
        else:
            self.icon = TrayIcon.icon

    def _create(self):
        self.image = PIL.Image.open('httpserver.ico')
        items = []
        for item in TRAY_MENU:
            if item['show']:
                items.append(pystray.MenuItem(item['text'], item['cmd'], default=item.get('default', False)))
        self.menu = pystray.Menu(*items)
        self.icon = pystray.Icon("mbplugin", self.image, "mbplugin", self.menu)
        TrayIcon.icon = self.icon
        self.icon.run()

    def stop(self):
        print('STOP')
        if self.icon is not None:
            self.icon.visible = False
            self.icon.stop()


class Scheduler():
    '''Класс для работы с расписанием'''
    # TODO Пока просто заглушка, размышляю как лучше сделать параметр
    # В теориии должно быть как-то так 
    # schedule.every(4).hour.do(httpserver_mobile.detbalance_standalone, filter=filter)
    # или так
    # schedule.every().day.at("10:30").do(...
    # В каком виде это записывать в ini пока не придумал
    # В теории строк с заданиями может быть несколько и их можно пихать в ini как
    # sheduler= ... sheduler1=... и т.д как сделано с table_format
    def __init__(self) -> None:
        threading.Thread(target=self._forever, name='Scheduler',  daemon=True).start()
        logging.info('Scheduler started')

    def _forever(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def validate(self, sched_str):
        'Проверяет расписание на валидность'
        pass


class TelegramBot():
    def auth_decorator(func):  # pylint: disable=no-self-argument
        def wrapper(self, update, context):
            # update.message.chat_id отсутствует у CallbackQueryHandler пробуем через update.effective_chat.id:
            if update.effective_chat.id in self.auth_id():
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
    def get_help(self, update, context):
        """Send help."""
        help_text = '''/help\n/id\n/balance\n/balancefile\n/receivebalance\n/receivebalancefailed\n/restart\n/getone\n/checkone'''
        logging.info(f'TG:{update.message.chat_id} /help')
        update.message.reply_text(help_text, parse_mode=telegram.ParseMode.HTML)
   
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

    @auth_decorator
    def restartservice(self, update, context):
        """Hard reset service"""
        update.message.reply_text('Service will be restarted', parse_mode=telegram.ParseMode.HTML)
        restart_program(reason=f'TG:{update.message.chat_id} /restart {context.args}')

    @auth_decorator
    def receivebalance_OLD(self, update, context):
        """Receive balance by filter, only auth user."""
        logging.info(f'TG:{update.message.chat_id} /receivebalance {context.args}')
        #baltxt = prepare_balance('FULL')
        update.message.reply_text('Request received. Wait...', parse_mode=telegram.ParseMode.HTML)
        detbalance_standalone(filter=context.args)
        params = {'include': None if context.args == [] else ','.join(context.args)}
        baltxt = prepare_balance('FULL', params=params)
        update.message.reply_text(baltxt, parse_mode=telegram.ParseMode.HTML)

    @auth_decorator
    def receivebalance(self, update, context):
        """ Запросить балансы по всем номерам 
        /receivebalance
        /receivebalancefailed
        """
        def feedback(txt):
            'команда для показа прогреса'
            try:
                msg.edit_text(txt, parse_mode=telegram.ParseMode.HTML)
            except Exception:
                logging.info(f'Unsuccess tg send:{txt} {"".join(traceback.format_exception(*sys.exc_info()))}')
        filtertext = '' if len(context.args)==0 else f", with filter by {' '.join(context.args)}"
        msg = update.message.reply_text(f'Request all number{filtertext}. Wait...', parse_mode=telegram.ParseMode.HTML)
        detbalance_standalone(filter=context.args, only_failed=(update.message.text=="/receivebalancefailed"), feedback=feedback)
        params = {'include': None if context.args == [] else ','.join(context.args)}
        baltxt = prepare_balance('FULL', params=params)
        msg.edit_text(baltxt, parse_mode=telegram.ParseMode.HTML)

    @auth_decorator
    def getone(self, update, context):
        """Receive one balance with inline keyboard, only auth user."""
        '/checkone - получаем баланс /getone - показываем'
        logging.info(f'TG:{update.message.chat_id} {update.message.text}')
        phones = store.ini('phones.ini').phones()
        keyboard = []
        for val in list(phones.values())+[{'Alias':'Cancel', 'Region':'Cancel', 'Number':'Cancel'}]:
            # ключом для calback у нас <3 буквы команды>_Region_Number
            btn = InlineKeyboardButton(val['Alias'], callback_data=f"{update.message.text[1:4]}_{val['Region']}_{val['Number']}")
            if len(keyboard) == 0 or len(keyboard[-1]) == 3:
                keyboard.append([btn])
            else:
                keyboard[-1].append(btn)
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please choose:', reply_markup=reply_markup)

    @auth_decorator
    def button(self, update, context) -> None:
        'Ответ для команд /checkone - получаем баланс и /getone - показываем'
        query = update.callback_query
        query.answer()
        cmd = query.data[:3]
        keypair = query.data[4:]
        if keypair.startswith('Cancel'):
            query.edit_message_text('Canceled', parse_mode=telegram.ParseMode.HTML)
            return
        logging.info(f'TG:reply /getone to {update.effective_chat.id} CHOISE:{context}')
        query.edit_message_text('Request received. Wait...', parse_mode=telegram.ParseMode.HTML)
        if cmd.lower() == 'che':  # /checkone - получаем баланс /getone - показываем
            detbalance_standalone(filter=[f'__{keypair}__'])  # приходится добавлять попчеркивания чтобы исключить попадание по части строки
        params = {'include': f'__{keypair}__'}
        baltxt = prepare_balance('FULL', params=params)
        query.edit_message_text(baltxt, parse_mode=telegram.ParseMode.HTML)
        # Детализация UslugiList по ключу val['Region']}_{val['Number']
        responses = dbengine.responses()
        if keypair in responses:
            response = json.loads(responses[f"{keypair}"])
        else:
            logging.info(f'Not found responce in responses for {keypair}')
            return
        # берем всю информацию по номеру
        response = {k:(round(v,2) if type(v)==float else v)for k,v in response.items()}
        detailed = '\n'.join([f'{name} = {response[k]}' for k,name in dbengine.PhonesHText.items() if k in response])
        uslugi = ''
        if response.get('UslugiList','') != '':
            ul = response['UslugiList'].split('\n')
            if str(store.options('ShowOnlyPaid', section='Telegram')) == '1':
                ul = [line for line in ul if '\t0' not in line]
            uslugi = '\n'.join(ul).replace('\t',' = ')
        else:
            logging.info(f'Not found UslugiList in response for {keypair}')
        msgtxt = f"{baltxt}\n{detailed}\n{uslugi}".strip()
        if baltxt != msgtxt:  # TG ругается если новое сообщение совпадает со старым, приходится проверять
            try:
                query.edit_message_text(msgtxt, parse_mode=telegram.ParseMode.HTML)
            except Exception:
                msgtxt = msgtxt.replace('<','').replace('>','')
                query.edit_message_text(msgtxt, parse_mode=telegram.ParseMode.HTML)

    def send_message(self, text, parse_mode='HTML', ids=None):
        if self.updater is None or text == '':
            return
        if ids is None:
            lst = self.auth_id()
        else:
            lst = ids
        for id in lst:
            try:
                self.updater.bot.sendMessage(chat_id=id, text=text, parse_mode=parse_mode)
            except Exception:
                exception_text = f'Ошибка отправки сообщения {text} для {id} telegram bot {"".join(traceback.format_exception(*sys.exc_info()))}'
                logging.error(exception_text)            

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
        if 'telegram' not in sys.modules:
            return  # Нет модуля TG - просто выходим
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
                dp.add_handler(CommandHandler("help", self.get_help))
                dp.add_handler(CommandHandler("id", self.get_id))
                dp.add_handler(CommandHandler("balance", self.get_balancetext))
                dp.add_handler(CommandHandler("balancefile", self.get_balancefile))
                dp.add_handler(CommandHandler("receivebalance", self.receivebalance))
                dp.add_handler(CommandHandler("receivebalancefailed", self.receivebalance))
                dp.add_handler(CommandHandler("restart", self.restartservice))
                dp.add_handler(CommandHandler("getone", self.getone))
                dp.add_handler(CommandHandler("checkone", self.getone))
                dp.add_handler(CallbackQueryHandler(self.button))
                self.updater.start_polling()  # Start the Bot
                logging.info('Telegram bot started')
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
        turn_logging()
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
        with wsgiref.simple_server.make_server(self.host, self.port, self.web_app, server_class=ThreadingWSGIServer, handler_class=Handler) as self.httpd:
            logging.info(f'Listening {self.host}:{self.port}....')
            threading.Thread(target=self.httpd.serve_forever, name='httpd', daemon=True).start()
            if 'pystray' in sys.modules:  # Иконка в трее
                self.tray_icon = TrayIcon()  # tray icon (он сам все запустит в threading)
            if 'telegram' in sys.modules:  # telegram bot (он сам все запустит в threading)
                self.telegram_bot = TelegramBot()
            if 'schedule' in sys.modules:  # Scheduler (он сам все запустит в threading)
                self.scheduler = Scheduler()
            # Запустили все остальное демонами и ждем, когда они пришлют сигнал
            self.cmdqueue.get()
            self.telegram_bot.stop()
            self.httpd.shutdown()
        logging.info(f'Shutdown server {self.host}:{self.port}....')

    def editor(self, environ):
        ''' Редактор конфигов editcfg
        возвращаем Content-type, text, status, add_headers'''
        ## print(environ)
        # т.к. возвращаем разные статусы и куки, готовим переменные под них
        autorized = False  # Изначально считаем что пользователь не авторизован
        # breakpoint() if os.path.exists('breakpoint') else None
        status = '200 OK'
        add_headers = []
        cookie_store_name = os.path.join(store.options('storefolder'), 'authcookie')
        # Читаем список сохраненных кук
        if os.path.exists(cookie_store_name):
            with open(cookie_store_name) as f:
                authcookies = [i for i in map(str.strip,f.readlines()) if i!='']
        else:
            authcookies = []
        # Получаем переданные куки из заголовка
        cookies = {k:v[0] for k,v in urllib.parse.parse_qs(environ.get('HTTP_COOKIE','{}')).items()}
        # Авторизованы если переданная кука в списке сохраненных
        autorized = cookies.get('auth', 'None') in authcookies
        # Если пришли с localhost и разрешено локалхосту без авторизации
        local_autorized = environ.get('REMOTE_ADDR','None')=='127.0.0.1' and str(store.options('httpconfigeditnolocalauth'))=='1'
        if local_autorized:
            autorized = True        
        # если еще не открывали редактируемый ini открываем
        if not hasattr(self,'editini'):
            self.editini = store.ini()
        print(cookies, f"auth in authcookies={cookies.get('auth', 'None') in authcookies}",f'autorized={autorized}')
        if environ['REQUEST_METHOD'] == 'POST':
            try:
                request_size = int(environ['CONTENT_LENGTH'])
                request_raw = environ['wsgi.input'].read(request_size)
            except (TypeError, ValueError):
                request_raw = "0"
            try:
                request = json.loads(request_raw)
            except Exception:
                try:
                    request = urllib.parse.parse_qs(request_raw.decode())
                    request = {k:v[0] for k,v, in request.items()}
                except Exception:
                    request = {'cmd':'error'}
            print(f'request={request}')
            if autorized and request['cmd'] == 'update':
                params = settings.ini[request['sec']].get(request['id']+'_',{})
                # Если для параметра указана функция валидации - вызываем ее
                if not params.get('validate',lambda i:True)(request['value']):
                    return 'text/plain', 'ERROR', status, add_headers
                logging.info(f"ini change key [{request['sec']}] {request['id']} {self.editini.ini[request['sec']].get(request['id'],'default')}->{request['value']}")
                self.editini.ini[request['sec']][request['id']] = request['value']
                self.editini.write()
                #print('\n'.join([f'{k}={v}' for k,v in self.editini.ini[request['sec']].items()]))
            elif autorized and request['cmd'] == 'delete':
                logging.info(f"ini delete key [{request['sec']}] {request['id']} {self.editini.ini[request['sec']].get(request['id'],'default')}")
                self.editini.ini[request['sec']].pop(request['id'], None)
                self.editini.write()
            elif request['cmd'] == 'logon':
                status = '303 See Other'
                # Пароль совпал (и не пустой !!!) - выдаем токен
                passwd_from_ini = store.options('httpconfigeditpassword').strip()
                passwd_from_user = request.get('password', 'None').strip()
                if passwd_from_user == passwd_from_ini and passwd_from_ini != '':
                    auth_token = uuid.uuid4().hex  # auth cookie
                    authcookies.append(auth_token)
                    with open(cookie_store_name, 'w') as f:
                        f.write('\n'.join(authcookies))
                    add_headers = [('Set-Cookie', f'auth={auth_token}'),
                                    ('Set-Cookie', 'wrongpassword=deleted; expires=Thu, 01 Jan 1970 00:00:00 GMT')]
                else:
                    add_headers = [('Set-Cookie', 'wrongpassword=true')]
                return 'text/html', 'redirect', status, add_headers
            elif request['cmd'] == 'logout':
                # выкидываем куку
                with open(cookie_store_name, 'w') as f:
                    f.write('\n'.join([i for i in authcookies if i != cookies.get('auth', 'None')]))
                status = '303 See Other'
                add_headers = [('Set-Cookie', 'auth=deleted; expires=Thu, 01 Jan 1970 00:00:00 GMT')]
                return 'text/html', 'redirect', status, add_headers
            elif request['cmd'] == 'error':
                return 'text/plain', 'Error', status, add_headers
            else: 
                return 'text/plain', 'Error, unknown cmd', status, add_headers
            return 'text/plain', 'OK', status, add_headers
        if environ['REQUEST_METHOD']=='GET':
            self.editini = store.ini()
            self.editini.read()
            # TODO в финале editor.html будем брать из settings.py
            # editor_html = open('editor.html', encoding='cp1251').read()
            editor_html = settings.editor_html
            inidata = '{}'
            if autorized:
                inidata = self.editini.ini_to_json().replace('\\','\\\\')
            editor_html = editor_html.replace("inifile = JSON.parse('')", f"inifile = JSON.parse('{inidata}')")
            if local_autorized:
                editor_html = editor_html.replace('localAuthorized = false // init', f'localAuthorized = true // init')
            return 'text/html',editor_html, status, add_headers

    def web_app(self, environ, start_response):
        try:
            logging.debug('web_app start')
            status = '200 OK'
            add_headers = []
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
            elif cmd == 'logging_restart':  # logging_restart
                store.logging_restart()
                ct, text = 'text/html', 'OK'
            elif cmd == '' or cmd == 'report':  # report
                if store.options('sqlitestore') == '1':
                    ct, text = getreport(param)
                else:
                    ct, text = 'text/html', HTML_NO_REPORT
            elif cmd.lower() == 'main':  # главная страница
                ct, text = 'text/html; charset=cp1251', [settings.main_html]
            elif cmd.lower() == 'editcfg':  # вариант через get запрос
                if store.options('HttpConfigEdit') == '1':
                    ct, text, status, add_headers = self.editor(environ)
            elif cmd == 'flushlog':  # Start new log
                store.logging_restart()
                ct, text = 'text/html; charset=cp1251', ['OK']
            elif cmd == 'recompile':  # Recompile js lsmblh plugin
                compile_all_jsmblh.recompile()
                ct, text = 'text/html; charset=cp1251', ['OK']
            elif cmd == 'restart':  # exit cmd
                restart_program(reason=f'WEB: /restart') # TODO нужен редирект иначе она зацикливается на рестарте
            elif cmd == 'exit':  # exit cmd
                restart_program(reason=f'WEB: /exit', exit_only=True)
            if status.startswith('200'):
                headers = [('Content-type', ct)]
            if status.startswith('303'):
                headers = [('Location', '')] + add_headers
            start_response(status, headers)
            logging.debug('web_app done')
            return [line.encode('cp1251', errors='ignore') for line in text]
        except Exception:
            exception_text = f'Ошибка: {"".join(traceback.format_exception(*sys.exc_info()))}'
            logging.error(exception_text)
            headers = [('Content-type', 'text/html')]
            return ['<html>ERROR</html>'.encode('cp1251')]


def parse_arguments(argv, parcerclass=argparse.ArgumentParser):
    parser = parcerclass()
    parser.add_argument('--cmd', type=str, help='command for web server (start/stop)', default='start')
    return parser.parse_args(argv)

def main():
    try:
        ARGS = parse_arguments(sys.argv[1:])
        if ARGS.cmd.lower() == 'start':
            WebServer()
        if ARGS.cmd.lower() == 'stop':
            port = int(store.options('port', section='HttpServer'))
            requests.session().get(f'http://localhost:{port}/exit')
    except Exception:
        exception_text = f'Ошибка запуска WebServer: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)


if __name__ == '__main__':
    main()
