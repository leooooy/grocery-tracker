"""CLI 工具：把一条购物记录追加到 data/prices.csv。"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
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
