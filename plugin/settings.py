# -*- coding: utf8 -*-
''' Файл с общими установками, распространяется с дистрибутивом
Значения по умолчанию, здесь ничего не меняем, если хотим поменять меняем в mbplugin.ini
подробное описание см в readme.md
'''
import os, sys, re, locale
UNIT = {'TB': 1073741824, 'ТБ': 1073741824, 'TByte': 1073741824, 'TBYTE': 1073741824,
        'GB': 1048576, 'ГБ': 1048576, 'GByte': 1048576, 'GBYTE': 1048576,
        'MB': 1024, 'МБ': 1024, 'MByte': 1024, 'MBYTE': 1024,
        'KB': 1, 'КБ': 1, 'KByte': 1, 'KBYTE': 1,
        'DAY': 30, 'DAYLY': 30, 'MONTH': 1,
        'day': 30, 'dayly': 30, 'month': 1,
        }

PHONE_INI_KEYS = ['Region', 'Monitor', 'Alias', 'Number', 'Password', 'mdOperation', 'mdConstant', 'PauseBeforeRequest', 'ShowInBallon', 'Password2', 'Indication', 'IndicColor', 'TrayShow', 'CalcAverageDays', 'IgnoreAutoRequest', 'IgnoreZerroIsError']
PHONE_INI_KEYS_LOWER = ['region', 'monitor', 'alias', 'number', 'password', 'mdoperation', 'mdconstant', 'pausebeforerequest', 'showinballon', 'password2', 'indication', 'indiccolor', 'trayshow', 'calcaveragedays', 'ignoreautorequest', 'ignorezerroiserror']

MODE_LIB = 'lib'
MODE_MB = 'mb'
mode = MODE_LIB
# папка, в которой лежит папка mblugin и по дефолту там будет ini, база и т.п.
mbplugin_root_path = None
# путь к mbplugin.ini по дефолту он находится в папке mbplugin_root_path
mbplugin_ini_path = None
logging_on = False

# имя ini файла
mbplugin_ini = 'mbplugin.ini'

