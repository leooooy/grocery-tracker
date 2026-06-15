# Grocery Tracker 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建一个本地 Python CLI 录入 + GitHub Pages 静态网页展示的日常买菜价格追踪器。

**Architecture:** 用户在本地终端运行 `python tools/add.py` 把购物记录追加到 `data/prices.csv`，手动 `git push` 后由 GitHub Action 跑 `tools/build_site.py` 生成 `site/data.json`，并将 `site/` 部署到 GitHub Pages。前端是单页 HTML + Chart.js，通过 `fetch('./data.json')` 加载数据并渲染走势图、月度花费、品类排行。

**Tech Stack:** Python 3.11+（标准库 csv/argparse/json/datetime/collections）、pytest、HTML + Chart.js CDN、GitHub Actions（actions/checkout、setup-python、upload-pages-artifact、deploy-pages）。

**项目根目录：** `D:\grocery-tracker\`（所有相对路径基于此目录）

**Spec：** `docs/specs/2026-06-15-grocery-tracker-design.md`

---

## File Structure

| 文件 | 职责 |
|---|---|
| `data/prices.csv` | 主数据；CLI 追加，build 脚本读取 |
| `tools/add.py` | CLI 录入工具（CLI 入口 + 业务函数都在此） |
| `tools/build_site.py` | 读 CSV、聚合、写 `site/data.json` |
| `tools/__init__.py` | 空文件，允许测试 `import tools.add` |
| `tests/test_add.py` | `tools/add.py` 的单元测试 |
| `tests/test_build_site.py` | `tools/build_site.py` 的单元测试 |
| `tests/conftest.py` | 共用 fixture（临时 CSV 文件等） |
| `site/index.html` | 单页 HTML，引入 Chart.js CDN + app.js |
| `site/app.js` | 加载 data.json、渲染所有图表与表格 |
| `site/data.json` | build 脚本产物；初始为空骨架，方便本地直接打开 |
| `.github/workflows/build-and-deploy.yml` | push 触发构建 + 部署 |
| `requirements.txt` | 只有测试依赖 `pytest` |
| `.gitignore` | 忽略 venv、缓存、系统垃圾 |
| `README.md` | 安装、使用、推送、首次启用 Pages 步骤 |

**模块边界：**
- `tools/add.py` 把"业务函数"（`validate_record`、`append_record`、`parse_args`）和"CLI 入口" `main()` 分开，便于单元测试。
- `tools/build_site.py` 把 `build_data(records) -> dict` 设为纯函数，I/O 在 `main()` 里，便于测试聚合逻辑。
- 前端是纯静态，无构建工具。`app.js` 不分模块文件，控制在 ~200 行内。

---

## Task 1: 项目骨架与 git 初始化

**Files:**
- Create: `D:/grocery-tracker/.gitignore`
- Create: `D:/grocery-tracker/requirements.txt`
- Create: `D:/grocery-tracker/README.md`
- Create: `D:/grocery-tracker/data/prices.csv`
- Create: `D:/grocery-tracker/tools/__init__.py`
- Create: `D:/grocery-tracker/tests/__init__.py`

- [ ] **Step 1: 创建 .gitignore**

文件内容：

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
.pytest_cache/

# OS
.DS_Store
Thumbs.db
desktop.ini

# IDE
.vscode/
.idea/
*.swp
```

- [ ] **Step 2: 创建 requirements.txt**

文件内容：

```
pytest>=8.0
```

- [ ] **Step 3: 创建空 CSV（只含表头）**

`data/prices.csv` 内容（注意 UTF-8 无 BOM，末尾保留一个换行）：

```csv
date,item,unit_price,quantity,unit,on_sale,note
```

- [ ] **Step 4: 创建占位 README**

`README.md` 内容（完整版在 Task 7 完成）：

```markdown
# grocery-tracker

日常买菜价格追踪器。CLI 录入 + GitHub Pages 趋势可视化。

> 实施进行中，使用说明见 Task 7 完成后的完整 README。
```

- [ ] **Step 5: 创建空的 `tools/__init__.py` 和 `tests/__init__.py`**

两个文件都是空文件（0 字节），仅用于让 pytest 把 tests/ 当成包。

- [ ] **Step 6: 初始化 git 仓库并首次提交**

