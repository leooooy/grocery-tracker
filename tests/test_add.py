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
        note="",
    )
    append_record(tmp_csv, rec)

    content = tmp_csv.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert lines[0] == "date,item,unit_price,quantity,unit,on_sale,note"
    assert lines[1] == "2026-06-15,白菜,3.50,2.0,斤,false,"


def test_append_to_existing_does_not_rewrite_header(tmp_csv_with_header: Path):
    rec = Record(
        date="2026-06-15",
        item="鸡蛋",
        unit_price=12.8,
        quantity=1.0,
        unit="盒",
        on_sale=True,
        note="30枚装",
    )
    append_record(tmp_csv_with_header, rec)

    lines = tmp_csv_with_header.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[1] == "2026-06-15,鸡蛋,12.80,1.0,盒,true,30枚装"


def test_note_with_comma_is_quoted(tmp_csv: Path):
    rec = Record(
        date="2026-06-15",
        item="番茄",
        unit_price=5.0,
        quantity=1.0,
        unit="斤",
        on_sale=False,
        note="本地,有机",
    )
    append_record(tmp_csv, rec)

    lines = tmp_csv.read_text(encoding="utf-8").splitlines()
    assert lines[1] == '2026-06-15,番茄,5.00,1.0,斤,false,"本地,有机"'


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
                          quantity=2.0, unit=" 斤 ", on_sale=False, note="  ")
    assert rec.item == "白菜"
    assert rec.unit == "斤"
    assert rec.note == ""


from tools.add import parse_args


def test_parse_args_oneliner_minimal():
    ns = parse_args(["白菜", "3.5", "-q", "2", "-u", "斤"])
    assert ns.item == "白菜"
    assert ns.unit_price == 3.5
    assert ns.quantity == 2.0
    assert ns.unit == "斤"
    assert ns.on_sale is False
    assert ns.note == ""
    assert ns.date is None  # None 表示由 main() 用今天


def test_parse_args_oneliner_full():
    ns = parse_args([
        "鸡蛋", "12.8", "-q", "1", "-u", "盒",
        "--sale", "-n", "30枚装", "-d", "2026-06-14",
    ])
    assert ns.on_sale is True
    assert ns.note == "30枚装"
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
    assert lines[1] == "2026-06-15,白菜,3.50,2.0,斤,false,"
