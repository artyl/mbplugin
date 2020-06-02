# -*- coding: utf8 -*-
import sys;sys.dont_write_bytecode = True
import os,sys, pickle, requests

storefolder = 'C:\\mbplugin\\store'
storename = 'C:\\mbplugin\\store\\persistent_store'


def get_from_store(key):
    try:
        with open(storename, 'r') as f:
            data = f.read().split('\n')
        sdict = dict(line.split('=', 1) for line in data if '=' in line)
        return sdict.get(key, '')
    except Exception:
        return ''


def put_to_store(key, value):
    try:
        with open(storename, 'r') as f:
            data = f.read().split('\n')
    except Exception:
        data = ''
    sdict = dict(line.split('=', 1) for line in data if '=' in line)
    if key in sdict:
        del sdict[key]
    sdict[key] = value
    with open(storename, 'w') as f:
        f.write('\n'.join([f'{k}={v}' for k, v in sdict.items()]))


def save_session(storename, session):
    'Сохраняем сессию в файл'
    with open(os.path.join(storefolder, storename), 'wb') as f:
        pickle.dump(session, f)


def load_session(storename):
    'Загружаем сессию из файла'
    try:
        with open(os.path.join(storefolder, storename), 'rb') as f:
            return pickle.load(f)
    except Exception:
        return None  # return empty