在 `D:\grocery-tracker\` 下运行：

```bash
git init
git branch -M main
git add .gitignore requirements.txt README.md data/prices.csv tools/__init__.py tests/__init__.py docs/
git commit -m "chore: 项目骨架与 spec"
```

预期输出：包含 8 个以上文件被加入的提交。

---

## Task 2: CSV 写入与校验函数（TDD）

**Files:**
- Create: `D:/grocery-tracker/tests/conftest.py`
- Create: `D:/grocery-tracker/tests/test_add.py`
- Create: `D:/grocery-tracker/tools/add.py`

- [ ] **Step 1: 写 conftest.py 提供临时 CSV fixture**

`tests/conftest.py` 内容：

```python
import pytest
from pathlib import Path


@pytest.fixture
def tmp_csv(tmp_path: Path) -> Path:
    """返回一个临时目录下的 prices.csv 路径（文件尚未创建）。"""
    return tmp_path / "prices.csv"


@pytest.fixture
def tmp_csv_with_header(tmp_path: Path) -> Path:
    """返回一个已写入表头的临时 prices.csv 路径。"""
    p = tmp_path / "prices.csv"
    p.write_text(
        "date,item,unit_price,quantity,unit,on_sale,note\n",
        encoding="utf-8",
    )
    return p
