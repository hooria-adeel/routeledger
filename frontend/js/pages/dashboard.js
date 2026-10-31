import { api } from '../api.js';
import { compact, el, errorBox, money, num, spinner, svg, tooltip } from '../ui.js';

// Everything here is drawn as SVG by hand (no outside chart library), so the
// pages stay fast and the strict security policy can stay strict.

const monthLabel = (key, short = false) =>
  new Date(`${key.slice(0, 7)}-01T00:00:00`).toLocaleDateString('en-GB', short ? { month: 'short', year: '2-digit' } : { month: 'long', year: 'numeric' });
const share = (part, whole) => (whole > 0 ? (Number(part) / whole) * 100 : 0);
const fmtPct = (v) => (v >= 10 ? `${Math.round(v)}%` : `${v.toFixed(1)}%`);

function segmented(options, current, onPick) {
  return el('div', { class: 'seg-control', role: 'group' }, options.map((o) =>
    el('button', { type: 'button', class: `seg-btn ${o.value === current ? 'on' : ''}`, 'aria-pressed': String(o.value === current), onclick: () => onPick(o.value) }, o.label)));
}
const cardHead = (title, control) => el('div', { class: 'card-head' }, el('h2', {}, title), control);
const kpi = (label, value, title) => el('div', { class: 'kpi' }, el('div', { class: 'label' }, label), el('div', { class: 'value', title: title || false }, value));
const nothing = () => el('p', { class: 'empty-note' }, 'No sales in this period.');

// ---- squarified treemap: rectangles sized by value ----
function treemapLayout(items, W, H) {
  const total = items.reduce((s, i) => s + i.value, 0);
  const nodes = items.map((i) => ({ item: i, area: (i.value / total) * W * H }));
  const out = [];
  let x = 0, y = 0, w = W, h = H, row = [];
  const sum = (r) => r.reduce((s, n) => s + n.area, 0);
  const worst = (r, side) => {
    const s = sum(r), mx = Math.max(...r.map((n) => n.area)), mn = Math.min(...r.map((n) => n.area));
    return Math.max((side * side * mx) / (s * s), (s * s) / (side * side * mn));
  };
  const place = (r) => {
    const s = sum(r);
    if (w >= h) {
      const cw = s / h; let cy = y;
      for (const n of r) { const nh = n.area / cw; out.push({ item: n.item, x, y: cy, w: cw, h: nh }); cy += nh; }
      x += cw; w -= cw;
    } else {
      const rh = s / w; let cx = x;
      for (const n of r) { const nw = n.area / rh; out.push({ item: n.item, x: cx, y, w: nw, h: rh }); cx += nw; }
      y += rh; h -= rh;
    }
  };
  let i = 0;
  while (i < nodes.length) {
    const side = Math.min(w, h);
    if (!row.length || worst([...row, nodes[i]], side) <= worst(row, side)) { row.push(nodes[i]); i += 1; } else { place(row); row = []; }
  }
  if (row.length) place(row);
  return out;
}

