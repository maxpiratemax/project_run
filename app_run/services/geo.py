"""Утилиты для работы с географическими координатами."""

from django.core.validators import MaxValueValidator, MinValueValidator


LATITUDE_MIN = -90
LATITUDE_MAX = 90
LONGITUDE_MIN = -180
LONGITUDE_MAX = 180


def latitude_validators():
    """Валидаторы Django для поля широты."""
    return [
        MinValueValidator(LATITUDE_MIN),
        MaxValueValidator(LATITUDE_MAX),
    ]


def longitude_validators():
    """Валидаторы Django для поля долготы."""
    return [
        MinValueValidator(LONGITUDE_MIN),
        MaxValueValidator(LONGITUDE_MAX),
    ]


def is_valid_coordinate(latitude: float, longitude: float) -> bool:
    """Проверяет, что широта и долгота находятся в допустимых диапазонах."""
    return (
        LATITUDE_MIN <= latitude <= LATITUDE_MAX
        and LONGITUDE_MIN <= longitude <= LONGITUDE_MAX
    )
