# -*- coding: utf8 -*-
''' Автор ArtyLa
Модуль для работы с базами
Для интеграции с базой MDB необходимо установить 32битный ODBC драйвер для MDB AccessDatabaseEngine.exe:
Скачать можно отсюда:
https://www.microsoft.com/en-us/download/details.aspx?id=13255
Объяснение, почему не 32 битный python не работает с 64 битным ODBC и наоборот
https://stackoverflow.com/questions/45362440/32bit-pyodbc-for-32bit-python-3-6-works-with-microsofts-64-bit-odbc-driver-w
set up some constants

'''
import time, os, sys, re, logging, traceback, sqlite3, datetime, json
import settings, store

DB_SCHEMA = ['''
CREATE TABLE IF NOT EXISTS Phones (
    NN INTEGER NOT NULL DEFAULT NULL PRIMARY KEY AUTOINCREMENT,
    [PhoneNumber] [nvarchar] (150), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [MBPhoneNumber] [nvarchar] (150), -- COLLATE Cyrillic_General_CI_AS NULL ,
    Operator [nchar] (50), -- plugin name
    QueryDateTime timestamp DEFAULT NULL,
    SpendBalance [float] NULL ,
    KreditLimit [float] NULL ,
    UslugiOn [nchar] (50), -- COLLATE Cyrillic_General_CI_AS NULL ,
    Currenc [nchar] (10), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [Balance] [float] NULL ,
    [Balance2] [float] NULL ,
    [Balance3] [float] NULL ,
    [Average] [real] NULL ,
    [TurnOff] [smallint] NULL ,
    [Recomend] [real] NULL ,
    [SMS] [smallint] NULL ,
    [Minutes] [smallint] NULL ,
    [USDRate] [real] NULL ,
    [LicSchet] [nchar] (20), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [UserName] [nchar] (50), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [BalDelta] [real] NULL ,
    [JeansExpired] [smallint] NULL ,
    [ObPlat] [real] NULL ,
    [BeeExpired] [nchar] (20), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [RealAverage] [real] NULL ,
    [Seconds] [smallint] NULL ,
    [TarifPlan] [nchar] (50), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [BlockStatus] [nchar] (50), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [MinSonet] [real] NULL ,
    [MinLocal] [real] NULL ,
    [Internet] [real] NULL ,
    [TurnOffStr] [nchar] (30), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [SpendMin] [real] NULL ,
    [PhoneReal] [nchar] (20), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [BalanceRUB] [real] NULL ,
    [SMS_USD] [real] NULL ,
    [SMS_RUB] [real] NULL ,
    [InternetUSD] [real] NULL ,
    [InternetRUB] [real] NULL ,
    [Contract] [nchar] (20), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [MinAverage] [real] NULL ,
    [BalDeltaQuery] [real] NULL ,
    [MinDelta] [real] NULL ,
    [MinDeltaQuery] [real] NULL ,
    [NoChangeDays] [int] NULL ,
    [AnyString] [nchar] (250), -- COLLATE Cyrillic_General_CI_AS NULL ,
    [CalcTurnOff] [int] NULL
);''','''
CREATE TABLE IF NOT EXISTS Flags (
    [key] [nvarchar] (150) PRIMARY KEY, 
    [value] [nvarchar] (150) NULL
);''','''
CREATE TABLE IF NOT EXISTS Responses (
    [key] [nvarchar] (150) PRIMARY KEY, 
    [value] [nvarchar] (10000) NULL
)
-- CREATE INDEX idx_PhoneNumber_Operator ON Phones (PhoneNumber,Operator);
-- CREATE INDEX idx_QueryDateTime ON Phones (QueryDateTime);
''']
PhonesHText = {
    'NN': 'NN',
    'Alias': 'Псевдоним',
    'PhoneNumber': 'Номер',
    'PhoneNumberFormat1': 'Номер',
    'PhoneNumberFormat2': 'Номер',
    'MBPhoneNumber': 'Номер как в MB',
    'Operator': 'Оператор',
    'QueryDateTime': 'Время запроса',
    'SpendBalance': 'SpendBalance',
    'KreditLimit': 'Кр. лимит',
    'UslugiOn': 'Услуги',
    'Currenc': 'Валюта',
    'Balance': 'Баланс',
    'Balance2': 'Баланс2',
    'Balance3': 'Баланс3',
    'Average': 'Average',
    'TurnOff': 'TurnOff',
    'Recomend': 'Recomend',
    'SMS': 'SMS',
    'Minutes': 'Минут',
    'USDRate': 'USDRate',
    'LicSchet': 'Л.счет',
    'UserName': 'ФИО',
    'BalDelta': 'Delta (день)',
    'JeansExpired': 'JeansExpired',
    'ObPlat': 'ObPlat',
    'BeeExpired': 'BeeExpired',
    'RealAverage': '$/День(Р)',
    'Seconds': 'Секунд',
    'TarifPlan': 'Тариф. план',
    'BlockStatus': 'Статус блок.',
    'MinSonet': 'MinSonet',
    'MinLocal': 'MinLocal',
    'Internet': 'Инт.трафик',
    'TurnOffStr': 'TurnOffStr',
    'SpendMin': 'SpendMin',
    'PhoneReal': 'PhoneReal',
    'BalanceRUB': 'BalanceRUB',
    'SMS_USD': 'SMS_USD',
    'SMS_RUB': 'SMS_RUB',
    'InternetUSD': 'InternetUSD',
    'InternetRUB': 'InternetRUB',
    'Contract': 'Contract',
    'MinAverage': 'Мин/день ср',
    'BalDeltaQuery': 'Delta (запрос)',
    'MinDelta': 'Мин/день',
    'MinDeltaQuery': 'Мин Delta (запрос)',
    'NoChangeDays': 'Дней без изм.',
    'AnyString': 'AnyString',
    'CalcTurnOff': 'Откл (Р)',
}

