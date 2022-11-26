# -*- coding: utf8 -*-
'Модуль для хранения сессий и настроек а также чтения настроек из ini от MobileBalance'
import os, sys, locale, time, io, re, json, pickle, requests, urllib.request, configparser, pprint, zipfile, logging, traceback, collections, typing
from os.path import abspath
import settings

def exception_text():
    return "".join(traceback.format_exception(*sys.exc_info())).encode('cp1251', 'ignore').decode('cp1251', 'ignore')

def abspath_join(*argv):
    'собираем в путь все переданные куски, если получившийся не абсолютный, то приделываем к нему путь до корня'
    path = os.path.join(*argv)
    if not os.path.isabs(path):
        root = settings.mbplugin_root_path
        if root is None:
            root = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..', '..'))
        path = os.path.abspath(os.path.join(root, path))
    return path

def session_folder(storename):
    'Возвращает путь к папке хранения сессий'
    storefolder = abspath_join(options('storefolder'), storename)
    return storefolder

def version():
    'Возвращает версию mbplugin по информации из changelist.md'
    try:
        with open(abspath_join('mbplugin', 'changelist.md'), encoding='utf8') as f:
            res = re.findall(r'## mbplugin (v\d.*?) \(', f.read())[-1]
        return res
    except Exception:
        return 'unknown'

def path_split_all(path):
    'разбивает путь на список'
    res = []
    while True:
        p1, p2 = os.path.split(path)
        if p1 == path:  # Относительный
            res.insert(0, p1)
            break
        elif p2 == path:  # Абсолютный
            res.insert(0, p2)
            break
        else:
            path = p1
            res.insert(0, p2)
    return res

def find_file_up(folder, filename):
    'Нужен для совместимости со старым подходом, когда папка mbplugin могла находится на несколько уровней вложенности вниз'
    folder = os.path.abspath(folder)
    if os.path.exists(os.path.join(folder, filename)):
        return folder
    levels = [os.sep.join(folder.split(os.sep)[:i]) for i in range(len(folder.split(os.sep)), 1, -1)]
    for path in levels:
        if os.path.exists(os.path.join(path, filename)):
            return path
    return folder

def switch_to_mb_mode():
    'Переключаемся в режим mbplugin находим ini в корне и т.п.'
    settings.mode = settings.MODE_MB
    # По умолчанию вычисляем эту папку как папку на 2 уровня выше папки с этим скриптом
    # Этот путь используем когда обращаемся к подпапкам папки mbplugin
    settings.mbplugin_root_path = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..', '..'))
    # Для пути с симлинками в unix-like системах приходится идти на трюки:
    # Исходим из того что скрипт mbp привет нас в правильный корень
    # https://stackoverflow.com/questions/54665065/python-getcwd-and-pwd-if-directory-is-a-symbolic-link-give-different-results
    if sys.platform != 'win32':
        # В докере с симлинком другая проблема - нет $PWD, но зато os.getcwd() ведет нас в /mbstandalone
        pwd = os.environ.get('PWD', os.getcwd())
        if os.path.exists(os.path.abspath(os.path.join(pwd, 'mbplugin', 'plugin', 'util.py'))):
            mbplugin_root_path = pwd
        elif os.path.exists(os.path.abspath(os.path.join(pwd, '..', 'mbplugin', 'plugin', 'util.py'))):
            mbplugin_root_path = os.path.abspath(os.path.join(pwd, '..'))
        elif os.path.exists(os.path.abspath(os.path.join(pwd, '..', '..', 'mbplugin', 'plugin', 'util.py'))):
            mbplugin_root_path = os.path.abspath(os.path.join(pwd, '..', '..'))
    # Папка в которой по умолчанию находится mbplugin.ini, phones.ini, база
    # т.к. раньше допускалось что папка mbplugin может находится на несколько уровней вложенности вниз ищем вверх phones.ini
    settings.mbplugin_ini_path = find_file_up(settings.mbplugin_root_path, 'phones.ini')

def validate_json(data):
    'Проверяем строку на то что это валидный json'
    try:
        json.loads(data)
    except json.decoder.JSONDecodeError:
        return False  # Invalid JSON
    return True  # Valid JSON

