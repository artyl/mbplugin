import re
import pytest
import requests
import conftest
import zadarma  # pylint: disable=import-error

def test_zadarma():
    print(f'login_url={zadarma.login_url}')
    session = requests.session()
    response1 = session.get(zadarma.login_url)
    for chk in zadarma.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
    session.close()
