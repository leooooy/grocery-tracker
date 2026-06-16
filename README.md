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