def fix_num_params(result, int_params):
    'Коррекция SMS и Min (должны быть integer или приводится к integer), округление - удаление микрокопеек'
    for param in int_params:
        if param in result:
            result[param] = str(result[param])
            if re.match(r'^-?\d+(?:\.\d+)?$', result[param]):
                result[param] = int(float(result[param]))
            else:
                logging.error(f'Bad {param} value: {result[param]}')
                del result[param]
    for k, v in result.items():
        if type(v) == float:
            result[k] = round(v, 2)  # Чтобы не было паразитных микрокопеек
    return result

def correct_result(result, pkey):
    'Дополнительные коррекции после проверки'
    if type(result) != dict:
        return result
    result = fix_num_params(result, int_params=['SMS', 'Min'])
    if 'Balance' in result and 'Balance2' in result:
        b, b2 = result['Balance'], result['Balance2']
        if options('balance2', pkey=pkey) == 'swap':
            result['Balance'], result['Balance2'] = result['Balance2'], result['Balance']
        elif options('balance2', pkey=pkey) == 'add':
            result['Balance'] = result['Balance'] + result['Balance2']
        logging.info(f"Balance correct by option.Balance2={options('balance2', pkey=pkey)} {b},{b2} -> {result['Balance']}{result['Balance2']}")
    return result

class Feedback():
    '''Класс для создания функции обратной связи, используется чтобы откуда угодно кидать сообщения
    по ходу выполнения процесса например в телегу
    Отправитель шлет сообщения в store.feedback.text()
    Такая замена для print
    '''

    def __init__(self, feedback: typing.Callable = None):
        self._feedback: typing.Optional[typing.Callable[[str], None]] = None
        self.previous = ''

    def set(self, func: typing.Callable[[str], None]):
        'устанавливаем функцию для feedback'
        self._feedback = func

    def unset(self):
        'Закрываем возможность feedback'
        self._feedback = None

    def text(self, msg: str = '', append=False):
        'Отправляем сообщение'
        try:
            if self._feedback is not None:
                if append and self.previous != '':
                    msg = self.previous + '\n' + msg
                self._feedback(msg)
                self.previous = msg
            else:
                pass
                # print(msg)  # TODO можно так или в лог
        except Exception:
            # Независимо от результата мы не должны уйти в exception - это просто принт
            print('Fail feedback')

# Создаем экземпляр для работы
feedback = Feedback()


class Session():
    'Класс для сессии с дополнительными фишками для сохранения и проверки и с подтягиванием настроек'

    def __init__(self, storename=None, headers={}):
        '''если не указать storename то сессия без сохранения
        headers - если после создания сессии нужно прописать дополнительные'''
        self._session: requests.Session = None
        self.storename = storename
        self.storefolder = options('storefolder')
        self.pagecounter = 1  # Счетчик страниц для сохранения
        self.json_response = {}  # Сохраняем json ответы
        self.additional_headers = headers
        self.load_session()

    def get_headers(self):
        return self._session.headers

    def update_headers(self, headers):
        self._session.headers.update(headers)

    def drop_and_create(self):
        'удаляем сессию и создаем новую'
        try:
            os.remove(abspath_join(self.storefolder, self.storename))
        except Exception:
            pass
        self.load_session()

    def disable_warnings(self):
        'Запретить insecure warning - приходится включать для кривых сайтов'
        requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member

    def load_session(self, headers=None):
        'Загружаем сессии из файла, если файла нет, просто создаем заново, если drop=True то СТРОГО создаем заново, затем применяем хедера, прокси и пр.'
        if self.storename is None:
            self._session = requests.Session()
        else:
            try:
                with open(abspath_join(self.storefolder, self.storename), 'rb') as f:
                    self._session = pickle.load(f)
            except Exception:
                self._session = requests.Session()
        if options('node_tls_reject_unauthorized').strip() == '0':
            self._session.verify = False
        self.update_headers(self.additional_headers)
        # 'Применяем к сессии настройки'
        if options('requests_proxy') != '':
            if options('requests_proxy') != 'auto':
                proxy = urllib.request.getproxies()
                # fix для urllib urllib3 > 1.26.5
                if 'https' in proxy:
                    proxy['https'] = proxy['https'].replace('https://', 'http://')
            else:
                proxy = json.loads(options('requests_proxy'))
                self._session.proxies.update(proxy)

    def save_session(self):
        'Сохраняем сессию в файл'
        if self.storename is None or settings.mode != settings.MODE_MB:
            return
        with open(abspath_join(self.storefolder, self.storename), 'wb') as f:
            pickle.dump(self._session, f)

    def save_response(self, url, response, save_text=False):
        'debug сохранение по умолчанию только response.json() или если указано отдельно сохраняем text'
        if self.storename is None or settings.mode != settings.MODE_MB:
            return
        # Сохраняем по старинке в режиме DEBUG каждую страницу в один файл
        if not hasattr(response, 'content'):
            return
        if options('logginglevel') == 'DEBUG':
            fn = abspath_join(options('loggingfolder'), f'{self.storename}_{self.pagecounter}.html')
            open(fn, mode='wb').write(response.content)
        # Новый вариант сохранения - все json в один файл
        if options('logginglevel') == 'DEBUG' or str(options('log_responses')) == '1':
            try:
                idx = f'{url}_{self.pagecounter}'
                if save_text:
                    self.json_response[idx] = response.text
                else:
                    try:
                        self.json_response[idx] = response.json()
                    except Exception:
                        self.json_response[idx] = "It's not json"
                text = '\n\n'.join([f'{k}\n{pprint.PrettyPrinter(indent=4).pformat(v)}' for k, v in self.json_response.items()])
                open(abspath_join(options('loggingfolder'), self.storename + '.log'), 'w', encoding='utf8', errors='ignore').write(text)
            except Exception:
                pass
        self.pagecounter += 1

    def close(self):
        'Close session if opened'
        if type(self._session) == requests.Session:
            self._session.close()

    def __del__(self):
        self.close()

    def get(self, url, **kwargs) -> requests.Response:
        response: requests.Response = self._session.get(url, **kwargs)
        self.save_response(url, response)
        return response

    def post(self, url, data=None, json=None, **kwargs) -> requests.Response:
        response: requests.Response = self._session.post(url, data, json, **kwargs)
        self.save_response(url, response)
        return response

    def put(self, url, data=None, **kwargs) -> requests.Response:
        response: requests.Response = self._session.put(url, data, **kwargs)
        self.save_response(url, response)
        return response

