import conftest  # type: ignore # ignore import error
import strelka  # pylint: disable=import-error

def test_strelka():
    assert strelka.get_card_info('12345678901') == {"__all__":["Карта не найдена"]}
