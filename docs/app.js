/* All calculations and personal inputs stay in this browser. No analytics. */
(() => {
  'use strict';
  const D = window.HOUSING_DATA, MAP = window.PROVINCE_MAP, M = window.HousingMath;
  const $ = id => document.getElementById(id);
  if (!D || !MAP || !M) { $('hero-ratio').textContent = '加载失败'; return; }
  const records = D.records, byCode = new Map(records.map(r => [r.code, r]));
  const params = new URLSearchParams(location.search);
  const areas = [60,90,100,120,140,180];
  const qArea = Number(params.get('area')), qPeople = Number(params.get('people'));
  const state = {
    area:areas.includes(qArea) ? qArea : 90,
    people:Number.isInteger(qPeople) && qPeople >= 1 && qPeople <= 6 ? qPeople : 3,
    selected:byCode.has(params.get('province')) ? params.get('province') : '310000',
    metric:['ratio','price','income'].includes(params.get('metric')) ? params.get('metric') : 'ratio',
    view:params.get('view') === 'scatter' ? 'scatter' : 'map',
    compare:params.has('compare') ? [...new Set(params.get('compare').split(',').filter(c=>byCode.has(c)))].slice(0,3) : ['310000','110000','430000'],
    search:'', region:'all', sort:'ratio-desc', expanded:false, personalDirty:false
  };
  const fmt = (n, digits=0) => new Intl.NumberFormat('zh-CN',{minimumFractionDigits:digits,maximumFractionDigits:digits}).format(n);
  const ratio = r => M.provinceRatio(r, state.area, state.people);
  const nationalRatio = () => ratio(D.national);
  const maxRatio = () => Math.max(...records.map(ratio),nationalRatio());
  const value = r => state.metric === 'price' ? r.price : state.metric === 'income' ? r.urbanIncome : ratio(r);
  const palette = ['#e5f1f0','#d6dfea','#bec3e0','#a29acb','#8574b8','#6f539f','#53366d'];
  const metricExtent = () => [Math.min(...records.map(value)),Math.max(...records.map(value))];
  const color = r => {const [lo,hi]=metricExtent();return palette[Math.min(6,Math.floor((value(r)-lo)/(hi-lo)*6.999))];};
  let toastTimer;
  function toast(text) { $('toast').textContent=text;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,3200); }
  function updateUrl() {
    const p = new URLSearchParams({province:state.selected,area:state.area,people:state.people,metric:state.metric,view:state.view,compare:state.compare.join(',')});
    history.replaceState(null,'',location.pathname+'?'+p+location.hash);
  }
  function visibleRecords() {
    return records.filter(r=>(state.region==='all'||r.region===state.region)&&(!state.search||(r.name+r.fullName+r.region).includes(state.search))).sort((a,b)=>{
      if(state.sort==='ratio-asc')return ratio(a)-ratio(b);
      if(state.sort==='price-desc')return b.price-a.price;
      if(state.sort==='income-desc')return b.urbanIncome-a.urbanIncome;
      if(state.sort==='code')return a.code.localeCompare(b.code);
      return ratio(b)-ratio(a);
    });
  }
  function initMap() {
    const paths=MAP.features.map(f=>`<path class="province-path${f.available?'':' no-data'}" data-code="${f.code}" d="${f.path}" tabindex="0" role="button" aria-label="${f.name}${f.available?'，查看房价与收入':'，未纳入本次统计'}"><title>${f.name}</title></path>`).join('');
    const labels=MAP.features.map(f=>{
      if(!f.label)return '';
      const [x,y]=f.label,[dx,dy]=f.offset;
      const leader=dx||dy?`<path class="map-leader" d="M${x},${y}L${x+dx},${y+dy}"/>`:'';
      return `${leader}<text x="${x+dx}" y="${y+dy+3}" class="province-label${f.available?'':' small'}" data-label="${f.code}">${f.name}</text>`;
    }).join('');
    $('china-map').innerHTML=`<g>${paths}</g><g>${labels}</g><g aria-hidden="true"><rect class="map-inset" x="638" y="342" width="99" height="111" rx="4"/><path class="map-inset-line" d="${MAP.inset}"/><text class="map-inset-label" x="687" y="444" text-anchor="middle">南海诸岛</text></g>`;
  }
  function renderMap() {
    const visible=new Set(visibleRecords().map(r=>r.code));
    $('china-map').querySelectorAll('[data-code]').forEach(el=>{
      const r=byCode.get(el.dataset.code);
      if(!r)return;
      el.style.fill=color(r);
      el.style.opacity=visible.has(r.code)?1:.25;
      el.classList.toggle('selected',r.code===state.selected);
      el.setAttribute('aria-pressed',String(r.code===state.selected));
      el.setAttribute('aria-label',`${r.name}，房价收入比${fmt(ratio(r),2)}倍，查看详情`);
    });
    $('china-map').querySelectorAll('[data-label]').forEach(el=>el.classList.toggle('selected',el.dataset.label===state.selected));
    const [lo,hi]=metricExtent();
    $('legend-min').textContent=state.metric==='ratio'?fmt(lo,1)+'倍':fmt(lo)+'元';
    $('legend-max').textContent=state.metric==='ratio'?fmt(hi,1)+'倍':fmt(hi)+'元';
    $('legend-caption').textContent=state.metric==='ratio'?'收入倍数由低到高':state.metric==='price'?'住宅单价由低到高':'城镇人均年收入由低到高';
    $('chart-headline').textContent=state.view==='scatter'?'2024年 · 住宅价格与城镇人均收入':state.metric==='ratio'?'房价收入比 · 家庭年收入倍数':state.metric==='price'?'新建商品住宅销售均价 · 元/㎡':'城镇居民人均可支配收入 · 元/年';
  }
  function renderScatter() {
    const x=n=>67+(n-30000)/70000*630,y=n=>390-n/55000*337;
    let content='<text class="scatter-text" x="68" y="23">新建住宅均价（万元/㎡）</text>';
    [0,10000,20000,30000,40000,50000].forEach(n=>{content+=`<path class="scatter-grid" d="M67 ${y(n)}H697"/><text class="scatter-text" x="53" y="${y(n)+4}" text-anchor="end">${n/10000}</text>`;});
    [40000,60000,80000,100000].forEach(n=>{content+=`<path class="scatter-grid" d="M${x(n)} 53V390"/><text class="scatter-text" x="${x(n)}" y="413" text-anchor="middle">${n/10000}</text>`;});
    content+='<path class="scatter-axis" d="M67 53V390H697"/><text class="scatter-text" x="697" y="446" text-anchor="end">城镇人均可支配收入（万元/人/年）</text>';
    content+=`<path class="national-line" d="M${x(D.national.urbanIncome)} 53V390M67 ${y(D.national.price)}H697"/><text class="national-text" x="${x(D.national.urbanIncome)+5}" y="64">全国收入参考</text><text class="national-text" x="689" y="${y(D.national.price)-6}" text-anchor="end">全国住宅均价</text>`;
    const visible=new Set(visibleRecords().map(r=>r.code));
    records.filter(r=>r.code!==state.selected).concat(byCode.get(state.selected)).forEach(r=>{
      const sel=r.code===state.selected;
      content+=`<circle class="scatter-dot${sel?' selected':''}" data-code="${r.code}" role="button" tabindex="0" aria-label="${r.name}，查看房价与收入" cx="${x(r.urbanIncome)}" cy="${y(r.price)}" r="${sel?8:6}" fill="${color(r)}" opacity="${visible.has(r.code)?1:.15}"/>`;
      if(sel||['110000','310000','440000','460000','330000'].includes(r.code))content+=`<text class="scatter-label" x="${x(r.urbanIncome)+11}" y="${y(r.price)+3}">${r.name}</text>`;
    });
    $('scatter-chart').innerHTML=content;
  }
  function renderDetail() {
    const r=byCode.get(state.selected),n=nationalRatio(),v=ratio(r);
    $('detail-name').textContent=r.name;$('detail-region').textContent=r.region+' · 省级口径';
    $('detail-ratio').textContent=fmt(v,2);$('detail-price').textContent=fmt(r.price);$('detail-income').textContent=fmt(r.urbanIncome);$('detail-total').textContent=fmt(r.price*state.area/10000,2);
    $('detail-bar').style.width=(v/maxRatio()*100)+'%';$('national-marker').style.left=(n/maxRatio()*100)+'%';
    const delta=(v/n-1)*100;
    $('detail-benchmark').textContent=`全国参考 ${fmt(n,2)} 倍 · ${Math.abs(delta)<.05?'与全国参考接近':(delta>=0?'高于':'低于')+'全国参考 '+fmt(Math.abs(delta),0)+'%'}`;
    const added=state.compare.includes(r.code);
    $('add-comparison').disabled=added;$('add-comparison').innerHTML=added?'已加入对比 <span>✓</span>':'加入地区对比 <span>＋</span>';
  }
  function renderComparison() {
    let html=state.compare.map(code=>{
      const r=byCode.get(code);
      return `<article class="compare-item"><div class="compare-item-head"><button data-select="${code}" aria-label="查看${r.name}详情">${r.name}</button><button class="compare-remove" data-remove="${code}" aria-label="移除${r.name}对比">×</button></div><div class="compare-value">${fmt(ratio(r),2)}<small>倍年收入</small></div><div class="compare-bar"><span style="width:${ratio(r)/maxRatio()*100}%"></span></div><div class="compare-meta"><span>均价 ${fmt(r.price)}元/㎡</span><span>收入 ${fmt(r.urbanIncome/10000,2)}万元</span></div></article>`;
    }).join('');
    for(let i=state.compare.length;i<3;i++)html+='<div class="compare-empty"><span>＋</span><p>从地图或表格<br>加入一个地区</p></div>';
    $('comparison-list').innerHTML=html;
    $('clear-comparison').disabled=!state.compare.length;
  }
  function renderTable() {
    const rows=visibleRecords(),shown=state.expanded?rows:rows.slice(0,10);
    $('region-table-body').innerHTML=shown.length?shown.map((r,i)=>`<tr class="${r.code===state.selected?'is-selected':''}"><td><div class="table-name"><span>${String(i+1).padStart(2,'0')}</span><button data-select="${r.code}">${r.name}</button><small>${r.region}</small></div></td><td>${fmt(r.price)}</td><td>${fmt(r.urbanIncome)}</td><td><div class="ratio-cell"><b>${fmt(ratio(r),2)}</b><span class="mini-bar"><i style="width:${ratio(r)/maxRatio()*100}%"></i></span></div></td><td><button class="table-add${state.compare.includes(r.code)?' added':''}" data-compare="${r.code}" aria-label="${state.compare.includes(r.code)?'移除':'加入'}${r.name}对比">${state.compare.includes(r.code)?'✓':'＋'}</button></td></tr>`).join(''):'<tr><td class="no-results" colspan="5">没有找到匹配地区，请调整搜索或筛选。</td></tr>';
    $('result-count').textContent=`显示 ${shown.length} / ${rows.length} 个地区 · 2024年`;
    $('show-all').hidden=rows.length<=10;
    $('show-all').textContent=state.expanded?'收起地区列表 ↑':`展开全部${rows.length}个地区 ↓`;
  }
  function render() {
    document.querySelectorAll('[data-scenario-area]').forEach(el=>el.textContent=state.area);
    document.querySelectorAll('[data-scenario-people]').forEach(el=>el.textContent=state.people);
    $('hero-ratio').textContent=fmt(nationalRatio(),2);
    $('scenario-area').value=state.area;$('scenario-people').value=state.people;$('map-metric').value=state.metric;
    document.querySelectorAll('[data-view]').forEach(el=>{el.classList.toggle('active',el.dataset.view===state.view);el.setAttribute('aria-pressed',String(el.dataset.view===state.view));});
    $('map-container').hidden=state.view!=='map';$('scatter-container').hidden=state.view!=='scatter';
    renderMap();renderScatter();renderDetail();renderComparison();renderTable();updateUrl();
  }
  function selectRegion(code) {
    if(!byCode.has(code)){toast('该地区未纳入本次同口径统计，不填零。');return;}
    state.selected=code;render();
    $('map-tooltip').hidden=true;
  }
  function toggleComparison(code) {
    if(state.compare.includes(code))state.compare=state.compare.filter(c=>c!==code);
    else {if(state.compare.length>=3){toast('最多对比3个地区，请先移除一个。');return;}state.compare.push(code);}
    render();
  }
  function showTooltip(event) {
    const target=event.target.closest('[data-code]');if(!target)return;
    const r=byCode.get(target.dataset.code);if(!r)return;
    $('map-tooltip').innerHTML=`<b>${r.name}</b> <span>2024年</span><br>房价收入比 <strong>${fmt(ratio(r),2)}</strong> 倍<br>住宅均价 ${fmt(r.price)} 元/㎡<br>城镇人均年收入 ${fmt(r.urbanIncome)} 元`;
    $('map-tooltip').hidden=false;
    const bounds=$('map-tooltip').getBoundingClientRect();
    $('map-tooltip').style.left=Math.max(8,Math.min(event.clientX+15,innerWidth-bounds.width-10))+'px';
    $('map-tooltip').style.top=Math.max(8,Math.min(event.clientY+15,innerHeight-bounds.height-10))+'px';
  }
  for(const id of ['china-map','scatter-chart']) {
    $(id).addEventListener('click',e=>{const target=e.target.closest('[data-code]');if(target)selectRegion(target.dataset.code);});
    $(id).addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){const target=e.target.closest('[data-code]');if(target){e.preventDefault();selectRegion(target.dataset.code);}}});
    $(id).addEventListener('pointermove',showTooltip);$(id).addEventListener('pointerleave',()=>$('map-tooltip').hidden=true);
  }
  document.addEventListener('click',e=>{
    const select=e.target.closest('[data-select]');if(select)selectRegion(select.dataset.select);
    const compare=e.target.closest('[data-compare]');if(compare)toggleComparison(compare.dataset.compare);
    const remove=e.target.closest('[data-remove]');if(remove)toggleComparison(remove.dataset.remove);
    const view=e.target.closest('[data-view]');if(view){state.view=view.dataset.view;render();}
  });
  $('scenario-area').addEventListener('change',e=>{state.area=Number(e.target.value);render();if(!state.personalDirty)loadProvince();});
  $('scenario-people').addEventListener('change',e=>{state.people=Number(e.target.value);render();if(!state.personalDirty)loadProvince();});
  $('map-metric').addEventListener('change',e=>{state.metric=e.target.value;render();});
  $('reset-scenario').addEventListener('click',()=>{state.area=90;state.people=3;render();if(!state.personalDirty)loadProvince();});
  $('region-search').addEventListener('input',e=>{state.search=e.target.value.trim();state.expanded=false;renderTable();renderMap();renderScatter();});
  $('region-filter').addEventListener('change',e=>{state.region=e.target.value;state.expanded=false;renderTable();renderMap();renderScatter();});
  $('table-sort').addEventListener('change',e=>{state.sort=e.target.value;renderTable();});
  $('show-all').addEventListener('click',()=>{state.expanded=!state.expanded;renderTable();});
  $('add-comparison').addEventListener('click',()=>toggleComparison(state.selected));
  $('clear-comparison').addEventListener('click',()=>{state.compare=[];render();});
  $('share-button').addEventListener('click',async()=>{
    updateUrl();
    try{await navigator.clipboard.writeText(location.href);toast('已复制地区对比链接，不包含个人收入。');}
    catch{toast('对比参数已保存在地址栏，请复制浏览器地址分享。');}
  });
  $('export-csv').addEventListener('click',()=>{
    const rows=visibleRecords();if(!rows.length){toast('当前没有可导出的地区。');return;}
    const matrix=[['统计年度','地区','住宅均价(元/平方米)','城镇人均收入(元/年)','住宅面积(平方米)','家庭人口','房价收入比(倍)','房价来源','收入来源'],...rows.map(r=>[r.year,r.name,r.price,r.urbanIncome,state.area,state.people,ratio(r).toFixed(4),r.priceSource,r.incomeSource])];
    const url=URL.createObjectURL(new Blob([M.csv(matrix)],{type:'text/csv;charset=utf-8;'}));
    const a=document.createElement('a');a.href=url;a.download=`房价收入比_2024_${state.area}平方米_${state.people}人.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast(`已导出${rows.length}个地区，包含数据来源。`);
  });
  function loadProvince(scroll=false) {
    const r=byCode.get(state.selected);
    $('personal-price').value=r.price;$('personal-area').value=state.area;
    $('personal-income').value=(r.urbanIncome*state.people/12).toFixed(2);
    $('personal-source').textContent=`已带入${r.name}2024年统计参考：${state.people}人家庭。你可以改成具体城市、楼盘报价与实际家庭收入。`;
    state.personalDirty=false;calculatePersonal();
    if(scroll)$('calculator').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  }
  function calculatePersonal() {
    const form=$('personal-form');
    const outputIds=['personal-ratio','personal-total','personal-down-result','personal-saving-years','personal-payment','personal-payment-ratio'];
    try {
      if(!form.checkValidity())throw new Error('请检查输入：单价、面积和收入须大于0；比例为0–100%，贷款年限为1–40整数年，年利率为0–30%。');
      const values=Object.fromEntries(new FormData(form).entries());const result=M.personal(values);
      $('personal-error').hidden=true;
      $('personal-ratio').textContent=fmt(result.ratio,2);
      $('personal-total').textContent=fmt(result.total/10000,2)+' 万元';
      $('personal-down-result').textContent=fmt(result.down/10000,2)+' 万元';
      $('personal-saving-years').textContent=result.downYears===null?'无法积累（结余为0）':fmt(result.downYears,1)+' 年';
      $('personal-payment').textContent=fmt(result.monthly,0)+' 元/月';
      $('personal-payment-ratio').textContent=fmt(result.paymentRatio,1)+'%';
      $('payment-meter-fill').style.width=Math.min(result.paymentRatio,100)+'%';
      $('personal-result-note').textContent=(result.paymentRatio>100?'当前假设月供超过家庭月收入。':'')+'结余保持不变、不计存款收益；贷款按固定利率等额本息计算，未计税费和其他购房支出。';
    }catch(error){
      $('personal-error').textContent=error.message;$('personal-error').hidden=false;outputIds.forEach(id=>$(id).textContent='—');$('payment-meter-fill').style.width='0%';
    }
  }
  $('personal-form').addEventListener('submit',e=>e.preventDefault());
  $('personal-form').addEventListener('input',()=>{state.personalDirty=true;$('personal-source').textContent='当前使用你在此页填写的个人情景参数，仅在浏览器内计算。';calculatePersonal();});
  $('load-province').addEventListener('click',()=>loadProvince());
  $('use-personal').addEventListener('click',()=>loadProvince(true));
  $('source-links').innerHTML=D.sources.slice(0,2).map(s=>`<div class="source-card"><strong>${s.table}</strong><span>${s.publisher} · ${s.publication} · ${s.statisticalYear}年 · ${s.unit}</span><a href="${s.url}" target="_blank" rel="noopener noreferrer">查看官方原表 ↗</a><a class="source-local" href="data/${s.localFile}" target="_blank" rel="noopener noreferrer">本地留存 ↗</a></div>`).join('');
  document.querySelectorAll('[data-open-methods]').forEach(el=>el.addEventListener('click',()=>$('methods-dialog').showModal()));
  $('close-methods').addEventListener('click',()=>$('methods-dialog').close());
  $('methods-dialog').addEventListener('click',e=>{if(e.target===$('methods-dialog')){const b=$('methods-dialog').getBoundingClientRect();if(e.clientX<b.left||e.clientX>b.right||e.clientY<b.top||e.clientY>b.bottom)$('methods-dialog').close();}});
  initMap();render();loadProvince();
})();
