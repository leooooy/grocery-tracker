"""读 data/prices.csv，聚合并写出 site/data.json。"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path


def _today() -> date:
    """间接获取今天，便于测试 monkeypatch。"""
    return date.today()


def _parse_row(row: dict) -> dict | None:
    """把 CSV 字符串行解析成 Python 类型；坏行返回 None。"""
    try:
        d = row["date"]
        datetime.strptime(d, "%Y-%m-%d")
        item = row["item"].strip()
        unit_price = float(row["unit_price"])
        quantity = float(row["quantity"])
        unit = row["unit"].strip()
        on_sale = row["on_sale"].strip().lower() == "true"
        merchant = (row.get("merchant", "") or "").strip()
        note = row.get("note", "") or ""
        if not item or not unit or unit_price <= 0 or quantity <= 0:
            return None
        return {
            "date": d,
            "item": item,
            "unit_price": unit_price,
            "quantity": quantity,
            "unit": unit,
            "on_sale": on_sale,
            "merchant": merchant,
            "note": note,
            "total": round(unit_price * quantity, 2),
        }
    except (KeyError, ValueError, TypeError):
        return None


def build_data(rows: list[dict]) -> dict:
    parsed = []
    for raw in rows:
        rec = _parse_row(raw)
        if rec is None:
            print(f"warning: 跳过坏行 {raw}", file=sys.stderr)
            continue
        parsed.append(rec)

    today = _today()
    cur_month = today.strftime("%Y-%m")

    total_spend = round(sum(r["total"] for r in parsed), 2)
    mtd_spend = round(
        sum(r["total"] for r in parsed if r["date"].startswith(cur_month)),
        2,
    )
    dates = sorted(r["date"] for r in parsed)
    date_range = [dates[0], dates[-1]] if dates else [None, None]

    by_item_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in parsed:
        by_item_groups[(r["item"], r["unit"])].append(r)

    by_item = []
    for (item, unit), items in by_item_groups.items():
        prices = [x["unit_price"] for x in items]
        spend = round(sum(x["total"] for x in items), 2)
        by_item.append({
            "item": item,
            "unit": unit,
            "count": len(items),
            "total_spend": spend,
            "avg_price": round(sum(prices) / len(prices), 2),
            "min_price": round(min(prices), 2),
            "max_price": round(max(prices), 2),
            "last_date": max(x["date"] for x in items),
        })
    by_item.sort(key=lambda b: b["total_spend"], reverse=True)

    by_month_groups: dict[str, list[dict]] = defaultdict(list)
    for r in parsed:
        by_month_groups[r["date"][:7]].append(r)

    by_month = [
        {
            "month": m,
            "total_spend": round(sum(x["total"] for x in items), 2),
            "record_count": len(items),
        }
        for m, items in sorted(by_month_groups.items())
    ]

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "records": parsed,
        "summary": {
            "total_records": len(parsed),
            "total_spend": total_spend,
            "month_to_date_spend": mtd_spend,
            "date_range": date_range,
        },
        "by_item": by_item,
        "by_month": by_month,
    }


def main(csv_path: str = "data/prices.csv",
         out_path: str = "site/data.json") -> int:
    src = Path(csv_path)
    dst = Path(out_path)
    rows: list[dict] = []
    if src.exists():
        with src.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    data = build_data(rows)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✓ 已写入 {dst}（{data['summary']['total_records']} 条记录）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
