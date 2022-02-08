# -*- coding: utf8 -*-
''' Автор Pasha '''
''' проверка баланса SMS.RU https://sms.ru/ 
Вместо пароля указать api_id https://sms.ru/?panel=settings&subpanel=api'''
import os, sys, re, logging
import requests
import store

def get_balance(login, password, storename=None, **kwargs):
    result = {}
    session = store.Session(storename)
    response = session.get('https://sms.ru/my/balance?api_id=' + password + '&json=1')
    result['Balance'] = response.json().get('balance', '')

    session.save_session()
    return result

if __name__ == '__main__':
    print('This is module sms')
