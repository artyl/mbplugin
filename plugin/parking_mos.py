# -*- coding: utf8 -*-
'Оплата парковки parking.mos.ru'
'(Вход через логин/пароль на login.mos.ru)'
''' Автор ArtyLa '''
import os, sys, io, re, logging, json, random
import requests
import store, settings

icon = '789C9D53DB2B836118FF297F803FC1A5D2CCA1E44E960BA55D897B17AE28CA36931212CB056EA8D11C4A920B16FAB6B183651726DA2C5BB12D87D5AC1DB2B23944CDFBBCD6D2FA3E93B77EF5F43B3CBDCFFB3D9F42D9580E7E1A19AA182AF22843E5B790D77F1ED9FE206A0E54FF826C2F9F15D4A2A8330D7148E9855E12BAD6BB89C3C74BD44AF5289197312C876CAC874FBC47897CC91E4579B9A0C16AD88126CB08F36AD0E99AE390B39A7A58D82CE491CA4FFB8DD8899CA1E364160FD92472B91C07D5C4ED328D3C627999A0C26D260E856D02B1D7348E623EE802C6420FE248230F798BF3CDD6315CA523E871EBB9DF14F5A2CB358F851B0BFC8C278E34F290B738DF621B87EFE91EBDE72B857CFFC51A9CF100DA1C539C238D3CE4159B3FC2E66CB54FE2E5F31D42D403A573066ACF06BA4F1739471A79A4DE8FEE6A08DB3170B18ED4FB339FF52E9B40E6E38D7306F66DC82395AF376BE14E06A10F5AF99D477DDB1C5413471A797EDB9F06F33096425676CF145C896B0EAA8923EDAFFB47BBD6EED4A1FD58F7EBFE17FEC17FA07AAB0F5FC3BCACE5'

def get_balance(login, password, storename=None):
    result = {}
    session = store.Session(storename)
    response3 = session.get('https://lk.parking.mos.ru/ru/cabinet')
    if re.findall("(?usi)accountId\":(.*?),", response3.text) != []:
        logging.info('Old session is ok')
    else:
        logging.info('Old session is bad, relogin')
        session.drop_and_create()
        response1 = session.get('https://lk.parking.mos.ru/auth/social/sudir?returnTo=/../cabinet')
        csrf = re.findall("(?usi)csrf-token-value.*?content='(.*?)'", response1.text)[0]
        bfp = ''.join([hex(random.randrange(15))[-1] for i in range(32)])
        data = {'isDelayed': 'false', 'login': login, 'password': password,
                'csrftoken_w': csrf, 'bfp': bfp, 'alien': 'false', }
        response2 = session.post('https://login.mos.ru/sps/login/methods/password', data=data)
        _ = response2
        response3 = session.get('https://lk.parking.mos.ru/ru/cabinet')

    accountId = re.findall("(?usi)accountId\":(.*?),", response3.text)[0]
    response4 = session.put('https://lk.parking.mos.ru/api/2.40/accounts/getbalance', data={"accountId": accountId})
    result['Balance'] = response4.json()['balance']/100.

    session.save_session()
    return result


if __name__ == '__main__':
    print('This is module parking_mos')
