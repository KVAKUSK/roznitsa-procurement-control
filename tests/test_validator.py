from scripts.validator import expand_case_pack, round_up_to_case, supplier_allowed, validate_row, load_rules


RULES = load_rules()


def base_row():
    return {
        "supplier": "Амбирс",
        "manufacturer": "ООО Тест",
        "price_list": "Амбирс",
        "brand": "Тест",
        "source_file": "price.xlsx",
        "source_sheet": "Лист1",
        "source_row": 10,
        "selected_name": "Товар тестовый 100 г",
        "original_price": 50,
        "price_unit": "шт",
        "stock": 1000,
        "case_pack": 10,
        "requested_qty": 95,
        "selected_qty": 100,
        "comparable_price": 50,
        "purchase_fact": 50,
    }


def test_ten_is_forbidden():
    row = base_row()
    row["supplier"] = "Тэн"
    ok, reason = supplier_allowed(row, RULES)
    assert not ok
    assert "запрещён" in reason


def test_che_man_su_is_forbidden():
    row = base_row()
    row["supplier"] = "Че Ман Су"
    ok, _ = supplier_allowed(row, RULES)
    assert not ok


def test_vostok_only_orimi_price_list_and_manufacturer():
    row = base_row()
    row.update({"supplier": "Восток", "manufacturer": "Орими", "price_list": "Орими"})
    ok, reason = supplier_allowed(row, RULES)
    assert ok, reason

    row["manufacturer"] = "Другой"
    ok, _ = supplier_allowed(row, RULES)
    assert not ok


def test_makheev_only_ambirs():
    row = base_row()
    row.update({"brand": "Махеевъ", "supplier": "Другой"})
    ok, _ = supplier_allowed(row, RULES)
    assert not ok

    row["supplier"] = "Амбирс"
    ok, reason = supplier_allowed(row, RULES)
    assert ok, reason


def test_multilevel_case_pack_expands_fully():
    assert expand_case_pack("1×5×32") == 160
    assert expand_case_pack("5x32") == 160
    assert expand_case_pack("1/8") == 8


def test_rounding_is_up_to_full_case():
    assert round_up_to_case(161, "1×5×32") == 320
    assert round_up_to_case(240, "1/8") == 240


def test_equal_purchase_fact_is_allowed():
    row = base_row()
    assert not any("Красная позиция" in e for e in validate_row(row, RULES))


def test_price_above_purchase_fact_is_red():
    row = base_row()
    row["comparable_price"] = 50.01
    assert any("Красная позиция" in e for e in validate_row(row, RULES))


def test_stock_limits_selected_quantity():
    row = base_row()
    row["stock"] = 90
    assert any("превышает подтверждённый остаток" in e for e in validate_row(row, RULES))
