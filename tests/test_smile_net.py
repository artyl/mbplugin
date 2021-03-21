import re
import pytest
import requests
import conftest
smile_net = __import__('smile-net')  # pylint: disable=import-error

def test_smile_net():
    print(f'{smile_net.login_url=}')
    session = requests.session()
    response1 = session.get(smile_net.login_url)
    for chk in smile_net.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
    session.close()
