import re
import requests
import conftest  # type: ignore # ignore import error
import sipnet  # pylint: disable=import-error

def test_sipnet():
    print(f'login_url={sipnet.login_url}')
    session = requests.session()
    response1 = session.get(sipnet.login_url)
    for chk in sipnet.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
    session.close()
