import pytest
import conftest  # type: ignore # ignore import error
import onlime  # pylint: disable=import-error

@pytest.mark.slow
def test_onlime_logon_selectors():
    print(f'login_url={onlime.login_url}')
    self = onlime.browserengine('test', 'test', 'test', login_url=onlime.login_url, user_selectors=onlime.user_selectors)
    self.main('check_logon')
