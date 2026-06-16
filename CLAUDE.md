# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

日常买菜价格追踪器：本地 Python CLI 把购物记录追加到 `data/prices.csv`，手动 `git push` 后由 GitHub Action 跑构建脚本生成 `site/data.json`，并把 `site/` 部署到 GitHub Pages。前端是单页 HTML + Chart.js（CDN），通过 `fetch('./data.json')` 渲染价格走势、月度花费、品类排行。

**零运行时依赖**：CLI 与构建脚本只用 Python 标准库（`csv`/`argparse`/`json`/`datetime`/`collections`）。`requirements.txt` 里只有测试用的 `pytest`。前端无构建工具、无 npm。

## 当前实现状态（重要）

仓库目前只完成了项目骨架（Task 1）。**以下文件计划存在但尚未创建**：`tools/add.py`、`tools/build_site.py`、`tests/test_add.py`、`tests/test_build_site.py`、`tests/conftest.py`、`site/index.html`、`site/app.js`、`site/data.json`、`.github/workflows/build-and-deploy.yml`。

完整的逐任务实施计划（含每个文件的目标代码、TDD 步骤、提交信息）在 [docs/superpowers/plans/2026-06-15-grocery-tracker.md](docs/superpowers/plans/2026-06-15-grocery-tracker.md)。继续开发前请先读它。设计依据在 [docs/specs/2026-06-15-grocery-tracker-design.md](docs/specs/2026-06-15-grocery-tracker-design.md)。

实施这个计划时使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development` 子技能，按 Task 顺序逐步推进。

## 常用命令

```bash
# 安装测试依赖
pip install -r requirements.txt

# 跑全部测试
pytest -v

# 跑单个测试文件 / 单个用例
pytest tests/test_add.py -v
pytest tests/test_add.py::test_append_creates_file_with_header -v

# 录入一条记录（一行式）
python tools/add.py 白菜 3.5 -q 2 -u 斤
python tools/add.py 鸡蛋 12.8 -q 1 -u 盒 --sale -n "30枚装" -d 2026-06-14

# 交互式录入
python tools/add.py

# 本地构建 site/data.json，然后浏览器打开 site/index.html
python tools/build_site.py
```

测试以仓库根目录为工作目录运行（`tools` 是包，靠 `tools/__init__.py` 支持 `import tools.add`）。

## 架构与关键约定

**数据流**：`add.py`（追加）→ `data/prices.csv`（唯一事实来源，提交进 git）→ `build_site.py`（纯聚合）→ `site/data.json`（产物，也提交进 git）→ `app.js`（fetch 渲染）。

**模块边界——为可测试性而设计**：
- `tools/add.py`：业务函数（`Record`、`validate_record`、`append_record`、`top_units`、`parse_args`）与 CLI 入口 `main()`/`interactive_loop()` 分离。测试只覆盖纯函数，交互流程靠手工冒烟。
- `tools/build_site.py`：`build_data(rows) -> dict` 是纯函数（聚合逻辑全在这里，便于单测）；文件 I/O 只在 `main()` 里。`_today()` 单独封装，便于测试用 monkeypatch 锁定"今天"。

**`data/prices.csv` 格式**（固定列序，UTF-8）：`date,item,unit_price,quantity,unit,on_sale,merchant,note`
- `date` 为 `YYYY-MM-DD`；`on_sale` 为全小写 `true`/`false`；`merchant`（商家）可空；`note` 含逗号时由 `csv` 模块自动加引号。
- `build_site.py` 的 `_parse_row` 用 `row.get("merchant", "")` 容错，可读取无此列的旧 CSV。
- `total = unit_price * quantity` 是派生字段，**不存储**，在 `build_site.py` 里算。

**核心设计决策（改代码前务必遵守）**：
- **CLI 只追加，不重排序、不去重、不修改/删除**。同一天买两次同一品名是合法的。改老数据让用户直接编辑 CSV（便于 `git diff` 审查）。
- **不自动 `git commit`/`push`**——由用户手动控制。
- **单位换算仅 kg→斤、且仅录入时**：`add.py` 的 `convert_kg_to_jin` 在 `validate_record` 内把 `kg/千克/公斤` 换成「斤」（数量×2、单价÷2，花费守恒），CSV 只存斤。其余单位不换算。`build_site.py` 不做换算，聚合仍按 `(item, unit)` 联合分组，避免不同单位均价被错误平均。手动写进 CSV 的 kg 行不会被换算。
- **品名不规范化**：`by_item` 严格按字面分组（"白菜" 与 "大白菜" 是两项）。
- 坏数据在两处拦截：`add.py` 写入前用 `validate_record` 校验（拒绝脏数据进 repo）；`build_site.py` 读取时对坏行打 warning 到 stderr 并跳过（不中断），空 CSV 产出有效的空骨架 JSON。

**前端**（`site/`，纯静态、单文件、约 200 行内）：Chart.js 从 CDN 引入并 pin 到具体版本。`app.js` 渲染摘要卡片、品名走势折线图（打折点用不同 marker）、月度柱状图、可排序品类表、可过滤原始记录表。网页只读，无后端、无登录、无 cookie。

## 部署

push 到 `main` 且改动了 `data/**`、`tools/build_site.py` 或 `site/**` 时，GitHub Action（`.github/workflows/build-and-deploy.yml`）跑 `python tools/build_site.py` 并部署 `site/` 到 Pages（权限 `pages: write`/`id-token: write`/`contents: read`）。首次需在仓库 Settings → Pages 把 Source 设为 "GitHub Actions"。
