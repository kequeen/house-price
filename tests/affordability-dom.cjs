// Offline DOM simulation only; this does not launch a browser or request a URL.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {JSDOM} = require('./dom/node_modules/jsdom');
const root = path.join(__dirname,'../docs');
const html = fs.readFileSync(path.join(root,'index.html'),'utf8');
const dom = new JSDOM(html,{url:'https://example.invalid/house-price/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,d=w.document;
w.matchMedia=()=>({matches:true});
w.Element.prototype.scrollIntoView=function(){};
w.HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','');};
w.HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');};
let shared='';Object.defineProperty(w.navigator,'clipboard',{value:{writeText:async text=>{shared=text;}}});
for(const file of ['data/housing-data.js','data/map-data.js','core.js','app.js'])w.eval(fs.readFileSync(path.join(root,file),'utf8'));
const $=id=>d.getElementById(id),event=(id,type)=>$(id).dispatchEvent(new w.Event(type,{bubbles:true}));
const set=(id,value,type='input')=>{$(id).value=value;event(id,type);};
const checks=[];
function check(name,fn){fn();checks.push(name);}
check('initial render includes all 31 regions and correct national benchmark',()=>{
  assert.equal(d.querySelectorAll('#china-map .province-path:not(.no-data)').length,31);
  assert.equal(d.querySelectorAll('#scatter-chart .scatter-dot').length,31);
  assert.equal($('hero-ratio').textContent,'17.30');assert.equal($('detail-name').textContent,'上海');
  assert.equal(d.querySelectorAll('#region-table-body tr').length,10);
  assert.equal($('personal-error').hidden,true);
});
check('scenario controls update reference, detail, comparisons and ranking',()=>{
  set('scenario-area','120','change');assert.equal($('hero-ratio').textContent,'23.07');assert.equal($('detail-ratio').textContent,'60.87');
  assert.ok($('comparison-list').textContent.includes('60.87'));assert.ok($('region-table-body').textContent.includes('60.87'));
  $('reset-scenario').click();assert.equal($('hero-ratio').textContent,'17.30');
});
check('clicking a geographic region updates details and share parameters',()=>{
  d.querySelector('#china-map [data-code="440000"]').dispatchEvent(new w.MouseEvent('click',{bubbles:true}));
  assert.equal($('detail-name').textContent,'广东');assert.equal(new URL(w.location.href).searchParams.get('province'),'440000');
});
check('comparison maximum, removal, add and clear are enforced',()=>{
  $('add-comparison').click();assert.equal(d.querySelectorAll('.compare-item').length,3);assert.ok($('toast').textContent.includes('最多'));
  d.querySelector('[data-remove="310000"]').click();$('add-comparison').click();assert.equal(d.querySelectorAll('.compare-item').length,3);assert.ok($('comparison-list').textContent.includes('广东'));
  $('clear-comparison').click();assert.equal(d.querySelectorAll('.compare-item').length,0);assert.equal(d.querySelectorAll('.compare-empty').length,3);
});
check('search, empty state, regional filter and sorting work',()=>{
  set('region-search','湖南');assert.equal(d.querySelectorAll('#region-table-body tr').length,1);assert.ok($('region-table-body').textContent.includes('湖南'));
  set('region-search','不存在的地区');assert.ok($('region-table-body').textContent.includes('没有找到'));
  set('region-search','');set('region-filter','华中','change');assert.equal(d.querySelectorAll('#region-table-body tr').length,3);
  set('region-filter','all','change');set('table-sort','ratio-asc','change');assert.equal(d.querySelector('#region-table-body [data-select]').textContent,'湖南');
  $('show-all').click();assert.equal(d.querySelectorAll('#region-table-body tr').length,31);
});
check('scatter view and color metrics can be switched',()=>{
  d.querySelector('[data-view="scatter"]').click();assert.equal($('scatter-container').hidden,false);assert.equal($('map-container').hidden,true);
  set('map-metric','income','change');assert.ok($('legend-caption').textContent.includes('收入'));
  d.querySelector('[data-view="map"]').click();assert.equal($('map-container').hidden,false);
});
check('personal arithmetic, invalid values, zero savings and zero interest are handled',()=>{
  set('personal-price','10000');set('personal-area','100');set('personal-income','10000');set('personal-saving','50');set('personal-down','30');
  assert.equal($('personal-ratio').textContent,'8.33');assert.equal($('personal-saving-years').textContent,'5.0 年');
  set('personal-saving','0');assert.equal($('personal-saving-years').textContent,'无法积累（结余为0）');
  set('personal-interest','0');assert.equal($('personal-payment').textContent,'1,944 元/月');
  set('personal-down','100');assert.equal($('personal-payment').textContent,'0 元/月');
  set('personal-income','0');assert.equal($('personal-error').hidden,false);assert.equal($('personal-ratio').textContent,'—');
  set('personal-income','12345');assert.equal($('personal-error').hidden,true);
  set('scenario-area','120','change');assert.equal($('personal-income').value,'12345');
});
check('methodology opens, closes and includes official retained sources',()=>{
  d.querySelector('[data-open-methods]').click();assert.equal($('methods-dialog').open,true);
  assert.equal(d.querySelectorAll('#source-links .source-card').length,2);$('close-methods').click();assert.equal($('methods-dialog').open,false);
});
(async()=>{
  $('share-button').click();await new Promise(resolve=>setImmediate(resolve));
  check('share links omit personal financial inputs',()=>{assert.ok(shared.includes('province=440000'));assert.ok(!shared.includes('12345'));assert.ok(!shared.includes('monthlyIncome'));});
  console.log('Offline DOM checks passed: '+checks.length);checks.forEach(x=>console.log('  ✓ '+x));w.close();
})().catch(error=>{console.error(error);process.exitCode=1;w.close();});
