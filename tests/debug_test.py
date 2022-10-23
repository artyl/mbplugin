import sys, os, pdb, logging

if __name__ == '__main__':
    # ??? import pdb, rlcompleter;pdb.Pdb.complete = rlcompleter.Completer(locals()).complete
    # import sys,os;sys.path.insert(0, os.path.abspath('plugin')); sys.path.insert(0, os.path.abspath('tests')); from test_dbengine import *;test_create_db()

    sys.path.insert(0, os.path.abspath('plugin'))
    sys.path.insert(0, os.path.abspath('tests'))

    import test_dbengine  # noqa: E402
    logging.getLogger().setLevel(logging.DEBUG)
    print(f'{logging.getLogger().getEffectiveLevel()=}')
    # test_create_db()
    # ??? python -m pdb -c "b test_dbengine.py:18" -c c tests/debug_test.py
    # python\python -i tests\debug_test.py
    print('use\nb test_dbengine.py:41')
    #pdb.set_trace()  # b test_dbengine.py:18
    # test_create_db()
    tst = test_dbengine.Test()
    tst.setup_method()
    tst.test_create_db()
    tst.test_mdb_import()
    tst.test_flags()
    tst.teardown_method()
