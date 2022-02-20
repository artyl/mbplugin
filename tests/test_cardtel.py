import re
import requests
import conftest  # type: ignore # ignore import error
import cardtel  # pylint: disable=import-error
import store

def test_cardtel():
    print(f'login_url{cardtel.login_url}')
    session = store.Session()
    response1 = session.get(cardtel.login_url)
    for chk in cardtel.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
