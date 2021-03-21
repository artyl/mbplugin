import re
import pytest
import requests
import conftest
import sipnet  # pylint: disable=import-error

def test_sipnet():
    print(f'{sipnet.login_url=}')
    session = requests.session()
    response1 = session.get(sipnet.login_url)
    for chk in sipnet.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
    session.close()
