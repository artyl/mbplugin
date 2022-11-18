# -*- coding: utf8 -*-
''' Автор Pasha
проверка баланса SMS.RU https://sms.ru/ 
Вместо пароля указать api_id https://sms.ru/?panel=settings&subpanel=api'''
import os, sys, re, logging
import requests
import store

icon = '789cd5514b4b0251189d3be3f82a3297b5ca5c24d12094292d12492804cb0802895a1409b989a2951bdba93d405dd86b53193d88a8402c729142d1262aaa55bfe6f439f6203572961d38cc9df9cee3bb4cdfa05dc5c9b0132dc4c60f32aea534a0f96d4389ff056af509382e06c612d0685250e68ea048c6e2108435e226b4dacb5f33189b825e9f234d1c3cffe94d401477a0561f53ff193d8faafa45718fbe2f912f463d41b9afb87753d32eacd62b7474dcc268bc814e7741f9a7651923729720ac53fe16f58528270149da86cf97c3c4c43ddcee67180cafb4df35f9cfcbfce3f4be4ab3342c963c5a5b0f505fbf80c9c92ca2d147cccf3fc16c2ed03c4ffdd92afb8fd0dde2703832f0fb1fe0f5be90761f2ed701c2e13bb0ba2188292fed7688d2ae95309936100814904cbec1e9bc02d73c00952af2a5e567bafefc77365b1a1e4f06bc7e11aa95fe0a7d2d193f30dcf643afd84f1042bdb247b7ec013feb4031a378561432da2e7bca585b7fb0fb5b4ff7e1a73b95f78f4be0e77ac08d4915be7714c9b94e'

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    result = {}
    session = store.Session(storename)
    response = session.get('https://sms.ru/my/balance?api_id=' + password + '&json=1')
    result['Balance'] = response.json().get('balance', '')

    session.save_session()
    return result

if __name__ == '__main__':
    print('This is module sms')
