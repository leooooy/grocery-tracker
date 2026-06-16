import sys
from pathlib import Path

import pytest

from tools.add import Record, append_record


def test_append_creates_file_with_header(tmp_csv: Path):
    rec = Record(
        date="2026-06-15",
        item="白菜",
        unit_price=3.5,
        quantity=2.0,
        unit="斤",
        on_sale=False,
        merchant="",
        note="",
    )
    append_record(tmp_csv, rec)

    content = tmp_csv.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert lines[0] == "date,item,unit_price,quantity,unit,on_sale,merchant,note"
    assert lines[1] == "2026-06-15,白菜,3.50,2.0,斤,false,,"


def test_append_to_existing_does_not_rewrite_header(tmp_csv_with_header: Path):
    rec = Record(
        date="2026-06-15",
        item="鸡蛋",
        unit_price=12.8,
        quantity=1.0,
        unit="盒",
        on_sale=True,
        merchant="钱大妈",
        note="30枚装",
    )
    append_record(tmp_csv_with_header, rec)

    lines = tmp_csv_with_header.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[1] == "2026-06-15,鸡蛋,12.80,1.0,盒,true,钱大妈,30枚装"


def test_note_with_comma_is_quoted(tmp_csv: Path):
    rec = Record(
        date="2026-06-15",
        item="番茄",
        unit_price=5.0,
        quantity=1.0,
        unit="斤",
        on_sale=False,
        merchant="",
        note="本地,有机",
    )
    append_record(tmp_csv, rec)

    lines = tmp_csv.read_text(encoding="utf-8").splitlines()
    assert lines[1] == '2026-06-15,番茄,5.00,1.0,斤,false,,"本地,有机"'


from tools.add import ValidationError, validate_record


def test_validate_rejects_empty_item():
    with pytest.raises(ValidationError, match="品名"):
        validate_record(date="2026-06-15", item="  ", unit_price=3.5,
                        quantity=2.0, unit="斤", on_sale=False, note="")


def test_validate_rejects_bad_date():
    with pytest.raises(ValidationError, match="日期"):
        validate_record(date="2026/06/15", item="白菜", unit_price=3.5,
                        quantity=2.0, unit="斤", on_sale=False, note="")


def test_validate_rejects_non_positive_price():
    with pytest.raises(ValidationError, match="单价"):
        validate_record(date="2026-06-15", item="白菜", unit_price=0,
                        quantity=2.0, unit="斤", on_sale=False, note="")


def test_validate_rejects_non_positive_quantity():
    with pytest.raises(ValidationError, match="数量"):
        validate_record(date="2026-06-15", item="白菜", unit_price=3.5,
                        quantity=-1, unit="斤", on_sale=False, note="")


def test_validate_trims_whitespace_and_returns_record():
    rec = validate_record(date="2026-06-15", item="  白菜  ", unit_price=3.5,
                          quantity=2.0, unit=" 斤 ", on_sale=False,
                          merchant=" 永辉 ", note="  ")
    assert rec.item == "白菜"
    assert rec.unit == "斤"
    assert rec.merchant == "永辉"
    assert rec.note == ""


def test_validate_accepts_empty_merchant():
    rec = validate_record(date="2026-06-15", item="白菜", unit_price=3.5,
                          quantity=2.0, unit="斤", on_sale=False,
                          merchant="  ", note="")
    assert rec.merchant == ""


from tools.add import convert_kg_to_jin


def test_convert_kg_variants_to_jin():
    for u in ["kg", "KG", "Kg", "千克", "公斤", " kg "]:
        unit, price, qty = convert_kg_to_jin(u, 10.0, 1.0)
        assert unit == "斤"
        assert price == 5.0     # 单价 ÷ 2
        assert qty == 2.0       # 数量 × 2
        assert price * qty == 10.0  # 花费守恒


