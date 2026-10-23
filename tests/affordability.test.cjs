const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const M = require('../docs/core.js');
const data = JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/data/housing-income-2024.json'),'utf8'));
test('official data has 31 unique, complete same-year regions', () => {
  assert.equal(data.records.length,31);
  assert.equal(new Set(data.records.map(r=>r.code)).size,31);
  for(const r of data.records){assert.equal(r.year,2024);assert.ok(r.price>0);assert.ok(r.urbanIncome>0);assert.match(r.priceSource,/^https:\/\/www\.stats\.gov\.cn\//);assert.ok(Math.abs(r.crossCheckDifference)<1);}
});
test('national benchmark uses household population, not earners',()=>assert.ok(Math.abs(M.provinceRatio(data.national,90,3)-5.7683)<0.0001));
test('Shanghai and Beijing are faithfully reproduced',()=>{
  for(const r of data.records) assert.ok(Math.abs(M.provinceRatio(r,90,3)-r.defaultRatio90sqm3persons)<0.0001);
});
test('area and household population scale the ratio correctly',()=>{
  const r=data.records[0];assert.equal(M.provinceRatio(r,180,3),M.provinceRatio(r,90,3)*2);assert.equal(M.provinceRatio(r,90,6),M.provinceRatio(r,90,3)/2);
});
test('non-positive incomes, non-integer population and NaN are rejected',()=>{
  for(const n of [0,-1,NaN,Infinity])assert.throws(()=>M.ratio(10000,90,n),RangeError);
  assert.throws(()=>M.provinceRatio(data.national,90,1.5),RangeError);
});
test('annuity payment is numerically stable and zero-interest is supported',()=>{
  assert.ok(Math.abs(M.monthlyPayment(1000000,3,30)-4216.04)<0.01);
  assert.equal(M.monthlyPayment(120000,0,10),1000);
  assert.equal(M.monthlyPayment(0,3,30),0);
});
const input={price:10000,area:100,monthlyIncome:10000,savingRate:50,downRate:30,interest:3,years:30};
test('personal scenario keeps full income ratio and savings years separate',()=>{
  const r=M.personal(input);assert.equal(r.total,1000000);assert.equal(r.down,300000);assert.equal(r.downYears,5);assert.equal(r.ratio,1000000/120000);assert.equal(r.loan,700000);
});
test('zero saving rate never renders Infinity as savings years',()=>assert.equal(M.personal({...input,savingRate:0}).downYears,null));
test('all-cash and zero down payment cases are handled',()=>{
  const cash=M.personal({...input,downRate:100});assert.equal(cash.monthly,0);assert.equal(cash.totalInterest,0);assert.equal(cash.paymentRatio,0);
  assert.equal(M.personal({...input,downRate:0,savingRate:0}).downYears,0);
});
test('CSV quotes source names and preserves new lines safely',()=>assert.equal(M.csv([['a,b','x"y','a\nb']]),'\ufeff"a,b","x""y","a\nb"'));
