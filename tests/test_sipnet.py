import re
import requests
import conftest  # type: ignore # ignore import error
import sipnet  # pylint: disable=import-error
import store
import urllib3

def test_sipnet():
    print(f'login_url={sipnet.login_url}')
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = store.Session()
    response1 = session.get(sipnet.login_url, verify=sipnet.VERIFY_SSL)
    for chk in sipnet.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
