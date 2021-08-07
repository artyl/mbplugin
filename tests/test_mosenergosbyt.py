import pytest
import conftest  # type: ignore # ignore import error
import mosenergosbyt  # pylint: disable=import-error

@pytest.mark.slow
def test_mosenergosbyt_logon_selectors():
    print(f'login_url={mosenergosbyt.login_url}')
    self = mosenergosbyt.browserengine('test', 'test', 'test', login_url=mosenergosbyt.login_url, user_selectors=mosenergosbyt.user_selectors)
    self.main('check_logon')
