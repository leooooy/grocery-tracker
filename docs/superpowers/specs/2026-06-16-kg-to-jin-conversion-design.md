# kg→斤 录入时自动换算 设计文档

- **日期**：2026-06-16
- **背景**：录入时若单位为千克/kg，自动换算成「斤」存储，统一品类分组与走势。
- **关联**：基础设计见 [2026-06-15-grocery-tracker-design.md](../../specs/2026-06-15-grocery-tracker-design.md)。

## 1. 目标

让所有重量类记录统一以「斤」存储，避免「白菜(斤)」与「白菜(kg)」在
`by_item`（按 `(item, unit)` 分组）里被拆成两组。

**本文推翻**原 spec §5.1 与 CLAUDE.md 中「不做跨单位换算」的决定，
但**仅限 kg→斤 这一对**；其它单位（克/两/个/盒…）仍不换算。

## 2. 换算规则

1 kg = 2 斤，花费守恒：

| 字段 | 换算 |
|---|---|
| 单位 | → `斤` |
| 数量 | × 2 |
| 单价 | ÷ 2 |

校验：`total = 单价 × 数量` 换算前后相等（如 10 元/kg × 1 = 10 元 = 5 元/斤 × 2）。

**触发单位**（去空白后，对拉丁字母不分大小写）：`kg`、`千克`、`公斤`。
即 `unit.strip().lower() in {"kg", "千克", "公斤"}`。

## 3. 换算层：仅 CLI 录入时

只在 `tools/add.py` 写入前换算，CSV 直接存「斤」，所见即所存。
`build_site.py`、前端、`data.json` **不改**。手动写进 CSV 的 kg 行不会被换算
（如需统一，用户自行编辑）。

## 4. 实现（`tools/add.py`）

- 新增常量：`KG_UNITS = {"kg", "千克", "公斤"}`、`KG_TO_JIN = 2`、`JIN = "斤"`。
- 新增纯函数：
  ```
  def convert_kg_to_jin(unit, unit_price, quantity) -> tuple[str, float, float]:
      """单位为 kg 类则换算成斤（数量×2、单价÷2），否则原样返回。"""
  ```
  判定用 `unit.strip().lower() in KG_UNITS`。
- 新增谓词 `_is_kg_unit(unit) -> bool`，供 CLI 层判断是否提示。
- `validate_record` 在「strip + 数值校验」之后、构造 `Record` 之前调用
  `convert_kg_to_jin`，于是一行式与交互式两条路都自动生效。
- CLI 成功提示：当原输入单位是 kg 时追加换算说明，例如
  `✓ 已写入：苹果 5.00 x 2.0 斤（由 10.00/kg × 1.0 换算）`。

## 5. 精度

单价以 2 位小数存（`to_row` 的 `f"{unit_price:.2f}"`）。常见价无损
（10/kg→5.00、9.8/kg→4.90）。奇数价（9.99/kg→4.995→存 5.00）有 ≤1 分
舍入漂移，买菜场景可忽略，不做更高精度存储。

## 6. 测试（`tests/test_add.py`）

- `convert_kg_to_jin`：`kg`/`千克`/`公斤`/`KG` → `(斤, 单价/2, 数量×2)`；非 kg 原样。
- `validate_record(unit="kg", unit_price=10, quantity=1)` → `rec.unit=="斤"`，
  `unit_price==5.0`，`quantity==2.0`，且 `unit_price*quantity == 10`。
- 一行式 `main`：`-u kg` 写入后该行单位为 `斤`、数值已换算。
- 非 kg 单位（如 `斤`/`个`）经 `validate_record` 不变。

## 7. 同步更新

- README 录入说明加一句 kg 自动换算。
- CLAUDE.md 把「不做跨单位换算」改为「仅 kg→斤 在录入时换算，其余不换算」。