addition_phone_fields = {'MBPhoneNumber': '[nvarchar] (150)'}
addition_indexes = ['idx_QueryDateTime ON Phones (QueryDateTime ASC)',
                    'idx_Phonenumber ON Phones (PhoneNumber)',
                    'idx_MBPhonenumber ON Phones (MBPhoneNumber)']
addition_queries = [
    "delete from phones where phonenumber like 'p_%' or operator='p_test1' or (phonenumber='tinkoff' and operator='???') or operator in ('#01','#02')"]


class dbengine():
    def __init__(self, dbname=None, updatescheme=True, fast=False):
        'fast - быстрее, но менее безопасно'
        if dbname is None:
            dbname = store.abspath_join(settings.mbplugin_ini_path, 'BalanceHistory.sqlite')
        self.dbname = dbname
        self.conn = sqlite3.connect(self.dbname)  # detect_types=sqlite3.PARSE_DECLTYPES
        self.cur = self.conn.cursor()
        if fast:
            self.cur.execute('PRAGMA synchronous = OFF')
            self.conn.commit()
        if updatescheme:
            self.check_and_add_addition()
        rows = self.cur.execute('SELECT * FROM phones limit 1;')
        self.phoneheader = list(zip(*rows.description))[0]

    def write_result(self, plugin, login, result, commit=True):
        'Записывает результат в базу'
        # Делаем копию, чтобы не трогать оригинал
        result2 = {k: v for k, v in result.items()}
        # Исправляем поля которые в response называются не так как в базе
        if type(result2['Balance']) == str:
            result2['Balance'] = float(result2['Balance'])
        if 'Currency' in result2:  # Currency -> Currenc
            result2['Currenc'] = result2['Currency']
        if 'Min' in result2:  # Min -> Minutes
            result2['Minutes'] = result2['Min']
        if 'BalExpired' in result2:  # BalExpired -> BeeExpired
            result2['BeeExpired'] = result2['BalExpired']
        # Фильтруем только те поля, которые есть в таблице phone
        line = {k: v for k, v in result2.items() if k in self.phoneheader}
        # Добавляем расчетные поля и т.п.
        line['Operator'] = plugin
        line['PhoneNumber'] = login  # PhoneNumber=PhoneNum
        line['QueryDateTime'] = datetime.datetime.now().replace(microsecond=0)  # no microsecond
        self.cur.execute(f"select cast(julianday('now')-julianday(max(QueryDateTime)) as integer) from phones where phonenumber='{login}' and operator='{plugin}' and abs(balance-({result['Balance']}))>0.02")
        line['NoChangeDays'] = self.cur.fetchall()[0][0]  # Дней без изм.
        try:        
            options_ini = store.ini('Options.ini').read()
            average_days = int(options_ini['Additional']['AverageDays'])
        except Exception:
            average_days = int(store.options('average_days'))
        self.cur.execute(f"select {line['Balance']}-balance from phones where phonenumber='{login}' and operator='{plugin}' and QueryDateTime>date('now','-{average_days} day') and strftime('%Y%m%d', QueryDateTime)<>strftime('%Y%m%d', date('now')) order by QueryDateTime desc limit 1")
        qres = self.cur.fetchall()
        if qres != []:
            line['BalDelta'] = round(qres[0][0], 2)  # Delta (день)
        self.cur.execute(f"select {line['Balance']}-balance from phones where phonenumber='{login}' and operator='{plugin}' order by QueryDateTime desc limit 1")
        qres = self.cur.fetchall()
        if qres != []:
            line['BalDeltaQuery'] = round(qres[0][0], 2)  # Delta (запрос)
        self.cur.execute(f"select avg(b) from (select min(BalDelta) b from phones where phonenumber='{login}' and operator='{plugin}' and QueryDateTime>date('now','-{average_days} day') group by strftime('%Y%m%d', QueryDateTime))")
        qres = self.cur.fetchall()
        if qres != [] and qres[0][0] is not None:
            line['RealAverage'] = round(qres[0][0], 2)  # $/День(Р)
        if line.get('RealAverage', 0.0) < 0:
            line['CalcTurnOff'] = round(-line['Balance'] / line['RealAverage'], 2)
        self.cur.execute(f'insert into phones ({",".join(line.keys())}) VALUES ({",".join(list("?"*len(line)))})', list(line.values()))
        result2['QueryDateTime']=datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        self.cur.execute('REPLACE INTO responses(key,value) VALUES(?,?)', [f'{plugin}_{login}', json.dumps(result2, ensure_ascii=False)])
        if commit:
            self.conn.commit()

    def report(self):
        ''' Генерирует отчет по последнему состоянию телефонов'''
        reportsql = f'''select * from phones where QueryDateTime in (SELECT max(QueryDateTime) FROM Phones GROUP BY PhoneNumber,Operator order by Operator,PhoneNumber)'''
        cur = self.cur.execute(reportsql)
        dbheaders = list(zip(*cur.description))[0]
        dbdata = cur.fetchall()
        phones = store.ini('phones.ini').phones()
        dbdata.sort(key=lambda line: (phones.get(line[0:2], {}).get('NN', 999)))
        # округляем float до 2х знаков
        dbdata = [tuple([(round(i, 2) if type(i) == float else i) for i in line]) for line in dbdata]
        table = []  # результат - каждая строчка словарь элементов
        for line in dbdata:
            row = dict(zip(dbheaders, line))
            pair = (row['PhoneNumber'], row['Operator'])  # Пара PhoneNumber,Operator
            row['Alias'] = phones.get(pair, {}).get('Alias', 'Unknown')
            row['NN'] = phones.get(pair, {}).get('NN', 999)
            row['PhoneNumberFormat1'] = row['PhoneNumberFormat2'] = row['PhoneNumber']
            if type(row['PhoneNumber']) == str and row['PhoneNumber'].isdigit():
                # форматирование телефонных номеров
                row['PhoneNumberFormat1'] = re.sub(r'\A(\d{3})(\d{3})(\d{4})\Z', '(\\1) \\2-\\3', row['PhoneNumber'])
                row['PhoneNumberFormat2'] = row['PhoneNumberFormat1'].replace(' ', '')
            table.append(row)
        return table
    
    def history(self, phone_number, operator, days=7, lastonly=1):
        'Генерирует исторические данные по номеру телефона'
        if days == 0:
            return []
        historysql = f'''select * from phones where phonenumber=? and operator=? and QueryDateTime>date('now','-'|| ? ||' day') order by QueryDateTime desc'''
        cur = self.cur.execute(historysql, [phone_number, operator, days])
        dbheaders = list(zip(*cur.description))[0]
        dbdata = cur.fetchall()
        dbdata_sets = [set(l) for l in zip(*dbdata)]  # составляем список уникальных значений по каждой колонке
        dbdata_sets = [{i for i in l if str(i).strip() not in ['','None','0.0','0'] } for l in dbdata_sets]  # подправляем косяки
        if len(dbdata_sets) == 0:  # Истории нет - возвращаем пустой
            return []
        qtimes_num = dbheaders.index('QueryDateTime')
        qtimes = [line[qtimes_num] for line in dbdata]  # Список всех времен получения баланса
        qtimes_max = {max([k for k in qtimes if k.startswith(j)]) for j in {i.split()[0] for i in qtimes}}  # Последние даты получения баланса за сутки
        table = []  # результат - каждая строчка словарь элементов
        fields = store.options('HoverHistoryFormat').split(',')
        # выкидываем неинтересные колонки Там где только нули и None
        fields = [i for i in fields if i in dbheaders and dbdata_sets[dbheaders.index(i)] != set()]
        for line in dbdata:
            row = dict(zip(dbheaders, line))
            if str(lastonly) == '0' or row['QueryDateTime'] in qtimes_max:  # фильруем данные по qtimes_max
                table.append({k:row[k] for k in fields if k in row})
        return table[::int(store.options('SkipDay'))+1]

    def check_and_add_addition(self):
        'Создаем таблицы, добавляем новые поля, и нужные индексы если их нет'
        [self.cur.execute(query) for query in DB_SCHEMA]
        for k, v in addition_phone_fields.items():
            self.cur.execute("SELECT COUNT(*) AS CNTREC FROM pragma_table_info('phones') WHERE name=?", [k])
            if self.cur.fetchall()[0][0] == 0:
                self.cur.execute(f"ALTER TABLE phones ADD COLUMN {k} {v}")
        for idx in addition_indexes:
            self.cur.execute(f"CREATE INDEX IF NOT EXISTS {idx}")
        self.conn.commit()