```

- [ ] **Step 2: 写第一个失败测试 —— `append_record` 在文件不存在时创建表头**

`tests/test_add.py` 内容：

```python
from pathlib import Path

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
```

- [ ] **Step 3: 运行测试，确认失败**

在 `D:\grocery-tracker\` 下：

```bash
pytest tests/test_add.py::test_append_creates_file_with_header -v
```

预期：FAIL，错误是 `ImportError: cannot import name 'Record' from 'tools.add'` 或类似。

- [ ] **Step 4: 实现 `Record` 和 `append_record` 最小版本**

`tools/add.py` 内容（仅本步所需的部分）：

```python
"""CLI 工具：把一条购物记录追加到 data/prices.csv。"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

CSV_HEADER = ["date", "item", "unit_price", "quantity", "unit", "on_sale", "note"]


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


def append_record(csv_path: Path, record: Record) -> None:
    """把一条记录追加到 CSV。文件不存在则先写表头。"""
    write_header = not csv_path.exists()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(CSV_HEADER)
        writer.writerow(record.to_row())
```

- [ ] **Step 5: 运行测试，确认通过**

```bash
pytest tests/test_add.py::test_append_creates_file_with_header -v
```

预期：PASS。

- [ ] **Step 6: 加测试 —— 追加到已有文件不重写表头**

在 `tests/test_add.py` 末尾追加：

```python
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
```

运行：

```bash
pytest tests/test_add.py -v
```

预期：两个测试都 PASS。

- [ ] **Step 7: 加测试 —— 备注含逗号需要转义**

在 `tests/test_add.py` 末尾追加：

```python
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
```

运行：

```bash
pytest tests/test_add.py -v
```

预期：三个测试都 PASS（`csv` 模块默认就会引号转义）。

- [ ] **Step 8: 加测试 —— `validate_record` 拒绝坏数据**

在 `tests/test_add.py` 末尾追加：

```python
import pytest

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
```

运行：

```bash
pytest tests/test_add.py -v
```

预期：5 个新测试 FAIL（`ValidationError` 和 `validate_record` 还没定义）。

- [ ] **Step 9: 实现 `ValidationError` 和 `validate_record`**

在 `tools/add.py` 的 `Record` 数据类之后、`append_record` 之前插入：

```python
import re

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
```

运行：

```bash
pytest tests/test_add.py -v
```

预期：全部 8 个测试 PASS。

- [ ] **Step 10: 提交**

```bash
git add tools/add.py tests/conftest.py tests/test_add.py
git commit -m "feat: append_record 与 validate_record"
```

---

## Task 3: CLI 入口（一行式参数）

**Files:**
- Modify: `D:/grocery-tracker/tools/add.py`
- Modify: `D:/grocery-tracker/tests/test_add.py`

- [ ] **Step 1: 写一行式参数解析的失败测试**

在 `tests/test_add.py` 末尾追加：

```python
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
```

运行：

```bash
pytest tests/test_add.py::test_parse_args_oneliner_minimal -v
```

预期：FAIL（`parse_args` 不存在）。

- [ ] **Step 2: 实现 `parse_args`**

在 `tools/add.py` 顶部 import 区加 `import argparse`，并在文件末尾追加：

```python
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
```

运行：

```bash
pytest tests/test_add.py -v
```

预期：全部 PASS。

- [ ] **Step 3: 写 `main()` 一行式分支的集成测试**

在 `tests/test_add.py` 顶部 import 区加 `import sys`，末尾追加：

```python
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
```

运行：

```bash
pytest tests/test_add.py::test_main_oneliner_writes_record -v
```

预期：FAIL（`main` 不存在）。

- [ ] **Step 4: 实现 `main()` —— 仅处理一行式分支**

在 `tools/add.py` 末尾追加：

```python
from datetime import date as date_cls


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
```

运行：

```bash
pytest tests/test_add.py -v
```

预期：全部 PASS。

- [ ] **Step 5: 手工冒烟测试 —— 真的写到 data/prices.csv**

在 `D:\grocery-tracker\` 下：

```bash
python tools/add.py 白菜 3.5 -q 2 -u 斤 -d 2026-06-15
```

预期输出：`✓ 已写入 data\prices.csv：白菜 3.50 x 2.0 斤`

打开 `data/prices.csv` 验证最后一行就是这条。**验证后用 `git checkout data/prices.csv` 撤回，保持 CSV 仍只有表头**：

```bash
git checkout data/prices.csv
```

- [ ] **Step 6: 提交**

```bash
git add tools/add.py tests/test_add.py
git commit -m "feat: add.py CLI 一行式参数与 main 入口"
```

---

## Task 4: 交互式录入循环

**Files:**
- Modify: `D:/grocery-tracker/tools/add.py`
- Modify: `D:/grocery-tracker/tests/test_add.py`

> **说明：** 交互模式涉及 `input()` 和实时交互，自动化测试只覆盖底层"单位频次统计"与"单次输入分发"两个纯函数；完整交互流程靠手工冒烟。

- [ ] **Step 1: 写"单位频次统计"的失败测试**

在 `tests/test_add.py` 末尾追加：

```python
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
```

运行：

```bash
pytest tests/test_add.py::test_top_units_returns_top_n_by_frequency -v
```

预期：FAIL（`top_units` 不存在）。

- [ ] **Step 2: 实现 `top_units`**

在 `tools/add.py` 顶部加 `from collections import Counter`，并在 `interactive_loop` 之前插入：

```python
def top_units(csv_path: Path, n: int = 3) -> list[tuple[str, int]]:
    """按出现次数返回前 n 个单位。"""
    if not csv_path.exists():
        return []
    counter: Counter[str] = Counter()
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = (row.get("unit") or "").strip()
            if u:
                counter[u] += 1
    return counter.most_common(n)
```

运行：

```bash
pytest tests/test_add.py -v
```

预期：全部 PASS。

- [ ] **Step 3: 实现 `interactive_loop` 替换原占位**

把 `tools/add.py` 中已有的 `interactive_loop` 函数**整体替换**为：

```python
def _ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    if not raw and default is not None:
        return default
    return raw


def _ask_float(prompt: str) -> float:
    while True:
        raw = input(f"{prompt}: ").strip()
        try:
            v = float(raw)
            if v <= 0:
                print("  必须为正数，请重输")
                continue
            return v
        except ValueError:
            print("  不是有效数字，请重输")


def _ask_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = "[y/N]" if not default else "[Y/n]"
    raw = input(f"{prompt} {suffix}: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes")


def interactive_loop(csv_path: Path) -> int:
    print(f"交互式录入（CSV: {csv_path}），Ctrl+C 退出。")
    while True:
        today = date_cls.today().isoformat()
        try:
            d = _ask("日期", default=today)
            item = _ask("品名")
            while not item.strip():
                print("  品名不能为空")
                item = _ask("品名")

            units = top_units(csv_path, n=3)
            if units:
                hint = "  最近用过的单位：" + " ".join(
                    f"{u}({c})" for u, c in units
                )
                print(hint)
                default_unit = units[0][0]
            else:
                default_unit = None
            unit = _ask("单位", default=default_unit) if default_unit \
                else _ask("单位")
            while not unit.strip():
                print("  单位不能为空")
                unit = _ask("单位")

            price = _ask_float(f"单价 (元/{unit})")
            qty = _ask_float("数量")
            on_sale = _ask_yes_no("打折？", default=False)
            note = _ask("备注", default="")

            try:
                rec = validate_record(
                    date=d, item=item, unit_price=price, quantity=qty,
                    unit=unit, on_sale=on_sale, note=note,
                )
            except ValidationError as e:
                print(f"  ✗ 校验失败：{e}，本条已丢弃")
            else:
                append_record(csv_path, rec)
                print(f"  ✓ 已写入：{rec.item} {rec.unit_price:.2f} "
                      f"x {rec.quantity} {rec.unit}")
        except (KeyboardInterrupt, EOFError):
            print("\n退出")
            return 0

        if not _ask_yes_no("继续录入？", default=True):
            return 0
```

运行：

```bash
pytest tests/test_add.py -v
```

预期：所有已有测试仍然 PASS。

- [ ] **Step 4: 手工冒烟测试交互模式**

在 `D:\grocery-tracker\` 下：

```bash
python tools/add.py
```

按提示输入 1～2 条真实记录，最后选"继续录入？n"退出。
确认 `data/prices.csv` 末尾追加了新行，单位提示正常工作。

**验证完用 `git checkout data/prices.csv` 撤回**：

```bash
git checkout data/prices.csv
```

- [ ] **Step 5: 提交**

```bash
git add tools/add.py tests/test_add.py
git commit -m "feat: 交互式录入循环与单位频次提示"
```

---

## Task 5: 构建脚本 `build_site.py`（TDD）

**Files:**
- Create: `D:/grocery-tracker/tests/test_build_site.py`
- Create: `D:/grocery-tracker/tools/build_site.py`

- [ ] **Step 1: 写 `build_data` 的失败测试 —— summary 与基础结构**

`tests/test_build_site.py` 内容：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_build_site.py -v
```

预期：FAIL（`tools.build_site` 不存在）。

- [ ] **Step 3: 实现 `build_data` 的 summary 部分**

`tools/build_site.py` 初始内容：

```python
"""读 data/prices.csv，聚合并写出 site/data.json。"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
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

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "records": parsed,
        "summary": {
            "total_records": len(parsed),
            "total_spend": total_spend,
            "month_to_date_spend": mtd_spend,
            "date_range": date_range,
        },
        "by_item": [],   # Step 5 填充
        "by_month": [],  # Step 7 填充
    }
