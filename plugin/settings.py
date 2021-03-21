# -*- coding: utf8 -*-
''' Файл с общими установками, распространяется с дистрибутивом 
Значения по умолчанию, здесь ничего не меняем, если хотим поменять меняем в mbplugin.ini
подробное описание см в readme.md
'''
import os
UNIT = {'TB': 1073741824, 'ТБ': 1073741824, 'TByte': 1073741824, 'TBYTE': 1073741824,
        'GB': 1048576, 'ГБ': 1048576, 'GByte': 1048576, 'GBYTE': 1048576,
        'MB': 1024, 'МБ': 1024, 'MByte': 1024, 'MBYTE': 1024,
        'KB': 1, 'КБ': 1, 'KByte': 1, 'KBYTE': 1,
        'DAY': 30, 'DAYLY': 30, 'MONTH':1,
        'day': 30, 'dayly': 30, 'month':1,}

# имя ini файла
mbplugin_ini = 'mbplugin.ini'
# полный путь к корню где лежат ini файлы и база (пока используется в только в тестах)
mbplugin_root_path = ''

# сюда пропишем сразу возможные варианты для путя хрома
chrome_executable_path_alternate = [
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
        'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        f'{os.environ.get("LOCALAPPDATA","")}\\Yandex\\YandexBrowser\\Application\\browser.exe',
        'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
        'C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
        ]
