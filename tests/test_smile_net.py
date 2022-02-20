import re
import requests
import conftest  # type: ignore # ignore import error
smile_net = __import__('smile-net')  # pylint: disable=import-error
import store

def test_smile_net():
    # Fix for [SSL: DH_KEY_TOO_SMALL] dh key too small (_ssl.c:1131)
    # https://stackoverflow.com/questions/38015537/python-requests-exceptions-sslerror-dh-key-too-small
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
    print(f'login_url={smile_net.login_url}')
    session = store.Session()
    response1 = session.get(smile_net.login_url)
    for chk in smile_net.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
