# -*- coding: utf8 -*-
''' Автор ArtyLa '''
import re, logging
import store

icon = '789cd594fb5bcf6718c75fdfe6344b63b6396cb699310bdfc6b6b6b699b1759212e94c22a950115272e8208452513a53a193ce27253914954a6725158544947248e9b04f65bbf813f6beaef7f37e5ed77d3f3fdc3f3cf70255d9a10c4876084c1772f41b8b1831581041b6d4a0fbef0316a41cfeffb462587f8a50125249609bccf9a4d505105c6a8756cc580c122651df564e5f5f9fe05e824aac314995a6b5a389846a4fd422871355e9424d4b2156197218274f432f6e3cf2f2f2282828a0a8a888929212cacaca2c5cb810151515162d5a84aaaa2a6a6a6a2c5ebc18757575962c59c2d2a54bd1d0d060d9b265686a6aa2a5a585b6b6363a3a3ae8eaeaa2a7a787bebe3ecb972f67c58a15181818b072e54a0c0d0d59b56a15ab57afc6c8c888356bd6606c6cccdab56b313131c1d4d414333333d6ad5bc7faf5ebd9b06103e6e6e6585858606969c9c68d1bd9b469135656566cdebc992d5bb6b075eb56acadadd9b66d1b363636d8dadab27dfb76ecececd8b163073b77ee64d7ae5decdebd1b7b7b7b1c1c1c707474c4c9c9893d7bf6e0ececccdebd7bd9b76f1ffbf7efc7c5c58503070e70f0e0410e1d3a84abab2b6e6e6e1c3e7c187777773c3c3cf0f4f4e4c891231c3d7a142f2f2fbcbdbd3976ec183e3e3ef8fafae2e7e787bfbf3f010101040606121414c4f1e3c73971e204c1c1c1848484101a1acac993273975ea14a74f9f262c2c8cf0f070222222888c8c242a2a8a3367ce101d1d4d4c4c0cb1b1b1c4c5c5111f1f4f424202898989242525919c9c4c4a4a0aa9a9a99c3d7b96b4b434d2d3d33977ee1c1919199c3f7f9ecccc4c2e5cb8c0c58b17b974e912972f5f262b2b8becec6cae5cb9c2d5ab57c9c9c921373797bcbc3cae5dbb467e7e3e05050514161672fdfa758a8a8a282e2ea6a4a484d2d252cacaca282f2fa7a2a2821b376e50595949555515376fdea4baba9a5bb76e515353436d6d2d757575dcbe7d9b3b77ee505f5f4f43430377efdee5debd7bdcbf7f9fc6c6461e3c78405353130f1f3ee4d1a347343737f3f8f1639e3c79424b4b0badadad3c7dfa94b6b636dadbdb79f6ec19cf9f3fe7c58b17bc7cf9928e8e0e5ebd7a456767275d5d5dbc7efd9aeeee6e7a7a7ae8eded1df817c212909e3c63e6ac5933674c9616f681483475ca74f180a67f375524e034f17ffa76aa48e26bf15b9af2cd97a3dee6af264f12bfa32f26bccb9f4fec3f6566ffcb9f093c67de5f7fcf79c313c78bc5f3fe9c3b7f81cc204f182796f97dae9cdc1f6f1ac67d2239fbe75fe47efd6db02ef9e95829b1f8871f7f921dac7f2c211a397a8cccf7b30770cc471f0a038cfc4072f0ed282901850925de1b3274d8b0e123de9710e81f2d70dc13'

login_url = 'https://service.ntvplus.ru/account/action/quick-check-action'

# regexp для поиска баланса на странице
re_balance = r'(?usi)Баланс.*?--digits.>(\d+\.\d+)'
re_licSchet = r'(?usi)Номер карточки.*?--value.?>\D+(\d+)'
re_tarifPlan = r'(?usi)Подключённые пакеты.*?>(?:.*?item.>(.*?)<)+'
re_BlockStatus = r'(?usi)Состояние.*?--label.>(.*?)<'

def find_by_regexp(text, param, regexp, join=False, uslugi_list=False, uslugi_on=False):
    ''' Ищем по регулярке и возвращаем словарь {param : первый найденный по regexp}
        либо если указано:
        uslugi_list - клеим результаты в пары res1,res2 -> res1 \t 0  res2 \t 0
        uslugi_on - Возвращаем количество результатов res1,res2 -> 2
        join - объединяем все найденные патерны res1,res2 -> 'res1,res2' '''
    try:
        if uslugi_list:
            return {param: '\n'.join([f'{i}\t0' for i in re.findall(regexp, text)]).strip()}
        if uslugi_on:
            return {param: f'{len(re.findall(regexp, text))}'}
        if not join:
            return {param: re.findall(regexp, text)[0].strip()}
        else:
            return {param: ','.join(re.findall(regexp, text)).strip()}
    except Exception:
        logging.info(f'Not found {param}')
        return {}

def get_balance(login, password, storename=None, **kwargs):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    store.update_settings(kwargs)
    store.turn_logging()
    logging.info(f'start get_balance {login}')
    result = {}
    session = store.Session(storename)
    response0 = session.post(login_url, data={'id':login ,'lastname': password})
    if response0.status_code != 200:
        raise RuntimeError(f'POST Login page {login_url} error: status_code {response0.status_code}')
    try:
        response0.json()["load"]
    except Exception:
        raise RuntimeError(f'POST Login page {login_url} error: not found load {store.exception_text}')        
    url = f'https://service.ntvplus.ru{response0.json()["load"]}'
    response = session.get(url)
    session.save_response(url, response, save_text=True)  # сохраняем

    result['Balance'] = re.search(re_balance, response.text).group(1).replace(',', '.').strip()
    result.update(find_by_regexp(response.text, 'licSchet', re_licSchet))
    result.update(find_by_regexp(response.text, 'BlockStatus', re_BlockStatus))
    result.update(find_by_regexp(response.text, 'TarifPlan', re_tarifPlan, join=True))
    result.update(find_by_regexp(response.text, 'UslugiList', re_tarifPlan, uslugi_list=True))
    result.update(find_by_regexp(response.text, 'UslugiOn', re_tarifPlan, uslugi_on=True))
    
    

    return result


if __name__ == '__main__':
    print('This is module ntvplus')