########################################################################################
ini = {
    'MobileBalance': {
        'path_': {'descr':'Путь к папке с MobileBalance', 'type':'text', 'size':100, 'validate':lambda i:os.path.isdir(i)},
    },
    'Options': {  # Раздел mbplugin.ini [Options]
        # logging
        # Формат лога
        'loggingformat_': {'descr':'Формат лога', 'type':'text', 'size':100},
        'loggingformat': u'[%(asctime)s] %(levelname)s %(funcName)s %(message)s',
        # папка для логов
        'loggingfolder_': {'descr': 'папка для логов', 'type':'text', 'validate':lambda i:os.path.isdir(i)},
        'loggingfolder': '..\\log',
        # лог для ручного запуска и dll плагинов
        'loggingfilename_': {'descr':'лог для ручного запуска и dll плагинов', 'type':'text'},
        'loggingfilename': '..\\log\\mbplugin.log',
        # лог http сервера и плагинов из него
        'logginghttpfilename_': {'descr':'лог http сервера и плагинов из него', 'type':'text'},
        'logginghttpfilename': '..\\log\\http.log',
        # Уровень логгирования
        'logginglevel_': {'descr':'Уровень логгирования', 'type':'select', 'variants':'DEBUG INFO WARNING ERROR CRITICAL'},
        'logginglevel': 'INFO',
        # Папка для хранения сессий
        'storefolder_': {'descr':'Папка для хранения сессий', 'type':'text'},
        'storefolder': '..\\store',
        # Записывать результаты в sqlite БД
        'sqlitestore_': {'descr':'Записывать результаты в sqlite БД', 'type':'checkbox'},
        'sqlitestore': '0',
        # Создавать файлик html отчета, после получения данных
        'createhtmlreport_': {'descr':'Создавать файлик html отчета, после получения данных', 'type':'checkbox'},
        'createhtmlreport': '0',
        # путь к БД sqlite
        'dbfilename_': {'descr':'путь к БД sqlite', 'type':'text', 'size':100},
        'dbfilename': '..\\BalanceHistory.sqlite',
        # путь к html файлу, который создается после получения баланса
        'balance_html_': {'descr':'путь к html файлу, который создается после получения баланса', 'type':'text', 'size':100},
        'balance_html': '..\\DB\\balance.html',
        # Обновлять SQLite базу данными из MDB
        'updatefrommdb_': {'descr':'Обновлять SQLite базу данными из MDB', 'type':'checkbox'},
        'updatefrommdb': 0,
        # Обновлять SQLite базу данными из MDB на сколько дней в глубину
        'updatefrommdbdeep_': {'descr':'Обновлять SQLite базу данными из MDB на сколько дней в глубину', 'type':'text'},
        'updatefrommdbdeep': 30,
        # показывать иконку web сервера в трее
        'show_tray_icon_': {'descr':'показывать иконку web сервера в трее', 'type':'text'},
        'show_tray_icon': '1',
        # Прокси сервер для работы хром плагинов http://user:pass@12.23.34.56:6789 для socks5 пишем socks5://...
        'proxy_server_': {'descr':'Прокси сервер для работы хром плагинов http://user:pass@12.23.34.56:6789 для socks5 пишем socks5://...', 'type':'text'},
        'proxy_server': '',
        # показывать окно chrome если на странице найдена капча
        'show_captcha_': {'descr':'Показывать окно chrome если на странице найдена капча', 'type':'checkbox'},
        'show_captcha': '0',
        # максимальное время ожидания ввода капчи в секундах
        'max_wait_captcha_': {'descr':'Максимальное время ожидания ввода капчи в секундах', 'type':'text', 'validate':lambda i:i.isdigit()},
        'max_wait_captcha': '180',
        # Прятать окна Chrome (при logginglevel=DEBUG всегда показывает)
        'show_chrome_': {'descr':'Показывать окно crome', 'type':'checkbox'},
        'show_chrome': '0',
        # Путь к хрому - можно прописать явно в ini, иначе поищет из вариантов chrome_executable_path_alternate
        'chrome_executable_path_': {'descr':'Путь к хрому', 'type':'text', 'size':100, 'validate':lambda i:os.path.exists(i)},
        'chrome_executable_path': 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        # Для плагинов через хром сохранять в папке логов полученные responses 
        'log_responses_': {'descr':'Сохранять в папке логов полученные данные за последний запрос', 'type':'checkbox'},
        'log_responses': '0',
        # Для плагинов через хром не обрезать вычисляемое выражение в логе
        'log_full_eval_string_': {'descr':'Для плагинов через хром не обрезать вычисляемое выражение в логе', 'type':'checkbox'},
        'log_full_eval_string': '0',
        # В каких единицах идет выдача по интернету (варианты - см UNIT в начале файла settings.py)
        'interunit_': {'descr': 'В каких единицах идет выдача по интернету', 'type': 'select', 'variants': 'TB GB MB KB'},
        'interunit':'GB',  
        # спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный
        # 1 - показывать использованный трафик (usedByMe) по всем  или 0 - показывать оставшийся трафик (NonUsed) по всем
        # список тел, через запятую - показать использованный только для этого списка телефонов
        'mts_usedbyme_': {'descr':'По МТС возвращать использованный трафик вместо оставшегося', 'type':'checkbox'},
        'mts_usedbyme': '0',
        # спецвариант по просьбе dimon_s2020 при 0 берет данные по счетчику максимальные из всех
        # 1 - Переданные клиентом (ЛКК)
        # 2 - Снятые сотрудниками Мосэнергосбыт (АИИС КУЭ)
        # 3 - Поступившее через портал городских услуг (ПГУ)
        'mosenergosbyt_nm_indication_take_': {'descr':'Мосэнергосбыт: Какие данные по электросчетчику брать, 0 - взять максимальный', 'type':'text', 'validate':lambda i:i.isdigit()},
        'mosenergosbyt_nm_indication_take': '0',
        'mosenergosbyt_nm_indication_variants_': {'descr':'Мосэнергосбыт: Для электросчетчика, какие варианты данных искать', 'type':'text'},
        'mosenergosbyt_nm_indication_variants': '1:ЛКК,2:АИИС КУЭ,3:ПГУ',
        # Вести отдельный полный лог по стокам (stock.py)
        'stock_fulllog_': {'descr':'Вести отдельный полный лог по стокам (stock.py)', 'type':'checkbox'},
        'stock_fulllog': '0',
        # average_days - если нет в Options.ini Additional\AverageDays то возьмем отсюда
        # Количество дней для расчета среднего по истории
        'average_days_': {'descr':'Количество дней для расчета среднего по истории', 'type':'text', 'validate':lambda i:i.isdigit()},
        'average_days': 30,
        # Порог, ниже которого выдается предупреждение о низком балансе
        'balancelessthen_': {'descr':'Порог, ниже которого выдается предупреждение о низком балансе', 'type':'text', 'validate':lambda i:i.isdigit()},
        'balancelessthen': '2',
        # Порог дней, посл которого выдается предупреждение о скором отключении.
        'turnofflessthen_': {'descr':'Порог дней, посл которого выдается предупреждение о скором отключении.', 'type':'text', 'validate':lambda i:i.isdigit()},
        'turnofflessthen': '2',
        # В отчете будут показаны красным, если по номеру не было изменения более чем ... дней
        # Если данный параметр не выставлен индивидуально для номера в phones.ini
        'balancenotchangedmorethen_': {'descr':'Красить номера, бананс по которым не менялся ... дней', 'type':'text', 'validate':lambda i:i.isdigit()},
        'balancenotchangedmorethen': '60',
        # В отчете будут показаны красным, если по номеру были изменения менее чем ... дней
        # Если данный параметр не выставлен индивидуально для номера в phones.ini
        # Полезно когда вы следите за балансом который не должен меняться и вдруг начал меняться
        'balancechangedlessthen_': {'descr':'Красить номера, бананс по меньше чем', 'type':'text', 'validate':lambda i:i.isdigit()},
        'balancechangedlessthen': '0',
        # показывает в всплывающем окне историю на N дней назад. 0 - не показывает
        'realaveragedays_': {'descr':'Показывать в всплывающем окне историю на N дней назад. 0 - не показывает', 'type':'text', 'validate':lambda i:i.isdigit()},
        'realaveragedays': '0',
        # показывает только последнее значение за день
        'showonlylastperday_': {'descr':'Показывать только последнее значение за день', 'type':'checkbox'},
        'showonlylastperday': '1',
        # Пропускает n дней в отчете, т.е. 0 - каждый день 1 - через день, и т.д.
        'skipday_': {'descr':'Пропускает каждые n дней в отчете', 'type':'text', 'validate':lambda i:i.isdigit()},
        'skipday': '0',
        # Формат строк истории, можно выкинуть колонки, которые никогда не хотим видеть в истории
        # Пустые он сам выкинет
        'hoverhistoryformat_': {'descr':'Формат строк истории', 'type':'text', 'size':200},
        'hoverhistoryformat': 'QueryDateTime,KreditLimit,Currenc,Balance,BalanceRUB,Balance2,Balance3,SpendBalance,UslugiOn,NoChangeDays,CalcTurnOff,Average,TurnOff,Recomend,SMS,SMS_USD,SMS_RUB,Minutes,USDRate,LicSchet,BalDelta,JeansExpired,ObPlat,BeeExpired,RealAverage,Seconds,MinSonet,MinLocal,MinAverage,MinDelta,MinDeltaQuery,TurnOffStr,SpendMin,PhoneReal,Internet,InternetUSD,InternetRUB,Contract,BalDeltaQuery,AnyString,BlockStatus,TarifPlan',
        # css для hover
        'hovercss_': {'descr':'css для hover (всплывающего окна)', 'type':'text', 'size':200},
        'hovercss': 'display: block;position: fixed;top: 0; height: 100vh; overflow: auto',
        # Разрешить изменения в конфиге через http сервер config edit (пока до конца не реализовано)
        # Внимание, при сохранении все параметры будут в нижнем регистре а коментарии будут удалены
        'httpconfigedit_': {'descr':'Включить редактор конфига', 'type':'checkbox'},
        'httpconfigedit': '0',
    },
    'Telegram': {  # Раздел mbplugin.ini [Telegram]
        'start_tgbot_': {'descr':'Стартовать telegram bot вместе с http', 'type':'checkbox'},
        'start_tgbot': 1,  # Стартовать telegram bot вместе с http
        # Прокси сервер для работы телеграм пустая строка - без прокси, auto - брать из настроек браузера, 
        # Либо адрес https://user:pass@host:port либо socks5://user:pass@host:port
        'tg_proxy_': {'descr':'Прокси сервер для работы телеграм пустая строка - без прокси, auto - брать из настроек браузера, либо адрес https://user:pass@host:port либо socks5://user:pass@host:port, по умолчанию без прокси', 'type':'text'},
        'tg_proxy': '',  # По умолчанию без прокси
        'api_token_': {'descr':'Токен для бота', 'type':'text', 'size':100},
        'api_token': '',  # токен для бота - прописывается в ini
        'auth_id_': {'descr':'Список id пользователей, которые взаимодействовать с ТГ ботом', 'type':'text'},
        'auth_id': '',  # список id пользователей, которые авторизованы
        'send_balance_changes_': {'descr':'Отправлять изменения баланса по sendtgbalance', 'type':'checkbox'},
        'send_balance_changes': '1',  # отправлять изменения баланса по sendtgbalance (может приходится если мы не хотим получать полняй список а фильтровать по подписке)
        # формат для строки telegram bot из sqlite
        'tg_format_': {'descr':'Формат для строки telegram bot из sqlite', 'type':'text', 'size':200},
        'tg_format': '<b>{Alias}</b>\t<code>{PhoneNumberFormat2}</code>\t<b>{Balance}</b>({BalDeltaQuery})',
        'tg_from_': {'descr':'Источник данных для ТГ бота', 'type':'select', 'variants': 'mobilebalance sqlite'},
        'tg_from': 'sqlite',  # mobilebalance или sqlite
        'send_empty_': {'descr':'Посылать сообщения если изменений не было', 'type':'checkbox'},
        'send_empty': '1',  # посылать сообщения если изменений не было
        'showonlypaid_': {'descr':'В детализации услуг в TG показывать только платные', 'type':'checkbox'},
        'showonlypaid': '1',  # в детализации услуг в TG показывать только платные
        # формат для строки telegram bot из mobilebalance
        'tgmb_format_': {'descr':'Формат для строки telegram bot из mobilebalance', 'type':'text', 'size':200},
        'tgmb_format': '<b>{Alias}</b>\t<code>{PhoneNum}</code>\t<b>{Balance}</b>({BalDeltaQuery})',
        'mobilebalance_http_': {'descr':'Адрес web страницы mobilebalance (настройки\WWW). На конце обязательно слэш', 'type':'text', 'size':100},
        'mobilebalance_http': 'http://localhost:19778/123456/',
    },
    'HttpServer': {  # Раздел mbplugin.ini [HttpServer]
        'start_http_': {'descr':'Стартовать http сервер', 'type':'checkbox'},
        'start_http': 1,  # Стартовать http сервер
        'port_': {'descr':'Порт http сервера', 'type':'text'},
        'port': '19777',  # порт http сервера с отчетами
        # host '127.0.0.1' - доступ только локально, '0.0.0.0' - разрешить доступ к по сети
        'host_': {'descr':'127.0.0.1 - доступ только локально, 0.0.0.0 - разрешить доступ к веб серверу по сети', 'type':'select', 'variants': '127.0.0.1 0.0.0.0'},
        'host': '127.0.0.1',
        # формат вывода по умолчанию, для страницы http://localhost:19777/report
        # для форматирования номеров телефонов можно вместо PhoneNumber использовать 
        # PhoneNumberFormat1 - (916) 111-2234 или 
        # PhoneNumberFormat2 - (916)111-2234
        # Также можно сделать несколько альтернативных видов с разными наборами полей 
        # они должны быть вида table_formatNNN где NNN произвольное число, которое не должно повторяться, 
        # зайти на такие альтернативные report можно по ссылке http://localhost:19777/report/NNN
        'table_format_': {'descr':'Формат вывода по умолчанию, для страницы http://localhost:19777/report', 'size':200},
        'table_format': 'PhoneNumber,Operator,UslugiOn,Balance,RealAverage,BalDelta,BalDeltaQuery,NoChangeDays,CalcTurnOff,SpendMin,SMS,Internet,Minutes,TarifPlan,BlockStatus,QueryDateTime',  # ? UserName
    },
}
