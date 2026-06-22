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
    ? DATA.records.filter(r => r.item.includes(q) ||
        (r.merchant || "").includes(q) || (r.note || "").includes(q))
    : DATA.records;
  const sorted = [...filtered].sort((a, b) => b.date.localeCompare(a.date));
  document.getElementById("recordCount").textContent =
    `${sorted.length} / ${DATA.records.length} 条`;
  tbody.innerHTML = sorted.slice(0, 200).map(r => `
    <tr>
      <td>${r.date}</td>
      <td>${escapeHtml(r.item)}</td>
      <td class="right">¥ ${r.unit_price.toFixed(2)}</td>
      <td>${escapeHtml(r.unit)}</td>
      <td class="right">${r.quantity}</td>
      <td class="right">¥ ${r.total.toFixed(2)}</td>
      <td>${r.on_sale ? "✓" : ""}</td>
      <td>${escapeHtml(r.merchant || "")}</td>
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
