# -*- coding: utf8 -*- 
import sys;sys.dont_write_bytecode = True
import os, sys, re, logging
import requests
import store

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    return {'Balance':124.45, # double
    'Balance2':22, # double
    'Balance3':33, # double
    'LicSchet':'Лицевой счет',
    'UserName':'ФИО',
    'TarifPlan':'Тарифный план',
    'BlockStatus':'Статус блокировки',
    'AnyString':'Любая строка',
    'SpendBalance':12,# double Потрачено средств
    'KreditLimit':23, # double Кредитный лимит
    'Currenc':'Валюта',
    'Average':5,# double Средний расход в день
    'TurnOffStr':'Ожидаемая дата отключения',
    'Recomend':	54, # double Рекомендовано оплатить
    'SMS': 43,  # !!! integer Кол-во оставшихся/потраченных СМС
    'Min': 222, # !!! integer Кол-во оставшихся минут
    'SpendMin':32, # double Кол-во потраченных минут (с секундами)
    'Expired': 'Дата истечения баланса/платежа',
    'ObPlat':	14,   # double Сумма обещанного платежа
    'Internet': 1234, # double Кол-во оставшегося/потраченного трафика
    #'ErrorMsg':	'Сообщение об ошибке', # Если оо есть в Reponce то это ошибка
    'UslugiOn': '2/8',
    }

if __name__ == '__main__':
    print('This is module test')