class mdbengine():
    def __init__(self, dbname=None):
        import pyodbc
        if dbname is None:
            dbname = store.abspath_join(settings.mbplugin_ini_path, 'BalanceHistory.mdb')
        self.dbname = dbname
        DRV = '{Microsoft Access Driver (*.mdb)}'
        self.conn = pyodbc.connect(f'DRIVER={DRV};DBQ={dbname}')
        self.cur = self.conn.cursor()
        rows = self.cur.execute('SELECT top 1 * FROM phones')
        self.phoneheader = list(zip(*rows.description))[0]
        phones_ini = store.ini('phones.ini').read()
        # phones - словарь key=MBphonenumber values=[phonenumber,region]
        self.phones = {v['Number']: (re.sub(r' #\d+', '', v['Number']), v['Region'])
                       for k, v in phones_ini.items() if k.isnumeric() and 'Monitor' in v}

    def to_sqlite(self, line):
        '''конвертирует строчку для sqlite:
        Убираем последовательный номер NN
        PhoneNumber -> MBphoneNumber (оригинал)
        PhoneNumber -> PhoneNumber (без добавки пробел#n)
        Оператор(region) из ini -> Operator
        return header, newline
        '''
        idxp = self.phoneheader.index('PhoneNumber')
        mbphoneNumber = line[idxp]
        s1, s2 = re.search(r'\A(.*?)( #\d+)?\Z', mbphoneNumber).groups()
        s2 = s2.strip() if s2 else '???'
        phonenumber, region = self.phones.get(mbphoneNumber, [s1, s2])
        header = self.phoneheader[1:] + ('MBphoneNumber', 'Operator')
        newline = [i for i in line]  # pyodbc.Row object has no attribute copy
        newline[idxp] = phonenumber
        newline = newline[1:] + [mbphoneNumber, region]
        return header, newline


