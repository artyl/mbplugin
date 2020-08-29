# -*- coding: utf8 -*-
'Модуль для хранения сессий и настроек а также чтения настроек из ini от MobileBalance'
import os, sys, re, json, pickle, requests, configparser
import settings


def session_folder(storename):
    storefolder = options('storefolder')     
    os.path.join(storefolder, storename)

class Session():
    'Класс для сессии с дополнительными фишками для сохранения и проверки'
    def __init__(self, storename, headers=None):
        self.storename = storename
        self.storefolder = options('storefolder')
        self.pagecounter = 1  # Счетчик страниц для сохранения
        self.headers = headers
        try:
            with open(os.path.join(self.storefolder, self.storename), 'rb') as f:
                self.session = pickle.load(f)
                self.headers = self.session.headers
        except Exception:
            self.session = requests.Session()
            if self.headers:
                self.session.headers.update(self.headers)

    def update_headers(self, headers):
        self.headers.update(headers)
        self.session.headers.update(self.headers)

    def drop_and_create(self, headers=None):
        'удаляем сессию и создаем новую'
        try:
            os.remove(os.path.join(self.storefolder, self.storename))
        except Exception:
            pass
        self.session = requests.Session()
        if headers:
            self.headers = headers
        if self.headers:
            self.session.headers.update(self.headers)

    def save_session(self):
        'Сохраняем сессию в файл'
        with open(os.path.join(self.storefolder, self.storename), 'wb') as f:
            pickle.dump(self.session, f)

    def save_response(self, response):
        'debug save response'
        if options('logginglevel') == 'DEBUG' and hasattr(response, 'content'):
            fld = options('loggingfolder')
            fn = os.path.join(fld, f'{self.storename}_{self.pagecounter}.html')
            open(fn, mode='wb').write(response.content)
            self.pagecounter += 1        

    def get(self, *args, **kwargs):
        response = self.session.get(*args, **kwargs)
        self.save_response(response)
        return response
        
    def post(self, *args, **kwargs):
        response = self.session.post(*args, **kwargs)
        self.save_response(response)
        return response

    def put(self, *args, **kwargs):
        response = self.session.put(*args, **kwargs)
        self.save_response(response)
        return response


def find_files_up(fn):
    'Ищем файл вверх по дереву путей'
    allroot = [os.getcwd().rsplit('\\', i)[0]
               for i in range(len(os.getcwd().split('\\')))]
    all_ini = [i for i in allroot if os.path.exists(os.path.join(i, fn))]
    if all_ini != []:
        return os.path.join(all_ini[0], fn)
    else:
        return os.path.join('..', fn)


def options(param, default=None, section='Options', listparam=False):
    'Читаем параметр из mbplugin.ini либо дефолт из settings'
    'Если listparam=True, то читаем список из всех, что начинается на param'
    if default is None:
        default = settings.ini[section].get(param, None)
    options_all_sec = ini().read()
    if section in options_all_sec:
        options_sec = options_all_sec[section]
    else:
        options_sec = {}
    if listparam:
        return [v for k,v in options_sec.items() if k.startswith(param)]
    else:
        return options_sec.get(param, default)
    
