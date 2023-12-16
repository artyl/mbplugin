# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import typing, os, sys, io, random, re, time, json, threading, logging, importlib, queue, argparse, subprocess, glob, base64, collections
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
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
except ModuleNotFoundError:
    print('No telebot module installed, no telegram bot')

lang = 'p'  # Для плагинов на python префикс lang всегда 'p'

# Scheduler commands constants
CMD_CHECK = 'check'
CMD_CHECK_SEND = 'check_send'
CMD_CHECK_NEW_VERSION = 'check_new_version'
CMD_PING = 'ping'
CMD_GET_ONE = 'get_one'
SCHED_CMDS = (CMD_CHECK, CMD_CHECK_NEW_VERSION, CMD_CHECK_SEND, CMD_GET_ONE, CMD_PING)

Job = collections.namedtuple('Job', 'job_str job_sched cmd filter err_msg')

Q_CMD_EXIT = 'exit'
Q_CMD_CANCEL = 'cancel'
cmdqueue: queue.Queue = queue.Queue()  # Диспетчер команд - нужен для передачи сигналов между трэдами, в т.к. для завершения в докере - kill для pid=1 не работает

HTML_NO_REPORT = '''Для того чтобы были доступны отчеты необходимо в mbplugin.ini включить запись результатов в sqlite базу<br>
sqlitestore = 1<br>Также можно настроить импорт из базы BalanceHistory.mdb включив <br>
createhtmlreport = 1<br>
После включения, запустите mbplugin\\setup_and_check.bat
'''

