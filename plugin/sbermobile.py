# -*- coding: utf8 -*-
''' Автор: toposferapro (плагин написан агентом Фиксик)
СберМобайл (lk.sbermobile.ru) - баланс, тариф и остатки пакетов.

Логин - номер телефона, важен только десяток цифр (можно писать +7, 8, с пробелами).
Пароль - код из СМС, который СберМобайл присылает при входе.

Код одноразовый, поэтому плагин сохраняет полученный токен и при живом токене
пароль не нужен вообще. Если токена нет:
  * пароль пустой   - просим СберМобайл отправить код и в ErrorMsg пишем, что вписать;
  * пароль непустой - считаем его кодом, входим и сохраняем токен.

За основу взято описание эндпоинтов из проекта pocketpet/sbermobile-skill (клиент запросов).
'''
import json
import logging
import os
import re
import uuid

import store

BASE = 'https://lk.sbermobile.ru/v2/api'
USER_INFO = 'SBTMA/2.3 desktop/Mac OS X/PWA (desktop)'
TOKEN_FILE = 'sbermobile_token.json'

# по этим словам в подписях пакетов раскладываем остатки по полям результата
PACKAGE_FIELDS = {
    'Internet': ('интернет', 'гб', 'gb', 'traffic'),
    'Min': ('минут', 'min'),
    'SMS': ('смс', 'sms'),
}


