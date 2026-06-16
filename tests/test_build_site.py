from datetime import date

from tools.build_site import build_data


SAMPLE_ROWS = [
    {"date": "2026-04-10", "item": "白菜", "unit_price": "3.00",
     "quantity": "2", "unit": "斤", "on_sale": "false", "note": ""},
    {"date": "2026-04-15", "item": "白菜", "unit_price": "3.50",
     "quantity": "1", "unit": "斤", "on_sale": "true", "note": "促销"},
    {"date": "2026-05-01", "item": "白菜", "unit_price": "4.00",
     "quantity": "2", "unit": "斤", "on_sale": "false", "note": ""},
    {"date": "2026-05-20", "item": "鸡蛋", "unit_price": "12.00",
     "quantity": "1", "unit": "盒", "on_sale": "false", "note": ""},
    {"date": "2026-06-01", "item": "鸡蛋", "unit_price": "13.00",
     "quantity": "2", "unit": "盒", "on_sale": "false", "note": ""},
]


def test_build_data_summary(monkeypatch):
    # 锁定 "今天" 是 2026-06-15，让 month_to_date 测试可复现
    import tools.build_site as bs
    monkeypatch.setattr(bs, "_today", lambda: date(2026, 6, 15))

    data = build_data(SAMPLE_ROWS)
    s = data["summary"]
    assert s["total_records"] == 5
    # 总花费 = 3*2 + 3.5*1 + 4*2 + 12*1 + 13*2 = 6 + 3.5 + 8 + 12 + 26 = 55.5
    assert s["total_spend"] == 55.5
    # 本月（2026-06）只有 1 条：鸡蛋 13.0 * 2 = 26
    assert s["month_to_date_spend"] == 26.0
    assert s["date_range"] == ["2026-04-10", "2026-06-01"]


def test_build_data_by_item(monkeypatch):
    import tools.build_site as bs
    monkeypatch.setattr(bs, "_today", lambda: date(2026, 6, 15))
    data = build_data(SAMPLE_ROWS)
    by_item = {(b["item"], b["unit"]): b for b in data["by_item"]}

    cabbage = by_item[("白菜", "斤")]
    assert cabbage["count"] == 3
    # spend = 6 + 3.5 + 8 = 17.5
    assert cabbage["total_spend"] == 17.5
    # 三个 unit_price: 3, 3.5, 4 → 均价 3.5、min 3、max 4
    assert cabbage["avg_price"] == 3.5
    assert cabbage["min_price"] == 3.0
    assert cabbage["max_price"] == 4.0
    assert cabbage["last_date"] == "2026-05-01"

    eggs = by_item[("鸡蛋", "盒")]
    assert eggs["count"] == 2
    assert eggs["total_spend"] == 38.0  # 12 + 26
    assert eggs["last_date"] == "2026-06-01"


def test_build_data_by_month(monkeypatch):
    import tools.build_site as bs
    monkeypatch.setattr(bs, "_today", lambda: date(2026, 6, 15))
    data = build_data(SAMPLE_ROWS)
    by_month = {b["month"]: b for b in data["by_month"]}

    # 2026-04: 白菜 6 + 3.5 = 9.5, 共 2 条
    assert by_month["2026-04"] == {
        "month": "2026-04", "total_spend": 9.5, "record_count": 2,
    }
    # 2026-05: 白菜 8 + 鸡蛋 12 = 20, 共 2 条
    assert by_month["2026-05"] == {
        "month": "2026-05", "total_spend": 20.0, "record_count": 2,
    }
    # 2026-06: 鸡蛋 26, 1 条
    assert by_month["2026-06"] == {
        "month": "2026-06", "total_spend": 26.0, "record_count": 1,
    }

    # 月份升序
    months_order = [b["month"] for b in data["by_month"]]
    assert months_order == ["2026-04", "2026-05", "2026-06"]


def test_build_data_skips_bad_rows(monkeypatch, capsys):
    import tools.build_site as bs
    monkeypatch.setattr(bs, "_today", lambda: date(2026, 6, 15))
    rows = SAMPLE_ROWS + [
        {"date": "bad-date", "item": "x", "unit_price": "1",
         "quantity": "1", "unit": "个", "on_sale": "false", "note": ""},
        {"date": "2026-06-10", "item": "y", "unit_price": "-1",
         "quantity": "1", "unit": "个", "on_sale": "false", "note": ""},
    ]
    data = build_data(rows)
    assert data["summary"]["total_records"] == 5  # 坏行被跳过
    err = capsys.readouterr().err
    assert "warning" in err
