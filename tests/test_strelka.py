import conftest  # type: ignore # ignore import error
import strelka  # pylint: disable=import-error

def test_strelka():
    result = strelka.get_card_info('12345678901')
    assert result == {"__all__": ["Карта не найдена"]} or result == {"__all__": ["Внутренняя ошибка сервиса"]}
