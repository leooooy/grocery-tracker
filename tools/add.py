"""CLI 工具：把一条购物记录追加到 data/prices.csv。"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import date as date_cls
from pathlib import Path

CSV_HEADER = ["date", "item", "unit_price", "quantity", "unit", "on_sale", "note"]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class Record:
    date: str
    item: str
    unit_price: float
    quantity: float
    unit: str
    on_sale: bool
    note: str

    def to_row(self) -> list[str]:
        return [
            self.date,
            self.item,
            f"{self.unit_price:.2f}",
            str(self.quantity),
            self.unit,
            "true" if self.on_sale else "false",
            self.note,
        ]


class ValidationError(ValueError):
    """用户输入数据校验失败。"""


def validate_record(
    *,
    date: str,
    item: str,
    unit_price: float,
    quantity: float,
    unit: str,
    on_sale: bool,
    note: str,
) -> Record:
    """校验并返回规范化后的 Record。任何非法字段抛 ValidationError。"""
    if not DATE_RE.match(date):
        raise ValidationError(f"日期格式错误（需 YYYY-MM-DD）：{date!r}")
    item = item.strip()
    if not item:
        raise ValidationError("品名不能为空")
    if unit_price <= 0:
        raise ValidationError(f"单价必须为正数：{unit_price}")
    if quantity <= 0:
        raise ValidationError(f"数量必须为正数：{quantity}")
    unit = unit.strip()
    if not unit:
        raise ValidationError("单位不能为空")
    return Record(
        date=date,
        item=item,
        unit_price=float(unit_price),
        quantity=float(quantity),
        unit=unit,
        on_sale=bool(on_sale),
        note=note.strip(),
    )


def append_record(csv_path: Path, record: Record) -> None:
    """把一条记录追加到 CSV。文件不存在则先写表头。"""
    write_header = not csv_path.exists()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(CSV_HEADER)
        writer.writerow(record.to_row())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把一条购物记录追加到 data/prices.csv",
    )
    parser.add_argument("item", nargs="?", help="品名（省略则进入交互模式）")
    parser.add_argument("unit_price", nargs="?", type=float, help="单价（元）")
    parser.add_argument("-q", "--quantity", type=float, help="数量")
    parser.add_argument("-u", "--unit", help="单位（斤/kg/盒…）")
    parser.add_argument("-d", "--date", help="日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--sale", dest="on_sale", action="store_true",
                        help="标记为打折商品")
    parser.add_argument("-n", "--note", default="", help="备注")
    parser.add_argument(
        "--csv", default="data/prices.csv",
        help="目标 CSV 路径（默认 data/prices.csv）",
    )
    return parser.parse_args(argv)


def main() -> int:
    ns = parse_args()
    csv_path = Path(ns.csv)

    if ns.item is not None and ns.unit_price is not None:
        if ns.quantity is None or ns.unit is None:
            print("错误：一行式录入需要同时提供 -q/--quantity 和 -u/--unit",
                  flush=True)
            return 2
        chosen_date = ns.date or date_cls.today().isoformat()
        try:
            rec = validate_record(
                date=chosen_date,
                item=ns.item,
                unit_price=ns.unit_price,
                quantity=ns.quantity,
                unit=ns.unit,
                on_sale=ns.on_sale,
                note=ns.note,
            )
        except ValidationError as e:
            print(f"错误：{e}", flush=True)
            return 1
        append_record(csv_path, rec)
        print(f"✓ 已写入 {csv_path}：{rec.item} {rec.unit_price:.2f} "
              f"x {rec.quantity} {rec.unit}")
        return 0

    return interactive_loop(csv_path)


def interactive_loop(csv_path: Path) -> int:
    """交互模式的占位 —— Task 4 实现。"""
    print("交互模式尚未实现（Task 4）。请使用一行式参数，例如：")
    print("  python tools/add.py 白菜 3.5 -q 2 -u 斤")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
