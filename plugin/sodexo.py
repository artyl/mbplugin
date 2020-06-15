# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, random, logging
import requests
import store

def get_balance(login, password, storename=None):
    result = {}
    cardno = login
    session = requests.Session()
    session.headers = {'X-Requested-With': 'XMLHttpRequest'}
    cardtype = 'virtual-cards' if cardno.startswith('+') else 'cards'
    response = session.get(
        f'https://sodexo.gift-cards.ru/api/1/{cardtype}/{cardno}?limit=100&rid={random.randint(1000000000,9999999999)}')
    data = response.json()['data']
    logging.debug(data)
    result['Balance'] = 0.001+data['balance']['availableAmount']
    result['Currenc'] = data['balance']['currency']
    result['TurnOffStr'] = data['validUntil']
    return result


if __name__ == '__main__':
    'Виртуальные карты передаются в формате "+79161234567/9876"'
    '9876 - последние 4 цифры карты'
    print('This is module sodexo')
