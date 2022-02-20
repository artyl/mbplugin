import pytest
import os, sys, shutil, filecmp
import conftest  # type: ignore # ignore import error
import store, settings  # pylint: disable=import-error

def test_ini_class_mbplugin_ini_write():
    ini_path = os.path.join(conftest.data_path,'mbplugin.ini')
    shutil.copyfile(ini_path+'.ori', ini_path)
    ini=store.ini()
    ini.fn = 'mbplugin.ini'
    ini.inipath = ini_path
    print(f'inipath={ini.inipath}')
    ini.read()
    ini.ini['Options']['show_chrome'] = '0'
    ini.write()
    assert not conftest.ini_compare(ini_path+'.ori', ini_path)  # Проверяем что файл изменился
    ini.ini['Options']['show_chrome'] = '1'
    ini.write()
    assert conftest.ini_compare(ini_path+'.ori', ini_path)  # Проверяем идентичность первоначального и сохраненного файла


def test_ini_class_phones_ini_write():
    ini = store.ini('phones.ini')
    phones = ini.phones()
    print(f'inipath={ini.inipath}')
    print(f'mbplugin_root_path={settings.mbplugin_root_path}')
    expected_result1 = [('region', 'p_test1'), ('monitor', 'TRUE'), ('alias', 'Иваныч'), ('number', '9161112233'), ('balancenotchangedmorethen', '40'),
                       ('balancechangedlessthen', '1'), ('balancelessthen', '100.0'), ('turnofflessthen', '1')]
    # expected_result2 = {'nn': 1, 'Alias': 'Иваныч', 'region': 'p_test1', 'number': '9161112233', 'phonedescription': '', 'monitor': 'TRUE',
    #                    'balancelessthen': '100.0', 'turnofflessthen': '1', 'balancenotchangedmorethen': '40', 'balancechangedlessthen': '1', 'password2': '123password'}
    # expected_result2 = {'NN': 1, 'Alias': 'Иваныч', 'Region': 'p_test1', 'Number': '9161112233', 'PhoneDescription': '', 'Monitor': 'TRUE',
    #                    'BalanceLessThen': 100.0, 'TurnOffLessThen': 1, 'BalanceNotChangedMoreThen': 40, 'BalanceChangedLessThen': 1, 'Password2': '123password'}
    expected_result2 = { 'NN': 1, 'Alias': 'Иваныч', 'Region': 'p_test1', 'Number': '9161112233', 'Monitor': 'TRUE', 'Password2': '123password',
                         'nn': 1, 'alias': 'Иваныч', 'region': 'p_test1', 'number': '9161112233', 'monitor': 'TRUE', 
                         'balancelessthen': '100.0', 'turnofflessthen': '1', 'balancenotchangedmorethen': '40', 'balancechangedlessthen': '1', 'password2': '123password'}
    assert list(ini.ini['1'].items()) == expected_result1
    assert phones[('9161112233', 'p_test1')] == expected_result2


@pytest.fixture(scope="function", params=[
    ({'Balance': 124.45, 'SMS': 43, 'Min': 222}, '<Response><Balance>124.45</Balance><SMS>43</SMS><Min>222</Min></Response>'),
    ({'Balance': 124.45, 'SMS': '43', 'Min': '222'}, '<Response><Balance>124.45</Balance><SMS>43</SMS><Min>222</Min></Response>'),
])
def param_test_result_to_xml(request):
    return request.param

def test_result_to_xml(param_test_result_to_xml):
    (input, expected_result) = param_test_result_to_xml
    result = store.result_to_xml(input)
    print(f"input={input} result={result} expected_result={expected_result}")
    assert result == expected_result

@pytest.fixture(scope="function", params=[
({'Balance': 124.45, 'SMS': 43, 'Min': 222}, '<html><meta charset="windows-1251"><p id=response>{"Balance": 124.45, "SMS": 43, "Min": 222}</p></html>'),
    ({'Balance': 124.45, 'SMS': '43', 'Min': '222'}, '<html><meta charset="windows-1251"><p id=response>{"Balance": 124.45, "SMS": 43, "Min": 222}</p></html>'),
])
def param_test_result_to_html(request):
    return request.param

def test_result_to_html(param_test_result_to_html):
    (input, expected_result) = param_test_result_to_html
    result = store.result_to_html(input)
    print(f"input={input} result={result} expected_result={expected_result}")
    assert result == expected_result
