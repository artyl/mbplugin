import re
import pytest
import requests
import conftest
import cardtel  # pylint: disable=import-error

def test_cardtel():
    print(f'{cardtel.login_url=}')
    session = requests.session()
    response1 = session.get(cardtel.login_url)
    for chk in cardtel.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
    session.close()
