# -*- coding: utf8 -*-
'Модуль для хранения сессий и настроек а также чтения настроек из ini от MobileBalance'
import os, sys, re, json, pickle, requests, configparser
import settings


def save_session(storename, session):
    'Сохраняем сессию в файл'
    options = read_ini()['Options']
    storefolder = options.get('storefolder', settings.storefolder)    
    with open(os.path.join(storefolder, storename), 'wb') as f:
        pickle.dump(session, f)


def load_or_create_session(storename, headers=None):
    'Загружаем сессию из файла или создаем новую'
    options = read_ini()['Options']
    storefolder = options.get('storefolder', settings.storefolder)     
    try:
        with open(os.path.join(storefolder, storename), 'rb') as f:
            return pickle.load(f)
    except Exception:
        session = requests.Session()
        if headers:
            session.headers.update(headers)
        return session  # return new session


def drop_and_create_session(storename, headers=None):
    'удаляем сессию и создаем новую'
    options = read_ini()['Options']
    storefolder = options.get('storefolder', settings.storefolder)    
    try:
        os.remove(os.path.join(storefolder, storename))
    except Exception:
        pass
    session = requests.Session()
    if headers:
        session.headers.update(headers)
    return session  # return new session

def find_files_up(fn):
    'Ищем файл вверх по дереву путей'
    allroot = [os.getcwd().rsplit('\\', i)[0]
               for i in range(len(os.getcwd().split('\\')))]
    all_ini = [i for i in allroot if os.path.exists(os.path.join(i, fn))]
    if all_ini != []:
        return os.path.join(all_ini[0], fn)
    else:
        return os.path.join('..', fn)


def read_ini(fn=settings.mbplugin_ini):
    'Ищем и открываем ini, если не указали имя то смотрим mbplugin.ini'
    ini = configparser.ConfigParser()
    if fn.lower() == settings.mbplugin_ini:
        inipath = find_files_up(fn)
    else:
        path = read_ini(settings.mbplugin_ini)['MobileBalance']['path']
        inipath = os.path.join(path, fn)
    if os.path.exists(inipath):
        if fn.lower() == 'phones.ini':
            # phones.ini - нечестный ini читать приходится с извратами
            # replace [Phone] #123 -> [Phone #123]
            prep1 = re.sub(r'(?usi)\[Phone\] #(\d+)', r'[\1]', open(inipath).read())
            # TODO костыль, мы подменяем p_pluginLH на p_plugin чтобы при переключении плагина не разъезжались данные
            prep2 = re.sub(r'(?usi)(Region\s*=\s*p_\S+)LH', r'\1', prep1)
            ini.read_string(prep2)
        else:
            ini.read(inipath)
    elif not os.path.exists(inipath) and fn.lower() == settings.mbplugin_ini:
        # Создаем mbplugin.ini - он нам нужен для настроек и чтобы знать где ini-шники от mobilebalance
        mbpath = find_files_up('phones.ini')
        if os.path.exists(mbpath):
            # Если нашли mobilebalance - cоздадим mbplugin.ini и sqlite базу там же где и ini-шники mobilebalance
            inipath = os.path.join(os.path.split(mbpath)[0], fn)
            dbpath = os.path.join(os.path.split(
                mbpath)[0], os.path.split(settings.dbfilename)[1])
        else:
            # иначе создадим mbplugin.ini и базу в корне папки mbplugin
            ini['MobileBalance'] = {'path': ''}
            dbpath = settings.dbfilename
        ini['MobileBalance'] = {'path': os.path.split(mbpath)[0]}
        ini['Options'] = {'logginglevel': settings.logginglevel,
                          'sqlitestore': settings.sqlitestore,
                          'dbfilename': dbpath,
                          'createhtmlreport': settings.createhtmlreport,
                          'balance_html': settings.balance_html,
                          'updatefrommdb': settings.updatefrommdb,
                          'updatefrommdbdeep': settings.updatefrommdbdeep,
                          }
        ini['HttpServer'] = {'port': settings.port,
                             'host': settings.host,
                             'table_format': settings.table_format}

        ini.write(open(inipath, 'w'))
    else:
        raise RuntimeError(f'Not found {fn}')
    return ini


def read_stocks(stocks_name):
    'Читаем список стоков для плагина stock.py из mbplugin.ini'
    ini = read_ini()
    stocks = {'stocks': [], 'remain': {}, 'currenc': ''}
    items = ini['stocks_'+stocks_name].items()
    stocks_str = [list(map(str.strip, v.split(','))) for k, v in items if k.startswith('stock')]
    remain_str = [list(map(str.strip, v.split(','))) for k, v in items if k.startswith('remain')]
    stocks['currenc'] = ini['stocks_'+stocks_name]['currenc'].strip()
    stocks['stocks'] = [(i[0].upper(), int(i[1]), i[2].upper()) for i in stocks_str if len(i) == 3 and i[1].isnumeric()]
    stocks['remain'] = {i[0].upper(): int(i[1]) for i in remain_str if len(i) == 2 and i[1].isnumeric()}
    return stocks


def result_to_xml(result):
    'Конвертирует словарь результатов в готовый к отдаче вид '
    # Коррекция SMS и Min (должны быть integer)
    if 'SMS' in result:
        result['SMS'] = int(result['SMS'])
    if 'Min' in result:
        result['Min'] = int(result['Min'])
    for k, v in result.items():
        if type(v) == float:
            result[k] = round(v, 2)  # Чтобы не было паразитных микрокопеек
    body = ''.join([f'<{k}>{v}</{k}>' for k, v in result.items()])
    return f'<Response>{body}</Response>'


def result_to_html(result):
    'Конвертирует словарь результатов в готовый к отдаче вид '
    # Коррекция SMS и Min (должны быть integer)
    if 'SMS' in result:
        result['SMS'] = int(result['SMS'])
    if 'Min' in result:
        result['Min'] = int(result['Min'])
    body = json.dumps(result, ensure_ascii=False)
    return f'<html><meta charset="windows-1251"><p id=response>{body}</p></html>'    


if __name__ == '__main__':
    print('Module store')
    # print(list(read_ini('phones.ini').keys()))
    # print(list(read_ini('options.ini').keys()))
    # print(list(read_ini('mbplugin.ini').keys()))

    #ini = read_ini()
    #if ini['MobileBalance']['path'] == '':
    #    print('MobileBalance folder unknown')
    #print(list(read_ini('phones.ini').keys()))

    #stocks_name = 'broker_ru'
    #print(read_stocks(stocks_name))

    # import io;f = io.StringIO();ini.write(f);print(f.getvalue())
    #{'STOCKS':(('AAPL',1,'Y'),('TATNP',16,'M'),('FXIT',1,'M')), 'REMAIN': {'USD':5, 'RUB':536}, 'CURRENC': 'USD'}
    #p=read_ini('phones.ini')
