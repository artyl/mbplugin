# -*- coding: utf8 -*-
''' Файл с общими установками, распространяется с дистрибутивом 
Значения по умолчанию, здесь ничего не меняем, если хотим поменять меняем в mbplugin.ini
подробное описание см в readme.md
'''
import os
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
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
        'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        f'{os.environ.get("LOCALAPPDATA","")}\\Yandex\\YandexBrowser\\Application\\browser.exe',
        'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
        'C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
        ]
########################################################################################
ini = {
    'Options': {  # Раздел mbplugin.ini [Options]
        # logging
        'loggingformat': u'[%(asctime)s] %(levelname)s %(funcName)s %(message)s',
        'loggingfolder': '..\\log',  # папка для логов
        'loggingfilename': '..\\log\\mbplugin.log',  # лог для ручного запуска и dll плагинов
        'logginghttpfilename': '..\\log\\http.log',  # лог http сервера и плагинов из него
        'logginglevel': 'INFO',  # Уровень логгирования Варианты: DEBUG INFO WARNING ERROR CRITICAL
        'storefolder': '..\\store',  # Папка для хранения сессий
        'sqlitestore': '0',  # Записывать результаты в sqlite БД 0 нет, 1 да Варианты: 1 0
        'createhtmlreport': '0',  # Создавать файлик html отчета, после получения данных Варианты: 1 0
        # путь к БД sqlite если нужно поменять - mbplugin.ini Option dbfilename
        'dbfilename': '..\\BalanceHistory.sqlite',
        # путь к html файлу, который создается после получения баланса
        'balance_html': '..\\DB\\balance.html',
        # Обновлять SQLite базу данными из MDB и на сколько дней в глубину
        'updatefrommdb': 0,
        # Обновлять SQLite базу данными из MDB и на сколько дней в глубину
        'updatefrommdbdeep': 30,
        # показывать иконку в трее - 1 прятать - 1, (по умолчанию 1)
        'show_tray_icon': '1',
        # Прокси сервер для работы хром плагинов http://user:pass@12.23.34.56:6789 для socks5 пишем socks5://...
        'proxy_server': '',
        # показывать окно chrome если на странице найдена капча
        'show_captcha': '0',
        # максимальное время ожидания ввода капчи в секундах
        'max_wait_captcha': '180',
        # Прятать окна Chrome (при logginglevel=DEBUG всегда показывает)
        'show_chrome': '0',
        # Путь к хрому - можно прописать явно в ini, иначе поищет из вариантов chrome_executable_path_alternate
        'chrome_executable_path': 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        # Для плагинов через хром сохранять в папке логов полученные responses 
        'log_responses': '0',
        # Для плагинов через хром не обрезать вычисляемое выражение в логе
        'log_full_eval_string': '0',
        # В каких единицах идет выдача по интернету (варианты - см UNIT в начале файла settings.py)
        'interUnit':'GB',  
        # спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный
        # 1 - показывать использованный трафик (usedByMe) по всем  или 0 - показывать оставшийся трафик (NonUsed) по всем
        # список тел, через запятую - показать использованный только для этого списка телефонов
        'mts_usedbyme': '0',
        # спецвариант по просьбе dimon_s2020 при 0 берет данные по счетчику максимальные из всех
        # 1 - Переданные клиентом (ЛКК)
        # 2 - Снятые сотрудниками Мосэнергосбыт (АИИС КУЭ)
        # 3 - Поступившее через портал городских услуг (ПГУ)
        'mosenergosbyt_nm_indication_take': '0',
        'mosenergosbyt_nm_indication_variants': '1:ЛКК,2:АИИС КУЭ,3:ПГУ',
        # Вести отдельный полный лог по стокам (stock.py)
        'stock_fulllog': '0',
        # average_days - если нет в Options.ini Additional\AverageDays то возьмем отсюда
        # Количество дней для расчета среднего по истории
        'average_days': 30,
        # Порог, ниже которого выдается предупреждение о низком балансе
        'BalanceLessThen': '2.5',
        # Порог дней, посл которого выдается предупреждение о скором отключении.
        'TurnOffLessThen': '2',
        # В отчете будут показаны красным, если по номеру не было изменения более чем ... дней
        # Если данный параметр не выставлен индивидуально для номера в phones.ini
        'BalanceNotChangedMoreThen': '60',        
        # В отчете будут показаны красным, если по номеру были изменения менее чем ... дней
        # Если данный параметр не выставлен индивидуально для номера в phones.ini
        # Полезно когда вы следите за балансом который не должен меняться и вдруг начал меняться
        'BalanceChangedLessThen': '0',
        # показывает в всплывающем окне историю на N дней назад. 0 - не показывает
        'RealAverageDays': '0',
        # показывает только последнее значение за день
        'ShowOnlyLastPerDay': '1',
        # Пропускает n дней в отчете, т.е. 0 - каждый день 1 - через день, и т.д.
        'SkipDay': '0',
        # Формат строк истории, можно выкинуть колонки, которые никогда не хотим видеть в истории
        # Пустые он сам выкинет
        'HoverHistoryFormat': 'QueryDateTime,KreditLimit,Currenc,Balance,BalanceRUB,Balance2,Balance3,SpendBalance,UslugiOn,NoChangeDays,CalcTurnOff,Average,TurnOff,Recomend,SMS,SMS_USD,SMS_RUB,Minutes,USDRate,LicSchet,BalDelta,JeansExpired,ObPlat,BeeExpired,RealAverage,Seconds,MinSonet,MinLocal,MinAverage,MinDelta,MinDeltaQuery,TurnOffStr,SpendMin,PhoneReal,Internet,InternetUSD,InternetRUB,Contract,BalDeltaQuery,AnyString,BlockStatus,TarifPlan',
        # css для hover
        'HoverCss': 'display: block;position: fixed;top: 0; height: 100vh; overflow: auto',
        # Разрешить изменения в конфиге через http сервер config edit (пока не реализовано)
        # Внимание, при сохранении все параметры будут в нижнем регистре а коментарии будут удалены
        'HttpConfigEdit': '0',
    },
    'Telegram': {  # Раздел mbplugin.ini [Telegram]
        'start_tgbot': 1,  # Стартовать telegram bot вместе с http
        # Прокси сервер для работы телеграм пустая строка - без прокси, auto - брать из настроек браузера, 
        # Либо адрес https://user:pass@host:port либо socks5://user:pass@host:port
        'tg_proxy': '',  # По умолчанию без прокси
        'api_token': '',  # токен для бота - прописывается в ini
        'auth_id': '',  # список id пользователей, которые получают баланс
        'send_balance_changes': '1',  # отправлять изменения баланса по sendtgbalance (может приходится если мы не хотим получать полняй список а фильтровать по подписке)
        # формат для строки telegram bot из sqlite
        'tg_format': '<b>{Alias}</b>\t<code>{PhoneNumberFormat2}</code>\t<b>{Balance}</b>({BalDeltaQuery})',
        'tg_from': 'sqlite',  # mobilebalance или sqlite
        'send_empty': '1',  # посылать сообщения если изменений не было
        'ShowOnlyPaid': '1',  # в детализации услуг в TG показывать только платные
        # формат для строки telegram bot из mobilebalance
        'tgmb_format': '<b>{Alias}</b>\t<code>{PhoneNum}</code>\t<b>{Balance}</b>({BalDeltaQuery})',
        'mobilebalance_http': 'http://localhost:19778/123456/',
    },
    'HttpServer': {  # Раздел mbplugin.ini [HttpServer]
        'start_http': 1,  # Стартовать http сервер
        'port': '19777',  # порт http сервера с отчетами
        # host '127.0.0.1' - доступ только локально, '0.0.0.0' - разрешить доступ к по сети
        'host': '127.0.0.1',
        # формат вывода по умолчанию, для страницы http://localhost:19777/report
        # для форматирования номеров телефонов можно вместо PhoneNumber использовать 
        # PhoneNumberFormat1 - (916) 111-2234 или 
        # PhoneNumberFormat2 - (916)111-2234
        # Также можно сделать несколько альтернативных видов с разными наборами полей 
        # они должны быть вида table_formatNNN где NNN произвольное число, которое не должно повторяться, 
        # зайти на такие альтернативные report можно по ссылке http://localhost:19777/report/NNN
        'table_format': 'PhoneNumber,Operator,UslugiOn,Balance,RealAverage,BalDelta,BalDeltaQuery,NoChangeDays,CalcTurnOff,SpendMin,SMS,Internet,Minutes,TarifPlan,BlockStatus,QueryDateTime',  # ? UserName
    },
}