def get_pkey(login, plugin_name):
    '''Все взятия pkey - пары (логин, p_плагин) через эту функцию, чтобы в случае чего
    нестыковки исправить здесь, если у плагина уже есть префикс p_ то второй раз не прибавляем '''
    lang = 'p'
    if plugin_name.startswith(f'{lang}_'):
        return (login, plugin_name)
    return (login, f'{lang}_{plugin_name}')

def options(param, default=None, section='Options', listparam=False, mainparams={}, pkey=None, flush=False):
    '''Читаем параметр из mbplugin.ini либо дефолт из settings
    Если listparam=True, то читаем список из всех, что начинается на param
    mainparams - перекрывает любые другие варианты, если пришли помним их до перезапуска, если в нем присутствует параметр - берем его
    Если результат путь (settings.path_param) - то вычисляем для него абсолютный путь
    Если указан pkey (number, plugin) и секция Options то пытаемся прочитать индивидуальные параметры для этого телефона из phones.ini/phones_add.ini
    если указан flush - кэш очищается
    Приоритет:
    mbplugin.ini < phones.ini < mainparam(cmd -p options)
    '''
    if settings.mode != settings.MODE_MB:
        return settings.ini[section][param]
    if not hasattr(options, 'mainparams'):
        options.mainparams = {}
    if len(mainparams) > 0:
        logging.info(f'Options add {mainparams=} to {options.mainparams}')
        options.mainparams.update({k.lower(): v for k, v in mainparams.items()})
    if not hasattr(options, 'mbplugin_ini') or flush:
        options.mbplugin_ini = None
        options.phones = None
    if flush is True:
        logging.info(f'Flush options ini cache')
    if options.mbplugin_ini is None:
        options.mbplugin_ini = ini().read()
    phones_options = {}
    # Параметры из phones.ini/phones_add.ini
    if pkey is not None and section == 'Options':
        if options.phones is None:
            options.phones = ini('phones.ini').phones()
        if pkey in options.phones:
            phones_options = options.phones[pkey]
    # Параметр список, например subscriptionNNN
    if listparam:
        res = []
        if section in options.mbplugin_ini:
            res = [v for k, v in options.mbplugin_ini[section].items() if k.startswith(param.lower())]
    else:  # Обычный параметр
        if default is None:  # default не задан = возьмем из settings
            default = settings.ini[section].get(param.lower(), None)
        # Берем обычный параметр, если в ini его нет, то default
        res = options.mbplugin_ini.get(section, param.lower(), fallback=default)
        if param.lower() in settings.path_param:
            res = abspath_join(res)
    if param.lower() in options.mainparams:  # mainparams в приоритете над всем даже phones.ini
        return options.mainparams[param.lower()]
    else:  # Проверяем phones.ini, если есть берем его
        return phones_options.get(param.lower(), res)


