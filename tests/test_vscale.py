import pytest
import conftest  # type: ignore # ignore import error
import vscale  # pylint: disable=import-error

@pytest.mark.slow
def test_vscale_logon_selectors():
    print(f'login_url={vscale.login_url}')
    self = vscale.browserengine('test', 'test', 'test', login_url=vscale.login_url, user_selectors=vscale.user_selectors)
    self.main('check_logon')
