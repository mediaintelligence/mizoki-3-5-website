(function(){
  const $ = (sel)=>document.querySelector(sel);

  function fmtMoney(n){
    if(!isFinite(n)) return "—";
    return n.toLocaleString(undefined,{style:"currency", currency:"USD", maximumFractionDigits:0});
  }
  function fmtMonths(n){
    if(!isFinite(n)) return "—";
    return (Math.round(n*10)/10).toString();
  }

  const revenueEl = $('#rev');
  const leakageEl = $('#leak');
  const opexEl = $('#opex');
  const platformEl = $('#platform');
  const outMin = $('#outMin');
  const outMax = $('#outMax');
  const payMin = $('#payMin');
  const payMax = $('#payMax');

  function clamp(v,min,max){ return Math.max(min, Math.min(max, v)); }

  function calc(){
    const rev = Math.max(0, Number(revenueEl.value || 0));
    const leakPct = clamp(Number(leakageEl.value || 0)/100, 0, 1);
    const opex = Math.max(0, Number(opexEl.value || 0));
    const platform = Math.max(0, Number(platformEl.value || 0));

    // Conservative/optimistic improvements based on the narrative ranges
    const leakRedMin = 0.18, leakRedMax = 0.35;
    const opexRedMin = 0.22, opexRedMax = 0.41;

    const leakLoss = rev * leakPct;
    const leakSaveMin = leakLoss * leakRedMin;
    const leakSaveMax = leakLoss * leakRedMax;

    const opexSaveMin = opex * opexRedMin;
    const opexSaveMax = opex * opexRedMax;

    const totalMin = leakSaveMin + opexSaveMin;
    const totalMax = leakSaveMax + opexSaveMax;

    outMin.textContent = fmtMoney(totalMin);
    outMax.textContent = fmtMoney(totalMax);

    // Payback (months) if platform cost is provided
    const paybackMin = platform > 0 && totalMax > 0 ? (platform/totalMax)*12 : NaN;
    const paybackMax = platform > 0 && totalMin > 0 ? (platform/totalMin)*12 : NaN;

    payMin.textContent = isFinite(paybackMin) ? fmtMonths(paybackMin) : "—";
    payMax.textContent = isFinite(paybackMax) ? fmtMonths(paybackMax) : "—";
  }

  ['input','change'].forEach(evt=>{
    [revenueEl, leakageEl, opexEl, platformEl].forEach(el=>{
      if(el) el.addEventListener(evt, calc);
    });
  });

  calc();
})();
