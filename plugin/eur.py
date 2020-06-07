# -*- coding: utf8 -*-
import sys;sys.dont_write_bytecode = True
import os, sys, re, time, logging
import requests
import store

def get_balance(login, password, storename=None):
    result = {}
    session = requests.Session()
    url = time.strftime("http://cbrates.rbc.ru/tsv/978/%Y/%m/%d.tsv")
    response = session.get(url)
    result['Balance'] = response.text.split()[-1]
    result['userName'] = 'Курс евро от РБК'
    return result


if __name__ == '__main__':
    print('This is module EUR')