```

运行：

```bash
pytest tests/test_build_site.py -v
```

预期：PASS。

- [ ] **Step 4: 加 `by_item` 测试**

在 `tests/test_build_site.py` 末尾追加：

```python
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
```

运行：

```bash
pytest tests/test_build_site.py -v
```

预期：FAIL（`by_item` 还是空列表）。

- [ ] **Step 5: 实现 `by_item` 聚合**

把 `tools/build_site.py` 中 `return { ... }` 之前插入：

```python
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
```

然后把 `"by_item": []` 改成 `"by_item": by_item`。

运行：

```bash
pytest tests/test_build_site.py -v
```

预期：全部 PASS。

- [ ] **Step 6: 加 `by_month` 测试**

在 `tests/test_build_site.py` 末尾追加：

```python
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
```

运行：

```bash
pytest tests/test_build_site.py -v
```

预期：FAIL。

- [ ] **Step 7: 实现 `by_month` 聚合**

在 `tools/build_site.py` 中 `by_item.sort(...)` 之后、`return` 之前插入：

```python
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
```

然后把 `"by_month": []` 改成 `"by_month": by_month`。

运行：

```bash
pytest tests/test_build_site.py -v
```

预期：全部 PASS。

- [ ] **Step 8: 加坏行容错测试**

在 `tests/test_build_site.py` 末尾追加：

```python
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
```

运行：

```bash
pytest tests/test_build_site.py -v
```

预期：PASS（`_parse_row` 已经做了容错）。

- [ ] **Step 9: 实现 `main()` 写 data.json**

在 `tools/build_site.py` 末尾追加：

```python
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
```

- [ ] **Step 10: 手工冒烟 —— 用真实 CSV 跑一次**

先临时填几条数据，跑一次 build：

```bash
python tools/add.py 白菜 3.5 -q 2 -u 斤 -d 2026-06-15
python tools/add.py 鸡蛋 12.8 -q 1 -u 盒 -d 2026-06-15 --sale -n "30枚装"
python tools/build_site.py
```

预期：`site/data.json` 被创建，打开看 `records` 有两条、`by_item` 有两项。

撤回临时数据，但保留 `site/data.json`（后续前端开发需要）：

```bash
git checkout data/prices.csv
python tools/build_site.py
```

第二次 build 后，`site/data.json` 会变成空骨架（0 条记录），这就是"提交进 repo 的初始 data.json"。

- [ ] **Step 11: 提交**

```bash
git add tools/build_site.py tests/test_build_site.py site/data.json
git commit -m "feat: build_site.py 聚合 CSV → data.json"
```

---

## Task 6: 前端页面

**Files:**
- Create: `D:/grocery-tracker/site/index.html`
- Create: `D:/grocery-tracker/site/app.js`

> **说明：** 前端不写自动化测试，靠手工冒烟。先填几条样例数据，再用浏览器打开 `site/index.html` 逐项验证。

- [ ] **Step 1: 写 `index.html`**

`site/index.html` 完整内容：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>Grocery Tracker</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; }
    body { margin: 0; padding: 1rem; max-width: 1100px; margin: 0 auto; color: #222; }
    h1 { font-size: 1.4rem; margin: 0 0 1rem; }
    h2 { font-size: 1.1rem; margin: 1.5rem 0 0.5rem; border-bottom: 1px solid #eee; padding-bottom: 0.25rem; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; }
    .card { background: #f7f7f8; padding: 0.75rem 1rem; border-radius: 6px; }
    .card .label { font-size: 0.8rem; color: #666; }
    .card .value { font-size: 1.3rem; font-weight: 600; margin-top: 0.25rem; }
    .chart-box { position: relative; height: 320px; }
    select, input { font: inherit; padding: 0.25rem 0.5rem; }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { padding: 0.4rem 0.5rem; border-bottom: 1px solid #eee; text-align: left; }
    th { background: #fafafa; cursor: pointer; user-select: none; }
    .right { text-align: right; }
    .controls { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .muted { color: #888; }
    #generatedAt { font-size: 0.8rem; color: #888; }
  </style>
</head>
<body>
  <h1>Grocery Tracker <span id="generatedAt" class="muted"></span></h1>

  <section class="summary" id="summary"></section>

  <h2>价格走势</h2>
  <div class="controls">
    <select id="itemSelect" multiple size="6" style="min-width: 240px"></select>
    <span class="muted">按住 Ctrl/Cmd 多选</span>
  </div>
  <div class="chart-box"><canvas id="trendChart"></canvas></div>

  <h2>月度花费</h2>
  <div class="chart-box"><canvas id="monthChart"></canvas></div>

  <h2>品类排行</h2>
  <table id="byItemTable">
    <thead>
      <tr>
        <th data-sort="item">品名</th>
        <th data-sort="unit">单位</th>
        <th data-sort="count" class="right">次数</th>
        <th data-sort="total_spend" class="right">累计花费</th>
        <th data-sort="avg_price" class="right">均价</th>
        <th data-sort="min_price" class="right">最低</th>
        <th data-sort="max_price" class="right">最高</th>
        <th data-sort="last_date">最近</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <h2>原始记录</h2>
  <div class="controls">
    <input id="filterText" type="search" placeholder="按品名/备注过滤…" />
    <span id="recordCount" class="muted"></span>
  </div>
  <table id="recordsTable">
    <thead>
      <tr>
        <th>日期</th><th>品名</th><th class="right">单价</th>
        <th class="right">数量</th><th>单位</th><th>打折</th><th>备注</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <script src="./app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 写 `app.js`**

`site/app.js` 完整内容：

```javascript
"use strict";

