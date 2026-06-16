# 新增「商家」列 设计文档

- **日期**：2026-06-16
- **背景**：在现有 grocery-tracker 的录入信息中增加一列「商家」（merchant）。
- **关联**：基础设计见 [2026-06-15-grocery-tracker-design.md](../../specs/2026-06-15-grocery-tracker-design.md)。

## 1. 目标与范围

给每条购物记录增加一个**可选**的「商家」字段，只做**记录与展示**，不引入商家维度的聚合分析。

**非目标**：按商家排行、同品跨商家比价、商家别名规范化（留待将来）。

## 2. 决策

| 关注点 | 决定 |
|---|---|
| 必填性 | **可选**（与 `note` 一致，可留空） |
| 用途 | **只记录 + 展示**，不改 `by_item`/`by_month`/`summary` 聚合 |
| 字段名 | 内部 `merchant`，界面显示「商家」 |
| CSV 列位置 | 放在 `note` **之前**：`date,item,unit_price,quantity,unit,on_sale,merchant,note` |
| CLI 参数 | 新增可选项 `-m / --merchant TEXT`，默认空 |

## 3. 数据格式变更

`data/prices.csv` 新列顺序（当前文件只有表头、无数据，改列零迁移成本）：

```csv
date,item,unit_price,quantity,unit,on_sale,merchant,note
2026-06-15,白菜,3.50,2.0,斤,false,永辉,
2026-06-15,鸡蛋,12.80,1.0,盒,true,钱大妈,30枚装
```

`site/data.json` 的每条 record 增加 `"merchant": "..."` 字段；`summary`/`by_item`/`by_month` 结构不变。

## 4. 各模块改动

### 4.1 `tools/add.py`
- `CSV_HEADER` 加入 `merchant`（在 `note` 前）。
- `Record` 数据类加 `merchant: str` 字段；`to_row()` 按新列顺序输出。
- `validate_record(...)` 新增关键字参数 `merchant`，只做 `.strip()`，**不校验非空**。
- `parse_args` 增加 `-m/--merchant`（`default=""`）。
- `main()` 一行式分支把 `ns.merchant` 传入 `validate_record`。
- `interactive_loop` 在「打折？」之后、「备注」之前插入 `商家:` 提问（可空，回车跳过）。

### 4.2 `tools/build_site.py`
- `_parse_row` 用 `row.get("merchant", "") or ""` 读取（缺列时容错为空，向后兼容旧 CSV），放进 record dict。
- 聚合逻辑不动。

### 4.3 前端 `site/`
- `index.html` 原始记录表表头增加「商家」列。
- `app.js` `renderRecords()` 输出商家单元格（`escapeHtml`）；过滤函数除 `item`/`note` 外，**也匹配 `merchant`**。
- 走势图、月度图、品类排行表不变。

## 5. 测试

- `tests/test_add.py`：
  - `Record`/`append_record` 用例的期望行更新为含 merchant 的新列顺序。
  - 新增用例：一行式 `-m 永辉` 写入后该列正确；不传 `-m` 时该列为空。
  - `validate_record` 新增用例：merchant 两端空白被 trim；空 merchant 合法（不抛错）。
- `tests/test_build_site.py`：
  - `SAMPLE_ROWS` 各行补 `merchant` 字段；断言 record 含 merchant。
  - 新增用例：CSV 缺 `merchant` 列时 `_parse_row` 容错为 `""`（向后兼容）。

## 6. 同步更新的文档
- `README.md` 数据格式表加一行 `merchant`，录入示例加 `-m`。
- `CLAUDE.md` 中 CSV 列说明更新。
- 重新生成空骨架 `site/data.json`。

## 7. 向后兼容

`_parse_row` 对 `merchant` 用 `.get()` 容错，旧数据（无此列）读取不会报错，merchant 视为空。CLI 与前端均把空 merchant 当正常情况处理。
