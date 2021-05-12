import re
import pytest
import requests
import conftest
import megafon  # pylint: disable=import-error

def test_megafon():
    print(f'login_url={megafon.login_url}')
    session = requests.session()
    response1 = session.get(megafon.login_url)
    for chk in megafon.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
    session.close()
