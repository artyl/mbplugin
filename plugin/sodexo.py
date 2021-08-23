# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import os, sys, re, random, logging, traceback, datetime
import requests
import store

icon = '789C73F235636100033320D600620128666450804840E5918182BCF2A0C04A8AAA38E574750C188C0C4D71CA5B585833DCB87E83212A3206ABDE0B172E30DCBC7113A719E7CE9D67F8FFFF3FC3F7EFDF51CC80E905C9817079590556FDEEEE5E0CEFDEBE03AB79F7EE3D8396962E86DECE8E6EBCFE0799F1F4E953B0FDF8F47A582B31D4C42B603543554583A0DEF33364196ECE9765684EC634035D2F0817E41711A51F5DEFD7AFDFC0F4DFBF7F31CC40773FBADEE9D36630D8DB3B313C7FFE02AB19E8F8F8F113287A61E2E866604B1F200C1207C53DB25E7433F6ECDE0B0E5F5C6E00A9C3256765698B57EF40611000008C6DF095'

api_url = f'https://sodexo.gift-cards.ru/api/1/'

def get_balance(login, password, storename=None):
    result = {}
    cardno = login
    session = store.Session(storename, headers={})
    session.update_headers({'X-Requested-With': 'XMLHttpRequest'})
    cardtype = 'virtual-cards' if cardno.startswith('+') else 'cards'
    response = session.get(f'{api_url}{cardtype}/{cardno}?limit=100&rid={random.randint(1000000000,9999999999)}')
    data = response.json()['data']
    logging.debug(data)

    import pprint
    open('..\\log\\sodexo.log','w').write(pprint.PrettyPrinter(indent=4).pformat(data))

    result['Balance'] = 0.001+data['balance']['availableAmount']
    if 'currency' in data['balance']:
        result['Currenc'] = data['balance']['currency']
    if 'validUntil' in data:
        result['TurnOffStr'] = data['validUntil']
    try:
        history = []
        for hist in data['history']:
            t_tz = datetime.datetime.strptime(hist['time'],'%Y-%m-%dT%H:%M:%S.%f%z')
            t_fix = t_tz.replace(tzinfo=None)-datetime.timedelta(hours=3)
            histdate = datetime.datetime.strftime(t_fix,'%Y-%m-%d %H:%M:%S')
            history.append([f"{histdate} {','.join([i.replace('3DI ','').replace('MD00','').replace('EPS*','') for i in hist['locationName']])}",f"{hist['amount']}"])
        result['UslugiOn'] = f'{len(data["history"])}'
        result['UslugiList'] = '\n'.join([f'{a}\t{b}' for a, b in sorted(history)])
    except Exception:
        logging.info(f'Ошибка при получении списка транзакций {"".join(traceback.format_exception(*sys.exc_info()))}')

    return result


if __name__ == '__main__':
    'Виртуальные карты передаются в формате "+79161234567/9876"'
    '9876 - последние 4 цифры карты'
    print('This is module sodexo')
