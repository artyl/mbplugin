# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import time, os, sys, logging, traceback, pyodbc, sqlite3, datetime
sys.path.append(os.path.split(os.path.abspath(sys.argv[0]))[0])
import settings, store

DB_SCHEMA = '''
CREATE TABLE IF NOT EXISTS Phones (
    NN INTEGER NOT NULL DEFAULT NULL PRIMARY KEY AUTOINCREMENT,
    [PhoneNumber] [nvarchar] (150), -- COLLATE Cyrillic_General_CI_AS NULL ,
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
) 
-- CREATE INDEX idx_PhoneNumber_Operator ON Phones (PhoneNumber,Operator);
-- CREATE INDEX idx_QueryDateTime ON Phones (QueryDateTime);
'''
PhonesHText={'NN':'NN',
'Alias':'Псевдоним',
'PhoneNumber':'Номер',
'Operator':'Оператор',
'QueryDateTime':'Время запроса',
'SpendBalance':'SpendBalance',
'KreditLimit':'Кр. лимит',
'UslugiOn':'Услуги',
'Currenc':'Валюта',
'Balance':'Баланс',
'Balance2':'Баланс2',
'Balance3':'Баланс3',
'Average':'Average',
'TurnOff':'TurnOff',
'Recomend':'Recomend',
'SMS':'SMS',
'Minutes':'Минут',
'USDRate':'USDRate',
'LicSchet':'Л.счет',
'UserName':'ФИО',
'BalDelta':'Delta (день)',
'JeansExpired':'JeansExpired',
'ObPlat':'ObPlat',
'BeeExpired':'BeeExpired',
'RealAverage':'$/День(Р)',
'Seconds':'Секунд',
'TarifPlan':'Тариф. план',
'BlockStatus':'Статус блок.',
'MinSonet':'MinSonet',
'MinLocal':'MinLocal',
'Internet':'Инт.трафик',
'TurnOffStr':'TurnOffStr',
'SpendMin':'SpendMin',
'PhoneReal':'PhoneReal',
'BalanceRUB':'BalanceRUB',
'SMS_USD':'SMS_USD',
'SMS_RUB':'SMS_RUB',
'InternetUSD':'InternetUSD',
'InternetRUB':'InternetRUB',
'Contract':'Contract',
'MinAverage':'Мин/день ср',
'BalDeltaQuery':'Delta (запрос)',
'MinDelta':'Мин/день',
'MinDeltaQuery':'Мин Delta (запрос)',
'NoChangeDays':'Дней без изм.',
'AnyString':'AnyString',
'CalcTurnOff':'Откл (Р)',}

class dbengine():
    def __init__(self, dbname):
        self.dbname = dbname
        self.conn = sqlite3.connect(self.dbname)  # detect_types=sqlite3.PARSE_DECLTYPES
        self.cur = self.conn.cursor()
        self.cur.execute(DB_SCHEMA)
        self.conn.commit()
        rows = self.cur.execute('SELECT * FROM phones limit 1;')
        self.phoneheaders = list(zip(*rows.description))[0]

    def write_result(self,plugin, login, result, commit=True):
        'Записывает результат в базу'
        # Делаем копию, чтобы не трогать оригинал
        result2 = {k:v for k,v in result.items()}
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
        line = {k:v for k,v in result2.items() if k in self.phoneheaders}
        # Добавляем расчетные поля и т.п.
        line['Operator'] = plugin
        line['PhoneNumber'] = login  # PhoneNumber=PhoneNum
        line['QueryDateTime'] = datetime.datetime.now().replace(microsecond=0) # no microsecond
        self.cur.execute(f"select cast(julianday('now')-julianday(max(QueryDateTime)) as integer) from phones where phonenumber='{login}' and operator='{plugin}' and abs(balance-{result['Balance']})>0.02")
        line['NoChangeDays'] = self.cur.fetchall()[0][0]  # Дней без изм.
        options_ini = store.read_ini('Options.ini')
        if 'Additional' in  options_ini and 'AverageDays' in options_ini['Additional']:
            average_days = int(options_ini['Additional']['AverageDays'])
        else:
            average_days = settings.average_days
        self.cur.execute(f"select {line['Balance']}-balance from phones where phonenumber='{login}' and operator='{plugin}' and QueryDateTime>date('now','-{average_days} day') and strftime('%Y%m%d', QueryDateTime)<>strftime('%Y%m%d', date('now')) order by QueryDateTime desc limit 1")
        qres = self.cur.fetchall()
        if qres != []:
            line['BalDelta']  = round(qres[0][0],2)  # Delta (день)
        self.cur.execute(f"select {line['Balance']}-balance from phones where phonenumber='{login}' and operator='{plugin}' order by QueryDateTime desc limit 1")
        qres = self.cur.fetchall()
        if qres != []:
            line['BalDeltaQuery']  = round(qres[0][0],2)  # Delta (запрос)
        self.cur.execute(f"select avg(b) from (select min(BalDelta) b from phones where phonenumber='{login}' and operator='{plugin}' and QueryDateTime>date('now','-{average_days} day') group by strftime('%Y%m%d', QueryDateTime))")
        qres = self.cur.fetchall()
        if qres != [] and qres[0][0] is not None:
            line['RealAverage']  = round(qres[0][0],2)  # $/День(Р)
        if line.get('RealAverage',0.0) < 0:
            line['CalcTurnOff'] = round(-line['Balance']/line['RealAverage'],2)
        self.cur.execute(f'insert into phones ({",".join(line.keys())}) VALUES ({",".join(list("?"*len(line)))})', list(line.values()))
        if commit:
            self.conn.commit()
    def report(self,fields):
        'Генерирует отчет по последнему состоянию телефонов'
        reportsql = f"SELECT {','.join(fields)},max(QueryDateTime) QueryDateTime FROM Phones where PhoneNumber is not NULL GROUP BY PhoneNumber,Operator order by Operator,PhoneNumber;"
        rows = self.cur.execute(reportsql)
        headers = list(zip(*rows.description))[0]
        data = rows.fetchall()
        return headers,data

if __name__ == '__main__':
    print('This is module dbengine')