class ini():
    def __init__(self, fn=settings.mbplugin_ini):
        self.ini = configparser.ConfigParser()
        self.fn = fn
        if self.fn.lower() == settings.mbplugin_ini:
            self.inipath = self.find_files_up(self.fn)        
        else:
            path = ini(settings.mbplugin_ini).read()['MobileBalance']['path']
            self.inipath = os.path.join(path, fn)
            
    def find_files_up(self, fn):
        'Ищем файл вверх по дереву путей'
        allroot = [os.getcwd().rsplit('\\', i)[0] for i in range(len(os.getcwd().split('\\')))]
        all_ini = [i for i in allroot if os.path.exists(os.path.join(i, fn))]
        if all_ini != []:
            return os.path.join(all_ini[0], fn)
        else:
            return os.path.join('..', fn)        
        
    def read(self):
        if os.path.exists(self.inipath):
            if self.fn.lower() == 'phones.ini':
                # phones.ini - нечестный ini читать приходится с извратами
                # replace [Phone] #123 -> [Phone #123]
                prep1 = re.sub(r'(?usi)\[Phone\] #(\d+)', r'[\1]', open(self.inipath).read())
                # TODO костыль, мы подменяем p_pluginLH на p_plugin чтобы при переключении плагина не разъезжались данные
                prep2 = re.sub(r'(?usi)(Region\s*=\s*p_\S+)LH', r'\1', prep1)
                self.ini.read_string(prep2)
            else:
                self.ini.read(self.inipath)
        elif not os.path.exists(self.inipath) and self.fn.lower() == settings.mbplugin_ini:
            self.create()
            self.write()
        else:
            raise RuntimeError(f'Not found {self.fn}')
        return self.ini

    def create(self):
        'Только создаем в памяти, но не записываем'
        # Создаем mbplugin.ini - он нам нужен для настроек и чтобы знать где ini-шники от mobilebalance
        mbpath = self.find_files_up('phones.ini')
        if os.path.exists(mbpath):
            # Если нашли mobilebalance - cоздадим mbplugin.ini и sqlite базу там же где и ini-шники mobilebalance
            self.inipath = os.path.join(os.path.split(mbpath)[0], self.fn)
            dbpath = os.path.abspath(os.path.join(os.path.split(mbpath)[0], os.path.split(settings.ini['Options']['dbfilename'])[1]))
        else:
            # иначе создадим mbplugin.ini и базу в корне папки mbplugin
            self.ini['MobileBalance'] = {'path': ''}
            dbpath = settings.ini['Options']['dbfilename']
        self.ini['MobileBalance'] = {'path': os.path.split(mbpath)[0]}
        # self.ini.update(settings.ini) # TODO in future
        self.ini['MobileBalance'] = {'path': os.path.split(mbpath)[0]}
        self.ini['Options'] = {'logginglevel': settings.ini['Options']['logginglevel'],
                          'sqlitestore': settings.ini['Options']['sqlitestore'],
                          'dbfilename': dbpath,
                          'createhtmlreport': settings.ini['Options']['createhtmlreport'],
                          'balance_html': os.path.abspath(settings.ini['Options']['balance_html']),
                          'updatefrommdb': settings.ini['Options']['updatefrommdb'],
                          'updatefrommdbdeep': settings.ini['Options']['updatefrommdbdeep'],
                          }
        self.ini['HttpServer'] = {'port': settings.ini['HttpServer']['port'],
                             'host': settings.ini['HttpServer']['host'],
                             'table_format': settings.ini['HttpServer']['table_format']
                             }    


    def write(self):
        if self.fn.lower() != settings.mbplugin_ini:
            return  # only mbplugin.ini
        self.ini.write(open(self.inipath, 'w'))
        
    def phones(self):
        if self.fn.lower() != 'phones.ini':
            raise RuntimeError(f'{self.fn} is not phones.ini')
        data = {}
        for secnum,el in self.read().items():
            if secnum.isnumeric() and 'Monitor' in el:
                key = (re.sub(r' #\d+','',el['Number']),el['Region'])
                data[key] = {}
                data[key]['NN'] = int(secnum)
                data[key]['Alias'] = el.get('Alias','')
                data[key]['PhoneDescription'] = el.get('PhoneDescription','')
        return data

def read_stocks(stocks_name):
    'Читаем список стоков для плагина stock.py из mbplugin.ini'
    ini_all_sec = ini().read()
    if 'stocks_'+stocks_name not in ini_all_sec:
        raise RuntimeError(f'section {"stocks_"+stocks_name} not in mbplugin.ini')
    stock_sec_ini = ini_all_sec['stocks_'+stocks_name]
    stocks = {'stocks': [], 'remain': {}, 'currenc': ''}
    items = stock_sec_ini.items()
    stocks_str = [list(map(str.strip, v.split(','))) for k, v in items if k.startswith('stock')]
    remain_str = [list(map(str.strip, v.split(','))) for k, v in items if k.startswith('remain')]
    stocks['currenc'] = stock_sec_ini['currenc'].strip()
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
    # print(list(ini('phones.ini').read().keys()))
    # print(list(ini('options.ini').read().keys()))
    # print(list(ini('mbplugin.ini').read().keys()))

    #ini = ini().read()
    #if ini['MobileBalance']['path'] == '':
    #    print('MobileBalance folder unknown')
    #print(list(ini('phones.ini').read().keys()))

    #stocks_name = 'broker_ru'
    #print(read_stocks(stocks_name))

    # import io;f = io.StringIO();ini.write(f);print(f.getvalue())
    #{'STOCKS':(('AAPL',1,'Y'),('TATNP',16,'M'),('FXIT',1,'M')), 'REMAIN': {'USD':5, 'RUB':536}, 'CURRENC': 'USD'}
    #p=ini('phones.ini').read()
