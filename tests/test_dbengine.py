import pytest
import os, sys, shutil, logging, threading, importlib.util
import conftest  # type: ignore # ignore import error
import dbengine, store, settings  # pylint: disable=import-error
import test1

class Test:

    def setup_method(self, test_method=None):
        # configure self.attribute
        # assert test_method.__name__ == 'test_create_db', test_method
        self.ini_path = os.path.join(conftest.data_path, 'mbplugin.ini')
        # logginglevel for putest see conftest.py
        logging.info(f'inipath={self.ini_path}')
        self.change_ini('updatefrommdb', '1')
        self.change_ini('sqlitestore', '1')
        shutil.copyfile(self.ini_path + '.ori', self.ini_path)
        self.db = dbengine.Dbengine()
        self.dbname_copy = self.db.dbname + '.cp.sqlite'

    def teardown_method(self, test_method=None):
        # tear down self.attribute
        self.db.conn.close()
        if 'mbplugin\\tests\\data' in self.db.dbname:
            os.remove(self.db.dbname)
            if os.path.exists(self.dbname_copy):
                os.remove(self.dbname_copy)
            os.remove(self.ini_path)

    def change_ini(self, option, value):
        ini = store.ini()
        # ini.fn = 'mbplugin.ini'
        logging.info(f'inipath={ini.inipath}')
        ini.read()
        ini.ini['Options'][option] = value
        ini.write()
        ini.inipath = self.ini_path
        store.options('updatefrommdb', flush=True)

    def test_create_db(self):
        phone_number = '9161234567'
        operator = 'p_test1'
        assert len(self.db.phoneheader) == 47
        assert self.db.cur_execute_00('select count(*) from phones') >= 0
        result1 = test1.get_balance(operator, phone_number, wait=False)
        self.db.write_result(operator, phone_number, result1)
        result2 = test1.get_balance(operator, phone_number, wait=False)
        result2.update({'Balance': '123', 'Currency': 'rub', 'Minutes': '23', 'BalExpired': '22.10.2022'})
        dbengine.write_result_to_db(operator, phone_number, result1)
        assert phone_number in self.db.cur_execute('select * from phones where PhoneNumber=? limit 1', [phone_number])[0], 'Отсутствует запись'
        with pytest.raises(KeyError) as e_info:
            self.db.write_result(operator, phone_number, {})
        dbengine.write_result_to_db(operator, phone_number, {})
        report = self.db.report()
        assert len(report) > 0
        history = self.db.history(phone_number, operator)
        assert len(history) > 0
        shutil.copyfile(self.db.dbname, self.dbname_copy)
        self.db.cur_execute_00('delete from phones where PhoneNumber=?', [phone_number])
        assert self.db.copy_data(os.path.join(conftest.data_path, 'aaabbb.sqlite')) is False, 'return False as error'
        self.db.copy_data(self.dbname_copy)
        assert self.db.cur_execute_00('select count(*) from phones') >= 0
        self.db.cur_execute_00('delete from phones where PhoneNumber=?', [phone_number])
        self.db.conn.commit()
        assert self.db.cur.rowcount > 0
        assert self.db.cur_execute_00('select count(*) from phones') == 0
        assert len(dbengine.responses()) > 0
        self.change_ini('sqlitestore', '0')
        assert len(dbengine.responses()) == 0
        self.change_ini('sqlitestore', '1')

    @pytest.mark.slow
    def test_mdb_import(self):
        if sys.platform == 'win32' and importlib.util.find_spec('pyodbc') is not None:
            import pyodbc
            if 'Driver do Microsoft Access (*.mdb)' in pyodbc.drivers():
                with pytest.raises(Exception) as e_info:
                    dbengine.update_sqlite_from_mdb_core(os.path.join(conftest.data_path, 'aaabbb.mdb'))
                assert dbengine.update_sqlite_from_mdb(os.path.join(conftest.data_path, 'aaabbb.mdb')) is False
                dbengine.update_sqlite_from_mdb(os.path.join(conftest.data_path, 'BalanceHistory_test.mdb'))
                assert self.db.cur_execute_00('select count(*) from phones') == 9

    def test_flags(self):
        dbengine.flags('set', 'key1', 'val1')
        dbengine.flags('set', 'key2', 'val2')
        dbengine.flags('set', 'key3', 'val1')
        getall = dbengine.flags('getall')
        assert len(getall) == 3, f'{getall=}'
        dbengine.flags('get', 'key1')
        # ??? assert dbengine.flags('get', 'key1') == 'val1'
        dbengine.flags('setunic', 'key1', 'val1')
        assert dbengine.flags('get', 'key3') is None
        assert dbengine.flags('get', 'key1') == 'val1'
        assert dbengine.flags('getall') == {'key1': 'val1', 'key2': 'val2'}
        dbengine.flags('delete', 'key1')
        assert len(dbengine.flags('getall')) == 1
        self.change_ini('sqlitestore', '0')
        assert len(dbengine.flags('getall')) == 0
        self.change_ini('sqlitestore', '1')
        assert len(dbengine.flags('getall')) == 1
        dbengine.flags('deleteall')
        assert len(dbengine.flags('getall')) == 0

    def thread(self):
        name = threading.current_thread().name
        for task in range(10):
            for i in range(10):
                if name == 'thr_0':
                    dbengine.flags('set', 'key1', 'val1')
                elif name == 'thr_1':
                    dbengine.flags('setunic', 'key1', 'val1')
                elif name == 'thr_2':
                    dbengine.flags('getall')
            print(f'{threading.currentThread().name} done task {task}')

    def test_multithread(self):
        for t in range(3):
            threading.Thread(target=self.thread, name=f'thr_{t}', daemon=True).start()
        [t.join() for t in threading.enumerate() if t.name.startswith('thr_')]


