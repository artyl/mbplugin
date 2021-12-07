# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, logging, random, time
import requests
import store

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    result = {}
    session = store.Session(storename)
    result = {'Balance': 124.45 + random.randint(1,5),  # double
            'Balance2': 22,  # double
            'Balance3': 33,  # double
            'LicSchet': 'Лицевой счет',
            'UserName': 'ФИО',
            'TarifPlan': 'Тарифный план',
            'BlockStatus': 'Статус блокировки',
            'AnyString': 'Любая строка',
            'SpendBalance': 12,  # double Потрачено средств
            'KreditLimit': 23,  # double Кредитный лимит
            'Currenc': 'Валюта',
            'Average': 5,  # double Средний расход в день
            'TurnOff': 20, # дней до отключения
            'TurnOffStr': 'Ожидаемая дата отключения',
            'Recomend':	54,  # double Рекомендовано оплатить
            'SMS': 43,  # !!! integer Кол-во оставшихся/потраченных СМС
            'Min': 222,  # !!! integer Кол-во оставшихся минут
            'SpendMin': 32,  # double Кол-во потраченных минут (с секундами)
            'Expired': 'Дата истечения баланса/платежа', # BalExpired->BeeExpired, Expired->BeeExpired
            'ObPlat':	14,   # double Сумма обещанного платежа
            'Internet': 1234,  # double Кол-во оставшегося/потраченного трафика
            # 'ErrorMsg':	'Сообщение об ошибке', # Если оо есть в Reponce то это ошибка
            'UslugiOn': '2/8',
            'UslugiList': 'Услуга1\t10р\nУслуга2\t20р\nУслуга3\t30р\nУслуга4\t40р' # Это будет показано в hover, если включено
            }
    session.save_session()     
    # В реальном случае мы получаем баланс гораздо больше чем за секунду
    # Если мы получаем несколько результатов в секунду, то у нас ломаются отчеты.
    # Так что чтобы не чинить что не сломано просто чуть подождем
    time.sleep(1)
    return result


if __name__ == '__main__':
    print('This is module test')