def update_sqlite_from_mdb_core(deep=None):
    'Обновляем данные из mdb в sqlite'
    if store.options('updatefrommdb') != '1':
        return
    logging.info(f'Добавляем данные из mdb')
    if deep is None:
        deep = int(store.options('updatefrommdbdeep'))
    # читаем sqlite БД
    db = dbengine(fast=True)
    mdb = mdbengine()  # BalanceHistory.mdb
    # Дата согласно указанному deep от которой сверяем данные
    dd = datetime.datetime.now() - datetime.timedelta(days=deep)
    logging.debug(f'Read from sqlite QueryDateTime>{dd}')
    db.cur.execute("SELECT * FROM phones where QueryDateTime>?", [dd])
    sqldata = db.cur.fetchall()
    dsqlite = {datetime.datetime.strptime(i[db.phoneheader.index('QueryDateTime')].split('.')[0], '%Y-%m-%d %H:%M:%S').timestamp(): i for i in sqldata}
    # теперь все то же самое из базы MDB
    logging.debug(f'Read from mdb QueryDateTime>{dd}')
    mdb.cur.execute("SELECT * FROM phones where QueryDateTime>?", [dd])
    mdbdata = mdb.cur.fetchall()
    dmdb = {i[mdb.phoneheader.index('QueryDateTime')].timestamp(): i for i in mdbdata}
    logging.debug('calculate')
    # Строим общий список timestamp всех данных
    allt = sorted(set(list(dsqlite) + list(dmdb)))
    # обрабарываем и составляем пары данных которые затем будем подправлять
    pairs = []  # mdb timestamp, sqlite timestamp
    while allt:
        # берем одну строчку из общего списка
        c = allt.pop(0)
        # Если для этого timestamp есть строчка в обазах добавляем из
        pair = [c if c in dmdb else None, c if c in dsqlite else None]
        if allt == [] or allt[0] in dmdb and pair[0] is not None or allt[0] in dsqlite and pair[1] is not None:
            # Это следующаяя строка или была последняя
            pairs.append(pair)
        elif allt[0] in dmdb and pair[0] is None and allt[0] - c < 10:
            # следующий timestamp это пара MDB к записи sqlite ?
            pair[0] = allt.pop(0)
            pairs.append(pair)
        elif allt[0] in dsqlite and pair[1] is None and allt[0] - c < 10:
            # следующий timestamp это пара sqlite к записи mdb ?
            pair[1] = allt.pop(0)
            pairs.append(pair)
    logging.debug('Before:')
    logging.debug(f'Difference time:{len([1 for a,b in pairs if a!=b and a is not None and b is not None])}')
    logging.debug(f'Only mdb:{len([1 for a,b in pairs if b is None])}')
    logging.debug(f'Only sqlite:{len([1 for a,b in pairs if a is None])}')
    update_param = []
    insert_param, insert_header = [], []
    for num, [mdb_ts, sqlite_ts] in enumerate(pairs):
        if mdb_ts != sqlite_ts and mdb_ts is not None and sqlite_ts is not None:
            # исправляем время в sqlite чтобы совпадало с mdb
            update_param.append([datetime.datetime.fromtimestamp(mdb_ts), datetime.datetime.fromtimestamp(sqlite_ts)])
            pairs[num][1] = mdb_ts
        elif mdb_ts is not None and sqlite_ts is None:
            # Копируем несуществующие записи в sqlite из mdb
            header, line = mdb.to_sqlite(dmdb[mdb_ts])
            insert_param.append(line)
            insert_header = header
            pairs[num][1] = mdb_ts

    # есть что вставить ?
    logging.debug(f'Insert {len(insert_param)}')
    if insert_param:
        db.cur.executemany(f'insert into phones ({",".join(insert_header)}) VALUES ({",".join(list("?"*len(insert_header)))})', insert_param)
        db.conn.commit()

    # есть что проапдейтить ?
    logging.debug(f'Update {len(update_param)}')
    if update_param:
        db.cur.executemany('update phones set QueryDateTime=? where QueryDateTime=?', update_param)
        db.conn.commit()

    # дополнительные фиксы (у меня в mdb мусор оказался, чтобы не трогать mdb чистим здесь)
    for sql in addition_queries:
        db.cur.execute(sql)
        db.conn.commit()
    # прописываем колонку mbnumber
    update_mbnumber = [[MBphonenumber, phonenumber, region] for MBphonenumber, (phonenumber, region) in mdb.phones.items()]
    db.cur.executemany(f'update phones set MBPhonenumber=? where MBPhonenumber is null and Phonenumber=? and operator=?', update_mbnumber)
    logging.debug(f'Update empty MBPhonenumber {db.cur.rowcount}:')
    db.conn.commit()

    logging.debug(f'After:')
    logging.debug(f'Difference time:{len([1 for a,b in pairs if a!=b and a is not None and b is not None])}')
    logging.debug(f'Only mdb:{len([1 for a,b in pairs if b is None])}')
    logging.debug(f'Only sqlite:{len([1 for a,b in pairs if a is None])}')
    logging.debug(f'Update complete')