def option_validate(param, section='Options', pkey=None) -> typing.Tuple[bool, str]:
    'Проверка корректности опции '
    val = options(param, section=section, pkey=pkey)
    prop: typing.Dict = settings.ini[section].get(param + '_', None)  # type: ignore
    err_mess = ''
    if prop is not None:
        if prop['type'] == 'checkbox' and str(val) not in ['0', '1']:
            err_mess = f'Error {param}={val}, must be 0 or 1'
        elif prop['type'] == 'select' and str(val) not in prop['variants'].split():
            err_mess = f'Error {param}={val}, must be {prop["variants"]}'
        elif prop['type'] == 'list' and 'validate' in prop:
            val_list = options(param, section=section, listparam=True)
            invalid = [i for i in val_list if not prop['validate'](i)]
            if invalid != []:
                err_mess = f'Error line {param} check {" ".join(invalid)}'
        elif 'validate' in prop and not prop['validate'](str(val)):
            err_mess = f'Error {param}="{val}", invalid (not check validation)'
    return (err_mess == ''), err_mess


class ini():
    def __init__(self, fn=settings.mbplugin_ini):
        'файл mbplugin.ini ищем в вышележащих папках либо в settings.mbplugin_ini_path если он не пустой'
        'остальные ini ищем в пути прописанном в mbplugin.ini\\MobileBalance\\path'
        'Все пути считаются относительными папки где лежит сам mbplugin.ini, если не указано иное'
        'Кодировка для windows cp1251, для остальных utf-8 см locale.getpreferredencoding()'
        self.ini = configparser.ConfigParser(interpolation=None)
        self.fn = fn
        self.inipath = abspath_join(settings.mbplugin_ini_path, self.fn)
        self.codepage = settings.ini_codepage  # для windows cp1251, для остальных utf-8

    def find_files_up(self, fn):
        'Ищем файл вверх по дереву путей'
        'Для тестов можно явно указать папку с mbplugin.ini в settings.mbplugin_ini_path '
        # TODO пока оставили чтобы не ломать тесты, потом уберем
        return abspath_join(settings.mbplugin_ini_path, fn)

    def read(self):
        'Читаем ini из файла'
        'phones.ini и phones_add.ini- нечестный ini читать приходится с извратами'
        'replace [Phone] #123 -> [123]'
        'Для чтения phones.ini с добавлением данных из phones_add.ini см метод ini.phones'
        if os.path.exists(self.inipath):
            if self.fn.lower() == 'phones.ini' or self.fn.lower() == 'phones_add.ini':
                with open(self.inipath, encoding=self.codepage) as f_ini:
                    prep1 = re.sub(r'(?usi)\[Phone\] #(\d+)', r'[\1]', f_ini.read())
                # TODO костыль N1, мы подменяем p_pluginLH на p_plugin чтобы при переключении плагина не разъезжались данные
                prep2 = re.sub(r'(?usi)(Region)(\s*=\s*p_\S+)(LH)', r'\1\2\n\1_orig\2\3', prep1)
                # TODO костыль N2, у Number то что идет в конце вида <пробел>#<цифры> это не относиться к логину а
                # сделано для уникальности логинов - выкидываем, оно нас только сбивает - мы работаем по паре Region_Number
                # Первоначальное значение сохраняется в Phone_orig и Region_orig
                prep3 = re.sub(r'(?usi)(Number)(\s*=\s*\S+)( #\d+)', r'\1\2\n\1_orig\2\3', prep2)
                self.ini.read_string(prep3)
            else:
                self.ini.read(self.inipath, encoding=self.codepage)
        elif not os.path.exists(self.inipath) and self.fn.lower() == settings.mbplugin_ini:
            self.create()
            self.write()
        elif not os.path.exists(self.inipath) and self.fn.lower() == 'phones_add.ini':
            self.ini.read_string('')  # Если нет - тихо вернем пустой
        else:
            raise RuntimeError(f'Not found {self.fn}')
        return self.ini

    def create(self):
        'Только создаем в памяти, но не записываем'
        # Создаем mbplugin.ini - он нам нужен для настроек и чтобы знать где ini-шники от mobilebalance
        # mbpath = self.find_files_up('phones.ini')
        mbpath = abspath_join(settings.mbplugin_ini_path, 'phones.ini')
        if not os.path.exists(mbpath):
            # Если нашли mobilebalance - создадим mbplugin.ini и sqlite базу там же где и ini-шники mobilebalance
            print(f'Not found phones.ini in {settings.mbplugin_ini_path}')
            raise RuntimeError(f'Not found phones.ini')
        # создадим mbplugin.ini над папкой mbplugin
        self.ini['Options'] = {
            'logginglevel': settings.ini['Options']['logginglevel'],
            'sqlitestore': settings.ini['Options']['sqlitestore'],
            'createhtmlreport': settings.ini['Options']['createhtmlreport'],
            'balance_html': abspath_join(settings.ini['Options']['balance_html']),
            'updatefrommdb': settings.ini['Options']['updatefrommdb'],
            'updatefrommdbdeep': settings.ini['Options']['updatefrommdbdeep'],
        }
        self.ini['HttpServer'] = {
            'port': settings.ini['HttpServer']['port'],
            'host': settings.ini['HttpServer']['host'],
            'table_format': settings.ini['HttpServer']['table_format']
        }

    def save_bak(self):
        'Сохраняем резервную копию файла в папку с логами в zip'
        if not os.path.exists(self.inipath):  # Сохраняем bak, только если файл есть
            return
        # Делаем резервную копию ini перед сохранением
        undozipname = abspath_join(options('storefolder'), 'mbplugin.ini.bak.zip')
        arc = []
        if os.path.exists(undozipname):
            # Предварительно читаем сохраненные варианты, открываем на чтение
            with zipfile.ZipFile(undozipname, 'r', zipfile.ZIP_DEFLATED) as zf1:
                for i in zf1.infolist():  # Во временную переменную прочитали
                    arc.append((i, zf1.read(i)))
        arc = sorted(arc, reverse=True, key=lambda i: i[0].filename)[0:int(options('httpconfigeditundo'))]
        name_bak = f'{os.path.split(self.inipath)[-1]}_{time.strftime("%Y%m%d%H%M%S", time.localtime())}'
        # Если быстро менять конфиг - то успеваем в одну секунду сохранить несколько раз - это лишнее
        # Если в эту секунду уже сохраняли - пропускаем
        if name_bak in [i[0].filename for i in arc]:
            print('We create undo too often - lets skip this one')
            return
        with zipfile.ZipFile(undozipname + '~tmp', 'w', zipfile.ZIP_DEFLATED) as zf2:
            # Sic! Для write write(filename, arcname) vs writestr(arcname, data)
            zf2.write(self.inipath, f'{name_bak}')
            for a_name, a_data in arc:
                zf2.writestr(a_name, a_data)
        if os.path.exists(undozipname):
            os.remove(undozipname)  # Удаляем первоначальный файл
        os.rename(undozipname + "~tmp", undozipname)  # Переименовываем временный на место первоначального

    def write(self):
        '''Сохраняем только mbplugin.ini и phones.ini для остальных - игнорируем
        phones.ini всегда сохраняем в phones.ini, без phones_add.ini, если есть phones_add.ini не работаем
        '''
        def ini_write_to_string(ini: configparser.ConfigParser) -> str:
            sf = io.StringIO()
            ini.write(sf)
            return sf.getvalue()
        if not (self.fn.lower() == settings.mbplugin_ini or self.fn.lower() == 'phones.ini' and str(options('phone_ini_save')) == '1'):
            return  # only mbplugin.ini
        data = ini_write_to_string(self.ini)
        if self.fn.lower() == 'phones.ini':  # для phones.ini отдельно приседаем
            t_ini = configparser.ConfigParser(interpolation=None)  # Делаем копию ini чтобы не портить загруженный оригинал
            t_ini.read_string(data)
            for sec in t_ini.sections():  # number_orig -> number, region_orig -> region
                for key in t_ini[sec]:
                    if key + '_orig' in t_ini[sec]:
                        t_ini[sec][key] = t_ini[sec][key + '_orig']
                        del t_ini[sec][key + '_orig']
            data = re.sub(r'(?m)^\[(\d+)\]$', r'[Phone] #\1', ini_write_to_string(t_ini))  # [36] -> [Phone] #36
            for key in settings.PHONE_INI_KEYS:
                data = data.replace(f'{key.lower()} =', f'{key:20} =')
            # print(data)
            # return
        raw = data.splitlines()  # ini-шник без комментариев (прогнали через честное сохранение)
        if os.path.exists(self.inipath):  # Если файл ini на диске есть сверяем с предыдущей версией
            self.save_bak()
            # TODO если сохраняем комменты (комменты попадут куда надо если меняем не больше одной строчки за раз):
            with open(self.inipath, encoding=self.codepage) as f_ini_r:
                for num, line in enumerate(f_ini_r.read().splitlines()):
                    if line.startswith(';'):
                        raw.insert(num, line)
        with open(self.inipath, encoding=self.codepage, mode='w') as f_ini_w:
            f_ini_w.write('\n'.join(raw))
        # TODO Если просто сохраняем то так
        # self.ini.write(open(self.inipath, 'w'))

    def ini_to_json(self):
        'Преобразуем ini в js для редактора editcfg'
        result = {}
        for sec in self.ini.values():
            if sec.name != 'DEFAULT':
                # Кидаем ключи из ini после Добавляем дефолтные ключи из settings если их не было в ini
                # TODO продумать, может их помечать цветом и сделать кнопку вернуть к дефолту, т.е. удалить ключ из ini
                for key, val in list(sec.items()) + list(settings.ini.get(sec.name, {}).items()):
                    if key.endswith('_'):
                        continue
                    params = settings.ini.get(sec.name, {}).get(key + '_', {})
                    param = {k: v for k, v in params.items() if k not in ['validate']}
                    line = {'section': sec.name, 'id': key, 'type': 'text', 'descr': f'DESC {sec.name}_{key}',
                            'value': val, 'default': key not in sec, 'default_val': settings.ini.get(sec.name, {}).get(key, None)}
                    line.update(param)
                    if f'{sec.name}_{key}' not in result:
                        result[f'{sec.name}_{key}'] = line
        return json.dumps(result, ensure_ascii=False)

    def phones(self):
        'Читает phones.ini добавляет данные из phones_add.ini дополнительную информацию'
        'И возвращает словарь с ключами в виде пары вида (number,region)'
        if self.fn.lower() != 'phones.ini':
            raise RuntimeError(f'{self.fn} is not phones.ini')
        # Читаем вспомогательный phones_add.ini - из него возьмем данные если они там есть, они перекроют данные в phones.ini
        phones_add = ini('phones_add.ini').read()
        data = {}
        for secnum, el in self.read().items():
            if secnum.isnumeric() and 'Monitor' in el:
                try:
                    key = (re.sub(r' #\d+', '', el['Number']), el['Region'])  # (1234567#1, mts) -> (1234567, mts)
                    data[key] = dict(el)
                    data[key]['NN'] = data[key]['nn'] = int(secnum)
                    data[key]['Alias'] = el.get('Alias', '')
                    data[key]['Region'] = el.get('Region', '')
                    data[key]['Number'] = el.get('Number', '')
                    data[key]['Monitor'] = el.get('Monitor', '')
                    data[key]['Password2'] = el.get('Password2', '')
                except Exception:
                    raise RuntimeError(f'Parse phones.ini error {exception_text()} in section{secnum}') from None
                if secnum in phones_add:
                    try:
                        # Проблема - configparser возвращает ключи в lowercase - так что приходится перебирать
                        # ключи чтобы не оказалось два одинаковых ключа с разным кейсом
                        if secnum in phones_add:
                            for k, v in phones_add[secnum].items():
                                data[key][k] = v
                    except Exception:
                        raise RuntimeError(f'Parse phones_add.ini error {exception_text()} in section{secnum}') from None
                # Выравниваем все значения, которые в CapitalCase присваивая им значения из lower case
                for k in data[key]:
                    if k.lower() != k and k.lower() in data[key]:
                        data[key][k] = data[key][k.lower()]
        return data