const CHART_COLORS = [
  "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
  "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
];

let DATA = null;
let trendChart = null;
let monthChart = null;
let recordsFilter = "";
let byItemSort = { key: "total_spend", desc: true };

async function main() {
  const resp = await fetch("./data.json", { cache: "no-store" });
  DATA = await resp.json();
  renderGeneratedAt();
  renderSummary();
  renderItemSelect();
  renderTrendChart();
  renderMonthChart();
  renderByItem();
  renderRecords();
  bindEvents();
}

function renderGeneratedAt() {
  const el = document.getElementById("generatedAt");
  el.textContent = `更新于 ${DATA.generated_at}`;
}

function renderSummary() {
  const s = DATA.summary;
  const cards = [
    { label: "总记录", value: s.total_records },
    { label: "累计花费", value: `¥ ${s.total_spend.toFixed(2)}` },
    { label: "本月花费", value: `¥ ${s.month_to_date_spend.toFixed(2)}` },
    {
      label: "时间范围",
      value: s.date_range[0]
        ? `${s.date_range[0]} ~ ${s.date_range[1]}`
        : "（暂无数据）",
    },
  ];
  document.getElementById("summary").innerHTML = cards
    .map(c => `<div class="card"><div class="label">${c.label}</div>
                 <div class="value">${c.value}</div></div>`)
    .join("");
}

