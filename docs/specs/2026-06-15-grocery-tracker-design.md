# Grocery Tracker 设计文档

- **日期**：2026-06-15
- **项目目录**：`D:\grocery-tracker\`
- **GitHub repo**：公开仓库（待创建，建议名 `grocery-tracker`）

## 1. 目标

记录日常购物（重点：买菜）的单价、数量、是否打折，通过 Git 持续追加，
并在 GitHub Pages 上以交互网页查看价格走势、月度花费、品类排行。

**非目标**：移动端录入、OCR 小票、多人协作、对接外部价格数据。

## 2. 用户场景

- **录入**：买菜回家后在电脑上，命令行运行 `python tools/add.py`，
  逐项输入当天的购物（或一行式参数批量录入）。一天可能录 1～10 条。
- **同步**：录完一段时间（一天或一周）后手动 `git push`。
- **查趋势**：任何时候在手机或电脑上打开 GitHub Pages URL，
  选品名查价格走势、看月度总花费、看品类排行。

## 3. 技术选型

| 关注点 | 选择 | 理由 |
|---|---|---|
| 数据存储 | CSV（`data/prices.csv`） | GitHub 自动渲染表格、`git diff` 一目了然、Excel 双击可开 |
| CLI 实现 | Python 标准库 `argparse` + `csv` | 零依赖、跨平台、字符编码可控（UTF-8） |
| 数据聚合 | Python 标准库 `csv` + `collections` | 数据量小（年量级 < 1 万行），不需要 pandas |
| 前端图表 | 单文件 HTML + Chart.js（CDN） | 不需要 npm/打包；浏览器双击即可本地预览 |
| 部署 | GitHub Actions → GitHub Pages | 免费、push 触发、零运维 |
| 仓库 | 公开 | GitHub Pages 在免费账户上对公开 repo 完全免费 |

## 4. 目录结构

```
grocery-tracker/
├── data/
│   └── prices.csv                 # 主数据，每行一条购物记录
├── tools/
│   ├── add.py                     # CLI 录入工具
│   └── build_site.py              # 读 CSV → 生成 site/data.json
├── site/
│   ├── index.html                 # 单页 + Chart.js
│   ├── app.js                     # 渲染逻辑
│   └── data.json                  # build_site.py 的产物，也提交进 repo
├── .github/
│   └── workflows/
│       └── build-and-deploy.yml   # push 后构建 + 部署
├── docs/
│   └── specs/
│       └── 2026-06-15-grocery-tracker-design.md
├── requirements.txt               # 空或仅注释（默认只用标准库）
├── .gitignore                     # 忽略 __pycache__/、.venv/、*.pyc
└── README.md
```

## 5. 数据格式

### 5.1 `data/prices.csv`

UTF-8，CRLF 或 LF 均可（`csv` 模块默认行为）。固定列顺序：

```csv
date,item,unit_price,quantity,unit,on_sale,note
2026-06-15,白菜,3.50,2,斤,false,
2026-06-15,鸡蛋,12.80,1,盒,true,30枚装
2026-06-14,猪肉,28.00,1.5,斤,false,五花
```

| 列 | 类型 | 规则 |
|---|---|---|
| `date` | string | `YYYY-MM-DD`，不能为空 |
| `item` | string | 自由文本，建议中文，不能为空。Trim 两端空白 |
| `unit_price` | decimal | 单价（元/单位），保留 2 位小数，`>0` |
| `quantity` | decimal | 数量，`>0`，可小数 |
| `unit` | string | 自由文本（"斤"、"kg"、"个"、"盒"…），不能为空 |
| `on_sale` | bool | `true` / `false`，全小写 |
| `note` | string | 可空。含逗号的需 CSV 标准引号包裹（`csv` 模块自动处理） |

**派生字段（不存储，计算时得出）**：
- `total = unit_price * quantity`

**单位归一化**：本项目**不做**自动单位换算（"斤" vs "kg"）。
分析时按 `(item, unit)` 联合分组，避免不同单位的均价被错误平均。
跨单位对比留给将来扩展。

### 5.2 `site/data.json`

由 `build_site.py` 生成，结构：

```json
{
  "generated_at": "2026-06-15T10:30:00+08:00",
  "records": [
    {"date": "2026-06-15", "item": "白菜", "unit_price": 3.50,
     "quantity": 2, "unit": "斤", "on_sale": false, "note": "",
     "total": 7.00}
  ],
  "summary": {
    "total_records": 47,
    "total_spend": 1234.56,
    "month_to_date_spend": 234.56,
    "date_range": ["2026-04-01", "2026-06-15"]
  },
  "by_item": [
    {"item": "白菜", "unit": "斤", "count": 8, "total_spend": 56.0,
     "avg_price": 3.42, "min_price": 2.80, "max_price": 4.50,
     "last_date": "2026-06-15"}
  ],
  "by_month": [
    {"month": "2026-04", "total_spend": 480.20, "record_count": 18},
    {"month": "2026-05", "total_spend": 520.00, "record_count": 17}
  ]
}
```

## 6. CLI 设计（`tools/add.py`）

### 6.1 交互式（默认）

```
$ python tools/add.py
日期 [2026-06-15]:
品名: 白菜
最近用过的单位：斤(20) 个(8) kg(3)
单位 [斤]:
单价 (元/斤): 3.5
数量: 2
打折？[y/N]:
备注:
✓ 已写入 data/prices.csv（第 48 行）
继续录入？[Y/n]: y
日期 [2026-06-15]:
品名: ...
```

**交互行为**：
- 日期默认今天，可按回车接受
- 品名为空则提示重新输入
- 单位提示"最近使用 Top 3"，按回车默认为最高频
- 数值字段不合法（非数字/≤0）会原地重问，不退出
- 打折默认 `n`
- 备注可空

### 6.2 一行式（适合熟练后批量）

```bash
python tools/add.py 白菜 3.5 -q 2 -u 斤
python tools/add.py 鸡蛋 12.8 -q 1 -u 盒 --sale -n "30枚装"
python tools/add.py 猪肉 28 -q 1.5 -u 斤 -d 2026-06-14
```

**位置参数**：`item` `unit_price`
**选项**：
- `-q, --quantity FLOAT`（必填）
- `-u, --unit TEXT`（必填）
- `-d, --date YYYY-MM-DD`（默认今天）
- `--sale`（开关，默认 false）
- `-n, --note TEXT`（默认空）

### 6.3 写入行为

- 文件不存在则创建并写表头
- 文件存在则**追加**（不重排序），让 `git diff` 只显示新增行
- 写入前再次校验：日期格式、数值正数、必填非空
- 写入后 `print` 出当前文件总行数和刚写的内容预览

### 6.4 不做的事

- **不自动 git commit、不自动 push** —— 由用户手动控制
- **不做去重检查** —— 同一天买两次同一品名是合法的
- **不修改/不删除** —— 老数据要改，用户自己编辑 CSV 文件

## 7. 构建脚本（`tools/build_site.py`）

输入：`data/prices.csv`
输出：`site/data.json`

逻辑：
1. 读 CSV，行级校验（坏行打 warning 到 stderr，跳过，不中断）
2. 计算 `total = unit_price * quantity`
3. 聚合：
   - `summary`：总条数、总花费、本月花费、日期范围
   - `by_item`：按 `(item, unit)` 分组，计数、累计、均价、最高/最低、最近日期
   - `by_month`：按 `YYYY-MM` 分组，月度总花费、条数
4. 写 `site/data.json`，UTF-8、`ensure_ascii=false`、2 空格缩进

**可独立运行**：用户本地跑 `python tools/build_site.py` 也能立刻看到最新数据。

## 8. 前端网页

### 8.1 `site/index.html`

单文件，结构：
- `<head>` 引 Chart.js CDN（pin 到具体版本，避免破坏性更新）
- `<body>` 容器：摘要卡片区、品名走势图、月度柱状图、品类排行表、原始记录表
- 末尾引入 `site/app.js`

### 8.2 `site/app.js`

逻辑：
1. `fetch('./data.json')` 加载数据（同源，无 CORS 问题）
2. 渲染顶部摘要卡片：本月花费、记录条数、最贵单品、平均日花费
3. 渲染**品名走势图**（折线图）：
   - 上方下拉框，多选品名（默认空，提示用户选）
   - 每个选中的 `(item, unit)` 一条线，按日期排序连点
   - 打折点用不同 marker（如空心圆）
4. 渲染**月度花费柱状图**：X = 月份，Y = 总花费
5. 渲染**品类排行表**：默认按累计花费降序，可切换"出现次数"排序
   - 点击品名行 → 自动选中并滚动到走势图
6. 渲染**原始记录表**：可按日期范围、品名关键字过滤；分页（每页 50 条）

### 8.3 不做的事

- 不做用户登录、不存 cookie、不做后端
- 不做数据修改（网页只读）

## 9. GitHub Action 工作流

### 9.1 `.github/workflows/build-and-deploy.yml`

**触发**：
- push 到 `main`，且改动了 `data/**`、`tools/build_site.py`、或 `site/**`
- 也支持手动触发（`workflow_dispatch`）

**步骤**：
1. `actions/checkout@v4`
2. `actions/setup-python@v5`（Python 3.11+）
3. `python tools/build_site.py` → 生成 `site/data.json`
4. `actions/upload-pages-artifact@v3`（path: `site/`）
5. `actions/deploy-pages@v4`

**权限**：`pages: write`、`id-token: write`、`contents: read`

### 9.2 首次启用步骤（写进 README）

1. push 到 GitHub
2. Settings → Pages → Source 选 "GitHub Actions"
3. 等第一次 Action 跑完，访问 `https://<user>.github.io/grocery-tracker/`

## 10. 质量保证

- **CLI 输入校验**：日期格式、数值类型、必填非空 —— 不让脏数据进 repo
- **build_site.py 容错**：坏行打 warning 跳过；空 CSV 产出有效但空的 JSON
- **README 涵盖**：安装、首次录入、推送、首次启用 Pages、日常使用循环
- **`.gitignore`**：`__pycache__/`、`*.pyc`、`.venv/`、`.DS_Store`、`Thumbs.db`

## 11. 风险与权衡

- **手动 push 可能遗忘** —— 用户可接受（设计选型时明确）
- **CSV 编辑器误改** —— 提交前 `git diff` 可见，且 GitHub 渲染表格易于审查
- **品名拼写不一致**（"白菜" vs "大白菜"） —— CLI 不强制规范化；
  build 脚本里 by_item 严格按字面分组。将来可加"别名映射"配置，本期不做。
- **隐私** —— 公开 repo 意味着购物记录任何人可见。
  用户已知悉并选择公开（接受透明度换免费 Pages）。

## 12. 后续可能扩展（本期不做）

- 月度预算与超支提醒
- 品名别名/规范化
- 拼音搜索
- 移动端 Issue 表单录入（方案 2）
- 多仓库（数据私有 + 渲染公开）拆分
- 对接超市/外卖小票 OCR
