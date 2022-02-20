import re
import requests
import conftest  # type: ignore # ignore import error
import zadarma  # pylint: disable=import-error
import store

def test_zadarma():
    print(f'login_url={zadarma.login_url}')
    session = store.Session()
    response1 = session.get(zadarma.login_url)
    for chk in zadarma.login_checkers:
        print(f'Check {chk}')
        assert re.search(chk, response1.text) is not None
