# -*- coding: utf8 -*-
''' Файл с общими установками, распространяется с дистрибутивом 
Значения по умолчанию, здесь ничего не меняем, если хотим поменять меняем в mbplugin.ini
'''
UNIT = {'TB': 1073741824, 'ТБ': 1073741824, 'TByte': 1073741824,
        'GB': 1048576, 'ГБ': 1048576, 'GByte': 1048576,
        'MB': 1024, 'МБ': 1024, 'MByte': 1024,
        'KB': 1, 'КБ': 1, 'KByte': 1,
        'day': 30, 'dayly': 30, 'month':1,}

# Раздел mbplugin.ini [Options]
# logging
loggingformat = u'[%(asctime)s] %(levelname)s %(funcName)s %(message)s'
loggingfolder = "..\\log"
loggingfilename = "..\\log\\mbplugin.log"
logginghttpfilename = "..\\log\\http.log"
logginglevel='INFO'

# имя ini файла
mbplugin_ini = 'mbplugin.ini'
# Папка для хранения сессий
storefolder = '..\\store'
# Записывать результаты в sqlite БД 0 нет, 1 да
sqlitestore = '0'
# Создавать файлик html отчета, после получения данных
createhtmlreport = '0'
# путь к БД sqlite если нужно поменять - mbplugin.ini Option dbfilename
dbfilename = '..\\BalanceHistory.sqlite'
# путь к html файлу, который создается после получения баланса
balance_html = '..\\DB\\balance.html'
# Количество дней для расчета среднего по истории, если не смогли взять из options.ini
average_days = 30
# Обновлять SQLite базу данными из MDB и на сколько дней в глубино
updatefrommdb = 0
updatefrommdbdeep = 30

# Раздел mbplugin.ini [HttpServer]
# порт http сервера с отчетами
port = '19777'
# host '127.0.0.1' - доступ только локально, '0.0.0.0' - разрешить доступ к по сети
host = '127.0.0.1'
# формат вывода по умолчанию
table_format = 'PhoneNumber,Operator,UslugiOn,Balance,RealAverage,BalDelta,BalDeltaQuery,NoChangeDays,CalcTurnOff,SpendMin,SMS,Internet,Minutes,TarifPlan,BlockStatus' # ? UserName
# спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный
# 1 - показывать использованный трафик (usedByMe) по всем  или 0 - показывать оставшийся трафик (NonUsed) по всем
# список тел, через запятую - показать использованный только для этого списка телефонов
mts_usedbyme  = '0'
