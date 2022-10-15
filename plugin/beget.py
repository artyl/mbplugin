# -*- coding: utf8 -*-
''' Автор d1mas
проверка баланса хостинг-провайдера BEGET
https://beget.com/ru
https://beget.com/ru/kb/api/beget-api '''
import os, sys, re, logging, time
import store, json

icon = '789c9dd1314bc3401407f03c7016475d24228820487488a2d65c3b38084a0675f123d4ef503737a1babaa89393273a28158b5849c10e17d468b79b7450280e4e0ecf7f5a05494a137bf05feeee77efee5d6ec9ee319ac3464691be9f9061b616b05ee96de57730732c4341d61db9177a5c393c7597e19c37a797af67dc767ba3197ccabaf00c2fe105bc052fe179bd349d7806bc8697d1797809af537886b7da7801cf09568df90e2fdcceaa2ebd09afe1cd6eef1f0dfa27fed3bf307b0f8beeb99ad48fb581e6ffad78f6d77679782badbd50130c2b3faa64352a24de2f49be9e10eb434aac0fab03d8e8bc3e2059dfa5c4f707b57e465d119dafef90e56f52c7fe8781e5c60dc5fe1f565437923dac7e2b51ecfed53cc9ab3523f1feb0eecb317ab58ff71649f805d40dedaac167f346aaff83759f8ba45581d8cb13c3ead34c3afb379f478e08d369cf370bb2b1ba'
login_url = 'https://api.beget.com'


def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError as e:
        return False
    return True

def get_balance(login, password, storename=None, **kwargs):
    logging.info(f'start get_balance {login}')
    baseurl = 'https://api.beget.com'
    url = 'https://api.beget.com/api/user/getAccountInfo?login=' + login + '&passwd=' + password + '&output_format=json'
    cookies = dict(beget='begetok')
    session = store.Session(storename)
    session.disable_warnings()
    response = session.get(url, cookies=cookies, headers={'Referer': baseurl + '/'}, verify=False)
    if response.status_code != 200:
        raise RuntimeError(f'Login error: status_code {response.status_code}!=200')
    if not is_json(response.text):
        raise RuntimeError(f'No JSON in reply: {response.text}')
    if response.json()['status'] != 'success':
        raise RuntimeError(f'Login error: reply {response.text}')
    logging.info(f'Parsing data')
    result = {}
    data = response.json()['answer']['result']
    result['Balance'] = data['user_balance']
    try:
        result['TarifPlan'] = data['plan_name']
    except Exception:
        logging.info(f'Not found TarifPlan')
    try:
        result['TurnOff'] = data['user_days_to_block']
    except Exception:
        logging.info(f'Not found TurnOff')

    session.save_session()
    time.sleep(1)  # Запрос отрабатывающий меньше секунды ломает логику, поэтому ставим задержку
    return result

if __name__ == '__main__':
    print('This is module beget')
