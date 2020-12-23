# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import time, os, sys, re, logging, traceback
import xml.etree.ElementTree as etree
import dbengine, store, settings, httpserver_mobile

lang = 'p'  # Для плагинов на python преффикс lang всегда 'p'

def main():
    logging.basicConfig(filename=store.options('loggingfilename'),
                        level=store.options('logginglevel'),
                        format=store.options('loggingformat'))
    # В коммандной строке указан плагин ?
    if len(sys.argv) < 2:
        exception_text = f'При вызове mbplugin.bat не указан модуль'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        return -1
    # Это плагин от python ?
    if not sys.argv[1].startswith(f'{lang}_'):
        # Это плагин не от python, тихо выходим
        logging.info(f'Not python prefix')
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
    if len(sys.argv) == 4: # plugin login password
        login = sys.argv[2]
        password = sys.argv[3]
    else: # request указан в переменной RequestVariable ?        
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
    dbengine.flags('set',f'{lang}_{plugin}_{login}','start')  # выставляем флаг о начале запроса
    try:
        storename = re.sub(r'\W', '_', f'{lang}_{plugin}_{login}')
        result = module.get_balance(login, password, storename)
        if 'Balance' not in result:
            raise RuntimeError(f'В result отсутствеут баланс')
    except Exception:
        exception_text = f'Ошибка при вызове модуля \n{plugin}: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        dbengine.flags('set',f'{lang}_{plugin}_{login}','error call')  # выставляем флаг о ошибке вызова
        return -1
    # Готовим результат
    try:
        sys.stdout.write(store.result_to_xml(result))
    except Exception:
        exception_text = f'Ошибка при подготовке результата: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)
        sys.stdout.write(exception_text)
        dbengine.flags('set',f'{lang}_{plugin}_{login}','error result')  # выставляем флаг о плохом результате]
        return -1
    dbengine.flags('delete',f'{lang}_{plugin}_{login}','start')  # запрос завершился успешно - сбрасываем флаг
    try:    
        # пишем в базу
        dbengine.write_result_to_db(f'{lang}_{plugin}', login, result)
        # обновляем данные из mdb
        dbengine.update_sqlite_from_mdb()
    except Exception:    
        exception_text = f'Ошибка при подготовке работе с БД: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)        
    try:
        # генерируем balance_html
        httpserver_mobile.write_report()
    except Exception:    
        exception_text = f'Ошибка при подготовке report: {"".join(traceback.format_exception(*sys.exc_info()))}'
        logging.error(exception_text)        
    logging.debug(f'result = {result}')
    logging.info(f'Complete {lang} {plugin} {login}\n')
    return 0


if __name__ == '__main__':
    # todo mbplugin.py plugin  (RequestVariable=<Request>\n<ParentWindow>007F09DA</ParentWindow>\n<Login>p_test_1234567</Login>\n<Password>pass1234</Password>\n</Request>)
    # todo mbplugin.py plugin login password (нужен для отладки)
    main()