export async function render(root) {
  const state = { month: null, metric: 'sales', tab: 'retailers' };
  let data = null;
  const head = el('div', { class: 'dash-head' });
  const kpis = el('div', { class: 'kpis' });
  const monthCard = el('div', { class: 'card' });
  const donutCard = el('div', { class: 'card' });
  const treeCard = el('div', { class: 'card' });
  const leadCard = el('div', { class: 'card' });
  const busyBoxes = [kpis, monthCard, donutCard, treeCard, leadCard];

  root.replaceChildren(spinner());

  async function load(first) {
    busyBoxes.forEach((b) => b.classList.add('busy'));
    try {
      data = await api.get('/dashboard', { month: state.month });
    } catch (problem) {
      if (first) { root.replaceChildren(errorBox(problem.message, () => render(root))); return; }
      busyBoxes.forEach((b) => b.classList.remove('busy'));
      return;
    }
    if (first) root.replaceChildren(head, kpis, el('div', { class: 'dash-grid a' }, monthCard, donutCard), el('div', { class: 'dash-grid b' }, treeCard, leadCard));
    drawHead(); drawKpis(); drawMonths(); drawDonut(); drawTree(); drawLeaders();
    busyBoxes.forEach((b) => b.classList.remove('busy'));
  }
  const setMonth = (key) => { state.month = state.month === key ? null : key; load(false); };

  // ---- header chip ----
  function drawHead() {
    head.replaceChildren(state.month
      ? el('span', { class: 'chip' }, `Showing ${monthLabel(state.month)}`,
        el('button', { class: 'chip-x', type: 'button', 'aria-label': 'Show all months', onclick: () => setMonth(state.month) }, '×'))
      : el('span', { class: 'muted' }, 'Showing all months. Click a month in the chart to look at it closely.'));
  }

  function drawKpis() {
    const t = data.totals;
    kpis.replaceChildren(
      kpi('Products', num(t.products)), kpi('Retailers', num(t.retailers)), kpi('Branches', num(t.branches)),
      kpi(state.month ? 'Orders (month)' : 'Orders', num(t.orders)),
      kpi(state.month ? 'Sales (month)' : 'Total sales', compact(t.total_sales), money(t.total_sales, 0)),
      kpi(state.month ? 'Cartons (month)' : 'Cartons sold', num(t.total_cartons)));
  }

  // ---- 1. months: click a bar to filter the whole dashboard ----
  function drawMonths() {
    const months = data.sales_by_month;
    const sales = state.metric === 'sales';
    const key = sales ? 'total_value' : 'cartons';
    const fmt = sales ? compact : (v) => num(v);
    const W = 560, H = 262, left = 10, right = 10, top = 30, bottom = 32;
    const max = Math.max(1, ...months.map((m) => Number(m[key])));
    const slot = (W - left - right) / Math.max(1, months.length);
    const barW = Math.min(76, slot * 0.62);
    const bestValue = Math.max(...months.map((m) => Number(m[key])));
    const chart = svg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart-svg', role: 'group', 'aria-label': 'Sales per month. Choose a month to filter the dashboard.' });
    for (const f of [0.25, 0.5, 0.75, 1]) {
      const y = H - bottom - f * (H - top - bottom);
      chart.append(svg('line', { x1: left, x2: W - right, y1: y, y2: y, class: 'grid' }));
    }
    months.forEach((m, i) => {
      const monthKey = m.month.slice(0, 7);
      const v = Number(m[key]);
      const h = Math.max(3, (v / max) * (H - top - bottom));
      const x = left + slot * i + (slot - barW) / 2;
      const y = H - bottom - h;
      const selected = state.month === monthKey;
      const dim = state.month && !selected;
      const best = !state.month && v === bestValue;
      const g = svg('g', { class: `bar-g ${selected ? 'selected' : ''} ${dim ? 'dim' : ''}`, tabindex: '0', role: 'button', 'aria-pressed': String(selected),
        'aria-label': `${monthLabel(monthKey)}: ${fmt(v)}. ${selected ? 'Press to show all months.' : 'Press to filter the dashboard.'}` },
      svg('rect', { x, y, width: barW, height: h, rx: 7, class: `bar c${i % 4} ${best ? 'hot' : ''}` }),
      svg('text', { x: x + barW / 2, y: y - 8, 'text-anchor': 'middle', class: 'val' }, fmt(v)),
      svg('text', { x: x + barW / 2, y: H - 11, 'text-anchor': 'middle', class: 'lab' }, monthLabel(monthKey, true)));
      g.addEventListener('click', () => setMonth(monthKey));
      g.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setMonth(monthKey); } });
      tooltip(g, () => [el('b', {}, monthLabel(monthKey)), el('span', {}, `Sales: ${money(m.total_value, 0)}`),
        el('span', {}, `Cartons: ${num(m.cartons)}`), el('span', {}, `Orders: ${num(m.orders)}`),
        el('em', {}, selected ? 'Click to show all months' : 'Click to filter the dashboard')]);
      chart.append(g);
    });
    monthCard.replaceChildren(
      cardHead('Sales per month', segmented([{ value: 'sales', label: 'Sales' }, { value: 'cartons', label: 'Cartons' }], state.metric, (v) => { state.metric = v; drawMonths(); })),
      chart, el('p', { class: 'hint' }, 'Tip: click a month to filter every number and chart on this page.'));
  }

  // ---- 2. category donut ----
  function drawDonut() {
    const rows = data.sales_by_category.filter((r) => Number(r.total_value) > 0);
    const total = rows.reduce((s, r) => s + Number(r.total_value), 0);
    if (!total) { donutCard.replaceChildren(cardHead('Sales by category'), nothing()); return; }
    const R = 78, C = 2 * Math.PI * R;
    const tTitle = svg('text', { x: 110, y: 104, 'text-anchor': 'middle', class: 'd-title' }, 'Total');
    const tValue = svg('text', { x: 110, y: 128, 'text-anchor': 'middle', class: 'd-value' }, compact(total));
    const tSub = svg('text', { x: 110, y: 148, 'text-anchor': 'middle', class: 'd-sub' }, `${rows.length} categories`);
    const ring = svg('svg', { viewBox: '0 0 220 220', class: 'donut-svg', role: 'img', 'aria-label': 'Sales by category' });
    const segs = [], items = [];
    let offset = 0;
    rows.forEach((r, i) => {
      const len = (Number(r.total_value) / total) * C;
      const dash = Math.max(0, len - 3);
      const seg = svg('circle', { cx: 110, cy: 110, r: R, fill: 'none', class: `seg s${i % 5}`, 'stroke-width': 30,
        'stroke-dasharray': `${dash} ${C - dash}`, 'stroke-dashoffset': -offset, transform: 'rotate(-90 110 110)', tabindex: '0', 'aria-label': `${r.category}: ${compact(r.total_value)}` });
      offset += len;
      segs.push(seg);
      ring.append(seg);
    });
    ring.append(tTitle, tValue, tSub);
    const focusSeg = (i) => {
      segs.forEach((s, j) => { s.classList.toggle('active', j === i); s.classList.toggle('faded', i !== null && j !== i); });
      items.forEach((b, j) => { b.classList.toggle('active', j === i); b.classList.toggle('faded', i !== null && j !== i); });
      if (i === null) { tTitle.textContent = 'Total'; tValue.textContent = compact(total); tSub.textContent = `${rows.length} categories`; }
      else { tTitle.textContent = rows[i].category; tValue.textContent = compact(rows[i].total_value); tSub.textContent = `${fmtPct(share(rows[i].total_value, total))} of sales`; }
    };
    segs.forEach((s, i) => {
      s.addEventListener('mouseenter', () => focusSeg(i)); s.addEventListener('mouseleave', () => focusSeg(null));
      s.addEventListener('focus', () => focusSeg(i)); s.addEventListener('blur', () => focusSeg(null));
    });
    const legend = el('ul', { class: 'legend' }, rows.map((r, i) => {
      const b = el('button', { type: 'button', class: 'legend-row', onmouseenter: () => focusSeg(i), onmouseleave: () => focusSeg(null), onfocus: () => focusSeg(i), onblur: () => focusSeg(null) },
        el('i', { class: `dot s${i % 5}` }), el('span', { class: 'lg-name' }, r.category),
        el('span', { class: 'lg-val' }, compact(r.total_value)), el('span', { class: 'lg-pct' }, fmtPct(share(r.total_value, total))));
      items.push(b);
      return el('li', {}, b);
    }));
    donutCard.replaceChildren(cardHead('Sales by category'), el('div', { class: 'donut-wrap' }, ring, legend));
  }

  // ---- 3. area treemap ----
  function drawTree() {
    const rows = data.sales_by_area.filter((r) => Number(r.total_value) > 0).map((r) => ({ ...r, value: Number(r.total_value) }));
    const total = rows.reduce((s, r) => s + r.value, 0);
    if (!total) { treeCard.replaceChildren(cardHead('Sales by area'), nothing()); return; }
    const W = 640, H = 340;
    const known = rows.filter((r) => r.area !== 'Not recorded');
    const rank = new Map(known.map((r, i) => [r.area, i]));
    const chart = svg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'tree-svg', role: 'group', 'aria-label': 'Sales by area. Bigger boxes mean more sales.' });
    for (const t of treemapLayout(rows, W, H)) {
      const r = t.item;
      const unknown = r.area === 'Not recorded';
      const level = unknown ? 'u' : `t${4 - Math.min(4, Math.floor((rank.get(r.area) / Math.max(1, known.length)) * 5))}`;
      const g = svg('g', { class: `tile ${level}`, tabindex: '0', role: 'img', 'aria-label': `${r.area}: ${compact(r.value)}, ${fmtPct(share(r.value, total))} of sales` });
      g.append(svg('rect', { x: t.x + 1.5, y: t.y + 1.5, width: Math.max(0, t.w - 3), height: Math.max(0, t.h - 3), rx: 8 }));
      const fit = Math.floor((t.w - 16) / 7.2);
      if (t.h > 32 && fit >= 4) {
        const name = r.area.length > fit ? `${r.area.slice(0, Math.max(1, fit - 1))}…` : r.area;
        g.append(svg('text', { x: t.x + 10, y: t.y + 22, class: 'tn' }, name));
        if (t.h > 52) g.append(svg('text', { x: t.x + 10, y: t.y + 40, class: 'tv' }, compact(r.value)));
      }
      tooltip(g, () => [el('b', {}, r.area), el('span', {}, `Sales: ${money(r.value, 0)}`), el('span', {}, `Share: ${fmtPct(share(r.value, total))}`), el('span', {}, `Cartons: ${num(r.cartons)}`)]);
      chart.append(g);
    }
    treeCard.replaceChildren(cardHead('Sales by area'), chart,
      el('p', { class: 'hint' }, 'Bigger box = more sales. Hover a box for details. Grey = orders where the area was not recorded.'));
  }

  // ---- 4. leaderboard ----
  function drawLeaders() {
    const isRetailer = state.tab === 'retailers';
    const rows = isRetailer ? data.top_retailers : data.top_products;
    const label = isRetailer ? 'retailer' : 'product';
    const total = Number(data.totals.total_sales);
    const control = segmented([{ value: 'retailers', label: 'Retailers' }, { value: 'products', label: 'Products' }], state.tab, (v) => { state.tab = v; drawLeaders(); });
    if (!rows.length) { leadCard.replaceChildren(cardHead('Top 5', control), nothing()); return; }
    const R = 15, C = 2 * Math.PI * R;
    const list = el('ol', { class: 'leaders' }, rows.map((r, i) => {
      const p = share(r.total_value, total);
      const ring = svg('svg', { viewBox: '0 0 40 40', class: 'ring', 'aria-hidden': 'true' },
        svg('circle', { cx: 20, cy: 20, r: R, class: 'ring-bg', fill: 'none', 'stroke-width': 5 }),
        svg('circle', { cx: 20, cy: 20, r: R, class: `ring-fg s${i % 5}`, fill: 'none', 'stroke-width': 5, 'stroke-linecap': 'round',
          'stroke-dasharray': `${(Math.min(100, p) / 100) * C} ${C}`, transform: 'rotate(-90 20 20)' }));
      const row = el('li', { class: 'leader', tabindex: '0' },
        el('span', { class: `rank r${i + 1}` }, String(i + 1)),
        el('span', { class: 'ld-name', title: r[label] }, r[label]),
        el('span', { class: 'ld-val' }, compact(r.total_value)),
        el('span', { class: 'ld-share' }, ring, el('b', {}, fmtPct(p))));
      tooltip(row, () => [el('b', {}, r[label]), el('span', {}, `Sales: ${money(r.total_value, 0)}`), el('span', {}, `Cartons: ${num(r.cartons)}`), el('span', {}, `${fmtPct(p)} of all sales in this period`)]);
      return row;
    }));
    leadCard.replaceChildren(cardHead('Top 5', control), list);
  }

  load(true);
}
