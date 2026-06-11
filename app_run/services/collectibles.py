from zipfile import BadZipFile

import openpyxl
from rest_framework.exceptions import ParseError

from app_run.models import CollectibleItem
from app_run.serializers import CollectibleItemSerializer

COLLECTIBLE_HEADER_TO_FIELD = {
    'name': 'name',
    'uid': 'uid',
    'value': 'value',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'url': 'picture',
}


def read_collectible_rows(file_obj) -> list[tuple[dict, tuple]]:
    file_obj.seek(0)
    try:
        workbook = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    except (BadZipFile, openpyxl.utils.exceptions.InvalidFileException) as exc:
        raise ParseError(f"Не удалось прочитать xlsx-файл: {exc}") from exc

    worksheet = workbook.active
    rows = worksheet.iter_rows(values_only=True)
    try:
        header_row = next(rows)
    except StopIteration:
        return []

    header = [str(cell).strip().lower() if cell is not None else '' for cell in header_row]
    try:
        field_by_index = [COLLECTIBLE_HEADER_TO_FIELD[cell] for cell in header]
    except KeyError as exc:
        raise ParseError(
            f"Неизвестная колонка в xlsx: {exc.args[0]!r}. "
            f"Ожидаются: {sorted(COLLECTIBLE_HEADER_TO_FIELD)}."
        ) from exc

    parsed: list[tuple[dict, tuple]] = []
    for raw_row in rows:
        if all(cell in (None, '') for cell in raw_row):
            continue

        row_data = {
            field: raw_row[idx] for idx, field in enumerate(field_by_index)
        }
        parsed.append((row_data, raw_row))
    return parsed


def split_valid_and_invalid(
    parsed_rows: list[tuple[dict, tuple]],
) -> tuple[list[CollectibleItem], list[tuple]]:
    valid_items: list[CollectibleItem] = []
    invalid_rows: list[tuple] = []

    for row_data, raw_row in parsed_rows:
        serializer = CollectibleItemSerializer(data=row_data)
        if serializer.is_valid():
            valid_items.append(CollectibleItem(**serializer.validated_data))
        else:
            invalid_rows.append(raw_row)

    return valid_items, invalid_rows
