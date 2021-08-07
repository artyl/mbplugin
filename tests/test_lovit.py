import pytest
import conftest  # type: ignore # ignore import error
import lovit  # pylint: disable=import-error

@pytest.mark.slow
def test_lovit_logon_selectors():
    print(f'login_url={lovit.login_url}')
    self = lovit.browserengine('test', 'test', 'test', login_url=lovit.login_url, user_selectors=lovit.user_selectors)
    self.main('check_logon')
