import re
import pytest
import requests
import conftest
import tele2  # pylint: disable=import-error

def test_strelka():
    session = requests.Session()
    headers = {
        'Tele2-User-Agent': '"mytele2-app/3.17.0"; "unknown"; "Android/9"; "Build/12998710"',
        'User-Agent': 'okhttp/4.2.0', 'X-API-Version': '1',
        'Content-Type': 'application/x-www-form-urlencoded'
    }    
    assert session.get(f'{tele2.api_url}79161234567/balance', headers=headers).text == '{"meta":{"status":"ERROR","message":"User must be logged in."}}'
    session.close()
