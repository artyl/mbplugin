import requests
import conftest  # type: ignore # ignore import error
import sodexo  # pylint: disable=import-error
import store

def test_sodexo():
    print(f'login_url={sodexo.api_url}')
    session = store.Session()
    response1 = session.get(f'{sodexo.api_url}cards/1234567890123')
    expected_result1 = '{"status":"FAIL","messages":[{"type":"ERROR","context":"FIELD","code":"EAN_OUT_OF_RANGE","path":"ean"}]}'
    assert response1.text == expected_result1
    response2 = session.get(f'{sodexo.api_url}virtual-cards/+79161234567/1234')
    expected_result2 = '{"status":"NO_CARDS_WITH_PANTAIL","messages":[{"type":"ERROR","context":"LOCAL","code":"NO_CARDS_WITH_PANTAIL"}]}'
    assert response2.text == expected_result2