# TODO в командах для traymeny используется os.system(f'start ... это будет работать только в windows, но пока пофигу, т.к. сам pystray работает только в windows
# т.к. импортируем до включения MODE_MB пришлось завернуть это в функцию
def tray_menu():
    return (
        {'text': "Main page", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/main'), 'show': True},
        {'text': "View report", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/report'), 'show': True},
        {'text': "Edit config", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/editcfg'), 'show': str(store.options('HttpConfigEdit')) == '1'},
        {'text': "View log", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/log?lines=40'), 'show': True},
        {'text': "View screenshot log", 'cmd': lambda: os.system(f'start http://localhost:{store.options("port", section="HttpServer")}/log/list'), 'show': True},
        {'text': "Get balance request", 'cmd': lambda: threading.Thread(target=getbalance_standalone, name='Getbalance', daemon=True).start(), 'show': True},
        {'text': "Flush log", 'cmd': lambda: store.logging_restart(), 'show': True},
        {'text': "Reload schedule", 'cmd': lambda: Scheduler().reload(), 'show': True},
        {'text': "Recompile jsmblh plugin", 'cmd': lambda: compile_all_jsmblh.recompile(), 'show': True},
        # {'text': "Version update", 'cmd': lambda: run_update(), 'show': True},  # TODO продумать как это показывать
        {'text': "Cancel balance request", 'cmd': lambda: cancel_query(reason='tray icon command'), 'show': True},
        {'text': "Restart server", 'cmd': lambda: restart_program(reason='tray icon command'), 'show': True},
        {'text': "Exit program", 'cmd': lambda: restart_program(reason='Tray icon exit', exit_only=True), 'show': True}
    )


def getbalance_standalone_one_pass(queue):
    ''' Получаем балансы самостоятельно без mobilebalance ОДИН ПРОХОД
    по списку queue_balance
    '''
    result: typing.Dict = {}
    for val in queue:
        keypair = f"{val['Region']}_{val['Number']}"
        prev_state = str(dbengine.flags('get', keypair))
        if not prev_state.endswith('queue'):
            dbengine.flags('set', keypair, f'{prev_state} queue')  # выставляем флаг о постановке в очередь в КОНЕЦ строки
    for val in queue:
        # TODO пока дергаем метод от веб сервера там уже все есть, потом может вынесем отдельно
        keypair = f"{val['Region']}_{val['Number']}"
        try:
            # проверяем на сигнал Q_CMD_CANCEL, все остальное - кладем обратно
            if Q_CMD_CANCEL in cmdqueue.queue:
                qu = [cmdqueue.get(block=False) for el in range(cmdqueue.qsize())]
                [cmdqueue.put(el) for el in qu if el != Q_CMD_CANCEL]  # type: ignore
                logging.info(f'Receive cancel signal to query')
                store.feedback.text(f"Receive cancel signal")
                return result
            store.feedback.text(f"Receive {val['Alias']}:{val['Region']}_{val['Number']}")
            r1 = getbalance_plugin('get', {'plugin': [val['Region']], 'login': [val['Number']], 'password': [val['Password2']], 'date': ['date']})
            result[keypair] = 'Balance' in repr(r1)
        except Exception:
            result[keypair] = False
            logging.error(f"Unsuccessful check {val['Region']} {val['Number']} {store.exception_text()}")
    return result


def getbalance_standalone(filter: list = [], only_failed: bool = False, retry: int = -1, **kwargs):
    ''' Получаем балансы делая несколько проходов по неудачным
    retry=N количество повторов по неудачным попыткам, после запроса по всем (повторы только при only_failed=False)
    kwargs добавлен чтобы забрать из _run все лишние параметры
    Результаты сохраняются в базу
    Если filter пустой то по всем номерам из phones.ini
    Если не пустой - то логин/алиас/оператор или его часть
    для автономной версии в поле Password2 находится незашифрованный пароль
    ВНИМАНИЕ! при редактировании файла phones.ini через MobileBalance строки с паролями будут удалены
    для совместного использования с MobileBalance храните пароли password2 и другие специфичные опции
    для Standalone версии в файле phones_add.ini
    only_failed=True - делать запросы только по тем номерам, по которым прошлый запрос был неудачный
    '''
    store.turn_logging(httplog=True)  # Т.к. сюда можем придти извне, то включаем логирование здесь
    logging.info(f'getbalance_standalone: filter={filter}')
    phones = store.ini('phones.ini').phones()
    queue_balance = []  # Очередь телефонов на получение баланса
    for val in phones.values():
        if val['monitor'].upper() != 'TRUE':
            continue  # только те у кого включен мониторинг
        keypair = f"{val['Region']}_{val['Number']}"
        # Проверяем все у кого задан плагин, логин и пароль пароль
        if val['Number'] != '' and val['Region'] != '' and val['Password2'] != '':
            if len(filter) == 0 or [1 for i in filter if i.lower() in f"__{keypair}__{val['Alias']}".lower()] != []:
                # Формируем очередь на получение балансов и размечаем балансы из очереди в таблице flags чтобы красить их по другому
                queue_balance.append(val)
                logging.info(f'getbalance_standalone queued: {keypair}')
    store.feedback.text(f'Queued {len(queue_balance)} numbers')
    if retry == -1:
        retry = int(store.options('retry_failed', flush=True))
    result = {}
    if only_failed:
        queue_fail = [val for val in queue_balance if str(dbengine.flags('get', f"{val['Region']}_{val['Number']}")).startswith('error')]
        getbalance_standalone_one_pass(queue_fail)
    else:
        result.update(getbalance_standalone_one_pass(queue_balance))
        for i in range(retry):
            queue_fail = [val for val in queue_balance if str(dbengine.flags('get', f"{val['Region']}_{val['Number']}")).startswith('error')]
            result.update(getbalance_standalone_one_pass(queue_fail))
    return result


def get_full_info_one_number(keypair: str, check: bool = False) -> str:
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
    pkey = store.get_pkey(param['login'], param['fplugin'])  # (param['login'], param['fplugin'])
    store.options('logginglevel', flush=True)  # Запускаем, чтобы сбросить кэш и перечитать ini
    phone_items = store.ini('phones.ini').phones().get(pkey, {}).items()
    individual = ','.join([f'{k}={v}' for k, v in phone_items if k.lower() in store.settings.ini['Options'].keys()])
    unused = ','.join([f'{k}={v}' for k, v in phone_items
                       if all([k.lower() not in store.settings.ini['Options'].keys(),
                               k.lower() not in store.settings.PHONE_INI_KEYS_LOWER,
                               k.lower() != 'nn' and not k.lower().endswith('_orig')])
                       ])
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
            if store.option_validate('jitter')[0]:
                jitters = store.options('jitter').split(',', 1)
                # n и m сортируем по возрастанию т.к. randint не любит когда n>m
                j_time = random.uniform(*sorted([int(jitters[0]), int(jitters[1])]))
                logging.info(f'Jitter {j_time:.2f} seconds')
                time.sleep(j_time)
            result = module.get_balance(param['login'], param['password'], storename, pkey=pkey)
            result = store.correct_and_check_result(result, pkey=pkey)
            text = store.result_to_html(result)
        except Exception:
            logging.info(f'{plugin} fail: {store.exception_text()}')
            dbengine.flags('set', f"{lang}_{plugin}_{param['login']}", f'error call {time.asctime()}')  # выставляем флаг о ошибке вызова
            return 'text/html', [f"<html>Error call {param['fplugin']}<br><pre>{store.exception_text()}</pre></html>"]
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
    all_match = [re.search(r'(.*)_\d+\.png', os.path.split(fn)[-1]) for fn in ss]
    all_groups = sorted(set([m.groups()[0] for m in all_match if m]))
    return all_groups

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
    def pp_field(pkey, he, el, hover, unwanted=False, link=''):
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
        if link != '':
            el = f'<div class="operatorlink"><a href="{link}" target="_blank" rel="noopener noreferrer">{el}</a></div>'
        return f'<{"th" if he=="NN" else "td"} id="{he}"{mark}>{el}</td>'
    store.options('logginglevel', flush=True)  # Запускаем, чтобы сбросить кэш и перечитать ini
    template_page = settings.table_template['page']
    template_history = settings.table_template['history']
    template_style = settings.table_template['style']
    html_script = settings.table_template['script']
    db = dbengine.Dbengine()
    flags = dbengine.flags('getall')  # берем все флаги словарем
    responses = dbengine.responses()  # все ответы по запросам
    # номера провайдеры и логины из phones.ini
    num_format = '' if len(param) == 0 or not param[0].isnumeric() else str(int(param[0]))
    groups = [p.replace('group_', '').lower() for p in param if p.startswith('group_')]
    table_format = store.options('table_format' + num_format, default=store.options('table_format', section='HttpServer'), section='HttpServer')
    table = db.report()
    phones = store.ini('phones.ini').phones()
    if 'Alias' not in table_format:
        table_format = 'NN,Alias,' + table_format  # Если старый ini то этих столбцов нет - добавляем
    table = [i for i in table if i['Alias'] != 'Unknown']  # filter Unknown
    table.sort(key=lambda i: [i['NN'], i['Alias']])  # sort by NN, after by Alias
    header = [i.strip() for i in table_format.split(',')]
    # классы для формата заголовка
    header_class = {'Balance': 'p_b', 'RealAverage': 'p_r', 'BalDelta': 'p_r', 'BalDeltaQuery': 'p_r', 'NoChangeDays': 'p_r', 'CalcTurnOff': 'p_r', 'MinAverage': 'p_r', }
    html_header = ''.join([f'<th id="h{h}" class="order {header_class.get(h,"p_n")}">{dbengine.PhonesHText.get(h, h)}</th>' for h in header])
    html_table = []
    for line in table:
        html_line = []
        pkey = store.get_pkey(line['PhoneNumber'], line['Operator'])
        # Group of numbers (Indication) - use /group_aaa/group_bbb in url
        if len(groups) > 0 and phones[pkey].get('indication', '').lower() not in groups:
            continue
        uslugi = json.loads(responses.get(f"{line['Operator']}_{line['PhoneNumber']}", '{}')).get('UslugiList', '')
        subscription_keyword = [i.strip() for i in store.options('subscription_keyword', pkey=pkey).lower().split(',')]
        unwanted_kw = [kw for kw in subscription_keyword if kw in uslugi.lower()]  # встретившиеся нежелательные
        for he in header:
            if he not in line:
                continue
            hover, link = '', ''
            if he == 'Alias':
                if str(store.options('htmlreportoperatorlink')) == '1':
                    link = settings.operator_link.get(line['Operator'], '')
            if he == 'UslugiOn':  # На услуги вешаем hover со списком услуг
                if uslugi != '':
                    h_html_header = f'<th id="hUsluga" class="p_n">Услуга</th><th id="hPrice" class="p_n">р/мес</th>'
                    h_html_table = []
                    for h_line in [li.split('\t', 1) for li in sorted(uslugi.split('\n')) if '\t' in li]:
                        txt = h_line[0].replace("  ", " &nbsp;")
                        bal = f'{float(h_line[1]):.2f}' if re.match(r'^ *-?\d+(?:\.\d+)? *$', h_line[1]) else h_line[1]
                        h_html_line = f'<td id="Alias">{txt}</td><td id="Balance">{bal}</td>'
                        u_classflag = 'n'
                        if len(unwanted_kw) > 0 and len([kw for kw in unwanted_kw if kw in h_line[0].lower()]) > 0:
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
            html_line.append(pp_field(pkey, he, line[he], hover, unwanted=(len(unwanted_kw) > 0), link=link))  # append <td>...</td>
        classflag = 'n'  # красим строки - с ошибкой красным, текущий - зеленым, еще в очереди - серым и т.д.
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}", '').startswith('error'):
            classflag = 'e_us'
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}", '').startswith('start'):
            classflag = 's_us'
        if flags.get(f"{line['Operator']}_{line['PhoneNumber']}", '').endswith('queue'):
            classflag = 'n_us'
        html_table.append(f'<tr id="row" class="order {classflag}">{"".join(html_line)}</tr>')
    template_style = template_style.replace('{HoverCss}', store.options('HoverCss'))  # HoverCss общий на всю страницу, поэтому берем без pkey
    res = template_page.format(style=template_style, html_header=html_header, html_table='\n'.join(html_table), title=store.version(), html_script=html_script)
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


def filter_balance(table: typing.List[typing.Dict], filter: str = 'FULL', params: typing.Dict = {}) -> typing.List[typing.Dict]:
    ''' Фильтруем данные для отчета
    filter = FULL - Все телефоны, LASTDAYCHANGE - Изменившиеся за день, LASTCHANGE - Изменившиеся в последнем запросе
    params['include'] = None - все, либо список через запятую псевдонимы или логины или какая-то их уникальная часть для включения в результат
    params['exclude'] = None - все, либо список через запятую псевдонимы или логины или какая-то их уникальная часть для исключения из результата'''
    flags = dbengine.flags('getall')
    # фильтр по filter_include - оставляем только строчки попавшие в фильтр
    # from send_subscriptions params like {'id':'123456', 'include':'1111,2222'}
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
                 if any([
                     all([line['BalDeltaQuery'] != 0,
                          line['Balance'] != 0,
                          line['BalDeltaQuery'] != line['Balance'],
                          line['BalDeltaQuery'] != '',
                          line['Balance'] != '']),
                     flags.get(f"{line.get('Operator', '')}_{line.get('PhoneNumber', '')}", '').startswith('error')])
                 ]
    elif filter == 'LASTDAYCHANGE':
        table = [line for line in table if line['BalDelta'] != 0 and line['Balance'] != 0]
        table = [line for line in table if line['BalDelta'] != '' and line['Balance'] != '']
    return table


def prepare_balance_mobilebalance(filter: str = 'FULL', params: typing.Dict = {}):
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


def prepare_balance_sqlite(filter: str = 'FULL', params: typing.Dict = {}):
    'Готовим данные для отчета из sqlite базы'
    def alert_suffix(line):
        pkey = store.get_pkey(line['PhoneNumber'], line['Operator'])
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
            unwanted_kw = [kw.strip() for kw in store.options('subscription_keyword', pkey=pkey).split(',') if kw.strip() in uslugi]
            if len(unwanted_kw) > 0:
                unwanted = '\n'.join([line for line in uslugi.split('\n') if len([kw for kw in unwanted_kw if kw in line]) > 0])
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
        table_format = ' '.join([f'{{{i.strip()}}}' for i in table_format.split(',')])
    table = [i for i in table if i['Alias'] != 'Unknown']  # filter Unknown
    table.sort(key=lambda i: [i['NN'], i['Alias']])  # sort by NN, after by Alias
    table = filter_balance(table, filter, params)
    table = [{k:(0 if v is None else v) for k,v in line.items()} for line in table] # convert None to 0
    res = [table_format.format(**line) + alert_suffix(line) for line in table]
    return '\n'.join(res)


def prepare_balance(filter: str = 'FULL', params: typing.Dict = {}):
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


def send_telegram_over_requests(text=None, auth_id=None, filter: str = 'FULL', params: typing.Dict = {}):
    """Отправка сообщения в телеграм через requests без использования python-telegram-bot
    Может пригодится при каких-то проблемах с ботом или в ситуации когда на одной машине у нас крутится бот,
    а с другой в этого бота мы еще хотим засылать инфу
    text - сообщение, если не указано, то это баланс для телефонов у которых он изменился
    auth_id - список id через запятую на которые слать, если не указано, то берется список из mbplugin.ini
    """
    store.switch_to_mb_mode()
    store.turn_logging(httplog=True)  # Т.к. сюда можем придти извне, то включаем логирование здесь
    if text is None:
        text = prepare_balance(filter, params)
    api_token = store.options('api_token', section='Telegram', mainparams=params).strip()
    if len(api_token) == 0:
        logging.info('Telegram api_token not found')
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
        subprocess.Popen(cmd)  # Cross platform run process
    # TODO ??? для coverage выключил, возможно он нужен когда нужно выходить во время работающего хрома
    if 'coverage' not in sys.modules:
        psutil.Process().kill()
    if Q_CMD_EXIT not in cmdqueue.queue:  # Если есть то второй раз не кладем
        cmdqueue.put(Q_CMD_EXIT)  # Если kill не сработал (для pid=1 не сработает) - шлем сигнал

def cancel_query(reason=''):
    'Cancel query in getbalance_standalone_one_pass by Q_CMD_CANCEL'
    logging.info(f'Press Cancel')
    if Q_CMD_CANCEL not in cmdqueue.queue:  # Если есть то второй раз не кладем
        cmdqueue.put(Q_CMD_CANCEL)
        logging.info(f'Send cancel signal to query')

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
    if not (cmd == 'exit' and force):
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
        if sys.platform != 'win32':
            return
        icon_fn = store.abspath_join('mbplugin', 'plugin', 'httpserver.ico')
        self.image = PIL.Image.open(icon_fn)
        items = []
        for item in tray_menu():
            if item['show']:
                items.append(pystray.MenuItem(item['text'], item['cmd'], default=(len(items) + 1 == int(store.options('tray_default')))))
        self.menu = pystray.Menu(*items)
        host = store.options('host', section='HttpServer')
        port = int(store.options('port', section='HttpServer'))
        self.icon = pystray.Icon('mbplugin', icon=self.image, title=f"Mbplugin {store.version()} ({host}:{port})", menu=self.menu)
        TrayIcon.icon = self.icon
        self.icon.run()

    def stop(self):
        print('STOP')
        if self.icon is not None:
            self.icon.visible = False
            self.icon.stop()


class Scheduler():
    '''Класс для работы с расписанием
    check_only - если не хотим чтобы шедулер стартовал при первом вызове'''
    instance = None
    # Форматы расписаний см https://schedule.readthedocs.io
    # schedule2 = every().day.at("10:30"),megafon
    # строк с заданиями может быть несколько и их можно пихать в ini как
    # scheduler= ... scheduler1=... и т.д как сделано с table_format

    def __init__(self, check_only=False) -> None:
        if Scheduler.instance is None and not check_only:
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
            cmd = cmd.replace('_once', '')
        try:
            if cmd == CMD_CHECK or cmd == CMD_CHECK_SEND:
                getbalance_standalone(**kwargs)
                baltxt = prepare_balance('FULL', params=kwargs.get('params', {}))
                store.feedback.text(baltxt)
                # Шлем по адресатам прописанным в ini
                if TelegramBot.instance is not None and cmd == CMD_CHECK_SEND:
                    TelegramBot.instance.send_balance()
                    TelegramBot.instance.send_subscriptions()
            elif cmd == CMD_GET_ONE:
                get_full_info_one_number(**kwargs)
            elif cmd == CMD_CHECK_NEW_VERSION:
                if TelegramBot.instance is not None:
                    ue = updateengine.UpdaterEngine()
                    if ue.check_update():
                        msg = f'Найдена новая версия\n' + '\n'.join(ue.latest_version_info(short=True))
                        TelegramBot.instance.send_message(msg)
            elif cmd == CMD_PING:
                if TelegramBot.instance is not None:
                    msg = ' '.join(kwargs['filter']).strip()
                    TelegramBot.instance.send_message('ping' if msg == '' else msg)
            else:
                logging.error(f'Scheduler: Unknown command {cmd}: {store.exception_text()}')
            store.feedback.unset()  # После обработки задания отменяем
        except Exception:
            logging.info(f'Scheduler: Error while run job {current_job}: {store.exception_text()}')
        self._job_running = False
        if once:
            return schedule.CancelJob

    def job_is_running(self):
        return Scheduler.instance._job_running

    def run_once(self, cmd, delay: int = 1, feedback_func: typing.Callable = None, kwargs={}) -> bool:
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

    def _validate_sched(self, sched) -> schedule.Job:
        'Проверяет одно расписание на валидность и возвращает в виде job'
        # every(4).day.at("10:30")
        m = re.match(r'^every\((?P<every>\d*)\)(\.to\((?P<to>\d+)\))?\.(?P<interval>\w*)(\.at\("(?P<at>.*)"\))?$', sched.strip())
        try:
            if not m:
                raise
            # every(4).hours,mts,beeline -> {'every': '4', 'interval': 'hours', 'at': None}
            param = m.groupdict()
            param['every'] = int(param['every']) if param['every'].isdigit() else 1
            job = schedule.every(int(param['every']))
            if param['to'] is not None:
                job = job.to(int(param['to']))
            job = getattr(job, param.get('interval', ''))
            if param['at'] is not None:
                job = job.at(param['at'])
            return job
        except Exception:
            logging.error(f'Error parse {sched}')

    def read_from_ini(self) -> typing.List[Job]:
        'Чтение шедулера с диагностикой'
        schedules = store.options('schedule', section='HttpServer', listparam=True, flush=True)
        jobs = []
        for schedule_str in schedules:
            err_msg = []
            job_has_errors = False
            cmd, filter = None, None
            if len(schedule_str.split(',')) < 2:
                err_msg.append(f'Bad schedule "{schedule_str}", cmd not found skipped')
                job_has_errors = True
            if not job_has_errors:
                sched = schedule_str.split(',')[0].strip()
                cmd = schedule_str.split(',')[1].strip().lower()
                filter = [i.strip() for i in schedule_str.split(',')[2:]]
                job_sched = self._validate_sched(sched)
                if job_sched is None:
                    err_msg.append(f'Bad schedule "{schedule_str}", error parse job, skipped')
                    job_has_errors = True
                if cmd not in SCHED_CMDS and cmd.replace('_once', '') not in SCHED_CMDS:
                    err_msg.append(f'Bad cmd {cmd} in schedule "{schedule_str}", skipped')
                    job_has_errors = True
            if job_has_errors:
                job_sched = None
            jobs.append(Job(job_str=schedule_str, job_sched=job_sched, cmd=cmd, filter=filter, err_msg=', '.join(err_msg)))
        return jobs

    def _reload(self):
        'метод который отрабатывает в инстансе в котором работает _forever'
        schedule.clear()
        jobs = self.read_from_ini()
        for job in jobs:
            if job.job_sched is not None:
                job.job_sched.do(self._run, cmd=job.cmd, kwargs={'filter': job.filter})
            else:
                logging.info(job.err_msg)
        logging.info('Schedule was reloaded')
        return 'OK'

    def reload(self):
        'Читает расписание из ini'
        Scheduler.instance._reload()

    def view_html(self) -> typing.Tuple[str, typing.List[str]]:
        'все задания html страницей'
        return 'text/html; charset=cp1251', ['<html><head></head><body><pre>', self.view_txt(), '</pre></body></html>']

    def view_txt(self) -> str:
        'Все задания текстом'
        jobs = self.read_from_ini()
        err_jobs = [f'{job.err_msg}\n{job.job_str}' for job in jobs if job.err_msg != '']
        # TODO !!! нужно сопоставить расписания (то что в jobs[n].job_sched у которого нет repr) и задания schedule.jobs
        res = '\n'.join(err_jobs) + ('\n\n' if err_jobs != [] else '') + '\n'.join(map(repr, schedule.jobs))
        return res + ' '

    def stop(self):
        'Останавливаем шедулер'
        Scheduler.instance._scheduler_running = False


def auth_decorator(errmsg=None, nonauth: typing.Callable = None):
    'Если хотим не залогиненому выдать сообщение об ошибке - указываем его в errmsg, если без авторизации хотим вызвать другой метод - указываем его в nonauth'
    def decorator(func):  # pylint: disable=no-self-argument
        def wrapper(self, message: telebot.types.Message):
            # update.message.chat_id отсутствует у CallbackQueryHandler пробуем через update.effective_chat.id:
            # Т.к. мы приходим сюда из разных handler то message это может быть и Message и CallbackQuery и кто-нибудь еще
            chat_id = message.json.get('chat', {}).get('id')
            if chat_id is None:
                chat_id = message.json.get('message', {}).get('chat', {}).get('id')
            if chat_id in self.auth_id():
                logging.info(f'TG auth:{chat_id} {func.__name__}')
                res = func(self, message)  # pylint: disable=not-callable
                return res
            elif nonauth is not None:
                nonauth(self, message)
            else:
                if errmsg is not None:
                    message.repl(errmsg)
                logging.info(f'TG:{chat_id} unauthorized {func.__name__}')
        return wrapper
    return decorator


class TelegramBot():

    # TODO make singleton class with __new__
    instance = None  # когда создадим класс сюда запишем ссылку на созданный экземпляр

    def __init__(self):
        if 'telebot' not in sys.modules:
            return  # Нет модуля TG - просто выходим
        # TgCommand для команд type(func) != str , для cmd_alias type(func) == str
        self.bot = None
        TgCommand = collections.namedtuple('TgCommand', 'name, description, func')
        commands_list: typing.List[TgCommand] = [
            TgCommand('/help', 'справка', self.get_help),
            TgCommand('/id', 'узнать id профиля', self.get_id),
            TgCommand('/balance', 'текущий баланс', self.get_balancetext),
            TgCommand('/balancefile', 'текущий баланс файлом', self.get_balancefile),
            TgCommand('/receivebalance', 'запросить балансы, аналог команды mbp get-balance (фильтр после пробела)', self.receivebalance),
            TgCommand('/receivebalancefailed', 'запросить балансы номеров с ошибками', self.receivebalance),
            TgCommand('/restart', 'перезапустить сервер', self.restartservice),
            TgCommand('/cancel', 'остановить очередь запросов', self.cancel),
            TgCommand('/getone', 'получить баланс одного номера', self.get_one),
            TgCommand('/checkone', 'запросить баланс одного номера', self.get_one, ),
            TgCommand('/schedule', 'текущие задачи в планировщике', self.get_schedule),
            TgCommand('/schedulereload', 'перезагрузка расписания', self.get_schedule),
            TgCommand('/getlog', 'отобразить лог', self.get_log),
        ]
        self.commands: typing.Dict[str, TgCommand] = {cmd.name: cmd for cmd in commands_list}
        # Читаем алиасы команд
        for line in store.options('cmd_alias', section='Telegram', listparam=True):
            try:
                name, description, func = line.split(':', 3)
                alias = TgCommand(re.sub('^//', '/', f'/{name.strip()}'), description, re.sub('^//', '/', f'/{func.strip()}'))
                self.commands[alias.name] = alias
            except Exception:
                logging.warning(f'Wrong tg alias {line}')
        self.start_bot()
        self.add_bot_menu()

    def start_bot(self):
        'Запускаем бота'
        api_token = store.options('api_token', section='Telegram').strip()
        request_kwargs = {}
        tg_proxy = store.options('tg_proxy', section='Telegram').strip()
        if tg_proxy.lower() == 'auto':
            telebot.apihelper.proxy = urllib.request.getproxies().get('https', None)
        elif tg_proxy != '' and tg_proxy.lower() != 'auto':
            telebot.apihelper.proxy = tg_proxy
            # ??? Надо или не надо ?
            # request_kwargs['urllib3_proxy_kwargs'] = {'assert_hostname': 'False', 'cert_reqs': 'CERT_NONE'}
        if api_token != '' and str(store.options('start_tgbot', section='Telegram')) == '1' and 'telebot' in sys.modules:
            try:
                logging.info(f'Module telegram starting for id={self.auth_id()}')
                self.bot = telebot.TeleBot(api_token)
                logging.info(f'{self.bot}')
                for cmd in self.commands.values():
                    if type(cmd.func) != str:  # только команды
                        # В handler надо класть без слэша '/help' -> 'help' поэтому [1:]
                        self.bot.register_message_handler(cmd.func, commands=[cmd.name[1:]])
                self.bot.register_callback_query_handler(self.button, func=lambda call: True)
                self.bot.register_message_handler(self.handle_catch_all, func=lambda message: True)
                # self.bot.infinity_polling()  # Start the Bot
                threading.Thread(target=self.bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
                logging.info('Telegram bot started')
                TelegramBot.instance = self  # Запустили бота - прописываем инстанс singleton
                if str(store.options('send_empty', section='Telegram')) == '1':
                    self.send_message(text='Hey there!', disable_notification=True)
            except Exception:
                exception_text = f'Ошибка запуска telegram bot {store.exception_text()}'
                logging.error(exception_text)
        elif 'telebot' not in sys.modules:
            logging.info('Module telegram not found')
        elif api_token == '':
            logging.info('Telegram api_token not found')
        elif str(store.options('start_tgbot', section='Telegram')) != '1':
            logging.info('Telegram bot start is disabled in mbplugin.ini (start_tgbot=0)')

    def add_bot_menu(self):
        'создает персональное меню бота [/] для всех id из auth_id из пунктов перечисленных в command_menu_list'
        if self.bot is None:
            return
        command_menu_list = store.options('command_menu_list', section='Telegram').strip().split(',')
        command_menu_list = [re.sub('^//', '/', f'/{i.strip()}') for i in command_menu_list]
        for aid in self.auth_id():
            # Перебираем команды из списка command_menu_list и те которые есть в command_menu_list вставляем в меню [/]
            cmds = [self.commands[c1] for c1 in command_menu_list if c1 in self.commands]
            self.bot.set_my_commands(
                [telebot.types.BotCommand(cmd.name, cmd.description) for cmd in cmds],
                scope=telebot.types.BotCommandScopeChat(aid))

    def auth_id(self) -> typing.List[int]:
        'return auth id from ini'
        auth_id_str = store.options('auth_id', section='Telegram').strip()
        if not re.match(r'(\d+,?)', auth_id_str):
            logging.error(f'incorrect auth_id in ini: {auth_id_str}')
            return []
        return map(int, auth_id_str.split(','))

    def get_id(self, message: telebot.types.Message):
        """Echo chat id."""
        logging.info(f'TG:{message.chat.id} /id')
        self.put_text(message, message.chat.id)

    def put_text(self, message: telebot.types.Message, text: str, msg_type=None, parse_mode='HTML') -> typing.Optional[telebot.types.Message]:
        '''Вызываем функцию для размещения текста'''
        try:
            if msg_type is None:
                return self.bot.send_message(message.chat.id, text, parse_mode=parse_mode)
            elif msg_type == 'reply_to':
                return self.bot.reply_to(message, text=text, parse_mode=parse_mode)
            elif msg_type == 'edit_message_text':
                return self.bot.edit_message_text(chat_id=message.chat.id, text=text, message_id=message.message_id)
        except Exception:
            try:
                return self.bot.send_message(message.chat.id, text, parse_mode=None)
            except Exception:
                exception_text = store.exception_text()
                if 'Message is not modified' not in exception_text:
                    logging.info(f'Unsuccess tg send:{text} {exception_text}')
                return None

    def edit_text(self, message: telebot.types.Message, text: str, parse_mode='HTML') -> typing.Optional[telebot.types.Message]:
        '''put_text(... msg_type='edit_message_text' ...)'''
        return self.put_text(message, text, msg_type='edit_message_text', parse_mode=parse_mode)

    def reply_text(self, message: telebot.types.Message, text: str, parse_mode='HTML') -> typing.Optional[telebot.types.Message]:
        '''put_text(... msg_type='reply_to' ...)'''
        return self.put_text(message, text, msg_type='reply_to', parse_mode=parse_mode)

    def handle_catch_all(self, message: telebot.types.Message):
        '''catch-all handler - отрабатываем алиасы и логируем все остальное что не попало в фильтры,
        аутентификацию можно не отрабатывать - она отработает когда пойдем в вызванную по алиасу команду'''
        # message or message.message  пока не пойму зачем так было сделано, оставил в таком виде
        effective_message: telebot.types.Message = message.json.get('message', message)
        if effective_message is not None:
            acmd = '/' + telebot.util.extract_command(effective_message.text)
            aargs = telebot.util.extract_arguments(effective_message.text).split()
            if acmd in self.commands and type(self.commands[acmd].func) == str:
                logging.info(f'TG catch alias:{effective_message.chat.id} {effective_message.text}')
                alias = self.commands[acmd]
                # реальный text который уйдет в команду, реальная команда и реальные аргументы
                real_text = ' '.join([alias.func] + aargs)
                rcmd = '/' + telebot.util.extract_command(real_text)
                if rcmd not in self.commands:
                    logging.info(f'TG for alias {acmd} not found command {alias.func}')
                    return
                logging.info(f'TG run for alias {effective_message.text} command {real_text}')
                cmd = self.commands[rcmd]
                effective_message.text = real_text
                cmd.func(message)
                return
            logging.info(f'TG catch-all:{effective_message.chat.id} {effective_message.text}')

    @auth_decorator(errmsg='/help\n/id')
    def get_help(self, message: telebot.types.Message):
        """Send help. only auth user"""
        help_text = [f'{cmd.name} - {cmd.description}' for cmd in self.commands.values()]
        args = telebot.util.extract_arguments(message.text)
        if args != '':
            help_text.insert(0, repr(args))
        self.put_text(message, '\n'.join(help_text).strip())

    @auth_decorator()
    def get_balancetext(self, message: telebot.types.Message):
        """Send balance only auth user."""
        baltxt = prepare_balance('FULL', params={'include': ','.join(telebot.util.extract_arguments(message.text).split())})
        self.put_text(message, baltxt)

    @auth_decorator()
    def get_balancefile(self, message: telebot.types.Message):
        """Send balance html file only auth user."""
        _, res = getreport()
        self.bot.send_document(chat_id=message.chat.id, visible_file_name='balance.htm', document=io.BytesIO('\n'.join(res).strip().encode('cp1251')))

    @auth_decorator()
    def restartservice(self, message: telebot.types.Message):
        """Hard reset service"""
        self.put_text(message, 'Service will be restarted')
        restart_program(reason=f'TG:{message.chat.id} {message.text}')

    @auth_decorator()
    def cancel(self, message: telebot.types.Message):
        """Send cancel signal to receive balance query"""
        self.put_text(message, 'Query will be canceled')
        cancel_query(reason=f'TG:{message.chat.id} {message.text}')

    @auth_decorator()
    def receivebalance(self, message: telebot.types.Message):
        """ Запросить балансы по всем номерам, only auth user.
        /receivebalance
        /receivebalancefailed
        """
        def feedback_func(txt):
            self.put_text(message, txt, msg_type='edit_message_text')
        args = telebot.util.extract_arguments(message.text).split()
        filtertext = '' if len(args) == 0 else f", with filter by {' '.join(args)}"
        self.put_text(message, f'Request all number{filtertext}. Wait...', msg_type='reply_to')
        # Если запросили плохие - то просто запрашиваем плохие
        # Если запросили все - запрашиваем все, потом два раза только плохие
        only_failed = (message.text == "/receivebalancefailed")
        params = {'include': None if args == [] else ','.join(args)}
        Scheduler().run_once(cmd=CMD_CHECK, feedback_func=feedback_func, kwargs={'filter': args, 'params': params, 'only_failed': only_failed})

    @auth_decorator()
    def get_schedule(self, message: telebot.types.Message):
        """Show schedule only auth user.
        /schedule
        /schedulereload
        """
        if message.text == "/schedulereload":
            Scheduler().reload()
        text = Scheduler().view_txt()
        self.put_text(message, text if text.strip() != '' else 'Empty')

    @auth_decorator()
    def get_one(self, src):
        """Receive one balance with inline keyboard/args, only auth user.
        /checkone - получаем баланс
        /getone - показываем"""
        # Заданы аргументы? Тогда спросим по ним.
        if not hasattr(src, 'data'):  # это запрос ?
            query: telebot.types.CallbackQuery = None
            message: telebot.types.Message = src
        else:
            query:telebot.types.CallbackQuery = src
            message: telebot.types.Message = query.message
        if query is None:  # это запрос ?
            args = telebot.util.extract_arguments(message.text).lower()
            if args != '':  # запрос с аргументами ? например /getone p_test3
                cmd = telebot.util.extract_command(message.text)
                filtered = [v for k, v in store.ini('phones.ini').phones().items() if v['number'].lower() == args or v['alias'].lower() == args]
                message1 = self.put_text(message, f'You have chosen {args}')
                if len(filtered) > 0:
                    val = filtered[0]
                    callback_data = f"{cmd}_{val['Region']}_{val['Number']}"
                    cmd, keypair = callback_data.split('_', 1)  # До _ команда, далее Region_Number
                else:
                    self.put_text(message1, f'Not found {args}', msg_type='edit_message_text')  # type: ignore
                    return
                feedback_func = lambda txt: self.put_text(message1, txt, msg_type='edit_message_text')  # type: ignore
                Scheduler().run_once(cmd=CMD_GET_ONE, feedback_func=feedback_func, kwargs={'keypair': keypair, 'check': cmd == 'checkone'})
                return
            #query = None  # ???? update.callback_query
            # Запрос без аргументов - создаем клавиатуру
            phones = store.ini('phones.ini').phones()
            keyboard: typing.List = []
            cmd = telebot.util.extract_command(message.text)  # checkone или getone
            for val in list(phones.values()) + [{'Alias': 'Cancel', 'Region': 'Cancel', 'Number': 'Cancel'}]:
                # ключом для calback у нас команда_Region_Number
                btn = InlineKeyboardButton(val['Alias'], callback_data=f"{cmd}_{val['Region']}_{val['Number']}")
                if len(keyboard) == 0 or len(keyboard[-1]) == 3:
                    keyboard.append([btn])
                else:
                    keyboard[-1].append(btn)
            reply_markup = InlineKeyboardMarkup(keyboard)
            self.bot.reply_to(message, 'Please choose:', reply_markup=reply_markup)
            return 
        else:  # реагируем на клавиатуру
            cmd, keypair = query.data.split('_', 1)  # До _ команда, далее Region_Number
            feedback_func = lambda txt: self.put_text(message, txt, msg_type='edit_message_text')  # type: ignore
            Scheduler().run_once(cmd=CMD_GET_ONE, feedback_func=feedback_func, kwargs={'keypair': keypair, 'check': cmd == 'checkone'})

    @auth_decorator()
    def get_log(self, src):
        """Receive one log with inline keyboard/param, only auth user.
        /getlog - лог по последнему запросу
        сюда приходим ДВА раза сначала чтобы создать клавиатуру(query=None),
        а потом чтобы отреагировать на нее
        """
        # reply(query.edit_message_text, query.message.reply_document, query.data)
        def reply(message, keypair):
            self.put_text(message, 'This is log', msg_type='edit_message_text')
            res = prepare_log_personal(keypair)
            self.bot.send_document(chat_id=message.chat.id, visible_file_name=f'{keypair}_log.htm', document=io.BytesIO(res.strip().encode('cp1251')))

        if not hasattr(src, 'data'):  # это запрос ?
            query: telebot.types.CallbackQuery = None
            message: telebot.types.Message = src
        else:
            query:telebot.types.CallbackQuery = src
            message: telebot.types.Message = query.message
        if query is None:  # это запрос ?            
            args = telebot.util.extract_arguments(message.text).lower()
            # Заданы аргументы? Тогда спросим по ним.
            # запрашиваем по заданному аргументу
            if args != '':
                logs = prepare_loglist_personal()
                filtered = [i for i in logs if args.lower() in i.lower()]
                new_msg = self.put_text(message, f'Info for {args}')
                if len(filtered) > 0 and new_msg is not None:
                    val = filtered[0]
                    reply(new_msg, val)
                else:
                    self.put_text(new_msg, f'Not found {args}')
                return
            keyboard: typing.List = []
            logs = prepare_loglist_personal()
            for val in logs + ['Cancel']:
                # ключом для calback у нас команда_Region_Number
                btn = InlineKeyboardButton(val, callback_data=f"getlog_{val}")
                if len(keyboard) == 0 or len(keyboard[-1]) == 3:
                    keyboard.append([btn])
                else:
                    keyboard[-1].append(btn)
            reply_markup = InlineKeyboardMarkup(keyboard)
            self.bot.reply_to(message, 'Please choose:', reply_markup=reply_markup)
        else:  # реагируем на клавиатуру
            reply(message, query.data.split('_', 1)[1])

    @auth_decorator()
    def button(self, query: telebot.types.CallbackQuery) -> None:
        '''Клавиатура, здесь реакция на нажатие
        Определяем откуда пришли и бросаем обратно'''
        if query is None or query.data is None:
            return
        logging.info(f'TG:reply keyboard to {query.message.chat.id} CHOICE:{query.data}')
        cmd, val = query.data.split('_', 1)  # До _ команда, далее кнопка, например Region_Number
        if val.startswith('Cancel'):
            self.put_text(query.message, 'Canceled', msg_type = 'edit_message_text')  # close keyboard
            return
        self.put_text(query.message, 'Request received. Wait...', msg_type = 'edit_message_text')
        # ключом для calback у нас 6 букв
        if cmd == 'getlog':  # /getlog - генерим лог и выходим
            self.get_log(query)
        if cmd in ['checkone', 'getone']:
            self.get_one(query)

    def send_message(self, text: str, parse_mode='HTML', ids=None, **kwargs):
        'Отправляем сообщение по списку ids, либо по списку auth_id из mbplugin.ini'
        if self.bot is None or text == '':
            return
        lst = self.auth_id() if ids is None else ids
        text = text if type(text) == str else str(text)
        for aid in lst:
            try:
                self.bot.send_message(chat_id=aid, text=text, parse_mode=parse_mode, **kwargs)
            except Exception:
                try:
                    self.bot.send_message(chat_id=aid, text=text[:4000], parse_mode=None, **kwargs)
                except Exception:
                    exception_text = f'Ошибка отправки сообщения {text} для {aid} telegram bot {store.exception_text()}'
                    logging.error(exception_text)

    def send_balance(self):
        'Отправляем баланс'
        if self.bot is None or str(store.options('send_balance_changes', section='Telegram')) == '0':
            return
        baltxt = prepare_balance('LASTCHANGE')
        self.send_message(text=baltxt, parse_mode='HTML')

    def send_subscriptions(self):
        'Отправляем подписки - это строки из ini вида:'
        'subscriptionXXX = id:123456 include:1111,2222 exclude:6666'
        if self.bot is None:
            return
        subscriptions = store.options('subscription', section='Telegram', listparam=True)
        for subscr in subscriptions:
            # id:123456 include:1111,2222 -> {'id':'123456', 'include':'1111,2222'}
            params = {k: v.strip() for k, v in [i.split(':', 1) for i in subscr.split(' ')]}
            baltxt = prepare_balance('LASTCHANGE', params)
            ids = [int(i) for i in params.get('id', '').split(',') if i.isdigit()]
            self.send_message(text=baltxt, parse_mode='HTML', ids=ids)

    def stop(self):
        '''Stop bot'''
        if self.bot is not None:
            self.bot.stop_bot()


class Handler(wsgiref.simple_server.WSGIRequestHandler):
    # Disable logging DNS lookups
    def address_string(self):
        return str(self.client_address[0])

    def log_message(self, format, *args):
        # убираем пароль из лога
        args = re.sub('(/.*?/.*?/.*?/)(.*?)(/.*)', r'\1xxxxxxx\3', args[0]), *args[1:]
        args = re.sub('(&password=)(.*?)(&)', r'\1xxxxxxx\3', args[0]), *args[1:]
        # а если это показ лога вообще в лог не пишем, а то фигня получается
        if 'GET /log' not in args[0] and 'GET /favicon.ico' and 'GET /favicon.png' not in args[0]:
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
            logging.info(f'Starting web server {store.version()} from {os.path.abspath(__file__)}')
            logging.info(f'Listening pid={os.getpid()} {self.host}:{self.port}....')
            threading.Thread(target=self.httpd.serve_forever, name='httpd', daemon=True).start()
            if 'pystray' in sys.modules:  # Иконка в трее
                self.tray_icon = TrayIcon()  # tray icon (он сам все запустит в threading)
            if 'telebot' in sys.modules:  # telegram bot (он сам все запустит в threading)
                self.telegram_bot = TelegramBot()
            if 'schedule' in sys.modules:  # Scheduler (он сам все запустит в threading)
                self.scheduler = Scheduler()
            # Запустили все остальное демонами и ждем, когда они пришлют сигнал exit
            while True:
                cmd = cmdqueue.get()
                if cmd != Q_CMD_EXIT:  # если это не наша команда - кладем обратно.
                    cmdqueue.put(cmd)
                else:
                    return
                time.sleep(1)

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
        authorized = False  # Изначально считаем что пользователь не авторизован
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
        authorized = cookies.get('auth', 'None') in authcookies
        # Если пришли с localhost и разрешено localhost без авторизации
        local_authorized = environ.get('REMOTE_ADDR', 'None') == '127.0.0.1' and str(store.options('httpconfigeditnolocalauth')) == '1'
        if local_authorized:
            authorized = True
        # если еще не открывали редактируемый ini открываем
        if not hasattr(self, 'editini'):
            self.editini = store.ini()
        # print(cookies, f"auth in authcookies={cookies.get('auth', 'None') in authcookies}", f'authorized={authorized}')
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
            # print(f'request={request}')
            if authorized and request['cmd'] == 'update':
                params = settings.ini[request['sec']].get(request['id'] + '_', {})
                # Если для параметра указана функция валидации - вызываем ее
                if not params.get('validate', lambda i: True)(request['value']):
                    return 'text/plain', 'ERROR', status, add_headers
                logging.info(f"ini change key [{request['sec']}] {request['id']} {self.editini.ini[request['sec']].get(request['id'], 'default')}->{request['value']}")
                self.editini.ini[request['sec']][request['id']] = request['value']
                self.editini.write()
                # print('\n'.join([f'{k}={v}' for k, v in self.editini.ini[request['sec']].items()]))
            elif authorized and request['cmd'] == 'delete':
                logging.info(f"ini delete key [{request['sec']}] {request['id']} {self.editini.ini[request['sec']].get(request['id'], 'default')}")
                self.editini.ini[request['sec']].pop(request['id'], None)
                self.editini.write()
            elif request['cmd'] == 'logon':
                status = '303 See Other'
                # Пароль совпал (и не пустой !!!) - выдаем токен
                passwd_from_ini = store.options('httpconfigeditpassword').strip()
                passwd_from_user = request.get('password', 'None').strip()
                if passwd_from_user == passwd_from_ini and passwd_from_ini != '':
                    logging.info('Authorized')
                    auth_token = uuid.uuid4().hex  # auth cookie
                    authcookies.append(auth_token)
                    with open(cookie_store_name, 'w') as f:
                        f.write('\n'.join(authcookies))
                    add_headers = [
                        ('Location', '/editcfg'),
                        ('Set-Cookie', f'auth={auth_token}'),
                        ('Set-Cookie', 'wrongpassword=deleted; expires=Thu, 01 Jan 1970 00:00:00 GMT')]
                else:
                    logging.info('Wrong password')
                    add_headers = [('Location', '/editcfg'), ('Set-Cookie', 'wrongpassword=true')]
                return 'text/html', 'redirect', status, add_headers
            elif request['cmd'] == 'logout':
                # выкидываем куку
                with open(cookie_store_name, 'w') as f:
                    f.write('\n'.join([i for i in authcookies if i != cookies.get('auth', 'None')]))
                status = '303 See Other'
                add_headers = [('Location', '/main'), ('Set-Cookie', 'auth=deleted; expires=Thu, 01 Jan 1970 00:00:00 GMT')]
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
            if authorized:
                inidata = self.editini.ini_to_json().replace('\\', '\\\\')
            editor_html = editor_html.replace("inifile = JSON.parse('')", f"inifile = JSON.parse('{inidata}')")
            if local_authorized:
                editor_html = editor_html.replace('localAuthorized = false // init', f'localAuthorized = true // init')
            return 'text/html', editor_html, status, add_headers

    def web_app(self, environ, start_response):
        try:
            logging.debug('web_app start')
            store.options('logginglevel', flush=True)  # Запускаем, чтобы сбросить кэш и перечитать ini
            status = '200 OK'
            add_headers = []
            ct, text = 'text/html', []
            fn = environ.get('PATH_INFO', None)
            _, cmd, *param = fn.split('/')
            print(f'{cmd}, {param}')
            if environ.get('PATH_INFO', None) == '/favicon.ico':
                start_response('200 OK', [('Content-type', 'image/x-icon')])
                return [open(store.abspath_join('mbplugin', 'plugin', 'httpserver.ico'), 'rb').read()]
            if environ.get('PATH_INFO', None) == '/favicon.png':
                start_response('200 OK', [('Content-type', 'image/png')])
                return [open(store.abspath_join('mbplugin', 'plugin', 'httpserver.png'), 'rb').read()]
            elif cmd.lower() == 'getbalance':  # старый вариант оставлен пока для совместимости
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
                    text = [settings.header_html] + [f'<a href=/log/{g}>{g}<a/><br>' for g in allgroups]
                elif len(param) > 0 and re.match(r'^\w*$', param[0]):  # /log/p_plugin_number
                    # text = [f'<img src=/screenshot/{os.path.split(fn)[-1]}/><br>' for fn in ss]
                    text = [settings.header_html] + [prepare_log_personal(param[0])]
                else:  # /log
                    qs = urllib.parse.parse_qs(environ['QUERY_STRING'])
                    ct, text = view_log(qs)
                    text = [settings.header_html] + text
            elif cmd.lower() == 'screenshot':  # скриншоты
                if len(param) == 0 or not re.match(r'^\w*\.png$', param[0]):
                    return
                with open(store.abspath_join(store.options('loggingfolder'), param[0]), 'rb') as f:
                    text = f.read()
                ct = 'image/png'
            elif cmd.lower() == 'schedule':  # просмотр расписания
                ct, text = Scheduler().view_html()
                text = [settings.header_html] + text
            elif cmd.lower() == 'reload_schedule':  # обновление расписания
                Scheduler().reload()
                ct, text = Scheduler().view_html()
                text = [settings.header_html] + text
            elif cmd.lower() == 'version_update':  # обновление версии
                res = run_update()
                ct, text = 'text/html', settings.header_html + f'\n<pre>\n{res}\n</pre>\n'
                if 'Update:' in text and 'No new version found' not in text:
                    logging.info('Schedule restart web service')
                    threading.Thread(target=lambda: restart_program(reason=f'WEB: /restart', delay=5), name='Restart', daemon=True).start()
                else:
                    logging.info('No new version, no restart')
            elif cmd == 'logging_restart':  # logging_restart
                store.logging_restart()
                ct, text = 'text/html', 'OK'
            elif cmd == '' or cmd == 'report':  # report
                if str(store.options('sqlitestore')) == '1':
                    ct, text = getreport(param)
                else:
                    ct, text = 'text/html', HTML_NO_REPORT
            elif cmd == 'fastreport':  # report from balance.html
                if str(store.options('sqlitestore')) == '1' and os.path.exists(store.options('balance_html')):
                    ct, text = 'text/html', open(store.options('balance_html')).read()
                else:
                    ct, text = 'text/html', HTML_NO_REPORT
            elif cmd.lower() == 'main':  # главная страница
                port = store.options('port', section='HttpServer')
                info = f'Mbplugin {store.version()} run on {socket.gethostname()}:{port} from {os.path.abspath(os.path.dirname(__file__))}<br>'
                phones = store.ini('phones.ini').phones()
                groups = sorted(set([p['indication'] for p in phones.values() if 'indication' in p]))
                group_urls = '<br>'.join([f'<a href=/report/group_{g}>Group_{g}</a> ' for g in groups])
                script = ''
                if str(store.options('HttpConfigEdit')) == '0':
                    script = 'document.getElementById("call_editor").style="display:none"'
                ct, text = 'text/html; charset=cp1251', [settings.main_html % {'group_urls': group_urls, 'info': info, 'script': script}]
            elif cmd.lower() == 'editcfg':  # вариант через get запрос
                if str(store.options('HttpConfigEdit')) == '1':
                    ct, text, status, add_headers = self.editor(environ)
            elif cmd == 'getbalance_standalone':  # start balance request
                # TODO подумать над передачей параметров в fetch - filter=filter,only_failed=only_failed
                Scheduler().run_once(cmd=CMD_CHECK)
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
            elif cmd == 'cancel':  # cancel query
                ct, text = 'text/html; charset=cp1251', ['OK']
                cancel_query(reason=f'WEB: /cancel')
            elif cmd == 'exit':  # exit cmd
                ct, text = 'text/html; charset=cp1251', ['OK']
                threading.Thread(target=lambda: restart_program(reason=f'WEB: /exit', exit_only=True, delay=0.1), name='Exit', daemon=True).start()
            if status.startswith('200'):
                headers = [('Content-type', ct)]
            if status.startswith('303'):
                headers = add_headers
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


def run_update():
    if sys.platform == 'win32':
        mbp_path = os.path.join(store.settings.mbplugin_root_path, 'mbp.bat')
        return os.popen(f'"{mbp_path}" version-update').read()
    else:
        mbp_path = os.path.join(store.settings.mbplugin_root_path, 'mbp')
        return os.popen(f'"{mbp_path}" version-update').read()


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
        if 'UnicodeDecodeError:' in exception_text:
            exception_text += f'\nWebServer не запустится если имя компьютера содержит русские буквы,\nв настоящий момент имя компьютера "{socket.gethostname()}"'
        logging.error(exception_text)


if __name__ == '__main__':
    store.switch_to_mb_mode()
    main()
