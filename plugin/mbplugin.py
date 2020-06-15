# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import time, os, sys, logging, traceback
import xml.etree.ElementTree as etree
sys.path.append(os.path.split(os.path.abspath(sys.argv[0]))[0])
import dbengine, store, settings

lang = 'p'  # Для плагинов на python преффикс lang всегда 'p'


def result_to_xml(result):
    'Конвертирует словарь результатов в готовый к отдаче вид '
    # Коррекция SMS и Min (должны быть integer)
    if 'SMS' in result:
        result['SMS'] = int(result['SMS'])
    if 'Min' in result:
        result['Min'] = int(result['Min'])
    body = ''.join([f'<{k}>{v}</{k}>' for k, v in result.items()])
    return f'<Response>{body}</Response>'


def main():
    logging_level = store.read_ini()['Options']['logginglevel']
    logging.basicConfig(filename="..\\log\\mbplugin.log", level=logging_level,
                        format=u'[%(asctime)s] %(levelname)s %(funcName)s %(message)s')
    # В коммандной строке указан плагин ?
    if len(sys.argv) < 2:
        exception_text = f'При вызове mbplugin.bat не указан модуль'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    # Это плагин от python ?
    if not sys.argv[1].startswith(f'{lang}_'):
        # Это плагин не от python, тихо выходим
        logging.info(f'Not python preffix')
        return -2
    plugin = sys.argv[1].split('_', 1)[1]  # plugin это все что после p_
    # Такой модуль есть ? Он грузится ?
    try:
        module = __import__(plugin, globals(), locals(), [], 0)
    except Exception:
        exception_text = f'Модуль {plugin} не грузится: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    # request указан в переменной RequestVariable ?
    try:
        RequestVariable = os.environ['RequestVariable'].strip(' "')
        root = etree.fromstring(RequestVariable)
        login = root.find('Login').text
        password = root.find('Password').text
    except Exception:
        exception_text = f'Не смог взять RequestVariable: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    logging.debug(f'request = {RequestVariable}')
    # Запуск плагина
    logging.info(f'Start {lang} {plugin} {login}')
    try:
        result = module.get_balance(
            login, password, f'{lang}_{plugin}_{login}')
    except Exception:
        exception_text = f'Ошибка при вызове модуля \n{plugin}: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    # Готовим результат
    try:
        sys.stdout.write(result_to_xml(result))
    except Exception:
        exception_text = f'Ошибка при подготовке результата: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    # пишем в базу
    try:
        options = store.read_ini()['Options']
        if options.get('sqlitestore','0') == '1':
            logging.info(f'Пишем в базу sqlite')
            dbfilename = options.get('dbfilename', settings.dbfilename)
            db = dbengine.dbengine(dbfilename)
            db.write_result(f'{lang}_{plugin}', login, result)
    except AttributeError:
        logging.info(f'Отсутствуют параметры {"".join(traceback.format_exception(*sys.exc_info()))} дополнительные действия не производятся')
    except Exception:
        logging.error(f'Ошибка при записи в БД {"".join(traceback.format_exception(*sys.exc_info()))}')
    try:
        options = store.read_ini()['Options']
        if options.get('createhtmlreport','0') == '1':
            import httpserver_mobile
            _,res = httpserver_mobile.getreport()
            balance_html = options.get('balance_html', settings.balance_html)
            open(balance_html,encoding='utf8',mode='w').write('\n'.join(res))
    except Exception:
        logging.error(f'Ошибка генерации {balance_html} {"".join(traceback.format_exception(*sys.exc_info()))}')
    logging.debug(f'result = {result}')
    logging.info(f'Complete {lang} {plugin} {login}\n')
    return 0


if __name__ == '__main__':
    # todo for test usage mbplugin.py login password
    # or mbplugin.py lang plugin login password
    main()
