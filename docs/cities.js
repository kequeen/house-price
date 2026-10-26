/* Official aggregate city statistics. No inferred missing prices or personal data. */
(() => {
  'use strict';
  const D = window.CHINA_CITY_DATA, M = window.HousingMath, $ = id => document.getElementById(id);
  if (!D || !M) { $('city-name').textContent = '数据未能加载'; return; }
  const q = new URLSearchParams(location.search), cities = new Map(D.cities.map(c => [c.id, c]));
  const sources = new Map(D.sources.map(s => [s.id, s]));
  const areas = [60, 90, 100, 120, 140, 180];
  const state = {city: cities.has(q.get('city')) ? q.get('city') : '420100', record: q.get('record'),
    market: ['all', 'new-residential', 'second-hand-residential', 'new-and-resale-residential', 'auxiliary'].includes(q.get('market')) ? q.get('market') : 'all',
    area: areas.includes(Number(q.get('area'))) ? Number(q.get('area')) : 90,
    people: Number.isInteger(Number(q.get('people'))) && Number(q.get('people')) >= 1 && Number(q.get('people')) <= 6 ? Number(q.get('people')) : 1,
    search: '', filter: 'all', incomeYear: q.get('incomeYear'),
    years: ['recent', '2026', '2025', 'all'].includes(q.get('years')) ? q.get('years') : (D.records.some(r => r.id === q.get('record') && r.period.slice(0, 4) < '2025') ? 'all' : 'recent')};
  const fmt = (n, digits = 0) => n == null ? '—' : new Intl.NumberFormat('zh-CN', {minimumFractionDigits: digits, maximumFractionDigits: digits}).format(n);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const residential = r => ['new-residential', 'second-hand-residential', 'new-and-resale-residential'].includes(r.houseType);
  const typeName = type => ({'new-residential':'新建住宅', 'second-hand-residential':'二手住宅', 'new-and-resale-residential':'新房及二手住宅合计',
    'new-all-commercial':'全部一手商品房（含非住宅）', 'all-housing-transactions-unspecified':'全类型房屋交易（非住宅专属）'}[type] || type);
  function periodName(r) {
    if (r.frequency === 'annual') return r.period + '年全年';
    if (r.frequency === 'quarterly') return r.period.replace(/(\d{4})-Q(\d)/, '$1年第$2季度');
    if (r.frequency === 'year-to-date') return r.period.replace(/(\d{4})-(\d{2})\/(\d{4})-(\d{2})/, (_, y, a, y2, b) => `${y}年${Number(a)}—${Number(b)}月累计`);
    return r.period.replace(/(\d{4})-(\d{2})/, (_, y, m) => `${y}年${Number(m)}月`);
  }
  function periodEnd(r) {
    if (r.frequency === 'annual') return r.period + '-12';
    if (r.frequency === 'quarterly') return r.period.slice(0, 4) + '-' + String(Number(r.period.slice(-1)) * 3).padStart(2, '0');
    return r.period.includes('/') ? r.period.split('/')[1] : r.period;
  }
  const cityRecords = c => D.records.filter(r => r.city === c.name);
  const summaries = c => cityRecords(c).filter(r => !r.district);
  const baselineFor = c => D.annualAffordability.filter(r => r.city === c.name).sort((a, b) => b.year - a.year)[0];
  const ordered = rows => rows.sort((a, b) => periodEnd(b).localeCompare(periodEnd(a)) || Number(residential(b)) - Number(residential(a)) || a.id.localeCompare(b.id));
  const latestFor = c => ordered(summaries(c))[0];
  const ratioYears = c => [...new Set([...D.incomes.filter(i => i.city === c.name).map(i => String(i.year)), ...summaries(c).filter(r => r.frequency === 'annual' && residential(r)).map(r => r.period)])].sort().reverse();
  const hasResidential = c => summaries(c).some(residential);
  const status = c => hasResidential(c) ? '住宅数据' : summaries(c).length ? '辅助数据' : '待接入';
  let toastTimer;
  function toast(text) { $('city-toast').textContent = text; $('city-toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('city-toast').hidden = true; }, 3200); }
  function updateUrl() {
    const params = new URLSearchParams({city: state.city, market: state.market, area: state.area, people: state.people, years: state.years});
    if (state.incomeYear) params.set('incomeYear', state.incomeYear);
    if (state.record) params.set('record', state.record);
    history.replaceState(null, '', location.pathname + '?' + params + location.hash);
  }
  function selectedRows() {
    return ordered(summaries(cities.get(state.city)).filter(r =>
      (state.years === 'all' || (state.years === 'recent' ? ['2025', '2026'].includes(r.period.slice(0, 4)) : r.period.startsWith(state.years))) &&
      (state.market === 'all' || (state.market === 'auxiliary' ? !residential(r) : r.houseType === state.market))));
  }
  function activeRecord() { return selectedRows().find(r => r.id === state.record); }
  function renderCityList() {
    const list = D.cities.filter(c => (!state.search || (c.name + c.coverageNote).includes(state.search)) &&
      (state.filter === 'all' || state.filter === 'residential' && hasResidential(c) || state.filter === 'ratio' && baselineFor(c) || state.filter === 'pending' && !summaries(c).length));
    $('city-list').innerHTML = list.length ? list.map(c => `<button class="city-choice${state.city === c.id ? ' active' : ''}" data-city="${c.id}" aria-pressed="${state.city === c.id}"><b>${esc(c.name)}</b><span>${baselineFor(c) ? '可算收入比' : status(c)}</span><small>${latestFor(c) ? '最新接入 · ' + esc(periodName(latestFor(c))) : c.coverageStatus === 'blocked' ? '入口访问受限' : '尚无可用记录'}</small></button>`).join('') : '<p class="no-results">没有匹配城市。</p>';
  }
  function sourceCard(id) {
    const source = sources.get(id); if (!source) return '';
    const excerpt = source.status === 'reviewed-evidence', hash = excerpt ? source.evidenceSha256 : source.rawSha256;
    const label = excerpt ? '官方网页核读摘录' : source.status === 'collected' ? '已读取原文' : '保留上一版，待复核';
    return `<article class="city-source-card"><span>${esc(source.provider)}${source.kind === 'statistics' ? ' · 统计销售 / 收入口径' : ' · 住建公开统计'}</span><a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.title)} ↗</a><small>发布：${esc(source.publishedAt ? source.publishedAt.slice(0, 10) : '原文未标明日期')} · 核读 / 采集：${esc((source.fetchedAt || '').slice(0, 10) || '未记录')} · ${label}</small><small title="${esc(hash)}">${excerpt ? '摘录' : '原文'} SHA256：${esc(hash?.slice(0, 20) || '—')}…</small>${excerpt ? `<small>${esc(source.evidenceNote)}</small><a href="${esc(source.evidenceFile.replace(/^docs\//, ''))}" target="_blank" rel="noopener noreferrer">查看数值核读摘录 ↗</a>` : ''}${source.error ? `<p>${esc(source.error)}</p>` : ''}</article>`;
  }
  function renderRecord() {
    const c = cities.get(state.city), rows = selectedRows();
    if (!rows.some(r => r.id === state.record)) state.record = rows[0]?.id || null;
    const r = activeRecord();
    $('city-name').textContent = c.name; $('city-description').textContent = c.coverageNote;
    $('city-provider').textContent = status(c) + ' · 官方来源逐条保留';
    $('city-province-link').href = 'index.html?province=' + c.provinceCode + '&area=' + state.area + '&people=' + state.people;
    $('city-market').value = state.market; $('city-years').value = state.years;
    const latest = rows[0], older = r && latest && periodEnd(r) < periodEnd(latest);
    $('record-freshness').hidden = !older;
    $('record-freshness-text').textContent = older ? `正在查看${periodName(r)}；当前筛选下已接入${periodName(latest)}。` : '';
    $('record-extra').textContent = '';
    $('city-record').innerHTML = rows.length ? rows.map(row => `<option value="${esc(row.id)}">${esc(periodName(row))} · ${esc(typeName(row.houseType))} · ${sources.get(row.sourceId)?.kind === 'statistics' ? '统计销售' : '住建发布'}</option>`).join('') : '<option>没有符合当前条件的记录</option>';
    $('city-record').value = state.record || $('city-record').options[0]?.value;
    $('city-record').disabled = !r; $('city-export').disabled = !r;
    const fields = ['record-period', 'record-type', 'record-provider', 'record-count', 'record-area', 'record-amount', 'record-price'];
    if (!r) {
      fields.forEach(id => { $(id).textContent = '—'; });
      $('record-scope').textContent = '当前没有可用的同口径记录。'; $('record-note').textContent = c.coverageNote;
      $('district-caption').textContent = '尚未取得明确期间的分区记录。';
      $('district-table').innerHTML = '<tr><td colspan="5" class="no-results">暂未接入，不以省级或邻近城市数据补值。</td></tr>';
      const unavailable = D.unavailableSources.filter(s => s.city === c.name);
      $('record-sources').innerHTML = unavailable.map(s => `<article class="city-source-card"><span>官方入口 · 尚未取得可用表格</span><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">打开原始入口 ↗</a><p>${esc(s.reason)}</p></article>`).join('');
      return;
    }
    $('record-period').textContent = periodName(r); $('record-type').textContent = typeName(r.houseType);
    $('record-provider').textContent = sources.get(r.sourceId)?.kind === 'statistics' ? '统计销售' : '住建公开发布';
    $('record-scope').textContent = '范围：' + r.scope;
    $('record-count').textContent = fmt(r.count); $('record-area').textContent = fmt(r.areaSqm == null ? null : r.areaSqm / 10000, 2);
    $('record-amount').textContent = fmt(r.amountCny == null ? null : r.amountCny / 100000000, 2);
    $('record-price').textContent = residential(r) ? fmt(r.priceCnyPerSqm) : '—';
    $('record-note').textContent = (r.qualityNote || '') + (r.amountCny == null ? ' 原表未公开同口径金额，本条不计算均价和收入比。' : ' 均价按本条同口径金额和面积计算，不代表具体楼盘报价。');
    const extras = [];
    if (r.averageUnitPriceCny != null) extras.push(`套均网签金额 ${fmt(r.averageUnitPriceCny / 10000)} 万元/套（不是元/㎡）`);
    if (r.areaYoyPercent != null) extras.push(`住宅网签面积同比 ${r.areaYoyPercent >= 0 ? '+' : ''}${fmt(r.areaYoyPercent, 1)}%（绝对量未公布）`);
    if (r.publishedReferencePriceCnyPerSqm != null) extras.push(`全部商品房报道参考 ${fmt(r.publishedReferencePriceCnyPerSqm)} 元/㎡（未限定住宅，不计算住宅收入比）`);
    $('record-extra').textContent = extras.join('；');
    const districts = cityRecords(c).filter(item => item.district && item.sourceId === r.sourceId && item.period === r.period && item.houseType === r.houseType);
    $('district-caption').textContent = districts.length ? `${periodName(r)} · ${typeName(r.houseType)} · 原表${districts.length}个分区 / 分组条目` : '这份官方资料未提供可采用的分区明细。';
    $('district-table').innerHTML = districts.length ? districts.map(item => `<tr class="${item.isComponent ? 'district-component' : ''}"><td>${item.isComponent ? '↳ ' : ''}${esc(item.district)}</td><td>${fmt(item.count)}</td><td>${fmt(item.areaSqm == null ? null : item.areaSqm / 10000, 2)}</td><td>${fmt(item.amountCny == null ? null : item.amountCny / 100000000, 2)}</td><td>${fmt(item.priceCnyPerSqm)}</td></tr>`).join('') : '<tr><td colspan="5" class="no-results">没有分区明细；上方数值按原文范围展示。</td></tr>';
    const ids = [...new Set([r.sourceId, ...(r.sourceIds || [])])];
    $('record-sources').innerHTML = ids.map(sourceCard).join('');
  }
  function renderRatio() {
    const c = cities.get(state.city), years = ratioYears(c);
    if (!years.includes(state.incomeYear)) state.incomeYear = years[0] || null;
    const b = D.annualAffordability.find(r => r.city === c.name && String(r.year) === state.incomeYear);
    const income = D.incomes.find(r => r.city === c.name && String(r.year) === state.incomeYear);
    const annual = summaries(c).filter(r => r.frequency === 'annual' && r.period === state.incomeYear && r.houseType === 'new-residential');
    $('ratio-baseline-year').innerHTML = years.length ? years.map(y => `<option value="${y}">${y}年${D.annualAffordability.some(r => r.city === c.name && String(r.year) === y) ? ' · 已配齐' : ' · 待补齐'}</option>`).join('') : '<option>暂无年度资料</option>';
    $('ratio-baseline-year').value = state.incomeYear || $('ratio-baseline-year').options[0].value;
    $('ratio-baseline-year').disabled = !years.length;
    $('ratio-area').value = state.area; $('ratio-people').value = state.people;
    $('ratio-city-title').textContent = c.name + ' · 同年统计情景';
    $('ratio-caption').textContent = `${state.area}㎡住房，相当于${state.people === 1 ? '个人' : state.people + '人家庭'}全年可支配收入`;
    $('ratio-year').textContent = state.incomeYear ? state.incomeYear + '年' : '未配齐同年数据';
    if (!b) {
      ['ratio-price', 'ratio-total', 'city-ratio'].forEach(id => { $(id).textContent = '—'; });
      $('ratio-income').textContent = income ? fmt(income.urbanDisposableIncomeCnyPerYear) + ' 元/人/年' : '—';
      const missing = [!annual.some(r => r.amountCny != null) && '住宅销售金额', !annual.some(r => r.areaSqm != null) && '住宅销售面积', !income && '城镇人均全年可支配收入'].filter(Boolean);
      const previous = baselineFor(c);
      $('ratio-missing').textContent = `${state.incomeYear ? state.incomeYear + '年尚缺' : '尚未配齐同年'}：${missing.join('、')}，暂不计算倍数。${previous ? '可在基准年份中切换到' + previous.year + '年查看完整基准。' : ''}2026年全年尚未结束，月度和年内累计不代替全年。`;
      $('ratio-source-links').innerHTML = [...new Set([income?.sourceId, ...annual.map(r => r.sourceId)].filter(Boolean))].map(sourceCard).join('');
      return;
    }
    $('ratio-price').textContent = fmt(b.priceCnyPerSqm) + ' 元/㎡';
    $('ratio-income').textContent = fmt(b.urbanDisposableIncomeCnyPerYear) + ' 元/人/年';
    $('ratio-total').textContent = fmt(b.priceCnyPerSqm * state.area / 10000, 2) + ' 万元';
    $('city-ratio').textContent = fmt(M.ratio(b.priceCnyPerSqm, state.area, b.urbanDisposableIncomeCnyPerYear * state.people), 2);
    $('ratio-missing').textContent = `${b.year}年城市年度统计情景，与上方选中的其他月份交易记录独立计算。统计平均数不等于你的实际收入或目标小区价格。`;
    $('ratio-source-links').innerHTML = [...new Set([b.salesSourceId, b.incomeSourceId])].map(sourceCard).join('');
  }
  function renderCoverage() {
    $('coverage-table').innerHTML = D.cities.map(c => {
      const has = hasResidential(c), district = new Set(cityRecords(c).filter(r => r.district).map(r => r.district)).size, b = baselineFor(c);
      return `<tr><td><button class="text-button" data-city="${c.id}">${esc(c.name)}</button></td><td><span class="coverage-status${has ? ' available' : ''}">${status(c)}</span></td><td>${latestFor(c) ? esc(periodName(latestFor(c))) : '—'}</td><td>${district ? district + '个条目' : '—'}</td><td>${b ? b.year + '年可算' : '未配齐'}${b && ratioYears(c)[0] > String(b.year) ? '；' + ratioYears(c)[0] + '年待补齐' : ''}</td><td class="coverage-note">${esc(c.coverageNote)}</td></tr>`;
    }).join('');
  }
  function render() { renderCityList(); renderRecord(); renderRatio(); updateUrl(); }
  document.addEventListener('click', event => {
    const city = event.target.closest('[data-city]');
    if (city && cities.has(city.dataset.city)) { state.city = city.dataset.city; state.record = null; state.market = 'all'; state.incomeYear = null; render(); }
  });
  $('city-search').addEventListener('input', event => { state.search = event.target.value.trim(); renderCityList(); });
  $('city-filter').addEventListener('change', event => { state.filter = event.target.value; renderCityList(); });
  $('city-market').addEventListener('change', event => { state.market = event.target.value; state.record = null; render(); });
  $('city-years').addEventListener('change', event => { state.years = event.target.value; state.record = null; render(); });
  $('record-latest').addEventListener('click', () => { state.record = selectedRows()[0]?.id || null; render(); });
  $('ratio-baseline-year').addEventListener('change', event => { state.incomeYear = event.target.value; render(); });
  $('city-record').addEventListener('change', event => { state.record = event.target.value; render(); });
  $('ratio-area').addEventListener('change', event => { state.area = Number(event.target.value); render(); });
  $('ratio-people').addEventListener('change', event => { state.people = Number(event.target.value); render(); });
  $('city-share').addEventListener('click', async () => { updateUrl(); try { await navigator.clipboard.writeText(location.href); toast('已复制城市、记录和情景链接。'); } catch { toast('请从地址栏复制当前链接。'); } });
  $('city-export').addEventListener('click', () => {
    const r = activeRecord(); if (!r) return;
    const all = [r, ...cityRecords(cities.get(state.city)).filter(item => item.district && item.sourceId === r.sourceId && item.period === r.period && item.houseType === r.houseType)];
    const rows = [['城市', '区县或分组', '子分项不重复累加', '期间', '频率', '住宅类型', '统计范围', '套数', '面积平方米', '金额元', '均价元每平方米', '说明', '来源', '原文SHA256', '核读摘录SHA256', '套均网签金额元每套', '住宅面积同比百分比', '非住宅专属报道参考元每平方米'], ...all.map(item => [item.city, item.district || '原文汇总', item.isComponent ? '是' : '否', item.period, item.frequency, typeName(item.houseType), item.scope, item.count, item.areaSqm, item.amountCny, item.priceCnyPerSqm, item.qualityNote, item.sourceUrl, sources.get(item.sourceId)?.rawSha256, sources.get(item.sourceId)?.evidenceSha256, item.averageUnitPriceCny, item.areaYoyPercent, item.publishedReferencePriceCnyPerSqm])];
    const url = URL.createObjectURL(new Blob([M.csv(rows)], {type:'text/csv;charset=utf-8;'})), a = document.createElement('a'); a.href = url; a.download = `${r.city}-${r.period}-官方交易数据.csv`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  $('stat-cities').textContent = D.cities.filter(hasResidential).length;
  $('stat-ratios').textContent = new Set(D.annualAffordability.map(r => r.city)).size;
  $('stat-districts').textContent = new Set(D.records.filter(r => r.district).map(r => r.city + ':' + r.district)).size;
  $('stat-sources').textContent = D.sources.filter(s => ['collected', 'reviewed-evidence'].includes(s.status)).length;
  $('snapshot-date').textContent = D.retrievedAt;
  renderCoverage(); render();
})();