def old_test_ini_class_phones_ini_write():
    ini = store.ini('phones.ini')
    phones = ini.phones()
    print(f'inipath={ini.inipath}')
    print(f'mbplugin_root_path={settings.mbplugin_root_path}')
    expected_result1 = [
        ('region', 'p_test1'), ('monitor', 'TRUE'), ('alias', 'Иваныч'), ('number', '9161112233'), ('balancenotchangedmorethen', '40'),
        ('balancechangedlessthen', '1'), ('balancelessthen', '100.0'), ('turnofflessthen', '1')]
    # expected_result2 = {'nn': 1, 'Alias': 'Иваныч', 'region': 'p_test1', 'number': '9161112233', 'phonedescription': '', 'monitor': 'TRUE',
    #                    'balancelessthen': '100.0', 'turnofflessthen': '1', 'balancenotchangedmorethen': '40', 'balancechangedlessthen': '1', 'password2': '123password'}
    # expected_result2 = {'NN': 1, 'Alias': 'Иваныч', 'Region': 'p_test1', 'Number': '9161112233', 'PhoneDescription': '', 'Monitor': 'TRUE',
    #                    'BalanceLessThen': 100.0, 'TurnOffLessThen': 1, 'BalanceNotChangedMoreThen': 40, 'BalanceChangedLessThen': 1, 'Password2': '123password'}
    expected_result2 = {
        'NN': 1, 'Alias': 'Иваныч', 'Region': 'p_test1', 'Number': '9161112233', 'Monitor': 'TRUE', 'Password2': '123password',
        'nn': 1, 'alias': 'Иваныч', 'region': 'p_test1', 'number': '9161112233', 'monitor': 'TRUE',
        'balancelessthen': '100.0', 'turnofflessthen': '1', 'balancenotchangedmorethen': '40', 'balancechangedlessthen': '1', 'password2': '123password'}
    assert list(ini.ini['1'].items()) == expected_result1
    assert phones[('9161112233', 'p_test1')] == expected_result2
