import pytest
import conftest  # type: ignore # ignore import error
import uminet  # pylint: disable=import-error

@pytest.mark.slow
def test_test3_logon_selectors():
    print(f'login_url={uminet.login_url}')
    self = uminet.browserengine('test', 'test', 'test', login_url=uminet.login_url, user_selectors=uminet.user_selectors)
    self.main('check_logon')
