from __future__ import annotations

from typing import Any


def parse_scalar(value: str) -> Any:
    raw = value.strip()
    if not raw:
        return ""
    lower = raw.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in {"null", "none"}:
        return None
    if raw.startswith(("'", '"')) and raw.endswith(("'", '"')) and len(raw) >= 2:
        return raw[1:-1]
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part) for part in inner.split(",")]
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _skip_ignored(lines: list[str], index: int) -> int:
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped and not stripped.startswith("#"):
            break
        index += 1
    return index


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_mapping_entries(lines: list[str], index: int, indent: int, initial: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
    mapping = dict(initial or {})
    while True:
        index = _skip_ignored(lines, index)
        if index >= len(lines):
            break
        line = lines[index]
        stripped = line.strip()
        current_indent = _line_indent(line)
        if current_indent < indent:
            break
        if current_indent != indent or stripped.startswith("- "):
            break
        if ":" not in stripped:
            raise ValueError(f"Invalid mapping entry near line {index + 1}: {line}")
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        index += 1
        if value:
            mapping[key] = parse_scalar(value)
            continue
        nested, index = _parse_block(lines, index, indent + 2)
        mapping[key] = nested
    return mapping, index


def _parse_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    items: list[Any] = []
    while True:
        index = _skip_ignored(lines, index)
        if index >= len(lines):
            break
        line = lines[index]
        stripped = line.strip()
        current_indent = _line_indent(line)
        if current_indent < indent:
            break
        if current_indent != indent or not stripped.startswith("- "):
            break

        inline = stripped[2:].strip()
        index += 1
        if not inline:
            nested, index = _parse_block(lines, index, indent + 2)
            items.append(nested)
            continue

        if ":" in inline:
            key, raw_value = inline.split(":", 1)
            item: dict[str, Any] = {}
            key = key.strip()
            value = raw_value.strip()
            if value:
                item[key] = parse_scalar(value)
            else:
                nested, index = _parse_block(lines, index, indent + 4)
                item[key] = nested
            item, index = _parse_mapping_entries(lines, index, indent + 2, initial=item)
            items.append(item)
            continue

        items.append(parse_scalar(inline))
    return items, index


def _parse_block(lines: list[str], index: int, indent: int) -> tuple[Any, int]:
    index = _skip_ignored(lines, index)
    if index >= len(lines):
        return {}, index
    line = lines[index]
    current_indent = _line_indent(line)
    stripped = line.strip()
    if current_indent < indent:
        return {}, index
    if current_indent != indent:
        raise ValueError(f"Unsupported indentation near line {index + 1}: {line}")
    if stripped.startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_mapping_entries(lines, index, indent)


def parse_yaml_document(text: str) -> Any:
    lines = text.splitlines()
    value, _ = _parse_block(lines, 0, 0)
    return value


def parse_yaml_mapping(block: str) -> dict[str, Any]:
    value = parse_yaml_document(block)
    if not isinstance(value, dict):
        raise ValueError("Expected a YAML mapping.")
    return value


def parse_navigation_yaml(text: str) -> list[dict[str, Any]]:
    value = parse_yaml_document(text)
    if not isinstance(value, list):
        raise ValueError("Expected navigation.yml to contain a top-level list.")
    return value