# Кодировка для windows cp1251, для остальных utf-8
ini_codepage = locale.getpreferredencoding()
# Список открытых ключей для подписи файла контрольных сумм для проверки при обновлении из интернета
public_keys = [b'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFtD5e5dyS4dmHWLL1tx2ZfBoqCY5G72sRYllLvWMX0R sign-key-20210818']
# сюда пропишем сразу возможные варианты для пути хрома
chrome_executable_path_alternate = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    f'{os.environ.get("LOCALAPPDATA","")}\\Yandex\\YandexBrowser\\Application\\browser.exe',
    'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
    'C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
]
# Список параметров которые являются путями, для них при обращении в store.options делаем абсолютные пути
path_param = ['loggingfolder', 'loggingfilename', 'logginghttpfilename', 'storefolder', 'balance_html']
# Если для response не прокатывает user-agent то используем эту строчку, если в ini ничего не указано
default_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
########################################################################################
# type variants text, checkbox, select, list(of str)
ini = {
    'Options': {  # Раздел mbplugin.ini [Options]
        'autoupdate_': {'descr': 'Проверять и предлагать устанавливать новые версии', 'type': 'checkbox'},
        'autoupdate': '0',
        'ask_update_': {'descr': 'При обновлении не задавать вопрос', 'type': 'checkbox'},
        'ask_update': '1',
        # logging
        # Формат лога
        'loggingformat_': {'descr': 'Формат лога', 'type': 'text', 'size': 100},
        'loggingformat': u'[%(asctime)s] %(levelname)s %(funcName)s %(message)s',
        # папка для логов
        'loggingfolder_': {'descr': 'папка для логов', 'type': 'text', 'validate': lambda i: os.path.isdir(i)},
        'loggingfolder': os.path.join('mbplugin', 'log'),  # mbplugin\log
        # лог для ручного запуска и dll плагинов
        'loggingfilename_': {'descr': 'лог для ручного запуска и dll плагинов', 'type': 'text', 'validate': lambda i: os.path.isfile(i)},
        'loggingfilename': os.path.join('mbplugin', 'log', 'mbplugin.log'),  # mbplugin\log\mbplugin.log
        # лог http сервера и плагинов из него
        'logginghttpfilename_': {'descr': 'лог http сервера и плагинов из него', 'type': 'text', 'validate': lambda i: os.path.isfile(i)},
        'logginghttpfilename': os.path.join('mbplugin', 'log', 'http.log'),  # mbplugin\log\http.log
        # Уровень логирования
        'logginglevel_': {'descr': 'Уровень логирования', 'type': 'select', 'variants': 'DEBUG INFO WARNING ERROR CRITICAL'},
        'logginglevel': 'INFO',
        # Кидать логи в консоль (это дополнительный логгер), удобно для докера (чтобы работал docker log), при использовании с MobileBalance должно быть выключено
        'logconsole_': {'descr': 'Вести дополнительное логирование в консоль', 'type': 'checkbox'},
        'logconsole': '0',
        # Папка для хранения сессий
        'storefolder_': {'descr': 'Папка для хранения сессий', 'type': 'text', 'validate': lambda i: os.path.isdir(i)},
        'storefolder': os.path.join('mbplugin', 'store'),  # ..\store
        # Записывать результаты в sqlite БД
        'sqlitestore_': {'descr': 'Записывать результаты в sqlite БД', 'type': 'checkbox'},
        'sqlitestore': '0',
        # Размер кэша для sqlite движка, если база большая - есть смысл увеличить
        'sqlite_cache_size_': {'descr': 'Размер кэша для sqlite движка, 0 - оставить системное значение, если база большая - есть смысл увеличить, подробности https://www.sqlite.org/pragma.html#pragma_cache_size', 'type': 'text', 'validate': lambda i: re.match(r'^-?\d+$', str(i))},
        'sqlite_cache_size': '0',
        # Создавать файл html отчета, после получения данных
        'createhtmlreport_': {'descr': 'Создавать файл html отчета, после получения данных', 'type': 'checkbox'},
        'createhtmlreport': '0',
        # Создавать файл html отчета, после получения данных
        'htmlreportoperatorlink_': {'descr': 'В файле html отчета колонку псевдоним делать ссылкой на оператора', 'type': 'checkbox'},
        'htmlreportoperatorlink': '1',
        # Сколько раз повторно опрашивать балансы, которые опросились неудачно
        'retry_failed_': {'descr': 'Сколько раз повторно опрашивать балансы, которые опросились неудачно', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'retry_failed': '2',
        # задержка перед работой плагина
        'jitter_': {'descr': 'Сколько ждать перед началом работы плагина от n до m секунд, по умолчанию 1,1', 'type': 'text', 'validate': lambda i: re.match(r'^\d+,\d+$', str(i))},
        'jitter': '1,1',
        # Режим работы плагина, если плагин поддерживает разные варианты работы с личным кабинетом, режим можно выставить индивидуально в phones.ini/phones_add.ini
        'plugin_mode_': {'descr': 'Режим работы плагина, если плагин поддерживает разные варианты работы с личным кабинетом, режим можно выставить индивидуально в phones.ini/phones_add.ini', 'type': 'text'},
        'plugin_mode': 'DEFAULT',
        # путь к БД sqlite - TODO не используем, всегда ищем ее в папке с phones.ini
        # 'dbfilename_': {'descr': 'путь к БД sqlite', 'type': 'text', 'size': 100},
        # 'dbfilename': os.path.join('BalanceHistory.sqlite'), # BalanceHistory.sqlite
        # путь к html файлу, который создается после получения баланса
        'balance_html_': {'descr': 'путь к html файлу, который создается после получения баланса', 'type': 'text', 'size': 100, 'validate': lambda i: os.path.isfile(i)},
        'balance_html': os.path.join('balance.html'),  # balance.html
        # Обновлять SQLite базу данными из MDB
        'updatefrommdb_': {'descr': 'Обновлять SQLite базу данными из MDB', 'type': 'checkbox'},
        'updatefrommdb': 0,
        # Обновлять SQLite базу данными из MDB на сколько дней в глубину
        'updatefrommdbdeep_': {'descr': 'Обновлять SQLite базу данными из MDB на сколько дней в глубину', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'updatefrommdbdeep': 30,
        # показывать иконку web сервера в трее
        'show_tray_icon_': {'descr': 'показывать иконку web сервера в трее', 'type': 'checkbox'},
        'show_tray_icon': '1',
        # Пункт меню по умолчанию
        'tray_default_': {'descr': 'Номер пункта меню по умолчанию (c 1)', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'tray_default': '1',
        # Прокси сервер для работы хром плагинов http://user:pass@12.23.34.56:6789 для socks5 пишем socks5://...
        'browser_proxy_': {'descr': 'Прокси сервер для работы хром плагинов http://user:pass@12.23.34.56:6789 для socks5 пишем socks5://...', 'type': 'text'},
        'browser_proxy': '',
        # Прокси сервер для работы обычных плагинов http://user:pass@12.23.34.56:6789 для socks5 пишем socks5://...
        'requests_proxy_': {'descr': '''Прокси сервер для работы обычных плагинов либо пусто тогда пытается работать как есть, либо auto, тогда пытается подтянуть системные(срабатывает не всегда), либо в формате json {"http": "http://10.10.1.10:3128", "https": "http://10.10.1.10:1080"}''', 'type': 'text'},
        'requests_proxy': '',
        # показывать окно chrome если на странице найдена капча
        'show_captcha_': {'descr': 'Показывать окно chrome если на странице найдена капча', 'type': 'checkbox'},
        'show_captcha': '0',
        # максимальное время ожидания ввода капчи в секундах
        'max_wait_captcha_': {'descr': 'Максимальное время ожидания ввода капчи в секундах', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'max_wait_captcha': '180',
        # Показывать окна Chrome (при logginglevel=DEBUG всегда показывает), отключить можно только в windows, на линукс и mac всегда показывается
        # Этот режим был сделан из-за нестабильности работа headles chrome на puppeteer, кроме того он позволяет возвращать видимость браузера,
        # например для показа капчи.
        'show_chrome_': {'descr': 'Показывать окно chrome', 'type': 'checkbox'},
        'show_chrome': '0',
        # Пытаться спрятаться от скриптов определяющих что мы не человек, по умолчанию включено
        'playwright_stealth_': {'descr': 'Режим playwright stealth', 'type': 'checkbox'},
        'playwright_stealth': '1',
        # Режим Headless Прятать окна Chrome (при logginglevel=DEBUG всегда показывает)
        # Честный headless chrome режим, из этого режима вернуть окно в видимое нельзя
        'headless_chrome_': {'descr': 'Headless режим работы chrome', 'type': 'checkbox'},
        'headless_chrome': '1',
        # Если в linux не установлен GUI или в докере чтобы запустить браузер не в headless может потребоваться включить xvfb
        # В докере он уже установлен из коробки
        'xvfb_': {'descr': 'Включить xvfb', 'type': 'checkbox'},
        'xvfb': '0',
        # NODE_TLS_REJECT_UNAUTHORIZED=0 отключить проверку сертификатов при загрузке движков
        'node_tls_reject_unauthorized_': {'descr': 'Отключение проверки сертификатов при загрузке браузерных движков, не меняйте этот параметр без крайней необходимости', 'type': 'text'},
        'node_tls_reject_unauthorized': '',
        # PLAYWRIGHT_BROWSERS_PATH
        'playwright_browsers_path_': {'descr': 'Путь по которому находится папка с движками браузеров, по умолчанию в LOCALAPPDATA\\ms-playwright, не меняйте этот путь без крайней необходимости', 'type': 'text'},
        'playwright_browsers_path': '',
        # Использовать браузер встроенный в движок playwright, если отключен, то движки не скачиваются
        'use_builtin_browser_': {'descr': 'Использовать браузер встроенный в движок playwright', 'type': 'checkbox'},
        'use_builtin_browser': '1',
        # Какой браузерный движок используется для запросов
        'browsertype_': {'descr': 'Какой браузерный движок используется для запросов', 'type': 'select', 'variants': 'chromium firefox'},
        'browsertype': 'chromium',
        # user-agent Какой user_agent использовать
        'user_agent_': {'descr': 'Какой user_agent использовать, если не указан использовать тот что есть', 'type': 'text', 'size': 200},
        'user_agent': '',
        # wait_screenshot - Перед тем как сделать скриншот подождать n секунд чтобы он успел прогрузиться
        'wait_screenshot_': {'descr': 'Перед тем как сделать скриншот подождать n секунд чтобы он успел прогрузиться', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'wait_screenshot': '0',
        # playwright_pause - остановить браузер после получения данных
        'playwright_pause_': {'descr': 'остановить браузер после получения данных и включить отладку. ВНИМАНИЕ!!!. Это отладочная опция, ее включение останавливает получение балансов', 'type': 'checkbox'},
        'playwright_pause': '0',
        # login_pause - остановить браузер перед вводом пароля на N секунд, пока на экране форма ввода пароля
        'login_pause_': {'descr': 'пауза перед вводом пароля при работе браузера в секундах - будет полезна при проблемах с логоном', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'login_pause': '0',
        # Путь к хрому - можно прописать явно в ini, иначе поищет из вариантов chrome_executable_path_alternate
        'chrome_executable_path_': {'descr': 'Путь к хрому', 'type': 'text', 'size': 100, 'validate': lambda i: (i == '' or os.path.exists(i))},
        'chrome_executable_path': '',
        # Для плагинов через хром сохранять в папке логов полученные responses и скриншоты
        'log_responses_': {'descr': 'Сохранять в папке логов полученные данные за последний запрос', 'type': 'checkbox'},
        'log_responses': '1',
        # Для плагинов через хром не загружать стили шрифты и картинки, включать с осторожностью
        'intercept_request_': {'descr': 'Не загружать стили, шрифты и картинки', 'type': 'checkbox'},
        'intercept_request': '0',
        # Для плагинов через хром не обрезать вычисляемое выражение в логе
        'log_full_eval_string_': {'descr': 'Для плагинов через хром не обрезать вычисляемое выражение в логе', 'type': 'checkbox'},
        'log_full_eval_string': '0',
        # В каких единицах идет выдача по интернету (варианты - см UNIT в начале файла settings.py)
        'interunit_': {'descr': 'В каких единицах идет выдача по интернету', 'type': 'select', 'variants': 'TB GB MB KB'},
        'interunit': 'GB',
        # Что делать с полями balance и balance2. ничего/(поменять местами с balance)/(прибавить к балансу)
        'balances_': {'descr': 'Что делать с полем balances', 'type': 'select', 'variants': 'nochange swap add'},
        'balances': 'nochange',
        # Считать нулевой баланс ошибкой (если включен balances=swap то ошибка будет если нулевой Balance2)
        'null_is_error_': {'descr': 'Считать нулевой баланс ошибкой', 'type': 'checkbox'},
        'null_is_error': '0',
        # Слова, которые встречаются в названиях тарифов, про которые нужно выдать предупреждение и красить номер, нежелательные unwanted услуги
        'subscription_keyword_': {'descr': 'Признаки подписок, через запятую', 'type': 'text'},
        'subscription_keyword': '90 дней,TV Club,Услуга4,unwanted,нежелательная',
        # спецвариант по просьбе Mr. Silver в котором возвращаются не остаток интернета, а использованный
        # 1 - показывать использованный трафик (usedByMe) по всем  или 0 - показывать оставшийся трафик (NonUsed) по всем
        # список тел, через запятую - показать использованный только для этого списка телефонов
        'mts_usedbyme_': {
            'descr': 'По МТС возвращать использованный трафик вместо оставшегося 1 - показывать использованный по всем, 0 - показывать оставшийся по всем, num1,num2,num3 - показывать использованный только по этим номерам',
            'type': 'text',
            'validate': lambda i: (i in ('0', '1') or re.match(r'^(\d\d\d+,)*\d\d\d+$', i))},
        'mts_usedbyme': '0',
        # спецвариант по просьбе dimon_s2020 при 0 берет данные по счетчику максимальные из всех
        # 1 - Переданные клиентом (ЛКК)
        # 2 - Снятые сотрудниками Мосэнергосбыт (АИИС КУЭ)
        # 3 - Поступившее через портал городских услуг (ПГУ)
        'mosenergosbyt_nm_indication_take_': {'descr': 'Мосэнергосбыт: Какие данные по электросчетчику брать, 0 - взять максимальный', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'mosenergosbyt_nm_indication_take': '0',
        'mosenergosbyt_nm_indication_variants_': {'descr': 'Мосэнергосбыт: Для электросчетчика, какие варианты данных искать', 'type': 'text'},
        'mosenergosbyt_nm_indication_variants': '1:ЛКК,2:АИИС КУЭ,3:ПГУ',
        # Номер на который придет SMS при входе в ЛК теле2
        'tele2_sms_num_': {'descr': 'Номер на который придет SMS при логине в ЛК теле2 в формате 10 цифр, если не задан используется логин', 'type': 'text', 'validate': lambda i: (i.strip() == '' or i.isdigit() and len(i.strip()) == 10)},
        'tele2_sms_num': '',
        # Вести отдельный полный лог по стокам (stock.py)
        'stock_fulllog_': {'descr': 'Вести отдельный полный лог по стокам (stock.py)', 'type': 'checkbox'},
        'stock_fulllog': '0',
        # average_days - если нет в Options.ini Additional\AverageDays то возьмем отсюда
        # Количество дней для расчета среднего по истории
        'average_days_': {'descr': 'Количество дней для расчета среднего по истории', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'average_days': 30,
        # Порог, ниже которого выдается предупреждение о низком балансе
        'balancelessthen_': {'descr': 'Порог, ниже которого выдается предупреждение о низком балансе', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'balancelessthen': '2',
        # Порог дней, после которого выдается предупреждение о скором отключении.
        'turnofflessthen_': {'descr': 'Порог дней, посл которого выдается предупреждение о скором отключении.', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'turnofflessthen': '2',
        # В отчете будут показаны красным, если по номеру не было изменения более чем ... дней
        # Если данный параметр не выставлен индивидуально для номера в phones.ini
        'balancenotchangedmorethen_': {'descr': 'Красить номера, баланс по которым не менялся ... дней', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'balancenotchangedmorethen': '60',
        # В отчете будут показаны красным, если по номеру были изменения менее чем ... дней
        # Если данный параметр не выставлен индивидуально для номера в phones.ini
        # Полезно когда вы следите за балансом который не должен меняться и вдруг начал меняться
        'balancechangedlessthen_': {'descr': 'Красить номера, баланс по которым изменился менее чем .. дней назад', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'balancechangedlessthen': '0',
        # показывает в всплывающем окне историю на N дней назад. 0 - не показывает
        'realaveragedays_': {'descr': 'Показывать в всплывающем окне историю на N дней назад. 0 - не показывает', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'realaveragedays': '0',
        # показывает только последнее значение за день
        'showonlylastperday_': {'descr': 'Показывать только последнее значение за день', 'type': 'checkbox'},
        'showonlylastperday': '1',
        # Пропускает n дней в отчете, т.е. 0 - каждый день 1 - через день, и т.д.
        'skipday_': {'descr': 'Пропускает каждые n дней в отчете', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'skipday': '0',
        # Формат строк истории, можно выкинуть колонки, которые никогда не хотим видеть в истории
        # Пустые он сам выкинет
        'hoverhistoryformat_': {'descr': 'Формат строк истории', 'type': 'text', 'size': 200, 'validate': lambda i: re.match(r'^(\w+,)*\w+$', str(i))},
        'hoverhistoryformat': 'QueryDateTime,KreditLimit,Currenc,Balance,BalanceRUB,Balance2,Balance3,SpendBalance,UslugiOn,NoChangeDays,CalcTurnOff,Average,TurnOff,Recomend,SMS,SMS_USD,SMS_RUB,Minutes,USDRate,LicSchet,BalDelta,JeansExpired,ObPlat,BeeExpired,RealAverage,Seconds,MinSonet,MinLocal,MinAverage,MinDelta,MinDeltaQuery,TurnOffStr,SpendMin,PhoneReal,Internet,InternetUSD,InternetRUB,Contract,BalDeltaQuery,AnyString,BlockStatus,TarifPlan',
        # css для hover
        'hovercss_': {'descr': 'css для hover (всплывающего окна)', 'type': 'text', 'size': 200},
        'hovercss': 'display: block;position: fixed;top: 0; height: 100vh; overflow: auto',
        # Разрешение сохранять phone.ini из скриптов 0 - запрещено 1 - разрешено.
        'phone_ini_save_': {'descr': 'Пропускает каждые n дней в отчете', 'type': 'checkbox'},
        'phone_ini_save': '0',
        # формат для строки telegram bot из sqlite, т.к. индивидуальные параметры возможны только в Options перенесли этот параметр из раздела Telegram
        'tg_format_': {'descr': 'Формат для строки telegram bot из sqlite, задается либо списком через запятую, либо в tg HTML формате', 'type': 'text', 'size': 200},
        'tg_format': '<b>{Alias}</b>\t<code>{PhoneNumberFormat2}</code>\t<b>{Balance}</b>({BalDeltaQuery})',        
        # Разрешить изменения в конфиге через http сервер config edit (пока до конца не реализовано)
        # Внимание, при сохранении все параметры будут в нижнем регистре, комментарии будут сохранены
        'httpconfigedit_': {'descr': 'Включить редактор конфига', 'type': 'checkbox'},
        'httpconfigedit': '0',
        'httpconfigeditnolocalauth_': {'descr': 'Без авторизации при заходе локально', 'type': 'checkbox'},
        'httpconfigeditnolocalauth': '1',
        'httpconfigeditpassword_': {'descr': 'Пароль для входа в редактор, должен быть не пустой', 'type': 'text'},
        'httpconfigeditpassword': '',
        # Undo пока ручное - идем в архив и копаемся там
        'httpconfigeditundo_': {'descr': 'Сколько предыдущих версий ini сохранять для undo', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'httpconfigeditundo': '1000',
    },
    'Telegram': {  # Раздел mbplugin.ini [Telegram]
        'start_tgbot_': {'descr': 'Стартовать telegram bot вместе с http', 'type': 'checkbox'},
        'start_tgbot': 1,  # Стартовать telegram bot вместе с http
        # Прокси сервер для работы телеграм пустая строка - без прокси, auto - брать из настроек браузера,
        # Либо адрес https://user:pass@host:port либо socks5://user:pass@host:port
        'tg_proxy_': {'descr': 'Прокси сервер для работы телеграм пустая строка - без прокси, auto - брать из настроек браузера, либо адрес https://user:pass@host:port либо socks5://user:pass@host:port, по умолчанию без прокси', 'type': 'text'},
        'tg_proxy': '',  # По умолчанию без прокси
        'api_token_': {'descr': 'Токен для бота', 'type': 'text', 'size': 100},
        'api_token': '',  # токен для бота - прописывается в ini
        'auth_id_': {'descr': 'Список id пользователей, которые взаимодействовать с ТГ ботом', 'type': 'text', 'validate': lambda i: re.match(r'^((\d+,)*(\d)+)?$', str(i))},
        'auth_id': '',  # список id пользователей, которые авторизованы
        'send_balance_changes_': {'descr': 'Отправлять изменения баланса по sendtgbalance', 'type': 'checkbox'},
        'send_balance_changes': '1',  # отправлять изменения баланса по sendtgbalance (может приходится если мы не хотим получать полный список а фильтровать по подписке)
        'tg_from_': {'descr': 'Источник данных для ТГ бота', 'type': 'select', 'variants': 'mobilebalance sqlite'},
        'tg_from': 'sqlite',  # mobilebalance или sqlite
        'send_empty_': {'descr': 'Посылать сообщения если изменений не было', 'type': 'checkbox'},
        'send_empty': '1',  # посылать сообщения если изменений не было
        'showonlypaid_': {'descr': 'В детализации услуг в TG показывать только платные', 'type': 'checkbox'},
        'showonlypaid': '1',  # в детализации услуг в TG показывать только платные
        # формат для строки telegram bot из mobilebalance
        'tgmb_format_': {'descr': 'Формат для строки telegram bot из mobilebalance', 'type': 'text', 'size': 200},
        'tgmb_format': '<b>{Alias}</b>\t<code>{PhoneNum}</code>\t<b>{Balance}</b>({BalDeltaQuery})',
        'mobilebalance_http_': {'descr': 'Адрес web страницы mobilebalance (настройки\\WWW). На конце обязательно слэш', 'type': 'text', 'size': 100},
        'mobilebalance_http': 'http://localhost:19778/123456/',
        'command_menu_list_': {'descr': 'Список команд, которые отображаются в меню TG', 'type': 'text', 'size': 200},
        'command_menu_list': 'help,id,balance',
        'cmd_alias_': {'descr': 'Дополнительные команды для бота в формате alias:description:command', 'type': 'list', 'size': 200, 'validate': lambda i: re.match(r'^/?[A-Za-z0-9]+:[^:]*:/?\w+.*', i)},
        'cmd_alias': '',
    },
    'HttpServer': {  # Раздел mbplugin.ini [HttpServer]
        'start_http_': {'descr': 'Стартовать http сервер', 'type': 'checkbox'},
        'start_http': 1,  # Стартовать http сервер - это полный запрет на запуск http сервера
        'autostart_http_': {'descr': 'Записать http сервер в автозагрузку при установке', 'type': 'checkbox'},
        'autostart_http': 1,  # Стартовать http сервер при старте OS
        'port_': {'descr': 'Порт http сервера', 'type': 'text', 'validate': lambda i: i.isdigit()},
        'port': '19777',  # порт http сервера с отчетами
        # host '127.0.0.1' - доступ только локально, '0.0.0.0' - разрешить доступ к по сети
        'host_': {'descr': '127.0.0.1 - доступ только локально, 0.0.0.0 - разрешить доступ к веб-серверу по сети', 'type': 'select', 'variants': '127.0.0.1 0.0.0.0'},
        'host': '127.0.0.1',
        # формат вывода по умолчанию, для страницы http://localhost:19777/report
        # для форматирования номеров телефонов можно вместо PhoneNumber использовать
        # PhoneNumberFormat1 - (916) 111-2234 или
        # PhoneNumberFormat2 - (916)111-2234
        # Также можно сделать несколько альтернативных видов с разными наборами полей
        # они должны быть вида table_formatNNN где NNN произвольное число, которое не должно повторяться,
        # зайти на такие альтернативные report можно по ссылке http://localhost:19777/report/NNN
        'table_format_': {'descr': 'Формат вывода по умолчанию, для страницы http://localhost:19777/report', 'type': 'text', 'size': 200, 'validate': lambda i: re.match(r'^(\w+ *, *)*\w+$', str(i))},
        'table_format': 'PhoneNumber,Operator,UslugiOn,Balance,RealAverage,BalDelta,BalDeltaQuery,NoChangeDays,CalcTurnOff,SpendMin,SMS,Internet,Minutes,TarifPlan,BlockStatus,QueryDateTime',  # ? UserName
        # расписание опросов, строк может быть несколько scheduler= ... scheduler1=... и т.д как сделано с table_format
        # расписание имеет вид:
        # every(4).hour либо every().day.at("10:30")
        # при желании после расписания можно указать фильтры (можно несколько) например так
        # schedule = every(4).hour,mts,beeline
        # если фильтры не указаны, то опрос проводится по всем телефонам, для которых указан password2 в phones.ini либо в phones_add.ini
        # после изменения расписания необходим перезапуск сервера или команда util.py reload-schedule
        # функция валидации упрощена и обрабатывает только самые простые кейсы, в сложном расписании может выдавать ошибку хотя расписание будет правильным и будет работать
        # В таких случаях надо ориентироваться на расписание на странице http://localhost:19777/schedule - если оно там есть значит оно правильное
        'schedule_': {
            'descr': 'Расписание опросов', 'type': 'list', 'size': 200,
            'validate': lambda i: re.match(r'^every\(\d*\)(\.to\(\d+\))?\.(?:minutes?|hours?|days?|weeks?)(\.at\(.+\))?,(?:check|check_send|check_new_version|ping)(_once)?(,.*)?', i)
        },
        'schedule': '',

    },
}

# TODO Пока не придумал в каком видe держать операторские линки, оставлю пока здесь
# Пока вручную выгружаем и вставляем, список операторов не так часто меняется
# ./mbp recompile-plugin --skip-dll --skip-jsmblh --prepare-link
# можно выключить опцией htmlreportoperatorlink=0
operator_link = {
    'p_a1by': 'https://my.a1.by/work.html',
    'p_avtodor-tr': 'https://avtodor-tr.ru/account/login',
    'p_beeline': 'https://beeline.ru/login',
    'p_beeline_uz': 'https://beeline.uz/ru',
    'p_beget': 'https://api.beget.com',
    'p_cardtel': 'https://my.cardtel.ru/home',
    'p_chailand': 'https://chailand.ru/balance',
    'p_currency': 'https://cbr.ru/currency_base/daily',
    'p_east': 'https://debet.east.ru/lk',
    'p_lifeby': 'https://life.com.by/id',
    'p_lovit': 'https://lk.lovit.ru/login',
    'p_mangooffice': 'https://lk.mango-office.ru',
    'p_megafon': 'https://lk.megafon.ru/',
    'p_megafonb2b': 'https://b2blk.megafon.ru/dashboard',
    'p_mgts': 'https://auth.mgts.ru/login/b2c',
    'p_mosenergosbyt': 'https://my.mosenergosbyt.ru/auth',
    'p_mts': 'https://lk.mts.ru/',
    'p_ntvplus': 'https://service.ntvplus.ru/account/action/quick-check-action',
    'p_onlime': 'https://my.rt.ru',
    'p_rostelecom': 'https://lk.rt.ru',
    'p_sipnet': 'https://www.sipnet.ru/cabinet/index',
    'p_smile-net': 'https://lk.virginconnect.ru/login',
    'p_stock': 'https://finance.yahoo.com/quote',
    'p_strelka': 'http://strelkacard.ru',
    'p_tele2': 'https://msk.tele2.ru/lk',
    'p_test3': 'https://lk.saures.ru/dashboard',
    'p_test5_yota2': 'https://my.yota.ru/selfcare/devices',
    'p_uminet': 'https://lk.uminet.ru/',
    'p_vscale': 'https://vds.selectel.ru/panel/login/',
    'p_yoomoney': 'https://yoomoney.ru/actions',
    'p_yota': 'https://my.yota.ru/selfcare/devices',
    'p_zadarma': 'https://my.novofon.com/auth/'
}

header_html = '''<html>
<head><link rel="shortcut icon" href="/favicon.png" type="image/png"><title>MobileBalance</title><meta http-equiv="content-type" content="text/html; charset=windows-1251"></head>
<body>
<a class="hdr" href=/main>Перейти на главную</a><br>
'''

main_html = r'''<html>
<head><link rel="shortcut icon" href="/favicon.png" type="image/png"><title>MobileBalance</title><meta http-equiv="content-type" content="text/html; charset=windows-1251"></head>
<body>
%(info)s
<a href=/report>View report</a><br>
%(group_urls)s<br>
<button onclick="fetch('/getbalance_standalone').then(function(response) {return response})">Get balance request</button><br>
<br>
<a href=/schedule>View schedule</a><br>
<a href=/profile>View profile</a><br>
<div id=call_editor><a href=/editcfg>Edit config</a><br></div>
<a href=/log?lines=40>View log</a><br>
<a href=/log/list>View screenshot log</a><br>
<a href=/version_update>Version update</a><br>
<button onclick="fetch('/flushlog').then(function(response) {return response})">Flush log</button><br>
<button onclick="fetch('/reload_schedule').then(function(response) {return response})">Reload schedule</button><br>
<button onclick="fetch('/recompile').then(function(response) {return response})">Recompile jsmblh plugin</button><br>
<button onclick="fetch('/restart').then(function(response) {return response})">Restart web server</button><br>
<button onclick="fetch('/cancel').then(function(response) {return response})">Cancel the balance request</button><br>
<button onclick="fetch('/exit').then(function(response) {return response})">Exit web server</button><br>
<br>
<a href=https://github.com/artyl/mbplugin/blob/master/readme.md>Документация на github</a><br>
<br>
<b>Обратная связь.</b><br>
Оптимальный способ обратной связи - <a href=https://github.com/artyl/mbplugin/issues>оставить issue на github</a> (для создания issue нужно зарегистрироваться)<br>
Также обсуждение работы проходит в <a href=https://4pda.to/forum/index.php?showtopic=985296>форуме 4pda посвященном программе MobileBalance</a><br>
Или <a href=https://t.me/mbplugin>в канале телеграмм</a> также для личной связи и передачи непубличных данных есть <a href=https://t.me/artyl_mbplugin_bot>бот для связи с автором</a><br>
</body>
<script>
%(script)s
</script>
</html>
'''

table_template = {
    'page': '''<html>
<head><link rel="shortcut icon" href="/favicon.png" type="image/png"><title>MobileBalance</title><meta http-equiv="content-type" content="text/html; charset=windows-1251"></head>{style}
<body style="font-family: Verdana; cursor:default">
<table class="BackgroundTable">
<tr><td class="hdr">Информация о балансе телефонов - MobileBalance Mbplugin {title} (<a class="hdr" href=/main>Перейти на главную</a>)</td></tr>
<tr><td bgcolor="#808080">
<table class="InfoTable" border="0" cellpadding="2" cellspacing="1">
    <tr class="header">{html_header}</tr>
    {html_table}
</table>
</td></tr>
</table>
{html_script}
</body>
</html>''',
    'style': '''<style type="text/css">
.BackgroundTable, .InfoTable {font-family: Verdana; font-size:85%}
.HistoryBgTable, .HistoryTable {font-family: Verdana; font-size:100%}
th {background-color: #D1D1D1;}
th.order {cursor: pointer;}
td{white-space: nowrap;text-align: right;}
tr:hover {background-color: #ffff99;}
.hdr  {text-align:left;color:#FFFFFF; font-weight:bold; background-color:#0E3292; padding-left:5}
a.hdr { color: #FFFFFF}
.n    {background-color: #FFFFE1}
.e    {background-color: #FFEBEB}
.e_us {background-color: #FFEBEB; color: #FF0000}
.n_us {background-color: #FFFFE1; color: #808080}
.s_us {background-color: lightgreen; color: #808080}
.mark{color:#FF0000}
.mark_us{color:#FA6E6E}
.summ{background-color: lightgreen; color:black}
.p_n{color:#634276}
.p_r{color:#006400}
.p_b{color:#800000}
.hoverHistory {display: none;}
.item:hover .hoverHistory {{HoverCss}}
#Balance, #SpendBalance {text-align: right; font-weight:bold}
#Indication, #Alias, #KreditLimit, #PhoneDescr, #UserName, #PhoneNum, #PhoneNumber, #BalExpired, #LicSchet, #TarifPlan, #BlockStatus, #AnyString, #LastQueryTime{text-align: left}
</style>''',
    'history': '''
<table class="HistoryBgTable">
<tr><td class="hdr">{h_header}</td></tr>
<tr><td bgcolor="#808080">
<table class="HistoryTable" border="0" cellpadding="2" cellspacing="1">
    <tr class="header">{html_header}</tr>
    {html_table}
</table>
</td></tr>
</table>
''',
    'script': r'''<script>
  // take from https://stackoverflow.com/questions/14267781/sorting-html-table-with-javascript
  function table_sort() {
    const styleSheet = document.createElement('style')
    styleSheet.innerHTML = `
          .order-inactive span {visibility:hidden;}
          .order-inactive:hover span {visibility:visible;}
          .order-active span {visibility: visible;}
      `
    document.head.appendChild(styleSheet)
    document.querySelectorAll('th.order').forEach(th_elem => {
      let asc = true
      const span_elem = document.createElement('span')
      span_elem.style = "font-size:0.8rem; margin-left:0.5rem"
      span_elem.innerHTML = String.fromCharCode(9660) // down arrow
      th_elem.appendChild(span_elem)
      th_elem.classList.add('order-inactive')

      const index = Array.from(th_elem.parentNode.children).indexOf(th_elem)
      th_elem.addEventListener('click', (e) => {
        document.querySelectorAll('th.order').forEach(elem => {
          elem.classList.remove('order-active')
          elem.classList.add('order-inactive')
        })
        th_elem.classList.remove('order-inactive')
        th_elem.classList.add('order-active')

        if (!asc) {
          th_elem.querySelector('span').innerHTML = String.fromCharCode(9650) // up arrow
        } else {
          th_elem.querySelector('span').innerHTML = String.fromCharCode(9660) // down arrow
        }
        const arr = Array.from(th_elem.closest("table").querySelectorAll('tbody tr.order'))//.slice(1)
        arr.sort((a, b) => {
          a_val = a.children[index].innerText
          b_val = b.children[index].innerText
          if(a_val.match(/^\s*[-+]?([0-9]*[.])?[0-9]+$/g) && b_val.match(/^\s*[-+]?([0-9]*[.])?[0-9]+$/g)) {
            a_val = parseFloat(a_val)
            b_val = parseFloat(b_val)
            return (asc) ? b_val-a_val : a_val-b_val
          }
          return (asc) ? a_val.localeCompare(b_val) : b_val.localeCompare(a_val)
        })
        arr.forEach(elem => {
          th_elem.closest("table").querySelector("tbody").appendChild(elem)
        })
        asc = !asc
      })
    })
  }
  table_sort()
</script>
'''
}

editor_html = r'''<html>
<head>
    <title>Editor</title>
    <meta http-equiv="Content-Type" content="text/html; charset=cp1251">
    <div id=logon class=hidden>
        <form action='' method='POST' accept-charset='utf-8'>Пароль1
            <input type="password" text='Aaaaa' name="password"/>
            <input type="hidden" name="cmd" value="logon">
            <input type="submit" value='Logon2'>
        </form>
    </div>
    <div id=logout class=hidden>
        <form action='' method='POST'>
            <input type="submit" value='Logoff2'>
            <input type="hidden" name="cmd" value="logout">
        </form>
    </div>
    <p id=wrongPassword class=hidden>Wrong Password</p>
    <p id=buttonBlock class=hidden><Button onclick='show_default()'>Показать умолчания</Button>
        <Button onclick='hide_default()'>Скрыть умолчания</Button></p>
    <div id=formIni class=hidden></div>
    <style>
        body,p {
         margin: 0; /* Убираем отступы */
        }
        button {
            padding: 0;
        }
        p.default {
            color:gray;
        }
        p.default button{
            display:none;
        }
        p#wrongPassword{
            color:red;
        }
        .hidden{
            display: none;
        }
       </style>
</head>
<body>
    <script>
        inifile = JSON.parse('') // Сюда вставим JSON сгенерированный из ini
        function getCookie(name) {
            let matches = document.cookie.match(new RegExp(
                "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
            ));
            return matches ? decodeURIComponent(matches[1]) : undefined;
        }
        function SendPost(url, params, reload=false){
            var http = new XMLHttpRequest();
            http.open('POST', url, true);
            http.setRequestHeader('Content-type', 'application/json');
            http.onreadystatechange = function() {//Call a function when the state changes.
                if(http.readyState === 4){
                    if (http.status === 200) {
                        console.log(http.responseText);
                        if (http.responseText!='OK') {alert('Ошибка')}
                        if (reload==true) {document.location.reload(true)}
                    }else {
                    console.log("Error", http.readyState, http.status, http.statusText);
                    alert('Потеряна связь с сервером')
                    }
                }
            }
            http.send(params);
        }
        //TODO Надо решить как быть с параметрами по умолчанию как их показывать может сделать кнопку - очистить все что не отличается от умолчания ?
        function change(val){
            //val.parentElement.querySelector('button').classList.remove('default') // показываем кнопку default
            val.parentElement.classList.remove('default');

            inp = val
            console.log('id=',inp.dataset.id,' val=',inp.value)
            if(inp.type=='checkbox'){value=inp.checked?'1':'0'}
            else{value=inp.value}
            var params = JSON.stringify({ cmd: 'update', sec: inp.dataset.section, id: inp.dataset.id, type: inp.type, value: value });
            console.log(params)
            SendPost('editcfg', params, false)
        }
        function reset_to_default(val) {
            val.parentElement.classList.add('default');
            // set value to default on screen
            var inp = val.parentElement.children[0]
            if (inp.dataset.default_val !== null) {
                inp.value = inp.dataset.default_val
                if (inp.type == 'checkbox') {
                    inp.checked = (inp.dataset.default_val == '1')
                }
            }
            //val.classList.add('default');
            var params = JSON.stringify({ cmd: 'delete', sec: inp.dataset.section, id: inp.dataset.id, type: inp.type});
            console.log(params)
            SendPost('editcfg', params, false)
            // POST delete from ini
            // HIDE val.parentElement.removeChild(val);
        }
        function show_default(){
            document.querySelectorAll('p.default').forEach(function(item){item.style.display=''})
        }
        function hide_default(){
            document.querySelectorAll('p.default').forEach(function(item){item.style.display='none'})
        }
        function main(){
            console.log(12345)
            localAuthorized = false // init
            if(getCookie('auth')==undefined && !localAuthorized){
                document.getElementById("logon").classList.remove('hidden')
            } else {
                if(!localAuthorized) {
                    document.getElementById("logout").classList.remove('hidden')
                }
                document.getElementById("buttonBlock").classList.remove('hidden')
                document.getElementById("formIni").classList.remove('hidden')
            }
            if(getCookie('wrongpassword')!=undefined){
                document.getElementById("wrongPassword").classList.remove('hidden')
            }

            var section=''
            for(var key in inifile) {
                if(section!=inifile[key].section){
                    formIni.appendChild(document.createTextNode('['+(inifile[key].section)+']'));
                    section=inifile[key].section;
                }
                var newdiv = document.createElement("div");
                if(inifile[key].type=='select'){
                    var inp = document.createElement("select");
                    newdiv.appendChild(inp)
                    inifile[key].variants.split(' ').forEach(function(item, i, arr) {
                        var opt = document.createElement('option')
                        opt.text = item
                        inp.appendChild(opt)
                    })
                } else {
                    var inp = document.createElement("input");
                    if (inifile[key].type == 'text' && inifile[key].hasOwnProperty('size')) { inp.size = inifile[key]['size'] }
                    if (inifile[key].type == 'checkbox') { inp.checked = (inifile[key].value == '1') }
                }
                inp.value=inifile[key].value
                inp.id=inifile[key].id
                inp.type=inifile[key].type
                inp.dataset.section = inifile[key].section
                inp.dataset.id = inifile[key].id
                inp.dataset.default_val = inifile[key].default_val
                inp.oninput=function(){change(this)}
                var newtxt = document.createElement("p");
                newtxt.innerText = inifile[key].descr+' '+inifile[key].id+'='
                newtxt.appendChild(inp)
                newdiv.appendChild(newtxt);
                var newbtn = document.createElement("button");
                newbtn.appendChild(document.createTextNode("default"));
                newtxt.appendChild(newbtn);
                newbtn.onclick = function () {reset_to_default(this)};
                //newtxt.style.margin=0
                if(inifile[key].default == true){
                    newtxt.classList.add('default');
                    //newbtn.classList.add('default')
                } else {

                    //Hide ->default button
                }
                formIni.appendChild(newdiv)
                hide_default()
            }
        }
        main()
    </script>
</body>
</html>
'''
