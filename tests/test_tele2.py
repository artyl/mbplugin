import requests
import conftest  # type: ignore # ignore import error
import tele2  # pylint: disable=import-error
import store

def test_strelka():
    session = store.Session()
    assert session.get(f'{tele2.api_url}79161234567/balance', headers=tele2.api_headers).text == '{"meta":{"status":"ERROR","message":"User must be logged in."}}'
