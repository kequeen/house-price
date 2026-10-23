(function (root) {
  'use strict';
  function positive(value, label) {
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0) throw new RangeError(label + '必须大于0');
    return n;
  }
  function between(value, min, max, label) {
    const n = Number(value);
    if (!Number.isFinite(n) || n < min || n > max) throw new RangeError(label + '超出范围');
    return n;
  }
  function ratio(price, area, annualHouseholdIncome) {
    return positive(price, '单价') * positive(area, '面积') / positive(annualHouseholdIncome, '家庭年收入');
  }
  function provinceRatio(record, area, people) {
    const persons = between(people, 1, 20, '家庭人口');
    if (!Number.isInteger(persons)) throw new RangeError('家庭人口应为整数');
    return ratio(record.price, area, positive(record.urbanIncome, '人均收入') * persons);
  }
  function monthlyPayment(principal, annualRate, years) {
    const loan = between(principal, 0, 1e12, '贷款金额');
    const rate = between(annualRate, 0, 30, '年利率') / 1200;
    const term = between(years, 1, 40, '贷款年限');
    if (!Number.isInteger(term)) throw new RangeError('贷款年限应为整数');
    if (loan === 0) return 0;
    if (rate === 0) return loan / (term * 12);
    return loan * rate / -Math.expm1(-term * 12 * Math.log1p(rate));
  }
  function personal(input) {
    const price = positive(input.price, '单价');
    const area = positive(input.area, '面积');
    const income = positive(input.monthlyIncome, '家庭月收入');
    const saving = between(input.savingRate, 0, 100, '结余比例') / 100;
    const downRate = between(input.downRate, 0, 100, '首付比例') / 100;
    const total = price * area;
    const down = total * downRate;
    const loan = total - down;
    const monthly = monthlyPayment(loan, input.interest, input.years);
    const savedPerMonth = income * saving;
    return {
      total, down, loan, monthly, savedPerMonth,
      ratio: ratio(price, area, income * 12),
      downYears: down === 0 ? 0 : savedPerMonth === 0 ? null : down / (savedPerMonth * 12),
      paymentRatio: monthly / income * 100,
      totalInterest: Math.max(0, monthly * Number(input.years) * 12 - loan)
    };
  }
  function csv(rows) {
    const quote = v => '"' + String(v ?? '').replaceAll('"', '""') + '"';
    return '\ufeff' + rows.map(row => row.map(quote).join(',')).join('\r\n');
  }
  const api = { ratio, provinceRatio, monthlyPayment, personal, csv };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.HousingMath = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
