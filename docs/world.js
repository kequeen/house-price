/* Static international reference data. Personal inputs stay in this browser. */
(() => {
  'use strict';
  const q = new URLSearchParams(location.search), isSea = q.get('scope') === 'sea';
  const D = isSea ? window.SEA_HOUSING : window.GLOBAL_HOUSING, MAP = window.WORLD_MAP, M = window.HousingMath;
  const $ = id => document.getElementById(id);
  if (!D || !MAP || !M) { $('world-detail-name').textContent = '数据未能加载'; return; }
  const records = D.records, byId = new Map(records.map(r => [r.id, r]));
  const areas = [60, 90, 100, 120, 140, 180], baseArea = D.baseAreaSqm || 60;
  const incomeLabel = D.incomeLabel || '职业收入', versionLabel = isSea ? '2026年版' : '2026报告';
  const regions = isSea ? ['all', ...new Set(records.map(r => r.country))] : ['all', '亚洲', '欧洲', '北美洲', '南美洲', '大洋洲'];
  const state = {
    area: areas.includes(Number(q.get('area'))) ? Number(q.get('area')) : 90,
    people: Number(q.get('people')) === 2 ? 2 : 1,
    city: byId.has(q.get('city')) ? q.get('city') : D.defaultCity || 'tokyo',
    compare: q.has('compare') ? [...new Set(q.get('compare').split(',').filter(id => byId.has(id)))].slice(0, 3) : (D.defaultComparison || ['tokyo', 'london', 'new-york']).filter(id => byId.has(id)),
    region: regions.includes(q.get('region')) ? q.get('region') : 'all',
    search: '', sort: q.get('sort') === 'asc' ? 'asc' : 'desc', continent: 'all'
  };
  if (!byId.has(state.city)) state.city = records[0].id;
  const esc = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const fmt = (n, digits = 1) => new Intl.NumberFormat('zh-CN', {maximumFractionDigits: digits, minimumFractionDigits: digits}).format(n);
  const factor = () => state.area / baseArea / state.people;
  const ratio = r => r.ratioApprox * factor();
  const approx = n => '约 ' + fmt(n) + ' 倍';
  const palette = ['#d6e9e5', '#c0d2e2', '#a9afd5', '#9988c3', '#8060aa', '#603780'];
  const lo = Math.min(...records.map(r => r.ratioApprox)), hi = Math.max(...records.map(r => r.ratioApprox));
  const color = r => palette[Math.min(5, Math.floor((r.ratioApprox - lo) / (hi - lo || 1) * 5.999))];
  let toastTimer, box = [0, 0, 1000, 520];
  function toast(text) { $('world-toast').textContent = text; $('world-toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('world-toast').hidden = true; }, 3500); }
  function project(lon, lat) {
    const theta = Math.asin(Math.sqrt(3) / 2 * Math.sin(lat * Math.PI / 180)), t2 = theta * theta, t6 = t2 ** 3;
    const x = lon * Math.PI / 180 * Math.cos(theta) / (Math.sqrt(3) / 2 * (1.340264 - 3 * 0.081106 * t2 + t6 * (7 * 0.000893 + 9 * 0.003796 * t2)));
    const y = theta * (1.340264 - 0.081106 * t2 + t6 * (0.000893 + 0.003796 * t2));
    return [500 + x * 178, 263 - y * 178];
  }
  function updateUrl() {
    const p = new URLSearchParams({scope: isSea ? 'sea' : 'global', city: state.city, area: state.area, people: state.people, compare: state.compare.join(','), region: state.region, sort: state.sort});
    history.replaceState(null, '', location.pathname + '?' + p + location.hash);
  }
  function visible() {
    const search = state.search.toLocaleLowerCase();
    return records.filter(r => (state.region === 'all' || (isSea ? r.country : r.region) === state.region) && (!search || [r.name, r.nameEn, r.country, r.countryEn, r.region].join(' ').toLocaleLowerCase().includes(search)))
      .sort((a, b) => state.sort === 'name' ? a.name.localeCompare(b.name, 'zh-CN') : state.sort === 'asc' ? ratio(a) - ratio(b) : ratio(b) - ratio(a));
  }
  function setViewBox(next) {
    const width = Math.max(160, Math.min(1000, next[2])), height = width * .52;
    box = [Math.max(0, Math.min(1000 - width, next[0])), Math.max(0, Math.min(520 - height, next[1])), width, height];
    $('world-map').setAttribute('viewBox', box.join(' '));
    $('world-zoom-in').disabled = width <= 160;
    $('world-zoom-out').disabled = width >= 1000;
    renderDots();
  }
  function continentView(name) {
    state.continent = name;
    document.querySelectorAll('[data-continent]').forEach(el => { el.classList.toggle('active', el.dataset.continent === name); el.setAttribute('aria-pressed', String(el.dataset.continent === name)); });
    const views = {'all': [0, 0, 1000, 520], '亚洲': [660, 130, 340, 176.8], '东南亚': [725, 177, 230, 119.6], '欧洲': [432, 63, 250, 130], '美洲': [30, 90, 650, 338], '大洋洲': [760, 290, 240, 124.8]};
    setViewBox(views[name] || views.all);
  }
  function zoom(multiplier) {
    const width = Math.max(160, Math.min(1000, box[2] * multiplier)), selected = byId.get(state.city), point = project(selected.lon, selected.lat);
    const inside = point[0] >= box[0] && point[0] <= box[0] + box[2] && point[1] >= box[1] && point[1] <= box[1] + box[3];
    const center = inside ? point : [box[0] + box[2] / 2, box[1] + box[3] / 2];
    setViewBox([center[0] - width / 2, center[1] - width * .26, width, width * .52]);
  }
  function renderDots() {
    const shown = new Set(visible().map(r => r.id)), scale = box[2] / 1000;
    $('world-markers').innerHTML = records.filter(r => r.id !== state.city).concat(byId.get(state.city)).map(r => {
      const [x, y] = project(r.lon, r.lat), selected = state.city === r.id;
      const label = selected || (box[2] < 500 && shown.has(r.id));
      return `<g class="world-city${selected ? ' selected' : ''}" data-city="${esc(r.id)}" tabindex="0" role="button" aria-pressed="${selected}" aria-label="${esc(r.name)}，${approx(ratio(r))}年${incomeLabel}，查看详情" opacity="${shown.has(r.id) ? 1 : .18}"><title>${esc(r.name)} · ${esc(r.country)}：${approx(ratio(r))}</title><circle class="city-hit" cx="${x}" cy="${y}" r="${14 * scale}"/><circle class="city-halo" cx="${x}" cy="${y}" r="${(selected ? 14 : 9) * scale}" fill="${color(r)}"/><circle class="city-core" cx="${x}" cy="${y}" r="${(selected ? 7 : 4.5) * scale}" fill="${color(r)}"/>${label ? `<text class="world-city-label" x="${x + 10 * scale}" y="${y - 10 * scale}" style="font-size:${12 * scale}px">${esc(r.name)}</text>` : ''}</g>`;
    }).join('');
  }
  function renderDetail() {
    const r = byId.get(state.city);
    $('world-detail-country').textContent = r.region + ' · ' + r.country;
    $('world-detail-name').textContent = r.name; $('world-detail-en').textContent = r.nameEn;
    $('world-detail-ratio').textContent = '≈ ' + fmt(ratio(r));
    $('world-detail-base').textContent = approx(r.ratioApprox);
    $('world-detail-scenario').textContent = `${state.area}㎡ / ${state.people}份${incomeLabel}`;
    const range = Number.isFinite(r.ratioLowApprox) && Number.isFinite(r.ratioHighApprox) ? ` 原图范围经情景缩放约${fmt(r.ratioLowApprox * factor())}–${fmt(r.ratioHighApprox * factor())}倍。` : '';
    $('world-detail-context').textContent = isSea
      ? `原表90㎡家庭模型为约${fmt(r.sourcePublishedFamilyRatio)}倍（假设1.5份税后工资）。当前按${state.people}份收入和${state.area}㎡换算，仍是模型约值。`
      : (state.area === 60 && state.people === 1 ? '原报告60㎡近市中心公寓的单人参照。' : '按原报告近似倍数作线性情景估算。') + range;
    const added = state.compare.includes(r.id);
    $('world-add').disabled = added; $('world-add').textContent = added ? '已加入对比 ✓' : '加入城市对比 ＋';
  }
  function renderComparisons() {
    const max = Math.max(...records.map(ratio));
    $('world-compare-caption').textContent = `最多3座城市 · 当前 ${state.area}㎡ / ${state.people}份${incomeLabel} · 均为约值`;
    let html = state.compare.map(id => {
      const r = byId.get(id);
      return `<article class="compare-item"><div class="compare-item-head"><button data-city="${esc(r.id)}">${esc(r.name)}</button><button class="compare-remove" data-remove-city="${esc(r.id)}" aria-label="移除${esc(r.name)}对比">×</button></div><div class="compare-value">≈ ${fmt(ratio(r))}<small>倍年收入</small></div><div class="compare-bar"><span style="width:${ratio(r) / max * 100}%"></span></div><div class="compare-meta"><span>${esc(r.country)} · ${versionLabel}</span><span>单人${incomeLabel}参照</span></div></article>`;
    }).join('');
    for (let i = state.compare.length; i < 3; i++) html += '<div class="compare-empty"><span>＋</span><p>从地图或表格<br>加入一座城市</p></div>';
    $('world-comparisons').innerHTML = html; $('world-clear').disabled = !state.compare.length;
  }
  function renderTable() {
    const rows = visible();
    $('world-table').innerHTML = rows.length ? rows.map((r, i) => `<tr class="${r.id === state.city ? 'is-selected' : ''}"><td><div class="table-name"><span>${String(i + 1).padStart(2, '0')}</span><button data-city="${esc(r.id)}">${esc(r.name)}</button></div><small class="world-country">${esc(r.country)} · ${esc(r.nameEn)}</small></td><td>≈ ${fmt(r.ratioApprox)}</td><td><b>≈ ${fmt(ratio(r))}</b></td><td><span class="basis-pill">${isSea ? '税后工资 · 模型换算' : '职业收入 · 图读约值'}</span></td><td><button class="table-add${state.compare.includes(r.id) ? ' added' : ''}" data-compare-city="${esc(r.id)}" aria-label="${state.compare.includes(r.id) ? '移除' : '加入'}${esc(r.name)}对比">${state.compare.includes(r.id) ? '✓' : '＋'}</button></td></tr>`).join('') : '<tr><td class="no-results" colspan="5">没有匹配的城市，请调整搜索或区域。</td></tr>';
    $('world-result-count').textContent = `显示 ${rows.length} / ${records.length} 座城市 · ${versionLabel}`;
  }
  function render() {
    $('world-area').value = state.area; $('world-people').value = state.people;
    $('world-region').value = state.region; $('world-sort').value = state.sort;
    $('scenario-note').textContent = isSea ? '按Numbeo原家庭模型换算为单人税后工资；面积可调整' : state.area === 60 && state.people === 1 ? '当前为原报告60㎡单人参照，数值为图读约值' : '当前为线性情景估算；原报告基准为60㎡ / 单人职业收入';
    $('world-map-title').textContent = `住房总价 / ${state.people === 1 ? '单人' : '两份等额'}年${incomeLabel} · ${state.area}㎡`;
    renderDots(); renderDetail(); renderComparisons(); renderTable(); updateUrl();
  }
  function selectCity(id) {
    if (!byId.has(id)) return;
    state.city = id;
    const r = byId.get(id), [x, y] = project(r.lon, r.lat);
    if (x < box[0] || x > box[0] + box[2] || y < box[1] || y > box[1] + box[3]) continentView(r.region.includes('美洲') ? '美洲' : r.region);
    render();
  }
  function compareCity(id) {
    if (!byId.has(id)) return;
    if (state.compare.includes(id)) state.compare = state.compare.filter(x => x !== id);
    else { if (state.compare.length >= 3) { toast('最多比较3座城市，请先移除一个。'); return; } state.compare.push(id); }
    render();
  }
  document.addEventListener('click', event => {
    const remove = event.target.closest('[data-remove-city]'); if (remove) { compareCity(remove.dataset.removeCity); return; }
    const compare = event.target.closest('[data-compare-city]'); if (compare) { compareCity(compare.dataset.compareCity); return; }
    const city = event.target.closest('[data-city]'); if (city) { selectCity(city.dataset.city); return; }
    const continent = event.target.closest('[data-continent]'); if (continent) continentView(continent.dataset.continent);
  });
  $('world-map').addEventListener('keydown', event => { const city = event.target.closest('[data-city]'); if (city && ['Enter', ' '].includes(event.key)) { event.preventDefault(); selectCity(city.dataset.city); } });
  for (const id of ['world-area', 'world-people']) $(id).addEventListener('change', () => { state.area = Number($('world-area').value); state.people = Number($('world-people').value); render(); });
  $('world-reset').addEventListener('click', () => { state.area = 90; state.people = 1; render(); });
  $('world-search').addEventListener('input', event => { state.search = event.target.value.trim(); renderTable(); renderDots(); });
  $('world-region').addEventListener('change', event => { state.region = event.target.value; render(); });
  $('world-sort').addEventListener('change', event => { state.sort = event.target.value; render(); });
  $('world-add').addEventListener('click', () => compareCity(state.city));
  $('world-clear').addEventListener('click', () => { state.compare = []; render(); });
  $('world-zoom-in').addEventListener('click', () => zoom(.7));
  $('world-zoom-out').addEventListener('click', () => zoom(1.5));
  $('world-zoom-reset').addEventListener('click', () => continentView('all'));
  $('world-share').addEventListener('click', async () => { updateUrl(); try { await navigator.clipboard.writeText(location.href); toast('已复制城市对比链接，不包含个人房价或收入。'); } catch { toast('请从地址栏复制当前链接，不包含个人输入。'); } });
  $('world-export').addEventListener('click', () => {
    const rows = [['城市', '英文名称', '国家及地区', '数据版本', `${baseArea}㎡单人${incomeLabel}倍数(约)`, '原图范围下界(约)', '原图范围上界(约)', '情景面积㎡', '等额收入份数', '情景倍数(约)', '收入口径', '来源'], ...visible().map(r => [r.name, r.nameEn, r.country, versionLabel, r.ratioApprox, r.ratioLowApprox, r.ratioHighApprox, state.area, state.people, ratio(r).toFixed(1), D.incomeDefinition, D.source.url])];
    const url = URL.createObjectURL(new Blob([M.csv(rows)], {type: 'text/csv;charset=utf-8;'})), a = document.createElement('a'); a.href = url; a.download = (isSea ? '东南亚' : '全球') + '城市住房负担-2026约值.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  const outputs = ['own-ratio', 'own-total', 'own-down', 'own-saving', 'own-payment', 'own-payment-ratio'];
  const currencyCode = () => $('own-currency').value === 'LOCAL' ? '本币' : $('own-currency').value;
  // Add browser-supported currencies without making any network or FX request.
  if (typeof Intl.supportedValuesOf === 'function' && typeof Intl.DisplayNames === 'function') {
    const names = new Intl.DisplayNames(['zh-CN'], {type:'currency'});
    const existing = new Set([...$('own-currency').options].map(option => option.value));
    for (const code of Intl.supportedValuesOf('currency')) {
      if (!existing.has(code)) $('own-currency').insertBefore(new Option(code + ' ' + names.of(code), code), $('own-currency').lastElementChild);
    }
  }
  function updateCurrency() { const c = currencyCode(); document.querySelectorAll('[data-currency-unit]').forEach(el => { el.textContent = c + '/㎡'; }); document.querySelectorAll('[data-income-unit]').forEach(el => { el.textContent = c + '/月'; }); }
  function calculatePersonal() {
    if (!$('own-price').value || !$('own-income').value) { outputs.forEach(id => { $(id).textContent = '—'; }); $('own-error').hidden = true; return; }
    try {
      if (!$('world-form').checkValidity()) throw new Error('请检查输入：面积、单价和收入须大于0；比例为0–100%，贷款年限为1–40整数年，年利率为0–30%。');
      const input = Object.fromEntries(new FormData($('world-form')).entries()), r = M.personal(input), c = currencyCode();
      const money = n => fmt(n, 0) + ' ' + c;
      $('own-error').hidden = true; $('own-ratio').textContent = fmt(r.ratio, 2);
      $('own-total').textContent = money(r.total); $('own-down').textContent = money(r.down);
      $('own-saving').textContent = r.downYears === null ? '无法积累（结余为0）' : fmt(r.downYears) + ' 年';
      $('own-payment').textContent = money(r.monthly) + '/月'; $('own-payment-ratio').textContent = fmt(r.paymentRatio) + '%';
    } catch (error) { outputs.forEach(id => { $(id).textContent = '—'; }); $('own-error').textContent = error.message; $('own-error').hidden = false; }
  }
  $('world-form').addEventListener('submit', event => event.preventDefault());
  $('world-form').addEventListener('input', calculatePersonal);
  $('own-currency').addEventListener('change', () => { $('own-price').value = ''; $('own-income').value = ''; updateCurrency(); calculatePersonal(); $('own-source').textContent = '已切换标注币种。请重新填写同币种的实际房价和个人可支配收入，不自动换汇。'; });
  $('world-use-city').addEventListener('click', () => {
    const r = byId.get(state.city);
    if (!$('own-price').value && !$('own-income').value) { $('own-currency').value = r.currency; updateCurrency(); }
    $('own-source').textContent = `正在为${r.name}测算。请自行填写实际单价和个人月可支配收入，二者须与所选币种一致；不会用参考倍数反推虚构报价。`;
  });
  function configureScope() {
    document.querySelectorAll('.scope-switch [data-scope]').forEach(a => {
      if (a.dataset.scope === (isSea ? 'sea' : 'global')) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    document.querySelector('[data-continent="东南亚"]').hidden = !isSea;
    if (!isSea) return;
    document.title = '安居尺度 · 东南亚城市住房负担';
    document.querySelector('meta[name="description"]').content = '东南亚7国12城住房负担参考。按Numbeo2026年版公开公式换算单人税后工资，支持国家筛选、地图、三城对比与本币个人测算。';
    $('world-title').innerHTML = '把东南亚的生活，<br>放进<span>安居的尺度。</span>';
    document.querySelector('.hero-copy>.eyebrow').textContent = 'SOUTHEAST ASIA / HOME OBSERVATORY';
    document.querySelector('.hero-copy>p').innerHTML = '从曼谷到吉隆坡，从河内到雅加达。<br>看看当地工资对应的住房负担，再用自己的收入，算一份适合你的答案。';
    document.querySelector('.hero-actions>.primary').innerHTML = '探索东南亚 <span>↗</span>';
    document.querySelectorAll('.world-orbit>i').forEach((el, index) => { el.textContent = ['Bangkok', 'Hanoi', 'Kuala Lumpur'][index]; });
    document.querySelector('.world-hero-card>strong').innerHTML = `<span id="hero-city-count">${records.length}</span> 座城市，看见东南亚的日常。`;
    document.querySelector('header nav>a').textContent = '东南亚城市';
    document.querySelector('.world-facts>div>span').textContent = '已接入东南亚城市';
    document.querySelector('.world-facts>div:nth-child(3)>span').textContent = '单人换算基准';
    document.querySelector('.world-facts>div:nth-child(3)>strong').innerHTML = '90<small> ㎡ / 单人税后工资</small>';
    document.querySelector('.facts-source>span').textContent = '参考数据版本';
    document.querySelector('.facts-source>a').textContent = '来源：Numbeo · 查看口径 ↗';
    document.querySelector('.world-scope-note>p').innerHTML = '来源为 <a href="https://www.numbeo.com/" target="_blank" rel="noopener noreferrer">Numbeo</a> 2026年版众包城市参考，按公开公式换算为<strong>单人税后平均工资</strong>。它不等于居民人均可支配收入；与瑞银职业收入数据独立展示。城市样本也不代表整个国家。';
    $('world-explore-title').textContent = '在东南亚，找到自己的尺度。';
    document.querySelector('#world-explore .section-heading p').textContent = '7国12城 · 2026年版快照 · 默认90㎡、1人；非官方成交统计。';
    document.querySelectorAll('[data-continent]').forEach(button => { button.hidden = !['all', '东南亚'].includes(button.dataset.continent); });
    document.querySelector('.world-visual>.chart-note').innerHTML = '来源：<a href="https://www.numbeo.com/property-investment/region_rankings.jsp?title=2026&amp;region=035" target="_blank" rel="noopener noreferrer">Numbeo 2026年版东南亚城市表 ↗</a> · 城市点位为指示位置<br>文莱、老挝、缅甸、东帝汶尚未接入；不以邻国数据代填。底图：Natural Earth。';
    document.querySelector('.world-detail .year-tag').textContent = '2026年版';
    document.querySelector('.world-detail-value>span').textContent = '倍年税后工资';
    document.querySelector('.world-detail dl>div:first-child>dt').textContent = '90㎡单人换算';
    document.querySelector('.world-detail dl>div:nth-child(3)>dd').textContent = '当地个人税后平均工资';
    document.querySelector('.world-detail dl>div:nth-child(4)>dd').textContent = '原表已舍入，换算仍为约值';
    document.querySelector('.world-detail>.detail-footnote').textContent = '工资和房价来自众包样本，未核验为官方成交或可支配收入；倍数不等于实际攒钱年数。';
    $('world-original').textContent = '查看Numbeo原始数据 ↗';
    document.querySelector('.ranking-heading>div>h3').textContent = '东南亚城市，逐一看清。';
    document.querySelector('.ranking-heading>div>p').textContent = '同一来源、同一模型；国家名称用于归组，仍是城市样本。';
    $('world-region').innerHTML = '<option value="all">全部国家</option>' + regions.slice(1).map(country => `<option>${esc(country)}</option>`).join('');
    document.querySelector('#world-explore th:nth-child(2)').innerHTML = '90㎡单人参照<small>模型换算 · 约数</small>';
    document.querySelector('#world-explore table>caption').textContent = 'Numbeo2026年版东南亚城市单人税后工资购房参考';
    $('world-search').placeholder = '搜索城市或国家，如曼谷 / Thailand';
    $('world-area').querySelector('[value="60"]').textContent = '60 ㎡';
    $('world-area').querySelector('[value="90"]').textContent = '90 ㎡（单人基准）';
    document.querySelector('#global-methods>h2').textContent = '东南亚的选择，也把口径讲清楚。';
    const cards = document.querySelectorAll('#global-methods .method-cards>article');
    const methodText = [
      ['7国12城，保留城市边界', '已接入泰国、越南、马来西亚、印尼、菲律宾、柬埔寨和新加坡。槟城为来源使用的地区名称，地图用乔治市作指示点；不能把它或其他城市当成国家均值。'],
      ['税后工资，明确模型换算', 'Numbeo原表用90㎡公寓价格除以1.5份平均税后工资。本页把这1.5份工资换算为1份，才得到单人参照；与居民人均可支配收入和瑞银职业收入均不等同。'],
      ['众包快照，约数展示', '房价取市中心与中心外单价的平均，收入为众包平均税后工资。2026年版不是实时成交；样本量和区域结构可能影响结果，原表舍入后换算仍是约值。']
    ];
    cards.forEach((card, index) => { card.querySelector('h3').textContent = methodText[index][0]; card.querySelector('p').textContent = methodText[index][1]; });
    document.querySelector('.global-source-panel .formula-block').textContent = '当前倍数 ≈ Numbeo原家庭倍数 × 1.5 × 面积 ÷ 90 ÷ 收入份数';
    document.querySelector('.global-source-panel>div>p:last-of-type').textContent = '例如原表假设1.5份税后工资，单人90㎡的结果是原表的1.5倍。面积调整假设单价不变；2份收入是假设两个同等工资的人共同购房。原表没有提供不确定区间，不能凭空补上。新加坡在瑞银与Numbeo两页数值不同，来自户型、收入群体及房价采样差异，不作跨来源高低排名。';
    $('global-pdf').textContent = '来源：Numbeo 东南亚原表 ↗';
    $('global-data-download').href = 'data/global/sea-housing-2026.json';
    $('global-data-download').textContent = '下载原倍数、单人换算及来源 JSON ↓';
    const actions = document.querySelector('.global-source-actions');
    for (const [label, href] of [['Numbeo 计算方法 ↗', D.source.methodologyUrl], ['Numbeo 个人网站引用条款 ↗', D.source.termsUrl]]) {
      const link = document.createElement('a'); link.textContent = label; link.href = href; link.className = 'text-button'; link.target = '_blank'; link.rel = 'noopener noreferrer'; actions.append(link);
    }
    document.querySelector('.footer>div>small').textContent = '东南亚：Numbeo 2026年版 · 独立口径 · 来源署名及回链保留';
  }
  $('hero-city-count').textContent = records.length; $('city-count').textContent = records.length;
  $('country-count').textContent = new Set(records.map(r => r.country)).size;
  for (const id of ['global-pdf', 'world-original']) $(id).href = D.source.url + (D.source.page ? '#page=' + D.source.page : '');
  $('global-source-description').textContent = isSea ? `${D.source.title}。个人网站引用，来源署名 Numbeo 并回链。原表为90㎡ / 1.5份税后工资，当前页换算为单人税后工资；2026年版快照，不是实时成交或官方统计。` : `${D.source.title} · 第${D.source.page}页 Price-to-income 图表，第${D.source.methodPage}页方法说明。数值为图读近似值，报告原文通过来源链接查看。`;
  $('world-map').innerHTML = `<g class="world-grid"><path d="${MAP.graticule}"/></g><g class="world-land">${MAP.features.map(f => `<path d="${f.path}" fill-rule="evenodd"><title>${esc(f.name)}</title></path>`).join('')}</g><g id="world-markers"></g>`;
  configureScope(); updateCurrency(); render();
  if (isSea) continentView('东南亚');
})();