def read_stocks(stocks_name):
    'Читаем список стоков для плагина stock.py из mbplugin.ini'
    ini_all_sec = ini().read()
    if 'stocks_' + stocks_name not in ini_all_sec:
        raise RuntimeError(f'section {"stocks_"+stocks_name} not in mbplugin.ini')
    stock_sec_ini = ini_all_sec['stocks_' + stocks_name]
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
    body = ''.join([f'<{k}>{v}</{k}>' for k, v in result.items()])
    return f'<Response>{body}</Response>'


def result_to_html(result):
    'Конвертирует словарь результатов в готовый к отдаче вид '
    body = json.dumps(result, ensure_ascii=False)
    return f'<html><meta charset="windows-1251"><p id=response>{body}</p></html>'


def logging_restart():
    'Останавливаем логирование и откидываем в отдельный файл'
    'Чтобы можно было почистить'
    filename = options('logginghttpfilename')
    filename_new = filename + time.strftime('%Y%m%d%H%M%S.log', time.localtime())
    logging.shutdown()
    os.rename(filename, filename_new)
    logging.info(f'Old log was renamed to {filename_new}')


def ini_by_expression(expression):
    '''берем из ini по path вида ini/Options/sqlitestore - нужно для cmd обращений к ini
    если указано ini/Options/sqlitestore - возвращает set sqlitestore=ЗНАЧЕНИЕ
    если указано ini/Options/sqlitestore=1 - устанавливает в ini'''
    mbplugin_ini = ini()
    mbplugin_ini.read()
    path = expression
    if '=' in expression:
        path, value = expression.split('=')
        _, section, key = path.split('\\')
        mbplugin_ini.ini[section][key] = value
        if value == 'default':
            del mbplugin_ini.ini[section][key]
        mbplugin_ini.write()
    else:
        _, section, key = path.split('\\')
    return f'set {key}={options(key, section=section)}'