function renderItemSelect() {
  const sel = document.getElementById("itemSelect");
  const opts = DATA.by_item.map(b => {
    const key = `${b.item}|${b.unit}`;
    return `<option value="${escapeAttr(key)}">${escapeHtml(b.item)} (${escapeHtml(b.unit)})</option>`;
  });
  sel.innerHTML = opts.join("");
}

function renderTrendChart() {
  const sel = document.getElementById("itemSelect");
  const selected = Array.from(sel.selectedOptions).map(o => o.value);
  const ctx = document.getElementById("trendChart");

  const datasets = selected.map((key, i) => {
    const [item, unit] = key.split("|");
    const points = DATA.records
      .filter(r => r.item === item && r.unit === unit)
      .sort((a, b) => a.date.localeCompare(b.date))
      .map(r => ({
        x: r.date, y: r.unit_price,
        pointStyle: r.on_sale ? "circle" : "rectRot",
        radius: r.on_sale ? 6 : 4,
      }));
    return {
      label: `${item} (${unit})`,
      data: points,
      borderColor: CHART_COLORS[i % CHART_COLORS.length],
      backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
      tension: 0.2,
    };
  });

  if (trendChart) trendChart.destroy();
  trendChart = new Chart(ctx, {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      parsing: false,
      scales: {
        x: { type: "category", title: { display: true, text: "日期" } },
        y: { title: { display: true, text: "单价（元）" }, beginAtZero: true },
      },
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const r = ctx.raw;
              return `${ctx.dataset.label}: ¥${r.y.toFixed(2)} 于 ${r.x}` +
                (r.pointStyle === "circle" ? "（打折）" : "");
            },
          },
        },
      },
    },
  });
}

function renderMonthChart() {
  const ctx = document.getElementById("monthChart");
  if (monthChart) monthChart.destroy();
  monthChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: DATA.by_month.map(m => m.month),
      datasets: [{
        label: "月度花费",
        data: DATA.by_month.map(m => m.total_spend),
        backgroundColor: "#1f77b4",
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, title: { display: true, text: "元" } } },
      plugins: { legend: { display: false } },
    },
  });
}

function renderByItem() {
  const tbody = document.querySelector("#byItemTable tbody");
  const rows = [...DATA.by_item].sort((a, b) => {
    const k = byItemSort.key;
    const av = a[k], bv = b[k];
    const cmp = typeof av === "number" ? av - bv : String(av).localeCompare(String(bv));
    return byItemSort.desc ? -cmp : cmp;
  });
  tbody.innerHTML = rows.map(b => `
    <tr data-item="${escapeAttr(b.item)}" data-unit="${escapeAttr(b.unit)}" style="cursor: pointer">
      <td>${escapeHtml(b.item)}</td>
      <td>${escapeHtml(b.unit)}</td>
      <td class="right">${b.count}</td>
      <td class="right">¥ ${b.total_spend.toFixed(2)}</td>
      <td class="right">¥ ${b.avg_price.toFixed(2)}</td>
      <td class="right">¥ ${b.min_price.toFixed(2)}</td>
      <td class="right">¥ ${b.max_price.toFixed(2)}</td>
      <td>${b.last_date}</td>
    </tr>
  `).join("");
}

function renderRecords() {
  const tbody = document.querySelector("#recordsTable tbody");
  const q = recordsFilter.trim();
  const filtered = q
    ? DATA.records.filter(r => r.item.includes(q) || (r.note || "").includes(q))
    : DATA.records;
  const sorted = [...filtered].sort((a, b) => b.date.localeCompare(a.date));
  document.getElementById("recordCount").textContent =
    `${sorted.length} / ${DATA.records.length} 条`;
  tbody.innerHTML = sorted.slice(0, 200).map(r => `
    <tr>
      <td>${r.date}</td>
      <td>${escapeHtml(r.item)}</td>
      <td class="right">¥ ${r.unit_price.toFixed(2)}</td>
      <td class="right">${r.quantity}</td>
      <td>${escapeHtml(r.unit)}</td>
      <td>${r.on_sale ? "✓" : ""}</td>
      <td>${escapeHtml(r.note || "")}</td>
    </tr>
  `).join("");
}

