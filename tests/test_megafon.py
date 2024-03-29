import re
import requests
import conftest  # type: ignore # ignore import error
import megafon  # pylint: disable=import-error
import store

def test_megafon():
    print(f'login_url={megafon.login_url}')
    session = store.Session()
    response1 = session.get(megafon.login_url)
    for chk in megafon.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
    print(f'login_url={megafon.login_url_old_lk}')
    session = store.Session()
    response1 = session.get(megafon.login_url_old_lk)
    for chk in megafon.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None