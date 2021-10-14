# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import typing, os, sys, io, re, time, json, threading, logging, importlib, queue, argparse, subprocess, glob, base64
import wsgiref.simple_server, socketserver, socket, urllib.parse, urllib.request
import requests, psutil, bs4, uuid, PIL.Image, schedule
import settings, store, dbengine, compile_all_jsmblh, updateengine  # pylint: disable=import-error
try:
    # TODO не смотря на декларированную кроссплатформенность pystray нормально заработал только на windows
    # на ubuntu он работает странно а на маке вызывает падение уже дальше по коду
    if sys.platform == 'win32':
        import pystray
except Exception:
    print('No pystray installed or other error, no tray icon')
try:
    import telegram
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
except ModuleNotFoundError:
    print('No telegram installed, no telegram bot')

lang = 'p'  # Для плагинов на python префикс lang всегда 'p'

cmdqueue: queue.Queue = queue.Queue()  # Диспетчер комманд - нужен для передачи сигналов между трэдами, в т.к. для завершения в докере - kill для pid=1 не работает

HTML_NO_REPORT = '''Для того чтобы были доступны отчеты необходимо в mbplugin.ini включить запись результатов в sqlite базу<br>
sqlitestore = 1<br>Также можно настроить импорт из базы BalanceHistory.mdb включив <br>
createhtmlreport = 1<br>
После включения, запустите mbplugin\\setup_and_check.bat
'''