function bindEvents() {
  document.getElementById("itemSelect")
    .addEventListener("change", renderTrendChart);

  document.getElementById("filterText").addEventListener("input", (e) => {
    recordsFilter = e.target.value;
    renderRecords();
  });

  document.querySelectorAll("#byItemTable th[data-sort]").forEach(th => {
    th.addEventListener("click", () => {
      const k = th.dataset.sort;
      if (byItemSort.key === k) byItemSort.desc = !byItemSort.desc;
      else { byItemSort.key = k; byItemSort.desc = true; }
      renderByItem();
    });
  });

  document.querySelector("#byItemTable tbody").addEventListener("click", (e) => {
    const tr = e.target.closest("tr");
    if (!tr) return;
    const key = `${tr.dataset.item}|${tr.dataset.unit}`;
    const sel = document.getElementById("itemSelect");
    Array.from(sel.options).forEach(o => { o.selected = (o.value === key); });
    renderTrendChart();
    document.getElementById("trendChart").scrollIntoView({ behavior: "smooth", block: "center" });
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function escapeAttr(s) { return escapeHtml(s); }

main().catch(err => {
  document.body.innerHTML = `<pre style="color:red">加载失败：${err}</pre>`;
});
```

- [ ] **Step 3: 手工冒烟 —— 填样例数据，浏览器验证**

在 `D:\grocery-tracker\` 下：

```bash
python tools/add.py 白菜 3.0 -q 2 -u 斤 -d 2026-06-10
python tools/add.py 白菜 3.5 -q 1 -u 斤 -d 2026-06-12 --sale -n "促销"
python tools/add.py 白菜 4.0 -q 2 -u 斤 -d 2026-06-15
python tools/add.py 鸡蛋 12.0 -q 1 -u 盒 -d 2026-06-13
python tools/add.py 鸡蛋 13.0 -q 2 -u 盒 -d 2026-06-15
python tools/build_site.py
```

然后用浏览器打开 `D:\grocery-tracker\site\index.html`（双击或拖入浏览器），逐项检查：

1. 顶部摘要 4 张卡片显示正确（5 条、累计 ¥55.50、本月花费、日期范围）
2. 在品名下拉选"白菜 (斤)"，走势图出现 3 点，其中 6-12 的点形状不同（打折）
3. 月度柱状图只显示 2026-06 一根柱
4. 品类排行表 2 行，按累计花费降序（白菜 17.50 在前，鸡蛋 38.00 在前？再核对——鸡蛋 12+26=38，比白菜 17.5 高，所以鸡蛋第一）
5. 点击品类排行的"鸡蛋"行，走势图切换显示鸡蛋
6. 原始记录表显示 5 行，按日期降序
7. 在过滤框输入"白菜"，记录表变 3 行

如果任何一项异常：在 app.js 找对应函数修，重跑 build_site.py，浏览器刷新（Ctrl+F5）。

- [ ] **Step 4: 撤回样例数据，重建空 data.json**

```bash
git checkout data/prices.csv
python tools/build_site.py
```

`site/data.json` 现在又是空骨架。

- [ ] **Step 5: 提交**

```bash
git add site/index.html site/app.js site/data.json
git commit -m "feat: 前端单页 HTML + Chart.js 走势/月度/排行/记录"
```

---

## Task 7: GitHub Action 工作流

**Files:**
- Create: `D:/grocery-tracker/.github/workflows/build-and-deploy.yml`

- [ ] **Step 1: 写 workflow 文件**

`.github/workflows/build-and-deploy.yml` 内容：

```yaml
name: Build and deploy site

on:
  push:
    branches: [main]
    paths:
      - "data/**"
      - "tools/build_site.py"
      - "site/**"
      - ".github/workflows/build-and-deploy.yml"
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Build site/data.json
        run: python tools/build_site.py
      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/build-and-deploy.yml
git commit -m "ci: GitHub Action 构建并部署 Pages"
```

---

## Task 8: 完整 README

**Files:**
- Modify: `D:/grocery-tracker/README.md`

- [ ] **Step 1: 覆盖 README 为完整版**

`README.md` 内容：

````markdown
# grocery-tracker

日常买菜价格追踪器。CLI 录入到 CSV、GitHub Pages 趋势可视化。

## 使用

### 录入（一行式）

```bash
python tools/add.py 白菜 3.5 -q 2 -u 斤
python tools/add.py 鸡蛋 12.8 -q 1 -u 盒 --sale -n "30枚装"
python tools/add.py 猪肉 28 -q 1.5 -u 斤 -d 2026-06-14
```

### 录入（交互式）

```bash
python tools/add.py
```

按提示输入日期/品名/单位/单价/数量/打折/备注。Ctrl+C 退出。

### 本地预览网页

```bash
python tools/build_site.py
# 然后浏览器打开 site/index.html
```

### 推送到 GitHub

```bash
git add data/prices.csv
git commit -m "买菜 2026-06-15"
git push
```

push 后 GitHub Action 会自动构建 `site/data.json` 并部署到 GitHub Pages，
约 1～2 分钟后访问 `https://<你的用户名>.github.io/grocery-tracker/` 即可看到最新数据。

## 首次启用 GitHub Pages（一次性）

1. 在 GitHub 上创建公开仓库 `grocery-tracker`
2. 本地添加远端并推送：

   ```bash
   git remote add origin git@github.com:<你的用户名>/grocery-tracker.git
   git push -u origin main
   ```

3. GitHub 仓库页 → Settings → Pages → 在 "Build and deployment" 下，
   把 Source 设为 **GitHub Actions**
4. 等第一次 Action 跑完，访问 `https://<你的用户名>.github.io/grocery-tracker/`

## 数据格式

`data/prices.csv` 列：

| 列 | 说明 |
|---|---|
| `date` | `YYYY-MM-DD` |
| `item` | 品名（中文） |
| `unit_price` | 单价（元/单位），2 位小数 |
| `quantity` | 数量，正数 |
| `unit` | 单位（斤/kg/盒…） |
| `on_sale` | `true` / `false` |
| `note` | 备注，可空；含逗号需 CSV 引号包裹（CLI 自动处理） |

总价不存储，由 `unit_price * quantity` 计算。**不做跨单位自动换算**，
"斤" 和 "kg" 视为两个独立分组。

## 修改与删除

`tools/add.py` 只追加，不修改也不删除。要改老数据，直接用编辑器打开
`data/prices.csv` 改完后 `git diff` 审查，提交即可。

## 测试

```bash
pip install -r requirements.txt
pytest -v
```

## 设计

详见 [docs/specs/2026-06-15-grocery-tracker-design.md](docs/specs/2026-06-15-grocery-tracker-design.md)。
````

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: 完整 README"
```

---

## Task 9: 最终检查与远端推送（手动）

> **说明：** 这一步包含需要用户手动确认的操作（创建 GitHub 仓库、添加远端）。
> 计划只到本地准备就绪为止；最终 `git push` 让用户在评审后手动执行。

- [ ] **Step 1: 全量跑一遍测试**

```bash
pytest -v
```

预期：所有测试 PASS。

- [ ] **Step 2: 跑构建脚本验证空数据状态**

```bash
python tools/build_site.py
```

预期：输出 `✓ 已写入 site\data.json（0 条记录）`；`site/data.json` 中 `summary.total_records` 为 0。

- [ ] **Step 3: 用浏览器打开 site/index.html 确认空态正常显示**

预期：摘要 4 张卡片显示 0 / ¥0.00 / ¥0.00 / "（暂无数据）"；表格为空；不报 JS 错。

- [ ] **Step 4: 检查仓库整洁度**

```bash
git status
git log --oneline
```

预期：工作区干净；提交历史按 Task 顺序排列，含义清晰。

- [ ] **Step 5: 提示用户手动创建 GitHub 仓库和首次 push**

把以下指引输出给用户：

```
本地已就绪。请你自己完成最后两步：

1. 在 GitHub 创建公开仓库 grocery-tracker
2. 在 D:\grocery-tracker\ 下运行：
     git remote add origin git@github.com:<你的用户名>/grocery-tracker.git
     git push -u origin main
3. 在仓库 Settings → Pages 把 Source 设为 "GitHub Actions"
4. 等 Action 跑完后访问 https://<你的用户名>.github.io/grocery-tracker/
```

---

## 完成标准

- 所有 pytest 测试通过
- 本地 `python tools/add.py 白菜 3.5 -q 2 -u 斤` 能成功追加到 CSV
- 本地 `python tools/build_site.py` 能产出有效 `site/data.json`
- 本地浏览器打开 `site/index.html` 能正常渲染（即使无数据也不报错）
- push 到 GitHub 后 Action 跑通、Pages 访问正常