def _phone(login):
    '''Оставляет от номера последние 10 цифр - в таком виде его ждёт API.'''
    digits = ''.join(ch for ch in str(login) if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits


def _token_path(storename):
    return os.path.join(store.session_folder(storename), TOKEN_FILE)


def _load_token(storename, phone):
    try:
        with open(_token_path(storename), encoding='utf8') as f:
            data = json.load(f)
        if _phone(data.get('phone', '')) == phone:
            return data.get('token')
    except (OSError, ValueError):
        pass
    return None


def _save_token(storename, phone, token):
    path = _token_path(storename)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf8') as f:
            json.dump({'phone': phone, 'token': token}, f)
    except OSError as exc:
        logging.warning(f'СберМобайл: не удалось сохранить токен: {exc}')


def _drop_token(storename):
    try:
        os.remove(_token_path(storename))
    except OSError:
        pass


def request_code(session, phone):
    '''Просит СберМобайл отправить код из СМС. Возвращает текст ошибки или None.'''
    try:
        response = session.post(f'{BASE}/gateway/send_password',
                                json={'number': phone, 'additional': 'false'})
    except Exception as exc:  # noqa: BLE001 - сетевые ошибки отдаём как текст
        return f'СберМобайл: не удалось попросить код ({exc})'
    if response.status_code != 200:
        return f'СберМобайл: сервис ответил {response.status_code} на запрос кода'
    return None


def do_login(session, phone, code):
    '''Вход по коду из СМС. Возвращает токен или None.'''
    body = {
        'number': phone,
        'password': str(code).strip(),
        'screen': '1920x1080',
        'appVersionName': '2.3',
        'appVersionCode': '2.0.0',
        'system': 'desktop',
        'systemVersion': 'mbplugin',
        'deviceId': str(uuid.uuid4()),
    }
    try:
        response = session.post(f'{BASE}/gateway/login', json=body)
    except Exception as exc:  # noqa: BLE001
        logging.warning(f'СберМобайл: ошибка входа: {exc}')
        return None
    try:
        data = response.json()
    except ValueError:
        return None
    inner = data.get('data') if isinstance(data.get('data'), dict) else {}
    return inner.get('token') or data.get('token') or data.get('access_token')


def _walk(data):
    '''Обходит json и отдаёт пары (ключ, значение) в порядке обхода.'''
    if isinstance(data, dict):
        for key, value in data.items():
            yield key, value
            yield from _walk(value)
    elif isinstance(data, list):
        for item in data:
            yield from _walk(item)


def find_number(data, keys):
    '''Первое число, чей ключ совпал с одним из keys (без учёта регистра).'''
    for key, value in _walk(data):
        if isinstance(value, (int, float)) and not isinstance(value, bool) and key.lower() in keys:
            return value
    return None


def find_text(data, keys):
    '''Первая непустая строка, чей ключ совпал с одним из keys.'''
    for key, value in _walk(data):
        if isinstance(value, str) and value.strip() and key.lower() in keys:
            return value.strip()
    return None


def find_flag(data, key):
    '''True, если по этому ключу где-то стоит true.'''
    return any(k.lower() == key and v is True for k, v in _walk(data))


def match_field(title, content_type):
    '''Определяет, в какое поле результата класть остаток опции.'''
    upper = (content_type or '').upper()
    if upper == 'INTERNET':
        return 'Internet'
    if upper in ('AUTORENEWAL_BLOCK', 'SECURE_ACCOUNT'):
        return None
    lower = (title or '').lower()
    for field, words in PACKAGE_FIELDS.items():
        if any(word in lower for word in words):
            return field
    return None


def parse_row(row, result):
    '''Разбирает строку ответа tariff/data. Деньги в ответе в копейках, трафик в мегабайтах.'''
    tariff = row.get('currentTariff') or {}
    if tariff.get('name'):
        result['TariffPlan'] = tariff['name']

    balance = row.get('balance') or {}
    if isinstance(balance.get('balanceValue'), (int, float)):
        result['Balance'] = round(balance['balanceValue'] / 100, 2)
    if isinstance(balance.get('limitValue'), (int, float)) and balance['limitValue']:
        result['KreditLimit'] = round(balance['limitValue'] / 100, 2)
    if balance.get('needPay'):
        result['BlockStatus'] = 'Нужна оплата'
    if row.get('subscriptionFeeDate'):
        result['Expired'] = str(row['subscriptionFeeDate'])[:10]

    lines = []
    plan = []
    for key, caption in (('minutesQuantity', 'минуты'), ('mbQuantity', 'интернет'), ('smsQuantity', 'смс')):
        volume = (tariff.get(key) or {}).get('volume')
        if volume is not None:
            plan.append(f'{caption} {volume}')
    if plan:
        lines.append('в тарифе: ' + ', '.join(plan))

    for option in ((row.get('connectedOptions') or {}).get('additionalOptions') or []):
        current = option.get('currentValue')
        total = option.get('totalValue')
        title = (option.get('title') or '').strip()
        if current is None or not title:
            continue
        lines.append(f'{title}: {current} из {total}' if total else f'{title}: {current}')
        field = match_field(title, option.get('contentType'))
        if field and field not in result and (total or current):
            result[field] = current

    if lines:
        result['UslugiList'] = '\n'.join(lines[:12])


def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    store.feedback.text('СберМобайл: получаю данные')
    result = {}
    phone = _phone(login)
    if len(phone) < 10:
        result['ErrorMsg'] = 'СберМобайл: в логине не видно номера телефона'
        return result

    session = store.Session(storename, headers={'X-User-info': USER_INFO})
    token = _load_token(storename, phone)

    if not token:
        if not password:
            error = request_code(session, phone)
            result['ErrorMsg'] = error or ('СберМобайл: код из СМС отправлен. '
                                           'Впишите его в поле пароля и повторите запрос.')
            return result
        token = do_login(session, phone, password)
        if not token:
            result['ErrorMsg'] = ('СберМобайл: не удалось войти. Код из СМС одноразовый - '
                                  'очистите пароль, запросите новый код и впишите его.')
            return result
        _save_token(storename, phone, token)

    numbers = [phone]
    extra = store.options('sbermobile_numbers', '', pkey=store.get_pkey(login, __name__)) or ''
    for part in re.split(r'[,;\s]+', str(extra)):
        candidate = _phone(part)
        if len(candidate) == 10 and candidate not in numbers:
            numbers.append(candidate)

    session.update_headers({'token': token})
    try:
        response = session.get(f'{BASE}/tariff-service/tariff/data', params={'numbers': ','.join(numbers)})
    except Exception as exc:  # noqa: BLE001
        result['ErrorMsg'] = f'СберМобайл: ошибка запроса данных ({exc})'
        return result

    if response.status_code in (401, 403):
        _drop_token(storename)
        result['ErrorMsg'] = ('СберМобайл: сохранённый токен больше не действует. '
                              'Очистите пароль, запросите новый код из СМС и впишите его.')
        return result
    if response.status_code != 200:
        result['ErrorMsg'] = f'СберМобайл: сервис ответил {response.status_code}'
        return result

    try:
        data = response.json()
    except ValueError:
        result['ErrorMsg'] = 'СберМобайл: сервис вернул не json'
        return result

    result['LicSchet'] = phone
    rows = ((data.get('data') or {}).get('extendedData')) or []
    row = next((item for item in rows if _phone(item.get('number', '')) == phone),
               rows[0] if rows else None)
    if row:
        parse_row(row, result)
    else:
        # запасной путь: структура ответа другая, ищем знакомые поля по всему ответу
        balance = find_number(data, {'balancevalue'})
        if balance is not None:
            result['Balance'] = round(balance / 100, 2)
        result['TariffPlan'] = find_text(data, {'tariffname'}) or ''
        if find_flag(data, 'needpay'):
            result['BlockStatus'] = 'Нужна оплата'

    # остальные номера аккаунта, перечисленные в настройке sbermobile_numbers
    others = [item for item in rows if _phone(item.get('number', '')) != phone]
    others.sort(key=lambda item: numbers.index(_phone(item.get('number', '')))
                if _phone(item.get('number', '')) in numbers else len(numbers))
    extra_lines = []
    for index, item in enumerate(others, start=2):
        other = {}
        parse_row(item, other)
        if 'Balance' in other:
            result[f'Balance{index}'] = other['Balance']
        parts = [str(item.get('number') or '')]
        if other.get('TariffPlan'):
            parts.append(other['TariffPlan'])
        if 'Balance' in other:
            parts.append(f"баланс {other['Balance']}")
        if other.get('BlockStatus'):
            parts.append(other['BlockStatus'])
        for option in ((item.get('connectedOptions') or {}).get('additionalOptions') or []):
            if option.get('totalValue'):
                parts.append(f"{option.get('title')}: {option.get('currentValue')} из {option.get('totalValue')}")
        extra_lines.append(', '.join(parts))
    if extra_lines:
        result['UslugiList'] = (result.get('UslugiList', '') + '\n' + '\n'.join(extra_lines)).strip()

    if 'Balance' not in result:
        result['ErrorMsg'] = 'СберМобайл: в ответе сервиса не найдено поле баланса'

    logging.info(f'СберМобайл: результат {result}')
    session.save_session()
    return result


if __name__ == '__main__':
    print('This is module sbermobile')