def update_sqlite_from_mdb(deep=None):
    try:
        update_sqlite_from_mdb_core(deep)
    except Exception:
        logging.error(f'Ошибка при переносе данных из mdb в sqlite {"".join(traceback.format_exception(*sys.exc_info()))}')


def write_result_to_db(plugin, login, result):
    'пишем в базу если в ini установлен sqlitestore=1'
    try:
        if store.options('sqlitestore') == '1':
            db = dbengine()
            logging.info(f'Пишем в базу {db.dbname}')
            db.write_result(plugin, login, result)
    except AttributeError:
        logging.info(f'Отсутствуют параметры {"".join(traceback.format_exception(*sys.exc_info()))} дополнительные действия не производятся')
    except Exception:
        logging.error(f'Ошибка при записи в БД {"".join(traceback.format_exception(*sys.exc_info()))}')


def flags(cmd, key=None, value=None):
    'Работаем с флагами (таблица Flags) если в ini установлен sqlitestore=1, если нет просто вернем None'
    try:
        if store.options('sqlitestore') == '1':
            logging.debug(f'Flag:{cmd}')
            db = dbengine()
            if cmd.lower() == 'set':
                db.cur.execute('REPLACE INTO flags(key,value) VALUES(?,?)', [key, value])
                db.conn.commit()
            elif cmd.lower() == 'get':
                db.cur.execute('select value from flags where key=?', [key])
                qres = db.cur.fetchall()
                if len(qres) > 0:
                    return qres[0][0]
            elif cmd.lower() == 'getall':
                db.cur.execute('select * from flags')
                qres = db.cur.fetchall()
                return {k: v for k, v in qres}
            elif cmd.lower() == 'deleteall':
                db.cur.execute('delete from flags')
                db.conn.commit()
            elif cmd.lower() == 'delete':
                db.cur.execute('delete from flags where key=?', [key])
                db.conn.commit()
        else:
            if cmd.lower() == 'getall':
                return {}
    except Exception:
        logging.error(f'Ошибка при записи в БД {"".join(traceback.format_exception(*sys.exc_info()))}')

def responses():
    'Возвращаем все responses словарем'
    try:
        if store.options('sqlitestore') == '1':
            logging.debug(f'Responses from sqlite')
            db = dbengine()
            db.cur.execute('select key,value from responses')
            qres = db.cur.fetchall()
            return {k: v for k, v in qres}
        else:
            return {}
    except Exception:
        logging.error(f'Ошибка при записи в БД {"".join(traceback.format_exception(*sys.exc_info()))}')

if __name__ == '__main__':
    print('This is module dbengine')
    if 'update_sqlite_from_mdb_all' in sys.argv:
        store.turn_logging(logginglevel=logging.DEBUG)
        update_sqlite_from_mdb(deep=10000)