# TODO в командах для traymeny используется os.system(f'start ... это будет работать только в windows, но пока пофигу, т.к. сам pystrayработает только в windows
TRAY_MENU = (
    {'text': "Main page", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/main'), 'show': True, 'default': True},
    {'text': "View report", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/report'), 'show': True},
    {'text': "Edit config", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/editcfg'), 'show': str(store.options('HttpConfigEdit')) == '1'},
    {'text': "View log", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/log?lines=40'), 'show': True},
    {'text': "View screenshot log", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/log/list'), 'show': True},
    {'text': "Get balance request", 'cmd': lambda: threading.Thread(target=getbalance_standalone, name='Getbalance', daemon=True).start(), 'show': True},
    {'text': "Flush log", 'cmd': lambda: store.logging_restart(), 'show': True},
    {'text': "Reload schedule", 'cmd': lambda: Scheduler().reload(), 'show': True},
    {'text': "Recompile jsmblh plugin", 'cmd': lambda: compile_all_jsmblh.recompile(), 'show': True},
    {'text': "Restart server", 'cmd': lambda: restart_program(reason='tray icon command'), 'show': True},
    {'text': "Exit program", 'cmd': lambda: restart_program(reason='Tray icon exit', exit_only=True), 'show': True}
)


def getbalance_standalone_one_pass(filter:list=[], only_failed:bool=False) -> None:
    ''' Получаем балансы самостоятельно без mobilebalance ОДИН ПРОХОД
    Если filter пустой то по всем номерам из phones.ini
    Если не пустой - то логин/алиас/оператор или его часть
    для автономной версии в поле Password2 находится незашифрованный пароль
    ВНИМАНИЕ! при редактировании файла phones.ini через MobileBalance строки с паролями будут удалены
    для совместного использования с MobileBalance храните пароли password2 и другие специфичные опции
    для Standalone версии в файле phones_add.ini
    only_failed=True - делать запросы только по тем номерам, по которым прошлый запрос был неудачный
    '''
    phones = store.ini('phones.ini').phones()
    queue_balance = []  # Очередь телефонов на получение баланса
    for val in phones.values():
        keypair = f"{val['Region']}_{val['Number']}"
        # Проверяем все у кого задан плагин, логин и пароль пароль
        if val['Number'] != '' and val['Region'] != '' and val['Password2'] != '':
            if len(filter) == 0 or [1 for i in filter if i.lower() in f"__{keypair}__{val['Alias']}".lower()] != []:
                if not only_failed or only_failed and str(dbengine.flags('get', keypair)).startswith('error'):
                    # Формируем очередь на получение балансов и размечаем балансы из очереди в таблице flags чтобы красить их по другому
                    queue_balance.append(val)
                    logging.info(f'getbalance_standalone queued: {keypair}')
                    dbengine.flags('set', f'{keypair}', 'queue')  # выставляем флаг о постановке в очередь
    store.feedback.text(f'Queued {len(queue_balance)} numbers')
    for val in queue_balance:
        # TODO пока дергаем метод от вебсервера там уже все есть, потом может вынесем отдельно
        try:
            store.feedback.text(f"Receive {val['Alias']}:{val['Region']}_{val['Number']}")
            getbalance_plugin('get', {'plugin': [val['Region']], 'login': [val['Number']], 'password': [val['Password2']], 'date': ['date']})
        except Exception:
            logging.error(f"Unsuccessful check {val['Region']} {val['Number']} {store.exception_text()}")

def getbalance_standalone(filter:list=[], only_failed:bool=False, retry:int=-1, params=None) -> None:
    ''' Получаем балансы делая несколько проходов по неудачным
    retry=N количество повторов по неудачным попыткам, после запроса по всем (повторы только при only_failed=False)
    params добавлен чтобы унифицировать вызовы
    Результаты сохраняются в базу'''
    store.turn_logging(httplog=True)  # Т.к. сюда можем придти извне, то включаем логирование здесь
    logging.info(f'getbalance_standalone: filter={filter}')
    if retry == -1:
        retry = int(store.options('retry_failed', flush=True))
    if only_failed:
        getbalance_standalone_one_pass(filter=filter, only_failed=True)
    else:
        getbalance_standalone_one_pass(filter=filter, only_failed=False)
        for i in range(retry):
            getbalance_standalone_one_pass(filter=filter, only_failed=True)


def get_full_info_one_number(keypair:str, check:bool=False) -> str:
    '''Получение подробной информации по одному 
    keypair - Region_Number
    check==True - запросить информацию по номеру перед возвратом  
    '''
    if check:  # /checkone - получаем баланс /getone - только показываем
        getbalance_standalone(filter=[f'__{keypair}__'])  # приходится добавлять подчеркивания чтобы исключить попадание по части строки
    params = {'include': f'__{keypair}__'}
    baltxt = prepare_balance('FULL', params=params)
    store.feedback.text(baltxt)
    # Детализация UslugiList по ключу val['Region']}_{val['Number']
    responses = dbengine.responses()
    if keypair in responses:
        response = json.loads(responses[f"{keypair}"])
    else:
        logging.info(f'Not found response in responses for {keypair}')
        return baltxt
    # берем всю информацию по номеру
    response = {k: (round(v, 2) if type(v) == float else v)for k, v in response.items()}
    detailed = '\n'.join([f'{name} = {response[k]}' for k, name in dbengine.PhonesHText.items() if k in response])
    uslugi = ''
    if response.get('UslugiList', '') != '':
        ul = response['UslugiList'].split('\n')
        if str(store.options('ShowOnlyPaid', section='Telegram')) == '1':
            ul = [line for line in ul if '\t0' not in line]
        uslugi = '\n'.join(ul).replace('\t', ' = ')
    else:
        logging.info(f'Not found UslugiList in response for {keypair}')
    msgtxt = f"{baltxt}\n{detailed}\n{uslugi}".strip()
    store.feedback.text(msgtxt)
    return msgtxt    


def getbalance_plugin(method, param_source):
    ''' Вызов плагинов jsmbLH
     fplugin, login, password, date
    date нужен чтобы не кэшировались запросы, туда можно класть что угодно
    В зависимости от method параметры принимаем либо
    url: список [fplugin, login, password, date]
    get: словарь как в get запросе {'fplugin':[...], 'login':[...], 'password':[...], 'date'[...]}
    '''
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
    pkey = (param['login'], param['fplugin'])
    store.options('logginglevel', flush=True)  # Запускаем, чтобы сбросить кэш и перечитать ini
    phone_items = store.ini('phones.ini').phones().get(pkey, {}).items()
    individual = ','.join([f'{k}={v}' for k,v in phone_items if k.lower() in store.settings.ini['Options'].keys()])
    unused = ','.join([f'{k}={v}' for k,v in phone_items if k.lower() not in store.settings.ini['Options'].keys() and k.lower() not in store.settings.PHONE_INI_KEYS_LOWER
                    and k.lower() != 'nn' and not k.lower().endswith('_orig')])
    individual = '' if individual == '' else f' Individual setup:{individual}'
    unused = '' if unused == '' else f' Unused param:{unused}'
    logging.info(f'Webserver thread_count={len(threading.enumerate())}')
    logging.info(f"Start {param['fplugin']} {param['login']} {individual}{unused}")
    # Это плагин от python ?
    if param['fplugin'].startswith(f'{lang}_'):
        # get balance
        plugin = param['fplugin'].split('_', 1)[1]  # plugin это все что после p_
        module = __import__(plugin, globals(), locals(), [], 0)
        importlib.reload(module)  # обновляем модуль, на случай если он менялся
        storename = re.sub(r'\W', '_', f"{lang}_{plugin}_{param['login']}")
        dbengine.flags('setunic', f"{lang}_{plugin}_{param['login']}", 'start')  # выставляем флаг о начале запроса
        try:
            result = module.get_balance(param['login'], param['password'], storename, pkey=pkey)
            if type(result) != dict or 'Balance' not in result:
                raise RuntimeError(f'В result отсутствует баланс')
            text = store.result_to_html(result)
        except Exception:
            logging.info(f'{plugin} fail: {store.exception_text()}')
            dbengine.flags('set', f"{lang}_{plugin}_{param['login']}", 'error call')  # выставляем флаг о ошибке вызова
            return 'text/html', [f"<html>Error call {param['fplugin']}</html>"]
        dbengine.flags('delete', f"{lang}_{plugin}_{param['login']}", 'start')  # запрос завершился успешно - сбрасываем флаг
        try:
            # пишем в базу
            dbengine.write_result_to_db(f'{lang}_{plugin}', param['login'], result)
            # обновляем данные из mdb
            dbengine.update_sqlite_from_mdb()
        except Exception:
            exception_text = f'Ошибка при подготовке работе с БД: {store.exception_text()}'
            logging.error(exception_text)
        try:
            # генерируем balance_html
            write_report()
        except Exception:
            exception_text = f'Ошибка при подготовке report: {store.exception_text()}'
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
        # .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if ' ERROR ' in res[num]:
            res[num] = f'<span style="color:red;background-color:white">{res[num]}</span>'
        elif ' WARNING ' in res[num]:
            res[num] = f'<span style="color:yellow;background-color:white">{res[num]}</span>'
    return 'text/html; charset=cp1251', ['<html><head></head><body><pre>'] + res + ['</pre><script>window.scrollTo(0,document.body.scrollHeight);</script></body></html>']

def prepare_loglist_personal():
    'Делает список пар по которым есть скриншоты'
    ss = glob.glob(store.abspath_join(store.options('loggingfolder'), '*.png'))
    allmatch = [re.search(r'(.*)_\d+\.png', os.path.split(fn)[-1]) for fn in ss]
    allgroups = sorted(set([m.groups()[0] for m in allmatch if m]))
    return allgroups

def prepare_log_personal(prefix):
    'Готовит html лог со скриншотами начинающимися на prefix'
    def png_to_jpg_base64(fn):
        im = PIL.Image.open(fn)
        im = im.convert('RGB')
        f = io.BytesIO()
        im.save(f, format="jpeg")
        return base64.b64encode(f.getvalue()).decode()
    ss = glob.glob(store.abspath_join(store.options('loggingfolder'), prefix + '*.png'))
    # text = [f'<img src=/screenshot/{os.path.split(fn)[-1]}/><br>' for fn in ss]
    text = [f'<img src="data:image/jpeg;base64,{png_to_jpg_base64(fn)}"/><br>\n' for fn in ss]
    return '\n'.join(text)

def getreport(param=[]):
    'Делает html отчет balance.html'
    def pp_field(pkey, he, el, hover, unwanted=False):
        'форматирует поле, красит, выкидывает None и нули в полях баланса - возвращает готовый тэг th или tr'
        'he - header'
        'el - element'
        'pkey - пара (номер,оператор)'
        mark = ''  # class="mark"
        if he == 'Balance' and el is not None and el < float(store.options('BalanceLessThen', pkey=pkey)):
            mark = ' class="mark" '  # Красим когда мало денег
        if he == 'CalcTurnOff' and el is not None and el < int(store.options('TurnOffLessThen', pkey=pkey)):
            mark = ' class="mark" '  # Красим когда надолго не хватит
        if he == 'NoChangeDays' and el is not None and pkey in phones and int(el) > int(store.options('BalanceNotChangedMoreThen', pkey=pkey)):
            mark = ' class="mark" '  # Красим когда давно не изменялся
        if he == 'NoChangeDays' and el is not None and pkey in phones and int(el) < int(store.options('BalanceChangedLessThen', pkey=pkey)):
            mark = ' class="mark" '  # Красим недавно поменялся а не должен был
        if he == 'UslugiOn' and el is not None and unwanted:
            mark = ' class="mark" '  # Красим если в списке есть нежелательные услуги
        if el is None:
            el = ''
        if he != 'Balance' and (el == 0.0 or el == 0) and mark == '':
            el = ''
        if type(el) == float:
            el = f'{el:.2f}'  # round(el, 2)
        if hover != '':
            el = f'<div class="item">{el}<div class="hoverHistory">{hover}</div></div>'
        return f'<{"th" if he=="NN" else "td"} id="{he}"{mark}>{el}</td>'
    template_page = settings.table_template['page']
    template_history = settings.table_template['history']
    temlate_style = settings.table_template['style']
    db = dbengine.Dbengine()
    flags = dbengine.flags('getall')  # берем все флаги словарем
    responses = dbengine.responses()  # все ответы по запросам
    # номера провайдеры и логины из phones.ini
    num_format = '' if len(param) == 0 or not param[0].isnumeric() else str(int(param[0]))
    table_format = store.options('table_format' + num_format, default=store.options('table_format', section='HttpServer'), section='HttpServer')
    table = db.report()
    phones = store.ini('phones.ini').phones()
    if 'Alias' not in table_format:
        table_format = 'NN,Alias,' + table_format  # Если старый ini то этих столбцов нет - добавляем
    table = [i for i in table if i['Alias'] != 'Unknown']  # filter Unknown
    table.sort(key=lambda i: [i['NN'], i['Alias']])  # sort by NN, after by Alias
    header = table_format.strip().split(',')
    # классы для формата заголовка
    header_class = {'Balance': 'p_b', 'RealAverage': 'p_r', 'BalDelta': 'p_r', 'BalDeltaQuery': 'p_r', 'NoChangeDays': 'p_r', 'CalcTurnOff': 'p_r', 'MinAverage': 'p_r', }
    html_header = ''.join([f'<th id="h{h}" class="{header_class.get(h,"p_n")}">{dbengine.PhonesHText.get(h, h)}</th>' for h in header])
    html_table = []
    for line in table:
        html_line = []
        pkey = (line['PhoneNumber'], line['Operator'])
        uslugi = json.loads(responses.get(f"{line['Operator']}_{line['PhoneNumber']}", '{}')).get('UslugiList', '')
        subscribtion_keyword = [i.strip() for i in store.options('subscribtion_keyword', pkey=pkey).lower().split(',')]
        unwanted_kw = [kw for kw in subscribtion_keyword if kw in uslugi.lower()]  # встретившиеся нежелательные
        for he in header:
            if he not in line:
                continue
            hover = ''
            if he == 'UslugiOn':  # На услуги вешаем hover со списком услуг
                if uslugi != '':
                    h_html_header = f'<th id="hUsluga" class="p_n">Услуга</th><th id="hPrice" class="p_n">р/мес</th>'
                    h_html_table = []
                    for h_line in [li.split('\t', 1) for li in sorted(uslugi.split('\n')) if '\t' in li]:
                        txt = h_line[0].replace("  ", " &nbsp;")
                        bal = f'{float(h_line[1]):.2f}' if re.match(r'^ *-?\d+(?:\.\d+)? *$', h_line[1]) else h_line[1]
                        h_html_line = f'<td id="Alias">{txt}</td><td id="Balance">{bal}</td>'
                        u_classflag = 'n'
                        if len(unwanted_kw)>0 and len([kw for kw in unwanted_kw if kw in h_line[0].lower()])>0:
                            u_classflag = 'e_us'
                        h_html_table.append(f'<tr id="row" class="{u_classflag}">{h_html_line}</tr>')
                    hover = template_history.format(h_header=f"Список услуг по {line['Alias']}", html_header=h_html_header, html_table='\n'.join(h_html_table))
            if he == 'Balance':  # На баланс вешаем hover с историей
                history = db.history(line['PhoneNumber'], line['Operator'], days=int(store.options('RealAverageDays', pkey=pkey)), lastonly=int(store.options('ShowOnlyLastPerDay', pkey=pkey)))
                if history != []:
                    h_html_header = ''.join([f'<th id="h{h}" class="{header_class.get(h, "p_n")}">{dbengine.PhonesHText.get(h, h)}</th>' for h in history[0].keys()])
                    h_html_table = []
                    for h_line in history:
                        h_html_line = ''.join([pp_field(pkey, h, v, '') for h, v in h_line.items()])
                        h_html_table.append(f'<tr id="row" class="n">{h_html_line}</tr>')
                    hover = template_history.format(h_header=f"История запросов по {line['Alias']}", html_header=h_html_header, html_table='\n'.join(h_html_table))
            html_line.append(pp_field(pkey, he, line[he], hover, unwanted=(len(unwanted_kw)>0)))  # append <td>...</td>
        classflag = 'n'  # красим строки - с ошибкой красным, текущий - зеленым, еще в очереди - серым и т.д.
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}", '').startswith('error'):
            classflag = 'e_us'
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}", '').startswith('start'):
            classflag = 's_us'
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}", '').startswith('queue'):
            classflag = 'n_us'
        html_table.append(f'<tr id="row" class="{classflag}">{"".join(html_line)}</tr>')
    temlate_style = temlate_style.replace('{HoverCss}', store.options('HoverCss'))  # HoverCss общий на всю страницу, поэтому берем без pkey
    res = template_page.format(style=temlate_style, html_header=html_header, html_table='\n'.join(html_table), title=store.version())
    return 'text/html', [res]


def write_report():
    'сохраняем отчет balance_html если в ini createhtmlreport=1'
    store.turn_logging(httplog=True)  # Т.к. сюда можем придти извне, то включаем логирование здесь
    try:
        if str(store.options('createhtmlreport')) == '1':
            balance_html = store.options('balance_html')
            logging.info(f'Создаем {balance_html}')
            _, res = getreport()
            open(balance_html, encoding='cp1251', mode='w').write('\n'.join(res))
    except Exception:
        logging.error(f'Ошибка генерации balance_html {store.exception_text()}')


def filter_balance(table:typing.List[typing.Dict], filter:str='FULL', params:typing.Dict={}) -> typing.List[typing.Dict]:
    ''' Фильтруем данные для отчета
    filter = FULL - Все телефоны, LASTDAYCHANGE - Изменившиеся за день, LASTCHANGE - Изменившиеся в последнем запросе
    params['include'] = None - все, либо список через запятую псевдонимы или логины или какая-то их уникальная часть для включения в результат
    params['exclude'] = None - все, либо список через запятую псевдонимы или логины или какая-то их уникальная часть для исключения из результата'''
    flags = dbengine.flags('getall')
    # фильтр по filter_include - оставляем только строчки попавшие в фильтр
    if params.get('include', None) is not None:
        filter_include = [re.sub(r'\W', '', el).lower() for el in params['include'].split(',')]
        table = [line for line in table if len([1 for i in filter_include if i in re.sub(r'\W', '', ('_'.join(map(str, line.values())) + '__' + line.get('Operator', '') + '_' + line.get('PhoneNumber', '') + '__').lower())]) > 0]
    # фильтр по filter_exclude - выкидываем строчки попавшие в фильтр
    if params.get('exclude', None) is not None:
        filter_exclude = [re.sub(r'\W', '', el).lower() for el in params['exclude'].split(',')]
        table = [line for line in table if len([1 for i in filter_exclude if i in re.sub(r'\W', '', '_'.join(map(str, line.values())).lower())]) == 0]
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
        table = [line for line in table if line['BalDelta'] != 0 and line['Balance'] != 0]
        table = [line for line in table if line['BalDelta'] != '' and line['Balance'] != '']
    return table


def prepare_balance_mobilebalance(filter:str='FULL', params:typing.Dict={}):
    """Формируем текст для отправки в telegram из html файла полученного из web сервера mobilebalance
    """
    phones = store.ini('phones.ini').phones()
    phones_by_num = {v['NN']: v for v in phones.values()}
    url = store.options('mobilebalance_http', section='Telegram')
    tgmb_format = store.options('tgmb_format', section='Telegram')
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
        line['Operator'] = line['Region'] = phones_by_num.get(int(line['NN']), '')['Region']
        line['PhoneNumber'] = phones_by_num.get(int(line['NN']), '')['Number'].split(' #')[0]  # Также отрезаем хвост <space>#num
    table2 = filter_balance(table, filter, params)
    res = [tgmb_format.format(**line) for line in table2]  # type: ignore
    return '\n'.join(res)


def prepare_balance_sqlite(filter:str='FULL', params:typing.Dict={}):
    'Готовим данные для отчета из sqlite базы'
    def alert_suffix(line):
        pkey = (line['PhoneNumber'], line['Operator'])
        uslugi = json.loads(responses.get(f"{line['Operator']}_{line['PhoneNumber']}", '{}')).get('UslugiList', '')
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}", '').startswith('error'):
            return f'<b> ! последняя попытка получить баланс завершилась ошибкой !</b>'
        if line['Balance'] is not None and line['Balance'] < float(store.options('BalanceLessThen', pkey=pkey)):
            return f'<b> ! достигнут порог баланса !</b>'
        if line['CalcTurnOff'] is not None and line['CalcTurnOff'] < int(store.options('TurnOffLessThen', pkey=pkey)):
            return f"<b> ! возможно скорое отключение - {line['CalcTurnOff']} дней !</b>"
        if line['NoChangeDays'] is not None and pkey in phones and line['NoChangeDays'] > int(store.options('BalanceNotChangedMoreThen', pkey=pkey)):
            return f"<b> ! баланс не изменялся более {store.options('BalanceNotChangedMoreThen', pkey=pkey)} дней !</b>"
        if line['NoChangeDays'] is not None and pkey in phones and line['NoChangeDays'] < int(store.options('BalanceChangedLessThen', pkey=pkey)):
            return f"<b> ! баланс изменился менее {store.options('BalanceChangedLessThen', pkey=pkey)} дней назад!</b>"
        if line['UslugiOn'] is not None:
            unwanted_kw = [kw.strip() for kw in store.options('subscribtion_keyword', pkey=pkey).split(',') if kw.strip() in uslugi]
            if len(unwanted_kw)>0:
                unwanted = '\n'.join([line for line in uslugi.split('\n') if len([kw for kw in unwanted_kw if kw in line])>0])
                return f"<b> ! В списке услуг присутствуют нежелательные: {unwanted}!</b>"
        return ''

    db = dbengine.Dbengine()
    table_format = store.options('tg_format', section='Telegram').replace('\\t', '\t').replace('\\n', '\n')
    phones = store.ini('phones.ini').phones()
    flags = dbengine.flags('getall')
    responses = dbengine.responses()
    table = db.report()
    # table_format = 'Alias,PhoneNumber,Operator,Balance'
    # Если формат задан как перечисление полей через запятую - переделываем под формат
    if re.match(r'^(\w+(?:,|\Z))*$', table_format.strip()):
        table_format = ' '.join([f'{{{i}}}' for i in table_format.strip().split(',')])
    table = [i for i in table if i['Alias'] != 'Unknown']  # filter Unknown
    table.sort(key=lambda i: [i['NN'], i['Alias']])  # sort by NN, after by Alias
    table = filter_balance(table, filter, params)
    res = [table_format.format(**line) + alert_suffix(line) for line in table]
    return '\n'.join(res)


def prepare_balance(filter:str='FULL', params:typing.Dict={}):
    """Готовим баланс для TG, смотрим параметр tg_from (sqlite или mobilebalance) и в зависимости от него кидаем на
    prepare_balance_sqlite - Готовим данные для отчета из sqlite базы
    prepare_balance_mobilebalance - Формируем текст для отправки в telegram из html файла полученного из web сервера mobilebalance
    """
    try:
        baltxt = ''
        if store.options('tg_from', section='Telegram') == 'sqlite':
            baltxt = prepare_balance_sqlite(filter, params)
        else:
            baltxt = prepare_balance_mobilebalance(filter, params)
        if baltxt == '' and str(store.options('send_empty', section='Telegram')) == '1':
            baltxt = 'No changes'
        return baltxt
    except Exception:
        exception_text = f'Ошибка: {store.exception_text()}'
        logging.error(exception_text)
        return 'error'


def send_telegram_over_requests(text=None, auth_id=None, filter:str='FULL', params:typing.Dict={}):
    """Отправка сообщения в телеграм через requests без задействия python-telegram-bot
    Может пригодится при каких-то проблемах с ботом или в ситуации когда на одной машине у нас крутится бот,
    а с другой в этого бота мы еще хотим засылать инфу
    text - сообщение, если не указано, то это баланс для телефонов у которых он изменился
    auth_id - список id через запятую на которые слать, если не указано, то берется список из mbplugin.ini
    """
    store.turn_logging(httplog=True)  # Т.к. сюда можем придти извне, то включаем логирование здесь
    if text is None:
        text = prepare_balance(filter, params)
    api_token = store.options('api_token', section='Telegram', mainparams=params).strip()
    if len(api_token) == 0:
        logging.info('Telegtam api_token not found')
        return
    if auth_id is None:
        auth_id = list(map(int, store.options('auth_id', section='Telegram', mainparams=params).strip().split(',')))
    else:
        auth_id = list(map(int, str(auth_id).strip().split(',')))
    r = [requests.post(f'https://api.telegram.org/bot{api_token}/sendMessage', data={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}) for chat_id in auth_id if text != '']
    return [repr(i) for i in r]


def restart_program(reason='', exit_only=False, delay=0):
    'Restart or exit with delay'
    time.sleep(delay)
    cmd = psutil.Process().cmdline()
    filename_pid = store.abspath_join(store.options('storefolder'), 'web-server.pid')
    # Fix нужен т.к. util.py переходит в другую папку и относительные пути ломаются
    # cmd = [(os.path.abspath('util.py') if i.endswith('util.py') else i) for i in cmd]
    logging.info(f'{"Exit" if exit_only else "Restart"} by {reason} with cmd:{subprocess.list2cmdline(cmd)}')
    TrayIcon().stop()
    if os.path.exists(filename_pid):
        with open(filename_pid) as f:
            pid_from_file = int(f.read())
        if pid_from_file == os.getpid():
            os.remove(filename_pid)
    if not exit_only:
        subprocess.Popen(cmd)  # Crossplatform run process
    psutil.Process().kill()
    cmdqueue.put('exit')  # Если kill не сработал (для pid=1 не сработает) - шлем сигнал


def send_http_signal(cmd, force=True):
    'Посылаем сигнал локальному веб-серверу'
    logging.info(f'Send {cmd} signal to web server')
    filename_pid = store.abspath_join(store.options('storefolder'), 'web-server.pid')
    if not os.path.exists(filename_pid) and not force:
        return
    port = int(store.options('port', section='HttpServer'))
    try:
        return requests.get(f'http://localhost:{port}/{cmd}', timeout=1).content.decode('cp1251')
    except Exception:
        pass
    # То что дальше - это вышибание процесса если web сервер не остановился
    if not(cmd == 'exit' and force):
        return
    for i in range(50):  # Подождем пока сервер остановится
        if os.path.exists(filename_pid):
            time.sleep(0.1)
    if os.path.exists(filename_pid):
        with open(filename_pid) as f:
            pid = int(open(filename_pid).read())
        if not psutil.pid_exists(pid):
            return
        proc = psutil.Process(pid)
        if len([c for c in proc.connections() if c.status == 'LISTEN' and c.laddr.port == port]) > 0:
            proc.kill()


class TrayIcon:
    'Создаем переменную класса, и при повторных вызовах не создаем новый а обращаемся к уже созданному'
    icon = None

    def __init__(self):
        if str(store.options('show_tray_icon')) != '1' or 'pystray' not in sys.modules:
            return
        if TrayIcon.icon is None:
            print('pystray traymeny')
            threading.Thread(target=self._create, name='TrayIcon', daemon=True).start()
            logging.info('Tray icon started')
        else:
            self.icon = TrayIcon.icon

    def _create(self):
        icon_fn = store.abspath_join('mbplugin', 'plugin', 'httpserver.ico')
        self.image = PIL.Image.open(icon_fn)
        items = []
        for item in TRAY_MENU:
            if item['show']:
                items.append(pystray.MenuItem(item['text'], item['cmd'], default=item.get('default', False)))
        self.menu = pystray.Menu(*items)
        host = store.options('host', section='HttpServer')
        port = int(store.options('port', section='HttpServer'))
        self.icon = pystray.Icon('mbplugin', icon=self.image, title=f"Mbbplugin {store.version()} ({host}:{port})", menu=self.menu)
        TrayIcon.icon = self.icon
        self.icon.run()

    def stop(self):
        print('STOP')
        if self.icon is not None:
            self.icon.visible = False
            self.icon.stop()


class Scheduler():
    '''Класс для работы с расписанием'''
    instance = None
    # Форматы расписаний см https://schedule.readthedocs.io
    # schedule2 = every().day.at("10:30"),megafon
    # строк с заданиями может быть несколько и их можно пихать в ini как
    # scheduler= ... scheduler1=... и т.д как сделано с table_format

    def __init__(self) -> None:
        if Scheduler.instance is None:
            self._scheduler_running = True  # Флаг, что шедулер работает
            self._job_running = False  # Флаг что в текущий момент задание выполняется
            self.thread = threading.Thread(target=self._forever, name='Scheduler', daemon=True)
            self.thread.start()
            Scheduler.instance = self
            logging.info('Scheduler started')
            self.reload()

    def _forever(self):
        while True:
            try:
                schedule.run_pending()
            except Exception:
                print('Schedule fail')
            time.sleep(1)
            if not self._scheduler_running:
                break

    def _run(self, cmd, once=False, kwargs={}):
        '''Запускаем задание, именно вызовы _run мы помещаем в очередь
        напрямую вызывать нельзя
        once - удалить задание после выполнения
        kwargs - передается сюда ИМЕННО как словарь без **'''
        self._job_running = True
        current_job = [job for job in schedule.jobs if job.should_run][0]
        if cmd.endswith('_once'):
            once = True
            cmd = cmd.replace('_once','')
        try:
            if cmd == 'check' or cmd == 'check_send':
                getbalance_standalone(**kwargs)
                baltxt = prepare_balance('FULL', params=kwargs.get('params', {}))
                store.feedback.text(baltxt)
                # Шлем по адресатам прописанным в ini
                if TelegramBot.instance is not None and cmd == 'check_send':
                    TelegramBot.instance.send_balance()
                    TelegramBot.instance.send_subscriptions()
            if cmd == 'get_one':
                get_full_info_one_number(**kwargs)
            if cmd == 'check_new_version':
                if TelegramBot.instance is not None:
                    ue = updateengine.UpdaterEngine()
                    if ue.check_update():
                        msg = f'Найдена новая версия\n'+'\n'.join(ue.latest_version_info(short=True))
                        TelegramBot.instance.send_message(msg)
            if cmd == 'ping':
                if TelegramBot.instance is not None:
                    msg = ' '.join(kwargs['filter']).strip()
                    TelegramBot.instance.send_message('ping' if msg == '' else msg)
            store.feedback.unset()  # После обработки задания отменяем 
        except Exception:
            logging.info(f'Scheduler: Error while run job {current_job}: {store.exception_text()}')
        self._job_running = False
        if once:
            return schedule.CancelJob

    def job_is_running(self):
        return Scheduler.instance._job_running

    def run_once(self, cmd, delay:int=1, feedback_func: typing.Callable=None,  kwargs={}) -> bool:
        '''Запланировать команду на однократный запуск, 
        cmd - команда для _run (check, check_send, get_one, check_new_version, ping и т.п.)
        delay - отложить старт на N секунд
        feedback - функция для отписки статуса, если смогли - вешаем на feedback, не смогли пишем в нее что не смогли
        kwargs - аргументы для cmd словарем, а не **
        возвращаем True - если запланировали и False если заняты
        при планировании once сразу блокируем возможность запланировать на раз еще что-то 
        чтобы не запутаться с feedback'''
        if Scheduler.instance is not None and not Scheduler().job_is_running():
            Scheduler.instance._job_running = True  # Сразу выставляем флаг что работаем, чтобы вдогонку не поставить второе
            schedule.every(delay).seconds.do(Scheduler.instance._run, cmd=cmd, once=True, kwargs=kwargs)
            if feedback_func is not None:
                store.feedback.set(feedback_func)
            return True
        else:
            if feedback_func is not None:
                feedback_func('Одно из заданий сейчас выполняется, попробуйте позже')
            return False

    def validate(self, sched) -> schedule.Job:
        'Проверяет одно расписание на валидность и возвращает в виде job'
        # every(4).day.at("10:30")
        m = re.match(r'^every\((?P<every>\d*)\)\.(?P<interval>\w*)(\.at\("(?P<at>.*)"\))?$', sched.strip())
        try:
            if not m:
                raise
            # every(4).hours,mts,beeline -> {'every': '4', 'interval': 'hours', 'at': None}
            param = m.groupdict()
            param['every'] = int(param['every']) if param['every'].isdigit() else 1
            job = getattr(schedule.every(int(param['every'])), param.get('interval',''))
            if param['at'] is not None:
                job = job.at(param['at'])
            return job
        except Exception:
            logging.error(f'Error parse {sched}')

    def _reload(self):
        'метод который отрабатывает в инстансе в котором работает _forever'
        schedule.clear()
        schedules = store.options('schedule', section='HttpServer', listparam=True)
        for schedule_str in schedules:
            if len(schedule_str.split(','))<2:
                logging.info(f'Bad schedule "{schedule_str}", cmd not found skipped')
                continue
            sched = schedule_str.split(',')[0].strip()
            cmd = schedule_str.split(',')[1].strip().lower()
            filter = [i.strip() for i in schedule_str.split(',')[2:]]
            job = self.validate(sched)
            if job is None:
                logging.info(f'Bad schedule "{schedule_str}", error parse job, skipped')
                continue
            job.do(self._run, cmd=cmd, kwargs={'filter':filter})
        logging.info('Schedule was reloaded')
        return 'OK'

    def reload(self):
        'Читает расписание из ini'
        Scheduler.instance._reload()

    def view_html(self) -> typing.Tuple[str, typing.List[str]]:
        'все задания html страницей'
        res = ['\n'.join(map(repr, schedule.jobs))]
        return 'text/html; charset=cp1251', ['<html><head></head><body><pre>'] + res + ['</pre></body></html>']

    def view_txt(self) -> str:
        'Все задания текстом'
        return '\n'.join(map(repr, schedule.jobs))+' '

    def stop(self):
        'Останавливаем шедулер'
        Scheduler.instance._scheduler_running = False

def auth_decorator(func):  # pylint: disable=no-self-argument
    def wrapper(self, update, context):
        # update.message.chat_id отсутствует у CallbackQueryHandler пробуем через update.effective_chat.id:
        if update.effective_chat.id in self.auth_id():
            if update is not None and update.effective_message is not None:
                logging.info(f'TG auth:{update.effective_chat.id} {update.effective_message.text}')            
            res = func(self, update, context)  # pylint: disable=not-callable
            return res
        else:
            logging.info(f'TG:{update.effective_chat.id} unauthorized {update.effective_message.text}')
    return wrapper

class TelegramBot():

    instance = None  # когда создадим класс сюда запишем ссылку на созданный экземпляр

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
                dp.add_handler(CommandHandler("getone", self.get_one))
                dp.add_handler(CommandHandler("checkone", self.get_one))
                dp.add_handler(CommandHandler("schedule", self.get_schedule))
                dp.add_handler(CommandHandler("schedulereload", self.get_schedule))
                dp.add_handler(CommandHandler("getlog", self.get_log))
                dp.add_handler(CallbackQueryHandler(self.button))
                dp.add_handler(MessageHandler(Filters.all, self.handle_catch_all))
                self.updater.start_polling()  # Start the Bot
                logging.info('Telegram bot started')
                if str(store.options('send_empty', section='Telegram')) == '1':
                    self.send_message(text='Hey there!')
                TelegramBot.instance = self  # Запустили бота - прописываем инстанс
            except Exception:
                exception_text = f'Ошибка запуска telegram bot {store.exception_text()}'
                logging.error(exception_text)
        elif 'telegram' not in sys.modules:
            logging.info('Module telegram not found')
        elif api_token == '':
            logging.info('Telegtam api_token not found')
        elif str(store.options('start_tgbot', section='Telegram')) != '1':
            logging.info('Telegtam bot start is disabled in mbplugin.ini (start_tgbot=0)')

    def handle_catch_all(self, update, context):
        'catch-all handler - логируем все что не попало в фильтры'
        if update is not None and update.effective_message is not None:
            logging.info(f'TG catch-all:{update.effective_chat.id} {update.effective_message.text}') 

    def auth_id(self):
        auth_id = store.options('auth_id', section='Telegram').strip()
        if not re.match(r'(\d+,?)', auth_id):
            logging.error(f'incorrect auth_id in ini: {auth_id}')
        return map(int, auth_id.split(','))

    def get_id(self, update, context):
        """Echo chat id."""
        logging.info(f'TG:{update.effective_message.chat_id} /id')
        self.put_text(update.effective_message.reply_text, update.effective_chat.id)

    def put_text(self, func: typing.Callable, text: str, parse_mode: str=telegram.ParseMode.HTML) -> typing.Optional[typing.Callable]:
        '''Вызываем функцию для размещения текста'''
        try:
            return func(text, parse_mode=parse_mode)
        except Exception:
            try:
                return func(text, parse_mode=None)
            except Exception:
                exception_text = store.exception_text()
                if 'Message is not modified' not in exception_text:
                    logging.info(f'Unsuccess tg send:{text} {exception_text}') 
                return None

    @auth_decorator
    def get_help(self, update, context):
        """Send help."""
        help_text = '''/help\n/id\n/balance\n/balancefile\n/receivebalance\n/receivebalancefailed\n/restart\n/getone\n/checkone\n/schedule\n/schedulereload\n/getlog'''
        logging.info(f'TG:{update.effective_message.chat_id} /help')
        self.put_text(update.effective_message.reply_text, help_text)

    @auth_decorator
    def get_balancetext(self, update, context):
        """Send balance only auth user."""
        baltxt = prepare_balance('FULL')
        self.put_text(update.effective_message.reply_text, baltxt)

    @auth_decorator
    def get_balancefile(self, update, context):
        """Send balance html file only auth user."""
        _, res = getreport()
        for id in self.auth_id():
            self.updater.bot.send_document(chat_id=id, filename='balance.htm', document=io.BytesIO('\n'.join(res).strip().encode('cp1251')))

    @auth_decorator
    def restartservice(self, update, context):
        """Hard reset service"""
        self.put_text(update.effective_message.reply_text, 'Service will be restarted')
        restart_program(reason=f'TG:{update.effective_message.chat_id} /restart {context.args}')

    @auth_decorator
    def receivebalance(self, update, context):
        """ Запросить балансы по всем номерам, only auth user.
        /receivebalance
        /receivebalancefailed
        """
        def feedback_func(txt):
            self.put_text(msg.edit_text, txt)
        filtertext = '' if len(context.args) == 0 else f", with filter by {' '.join(context.args)}"
        msg = self.put_text(update.effective_message.reply_text, f'Request all number{filtertext}. Wait...')
        # Если запросили плохие - то просто запрашиваем плохие
        # Если запросили все - запрашиваем все, потом два раза только плохие
        only_failed = (update.effective_message.text == "/receivebalancefailed")
        params = {'include': None if context.args == [] else ','.join(context.args)}
        Scheduler().run_once(cmd='check', feedback_func=feedback_func, kwargs={'filter':context.args, 'params':params, 'only_failed':only_failed})

    @auth_decorator
    def get_schedule(self, update, context):
        """Show schedule only auth user.
        /schedule
        /schedulereload
        """
        if update.effective_message.text == "/schedulereload":
            Scheduler().reload()
        text = Scheduler().view_txt()
        self.put_text(update.effective_message.reply_text, text if text.strip() != '' else 'Empty')

    @auth_decorator
    def get_one(self, update, context: telegram.ext.callbackcontext.CallbackContext):
        """Receive one balance with inline keyboard/args, only auth user.
        /checkone - получаем баланс
        /getone - показываем"""
        # Заданы агрументы? Тогда спросим по ним.
        args = ' '.join(context.args if context.args is not None else []).lower()
        if args != '' and update is not None:  # context.args
            cmd = (update.effective_message.text[1:]).split(' ')[0]
            filtered = [v for k,v in store.ini('phones.ini').phones().items() if v['number'].lower()==args or v['alias'].lower()==args]
            message = self.put_text(update.effective_message.reply_text, f'You have chosen {args}')
            if len(filtered) > 0:
                val = filtered[0]
                callback_data=f"{cmd}_{val['Region']}_{val['Number']}"
                cmd, keypair = callback_data.split('_', 1)  # До _ команда, далее Region_Number
            else:
                self.put_text(message.edit_text, f'Not found {args}')  # type: ignore
                return
            feedback_func = lambda txt:self.put_text(message.edit_text, txt)  # type: ignore
            Scheduler().run_once(cmd='get_one', feedback_func=feedback_func, kwargs={'keypair': keypair, 'check': cmd == 'checkone'})
            return
        query: typing.Optional[telegram.callbackquery.CallbackQuery] = update.callback_query
        if query is None:  # Создаем клавиатуру
            phones = store.ini('phones.ini').phones()
            keyboard: typing.List = []
            cmd = (update.effective_message.text[1:]).split(' ')[0]  # checkone или getone
            for val in list(phones.values()) + [{'Alias': 'Cancel', 'Region': 'Cancel', 'Number': 'Cancel'}]:
                # ключом для calback у нас команда_Region_Number
                btn = InlineKeyboardButton(val['Alias'], callback_data=f"{cmd}_{val['Region']}_{val['Number']}")
                if len(keyboard) == 0 or len(keyboard[-1]) == 3:
                    keyboard.append([btn])
                else:
                    keyboard[-1].append(btn)
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_text('Please choose:', reply_markup=reply_markup)
        else:  # реагируем на клавиатуру
            if query.data is None:
                return
            cmd, keypair = query.data.split('_', 1)  # До _ команда, далее Region_Number
            feedback_func = lambda txt:self.put_text(query.edit_message_text, txt)  # type: ignore
            Scheduler().run_once(cmd='get_one', feedback_func=feedback_func, kwargs={'keypair': keypair, 'check': cmd == 'checkone'})

    @auth_decorator
    def get_log(self, update: telegram.update.Update, context: telegram.ext.callbackcontext.CallbackContext):
        """Receive one log with inline keyboard/param, only auth user.
        /getlog - лог по последнему запросу
        сюда приходим ДВА раза сначала чтобы создать клавиатуру(query=None), 
        а потом чтобы отреагировать на нее
        """
        # reply(query.edit_message_text, query.message.reply_document, query.data)
        def reply(edit_text, message, keypair):
            self.put_text(edit_text, 'This is log')
            res = prepare_log_personal(keypair)
            message.reply_document(filename=f'{keypair}_log.htm', document=io.BytesIO(res.strip().encode('cp1251')))
        # Заданы агрументы? Тогда спросим по ним.
        args = ' '.join(context.args if context.args is not None else []).lower()
        # запрашиваем по заданному аргументу
        if args != '' and update is not None:  # context.args
            logs = prepare_loglist_personal()
            filtered = [i for i in logs if args.lower() in i.lower()]
            new_msg: telegram.message.Message = self.put_text(update.effective_message.reply_text, f'Info for {args}')  # type: ignore
            if len(filtered)>0 and new_msg is not None:
                val = filtered[0]
                reply(new_msg.edit_text, update.effective_message, val)
            else:
                self.put_text(new_msg.edit_text, f'Not found {args}')
            return
        query: typing.Optional[telegram.callbackquery.CallbackQuery] = update.callback_query
        if query is None:  # Создаем клавиатуру
            if update.effective_message is None:
                return
            keyboard: typing.List[typing.List[InlineKeyboardButton]] = []
            logs = prepare_loglist_personal()
            for val in logs + ['Cancel']:
                # ключом для calback у нас команда_Region_Number
                btn = InlineKeyboardButton(val, callback_data=f"getlog_{val}")
                if len(keyboard) == 0 or len(keyboard[-1]) == 3:
                    keyboard.append([btn])
                else:
                    keyboard[-1].append(btn)
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_text('Please choose:', reply_markup=reply_markup)
        else:  # реагируем на клавиатуру
            # ...
            if query.message is None or query.data is None:
                return
            reply(query.edit_message_text, query.message, query.data.split('_', 1)[1])

    @auth_decorator
    def button(self, update, context) -> None:
        '''Клавиатура, здесь реакция на нажатие
        Определяем откуда пришли и бросаем обратно'''
        query: typing.Optional[telegram.callbackquery.CallbackQuery] = update.callback_query
        if query is None or query.data is None:
            return
        query.answer()
        logging.info(f'TG:reply keyboard to {update.effective_chat.id} CHOICE:{query.data}')
        cmd,val = query.data.split('_', 1)  # До _ команда, далее кнопка, например Region_Number
        if val.startswith('Cancel'):
            self.put_text(query.edit_message_text, 'Canceled')
            return
        self.put_text(query.edit_message_text, 'Request received. Wait...')
        # ключом для calback у нас 6 букв
        if cmd == 'getlog':  # /getlog - генерим лог и выходим
            self.get_log(update, context)
        if cmd in ['checkone', 'getone']:
            self.get_one(update, context)

    def send_message(self, text:str, parse_mode=telegram.ParseMode.HTML, ids=None):
        'Отправляем сообщение по списку ids, либо по списку auth_id из mbplugin.ini'
        if self.updater is None or text == '':
            return
        lst = self.auth_id() if ids is None else ids
        text = text if type(text) == str else str(text)
        for id in lst:
            try:
                self.updater.bot.sendMessage(chat_id=id, text=text, parse_mode=parse_mode)
            except Exception:
                try:
                    self.updater.bot.sendMessage(chat_id=id, text=text[:4000], parse_mode=None)
                except Exception:
                    exception_text = f'Ошибка отправки сообщения {text} для {id} telegram bot {store.exception_text()}'
                    logging.error(exception_text)

    def send_balance(self):
        'Отправляем баланс'
        if self.updater is None or str(store.options('send_balance_changes', section='Telegram')) == '0':
            return
        baltxt = prepare_balance('LASTCHANGE')
        self.send_message(text=baltxt, parse_mode=telegram.ParseMode.HTML)

    def send_subscriptions(self):
        'Отправляем подписки - это строки из ini вида:'
        'subscriptionXXX = id:123456 include:1111,2222 exclude:6666'
        if self.updater is None:
            return
        subscriptions = store.options('subscription', section='Telegram', listparam=True)
        for subscr in subscriptions:
            # id:123456 include:1111,2222 -> {'id':'123456', 'include':'1111,2222'}
            params = {k: v.strip() for k, v in [i.split(':', 1) for i in subscr.split(' ')]}
            baltxt = prepare_balance('LASTCHANGE', params)
            ids = [int(i) for i in params.get('id', '').split(',') if i.isdigit()]
            self.send_message(text=baltxt, parse_mode=telegram.ParseMode.HTML, ids=ids)

    def stop(self):
        '''Stop bot'''
        if self.updater is not None:
            self.updater.stop()


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
        self.filename_pid = store.abspath_join(store.options('storefolder'), 'web-server.pid')
        store.turn_logging(httplog=True)
        self.port = int(store.options('port', section='HttpServer'))
        self.host = store.options('host', section='HttpServer')
        with socket.socket() as sock:
            sock.settimeout(0.2)  # this prevents a 2 second lag when starting the server
            if sock.connect_ex(('127.0.0.1', self.port)) == 0:
                logging.info(f"Port 127.0.0.1:{self.port} already in use, try restart.")
                try:
                    send_http_signal(cmd='exit')
                except Exception:
                    pass
        if str(store.options('start_http', section='HttpServer')) != '1':
            logging.info(f'Start http server disabled in mbplugin.ini (start_http=0)')
            return
        with wsgiref.simple_server.make_server(self.host, self.port, self.web_app, server_class=ThreadingWSGIServer, handler_class=Handler) as self.httpd:
            with open(self.filename_pid, 'w') as f:
                f.write(f'{os.getpid()}')
            logging.info(f'Starting web server from {os.path.abspath(__file__)}')
            logging.info(f'Listening pid={os.getpid()} {self.host}:{self.port}....')
            threading.Thread(target=self.httpd.serve_forever, name='httpd', daemon=True).start()
            if 'pystray' in sys.modules:  # Иконка в трее
                self.tray_icon = TrayIcon()  # tray icon (он сам все запустит в threading)
            if 'telegram' in sys.modules:  # telegram bot (он сам все запустит в threading)
                self.telegram_bot = TelegramBot()
            if 'schedule' in sys.modules:  # Scheduler (он сам все запустит в threading)
                self.scheduler = Scheduler()
            # Запустили все остальное демонами и ждем, когда они пришлют сигнал
            cmdqueue.get()

    def shutdown(self):
        self.telegram_bot.stop()
        self.scheduler.stop()
        self.httpd.shutdown()
        logging.info(f'Shutdown server {self.host}:{self.port}....')

    def editor(self, environ):
        ''' Редактор конфигов editcfg
        возвращаем Content-type, text, status, add_headers'''
        # print(environ)
        # т.к. возвращаем разные статусы и куки, готовим переменные под них
        autorized = False  # Изначально считаем что пользователь не авторизован
        # breakpoint() if os.path.exists('breakpoint') else None
        status = '200 OK'
        add_headers = []
        cookie_store_name = store.abspath_join(store.options('storefolder'), 'authcookie')
        # Читаем список сохраненных кук
        if os.path.exists(cookie_store_name):
            with open(cookie_store_name) as f:
                authcookies = [i for i in map(str.strip, f.readlines()) if i != '']
        else:
            authcookies = []
        # Получаем переданные куки из заголовка
        cookies = {k: v[0] for k, v in urllib.parse.parse_qs(environ.get('HTTP_COOKIE', '{}')).items()}
        # Авторизованы если переданная кука в списке сохраненных
        autorized = cookies.get('auth', 'None') in authcookies
        # Если пришли с localhost и разрешено локалхосту без авторизации
        local_autorized = environ.get('REMOTE_ADDR', 'None') == '127.0.0.1' and str(store.options('httpconfigeditnolocalauth')) == '1'
        if local_autorized:
            autorized = True
        # если еще не открывали редактируемый ini открываем
        if not hasattr(self, 'editini'):
            self.editini = store.ini()
        print(cookies, f"auth in authcookies={cookies.get('auth', 'None') in authcookies}", f'autorized={autorized}')
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
                    request = {k: v[0] for k, v, in request.items()}
                except Exception:
                    request = {'cmd': 'error'}
            print(f'request={request}')
            if autorized and request['cmd'] == 'update':
                params = settings.ini[request['sec']].get(request['id'] + '_', {})
                # Если для параметра указана функция валидации - вызываем ее
                if not params.get('validate', lambda i: True)(request['value']):
                    return 'text/plain', 'ERROR', status, add_headers
                logging.info(f"ini change key [{request['sec']}] {request['id']} {self.editini.ini[request['sec']].get(request['id'], 'default')}->{request['value']}")
                self.editini.ini[request['sec']][request['id']] = request['value']
                self.editini.write()
                # print('\n'.join([f'{k}={v}' for k, v in self.editini.ini[request['sec']].items()]))
            elif autorized and request['cmd'] == 'delete':
                logging.info(f"ini delete key [{request['sec']}] {request['id']} {self.editini.ini[request['sec']].get(request['id'], 'default')}")
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
                    add_headers = [
                        ('Set-Cookie', f'auth={auth_token}'),
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
        if environ['REQUEST_METHOD'] == 'GET':
            self.editini = store.ini()
            self.editini.read()
            # TODO в финале editor.html будем брать из settings.py
            # editor_html = open('editor.html', encoding='cp1251').read()
            editor_html = settings.editor_html
            inidata = '{}'
            if autorized:
                inidata = self.editini.ini_to_json().replace('\\', '\\\\')
            editor_html = editor_html.replace("inifile = JSON.parse('')", f"inifile = JSON.parse('{inidata}')")
            if local_autorized:
                editor_html = editor_html.replace('localAuthorized = false // init', f'localAuthorized = true // init')
            return 'text/html', editor_html, status, add_headers

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
                self.telegram_bot.send_subscriptions()
            elif cmd.lower() == 'get':  # вариант через get запрос
                param = urllib.parse.parse_qs(environ['QUERY_STRING'])
                ct, text = getbalance_plugin('get', param)
            elif cmd.lower() == 'log':  # просмотр лога /log/....
                if len(param) > 0 and param[0] == 'list':  # /log/list
                    allgroups = prepare_loglist_personal()
                    text = [f'<a href=/log/{g}>{g}<a/><br>' for g in allgroups]
                elif len(param) > 0 and re.match(r'^\w*$', param[0]):  # /log/p_plugin_number
                    # text = [f'<img src=/screenshot/{os.path.split(fn)[-1]}/><br>' for fn in ss]
                    text = [prepare_log_personal(param[0])]
                else:  # /log
                    qs = urllib.parse.parse_qs(environ['QUERY_STRING'])
                    ct, text = view_log(qs)
            elif cmd.lower() == 'screenshot':  # скриншоты
                if len(param) == 0 or not re.match(r'^\w*\.png$', param[0]):
                    return
                with open(store.abspath_join(store.options('loggingfolder'), param[0]), 'rb') as f:
                    text = f.read()
                ct = 'image/png'
            elif cmd.lower() == 'schedule':  # просмотр расписания
                ct, text = Scheduler().view_html()
            elif cmd.lower() == 'reload_schedule':  # обновление расписания
                Scheduler().reload()
                ct, text = Scheduler().view_html()
            elif cmd == 'logging_restart':  # logging_restart
                store.logging_restart()
                ct, text = 'text/html', 'OK'
            elif cmd == '' or cmd == 'report':  # report
                if str(store.options('sqlitestore')) == '1':
                    ct, text = getreport(param)
                else:
                    ct, text = 'text/html', HTML_NO_REPORT
            elif cmd.lower() == 'main':  # главная страница
                ct, text = 'text/html; charset=cp1251', [settings.main_html % {'info': f'Mbplugin {store.version()}<br>'}]
            elif cmd.lower() == 'editcfg':  # вариант через get запрос
                if str(store.options('HttpConfigEdit')) == '1':
                    ct, text, status, add_headers = self.editor(environ)
            elif cmd == 'getbalance_standalone':  # start balance request
                # TODO подумать над передачей параметров в fetch - filter=filter,only_failed=only_failed
                Scheduler().run_once(cmd='check')
                ct, text = 'text/html; charset=cp1251', ['OK']
            elif cmd == 'flushlog':  # Start new log
                store.logging_restart()
                ct, text = 'text/html; charset=cp1251', ['OK']
            elif cmd == 'recompile':  # Recompile js lsmblh plugin
                compile_all_jsmblh.recompile()
                ct, text = 'text/html; charset=cp1251', ['OK']
            elif cmd == 'restart':  # exit cmd
                ct, text = 'text/html; charset=cp1251', ['OK']
                # TODO нужен редирект иначе она зацикливается на рестарте
                threading.Thread(target=lambda: restart_program(reason=f'WEB: /restart', delay=0.1), name='Restart', daemon=True).start()
            elif cmd == 'exit':  # exit cmd
                ct, text = 'text/html; charset=cp1251', ['OK']
                threading.Thread(target=lambda: restart_program(reason=f'WEB: /exit', exit_only=True, delay=0.1), name='Exit', daemon=True).start()
            if status.startswith('200'):
                headers = [('Content-type', ct)]
            if status.startswith('303'):
                headers = [('Location', '')] + add_headers
            start_response(status, headers)
            logging.debug('web_app done')
            if 'png' in ct:
                return [text]
            return [line.encode('cp1251', errors='ignore') for line in text]
        except Exception:
            exception_text = f'Ошибка: {store.exception_text()}'
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
            send_http_signal(cmd='exit')
    except Exception:
        exception_text = f'Ошибка запуска WebServer: {store.exception_text()}'
        logging.error(exception_text)


if __name__ == '__main__':
    main()
