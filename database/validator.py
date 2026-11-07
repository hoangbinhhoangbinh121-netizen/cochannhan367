"""Kiểm tra dữ liệu theo schema (không phụ thuộc thư viện ngoài)."""
from __future__ import annotations

from typing import Any


class ValidationError(ValueError):
    pass


_TYPES = {"int": int, "float": (int, float), "str": str, "bool": bool,
          "dict": dict, "list": list, "any": object}


class Field:
    def __init__(self, type_: str, *, required: bool = True, nullable: bool = False,
                 min: float | None = None, max: float | None = None,
                 choices: list | None = None, schema: dict | None = None,
                 items: "Field | None" = None):
        if type_ not in _TYPES:
            raise ValueError(f"type không hợp lệ: {type_}")
        self.type, self.required, self.nullable = type_, required, nullable
        self.min, self.max, self.choices = min, max, choices
        self.schema, self.items = schema, items


def validate(data: Any, schema: dict[str, Field], path: str = "$") -> None:
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: cần dict")
    for key, field in schema.items():
        if key not in data:
            if field.required:
                raise ValidationError(f"{path}.{key}: thiếu trường bắt buộc")
            continue
        _check(data[key], field, f"{path}.{key}")


def _check(value: Any, field: Field, path: str) -> None:
    if value is None:
        if field.nullable:
            return
        raise ValidationError(f"{path}: không được null")
    if field.type != "any":
        expected = _TYPES[field.type]
        if isinstance(value, bool) and field.type in ("int", "float"):
            raise ValidationError(f"{path}: bool không phải số")
        if not isinstance(value, expected):
            raise ValidationError(f"{path}: cần {field.type}, nhận {type(value).__name__}")
    if field.min is not None and value < field.min:
        raise ValidationError(f"{path}: {value} < min {field.min}")
    if field.max is not None and value > field.max:
        raise ValidationError(f"{path}: {value} > max {field.max}")
    if field.choices is not None and value not in field.choices:
        raise ValidationError(f"{path}: {value!r} không thuộc {field.choices}")
    if field.schema is not None:
        validate(value, field.schema, path)
    if field.items is not None:
        for i, item in enumerate(value):
            _check(item, field.items, f"{path}[{i}]")
