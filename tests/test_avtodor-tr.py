import re
import pytest
import requests
import conftest  # type: ignore # ignore import error
avtodor_tr = __import__('avtodor-tr')  # pylint: disable=import-error

def test_avtodor_tr():
    print(f'login_url={avtodor_tr.login_url}')
    session = requests.session()
    response1 = session.get(avtodor_tr.login_url)
    for chk in avtodor_tr.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
    session.close()
