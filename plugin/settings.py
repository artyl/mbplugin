# -*- coding: utf8 -*-
''' Файл с общими установками, распространяется с дистрибутивом 
Значения по умолчанию, здесь ничего не меняем, если хотим поменять меняем в mbplugin.ini
подробное описание см в readme.md
'''
UNIT = {'TB': 1073741824, 'ТБ': 1073741824, 'TByte': 1073741824,
        'GB': 1048576, 'ГБ': 1048576, 'GByte': 1048576,
        'MB': 1024, 'МБ': 1024, 'MByte': 1024,
        'KB': 1, 'КБ': 1, 'KByte': 1,
        'day': 30, 'dayly': 30, 'month':1,}

# имя ini файла
mbplugin_ini = 'mbplugin.ini'

# сюда пропишем сразу возможные варианты для путя хрома
chrome_executable_path_alternate = [
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',]
########################################################################################
ini = {
    'Options': {  # Раздел mbplugin.ini [Options]
        # logging
        'loggingformat': u'[%(asctime)s] %(levelname)s %(funcName)s %(message)s',
        'loggingfolder': '..\\log',  # папка для логов
        'loggingfilename': '..\\log\\mbplugin.log',  # лог для ручного запуска и dll плагинов
        'logginghttpfilename': '..\\log\\http.log',  # лог http сервера и плагинов из него
        'logginglevel': 'INFO',  # Уровень логгирования
        'storefolder': '..\\store',  # Папка для хранения сессий
        'sqlitestore': '0',  # Записывать результаты в sqlite БД 0 нет, 1 да
        'createhtmlreport': '0',  # Создавать файлик html отчета, после получения данных
        # путь к БД sqlite если нужно поменять - mbplugin.ini Option dbfilename
        'dbfilename': '..\\BalanceHistory.sqlite',
        # путь к html файлу, который создается после получения баланса
        'balance_html': '..\\DB\\balance.html',
        'average_days': 30,  # Количество дней для расчета среднего по истории, если не смогли взять из options.ini
        'updatefrommdb': 0,  # Обновлять SQLite базу данными из MDB и на сколько дней в глубино
        # Обновлять SQLite базу данными из MDB и на сколько дней в глубино
        'updatefrommdbdeep': 30,
        # показывать иконку в трее - 1 прятать - 1, (по умолчанию 1)
        'show_tray_icon': '1',
        # Прятать окна Chrome (при logginglevel=DEBUG всегда показывает)
        'show_chrome': '0',
        # Путь к хрому - можно прописать явно в ini, иначе поищет из вариантов chrome_executable_path_alternate
        'chrome_executable_path': 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        # спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный
        # 1 - показывать использованный трафик (usedByMe) по всем  или 0 - показывать оставшийся трафик (NonUsed) по всем
        # список тел, через запятую - показать использованный только для этого списка телефонов
        'mts_usedbyme': '0',
    },
    'Telegram': {  # Раздел mbplugin.ini [Telegram]
        'api_token':'',  # токен для бота - прописывается в ini
        'auth_id': '',  # список id пользователей, которые получают баланс
        # формат для строки telegram bot из sqlite
        'tg_format': '<b>{Alias}</b>\t<code>{PhoneNumberFormat2}</code>\t<b>{Balance}</b>({BalDeltaQuery})',
        'tg_from': 'sqlite',  # mobilebalance или sqlite
        'send_empty': '1',  # посылать сообщения если изменений не было
        # формат для строки telegram bot из mobilebalance
        'tgmb_format': '<b>{Alias}</b>\t<code>{PhoneNum}</code>\t<b>{Balance}</b>({BalDeltaQuery})',
        'mobilebalance_http': 'http://localhost:19778/123456/',
    },
    'HttpServer': {  # Раздел mbplugin.ini [HttpServer]
        'port': '19777',  # порт http сервера с отчетами
        # host '127.0.0.1' - доступ только локально, '0.0.0.0' - разрешить доступ к по сети
        'host': '127.0.0.1',
        # формат вывода по умолчанию
        'table_format': 'PhoneNumber,Operator,UslugiOn,Balance,RealAverage,BalDelta,BalDeltaQuery,NoChangeDays,CalcTurnOff,SpendMin,SMS,Internet,Minutes,TarifPlan,BlockStatus',  # ? UserName
    },
}
