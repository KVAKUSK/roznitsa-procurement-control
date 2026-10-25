from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "rules" / "procurement_rules.json"


def load_rules(path: Path = RULES_PATH) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expand_case_pack(value: Any) -> int | None:
    """Return transport-case unit count from 8, '1/8', '5x32', '1×5×32'."""
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float) and value.is_integer() and value > 0:
        return int(value)

    text = str(value).strip().lower().replace("х", "x").replace("×", "x")
    if "/" in text and "x" not in text:
        parts = [p.strip() for p in text.split("/") if p.strip()]
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            return int(parts[-1])
    if "x" in text:
        parts = [p.strip() for p in text.split("x") if p.strip()]
        if parts and all(p.isdigit() for p in parts):
            result = 1
            for part in parts:
                result *= int(part)
            return result
    if text.isdigit():
        return int(text)
    return None


def round_up_to_case(requested_qty: float, case_pack: Any) -> int:
    pack = expand_case_pack(case_pack)
    if requested_qty < 0:
        raise ValueError("requested_qty must be non-negative")
    if not pack:
        raise ValueError("case_pack is not confirmed")
    return int(math.ceil(requested_qty / pack) * pack)


def supplier_allowed(row: Dict[str, Any], rules: Dict[str, Any]) -> tuple[bool, str | None]:
    supplier = str(row.get("supplier", "")).strip()
    manufacturer = str(row.get("manufacturer", "")).strip()
    price_list = str(row.get("price_list", "")).strip()

    forbidden = set(rules["supplier_rules"]["forbidden"])
    if supplier in forbidden:
        return False, f"Поставщик {supplier} запрещён"

    conditional = rules["supplier_rules"].get("conditional", {}).get(supplier)
    if conditional:
        allowed = conditional["allowed_only_when"]
        if manufacturer != allowed["manufacturer"] or price_list != allowed["price_list"]:
            return False, f"{supplier} разрешён только для производителя Орими из прайса Орими"

    locks = rules["supplier_rules"].get("brand_supplier_lock", {})
    brand = str(row.get("brand", "")).strip()
    if brand in locks and supplier != locks[brand]:
        return False, f"{brand} разрешён только у поставщика {locks[brand]}"

    return True, None


def validate_traceability(row: Dict[str, Any], rules: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field in rules["traceability"]["required_fields"]:
        value = row.get(field)
        if value is None or str(value).strip() == "":
            errors.append(f"Не подтверждено обязательное поле: {field}")
    return errors


def validate_row(row: Dict[str, Any], rules: Dict[str, Any] | None = None) -> List[str]:
    rules = rules or load_rules()
    errors: List[str] = []

    allowed, reason = supplier_allowed(row, rules)
    if not allowed and reason:
        errors.append(reason)

    errors.extend(validate_traceability(row, rules))

    case_pack = expand_case_pack(row.get("case_pack"))
    if not case_pack:
        errors.append("Вложимость не подтверждена")

    requested = row.get("requested_qty")
    selected = row.get("selected_qty")
    stock = row.get("stock")

    if requested is not None and selected is not None and case_pack:
        minimum = round_up_to_case(float(requested), case_pack)
        if float(selected) < minimum:
            errors.append("Количество округлено вниз или ниже полного короба")
        if int(selected) % case_pack != 0:
            errors.append("Количество не кратно транспортной вложимости")

    if stock is not None and selected is not None and float(selected) > float(stock):
        errors.append("Выбранное количество превышает подтверждённый остаток")

    comparable_price = row.get("comparable_price")
    purchase_fact = row.get("purchase_fact")
    if comparable_price is not None and purchase_fact is not None:
        if float(comparable_price) > float(purchase_fact):
            errors.append("Красная позиция: сопоставимая цена выше Закуп ФАКТ")

    original_price = row.get("original_price")
    price_unit = str(row.get("price_unit", "")).strip()
    if original_price is None or not price_unit:
        errors.append("Исходная цена поставщика и её единица должны быть сохранены")

    source_fields = ["source_file", "source_sheet", "source_row"]
    if any(row.get(field) in (None, "") for field in source_fields):
        errors.append("Неполная трассировка источника прайса")

    return sorted(set(errors))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate one procurement row from JSON")
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.json_file.read_text(encoding="utf-8"))
    problems = validate_row(payload)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        raise SystemExit(1)
    print("OK")