def test_convert_non_kg_unit_unchanged():
    assert convert_kg_to_jin("斤", 3.5, 2.0) == ("斤", 3.5, 2.0)
    assert convert_kg_to_jin("个", 1.0, 5.0) == ("个", 1.0, 5.0)


def test_validate_record_converts_kg():
    rec = validate_record(date="2026-06-15", item="苹果", unit_price=10.0,
                          quantity=1.0, unit="kg", on_sale=False, note="")
    assert rec.unit == "斤"
    assert rec.unit_price == 5.0
    assert rec.quantity == 2.0
    assert rec.unit_price * rec.quantity == 10.0


def test_main_oneliner_kg_writes_jin(tmp_path, monkeypatch):
    csv_path = tmp_path / "prices.csv"
    monkeypatch.setattr(sys, "argv", [
        "add.py", "苹果", "10",
        "-q", "1", "-u", "kg", "-d", "2026-06-15",
        "--csv", str(csv_path),
    ])
    from tools.add import main
    rc = main()
    assert rc == 0
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines[1] == "2026-06-15,苹果,5.00,2.0,斤,false,,"


from tools.add import parse_args


def test_parse_args_oneliner_minimal():
    ns = parse_args(["白菜", "3.5", "-q", "2", "-u", "斤"])
    assert ns.item == "白菜"
    assert ns.unit_price == 3.5
    assert ns.quantity == 2.0
    assert ns.unit == "斤"
    assert ns.on_sale is False
    assert ns.note == ""
    assert ns.merchant == ""
    assert ns.date is None  # None 表示由 main() 用今天


def test_parse_args_oneliner_full():
    ns = parse_args([
        "鸡蛋", "12.8", "-q", "1", "-u", "盒",
        "--sale", "-n", "30枚装", "-d", "2026-06-14", "-m", "永辉",
    ])
    assert ns.on_sale is True
    assert ns.note == "30枚装"
    assert ns.merchant == "永辉"
    assert ns.date == "2026-06-14"


def test_main_oneliner_writes_record(tmp_path, monkeypatch):
    csv_path = tmp_path / "prices.csv"
    monkeypatch.setattr(sys, "argv", [
        "add.py", "白菜", "3.5",
        "-q", "2", "-u", "斤", "-d", "2026-06-15",
        "--csv", str(csv_path),
    ])
    from tools.add import main
    rc = main()
    assert rc == 0
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines[1] == "2026-06-15,白菜,3.50,2.0,斤,false,,"


def test_main_oneliner_with_merchant(tmp_path, monkeypatch):
    csv_path = tmp_path / "prices.csv"
    monkeypatch.setattr(sys, "argv", [
        "add.py", "白菜", "3.5",
        "-q", "2", "-u", "斤", "-d", "2026-06-15", "-m", "永辉",
        "--csv", str(csv_path),
    ])
    from tools.add import main
    rc = main()
    assert rc == 0
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines[1] == "2026-06-15,白菜,3.50,2.0,斤,false,永辉,"


from tools.add import top_units


def test_top_units_returns_top_n_by_frequency(tmp_csv_with_header: Path):
    tmp_csv_with_header.write_text(
        "date,item,unit_price,quantity,unit,on_sale,note\n"
        "2026-06-01,白菜,3.0,1,斤,false,\n"
        "2026-06-02,白菜,3.0,1,斤,false,\n"
        "2026-06-03,鸡蛋,12.0,1,盒,false,\n"
        "2026-06-04,苹果,5.0,1,kg,false,\n"
        "2026-06-05,苹果,5.0,1,kg,false,\n"
        "2026-06-06,苹果,5.0,1,kg,false,\n",
        encoding="utf-8",
    )
    units = top_units(tmp_csv_with_header, n=3)
    assert units == [("kg", 3), ("斤", 2), ("盒", 1)]


def test_top_units_on_missing_file_returns_empty(tmp_path):
    assert top_units(tmp_path / "missing.csv") == []
