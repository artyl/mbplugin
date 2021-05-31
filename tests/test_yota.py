import pytest
import conftest
import yota  # pylint: disable=import-error

@pytest.mark.slow
def test_yota_logon_selectors():
    print(f'login_url={yota.login_url}')
    self = yota.browserengine('test', 'test', 'test', login_url=yota.login_url, user_selectors=yota.user_selectors)
    self.main('check_logon')