def update_settings(kwargs):
    for key, val in kwargs.items():
        if key in settings.ini['Options']:
            settings.ini['Options'][key] = val
            valid, msg = option_validate(key, 'Options')
            if not valid:
                raise RuntimeError(msg)
            settings.ini['Options'][key] = val


def turn_logging(httplog=False, logginglevel=None, force_turn=False):
    'Включение логирования и дополнительные инициализации'
    # Выставляем переменные, если они заданы в настройках
    if settings.logging_on and not force_turn:
        return  # если лог уже включен, то повторные вызовы игнорим если не force
    settings.logging_on = True
    # TODO WTF почему это здесь ?
    if options('node_tls_reject_unauthorized') != '':
        os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = options('node_tls_reject_unauthorized')
    if options('playwright_browsers_path') != '':
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = options('playwright_browsers_path')
    # logging.getLogger().handlers[0].stream.name
    if logginglevel is None:
        logginglevel = options('logginglevel')
    handlers = []
    if settings.mode == settings.MODE_MB:
        # Магия с предустановлеными именами логов из ini только в MODE_MB
        file_log = logging.FileHandler(abspath_join(options('logginghttpfilename' if httplog else 'loggingfilename')))
        handlers.append(file_log)
    if str(options('logconsole')) == '1':
        console_out = logging.StreamHandler()
        handlers.append(console_out)
    logging.basicConfig(
        force=True,
        handlers=handlers,
        level=logginglevel,
        format=options('loggingformat'))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Module store')
    else:
        # = в командной строке делит аргументы - чиним
        expression = sys.argv[1]
        if len(sys.argv) == 3:
            expression = sys.argv[1] + '=' + sys.argv[2]
        print(ini_by_expression(expression))

    # print(list(ini('phones.ini').read().keys()))
    # print(list(ini('options.ini').read().keys()))
    # print(list(ini('mbplugin.ini').read().keys()))

    # ini = ini().read()
    # if ini['MobileBalance']['path'] == '':
    #    print('MobileBalance folder unknown')
    # print(list(ini('phones.ini').read().keys()))

    # stocks_name = 'broker_ru'
    # print(read_stocks(stocks_name))

    # import io;f = io.StringIO();ini.write(f);print(f.getvalue())
    # {'STOCKS':(('AAPL',1,'Y'),('TATNP',16,'M'),('FXIT',1,'M')), 'REMAIN': {'USD':5, 'RUB':536}, 'CURRENC': 'USD'}
    # p=ini('phones.ini').read()
    # import store;ini=store.ini();ini.read();ini.ini['Options']['httpconfigedit']='1';ini.write()
