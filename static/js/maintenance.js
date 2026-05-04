(function(){
  if(window.__maintenanceInit) return; window.__maintenanceInit = true;
  try{ console.log('[LOAD]', 'maintenance.js', 'PAGE_MODE=' + (window.PAGE_MODE||'unset')); }catch(e){}
  // Only initialize on maintenance pages
  if(typeof window.PAGE_MODE === 'undefined' || window.PAGE_MODE !== 'maintenance') return;

  // helpers
  function parseFloatSafe(v){ var n = parseFloat(v); return isNaN(n)?0:n; }

  // update a single item row amount
  window.updateRowAmount = function(row){ try{ var q = parseFloatSafe(row.querySelector('.item-qty').value); var r = parseFloatSafe(row.querySelector('.item-rate').value); var d = parseFloatSafe(row.querySelector('.item-discount').value); var amt = q * r * (1 - d/100); var amtEl = row.querySelector('.item-amount'); if(amtEl) amtEl.value = amt.toFixed(3); return amt; }catch(e){return 0;} };

  // recompute totals including services
  window.recomputeTotals = function(){
    try{
      var subtotal = 0, totalDiscount = 0;
      document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var q = parseFloatSafe(row.querySelector('.item-qty').value); var r = parseFloatSafe(row.querySelector('.item-rate').value); var d = parseFloatSafe(row.querySelector('.item-discount').value); var line = q * r; var amt = window.updateRowAmount(row); subtotal += line; totalDiscount += (line - amt); }catch(e){} });
      document.getElementById('sub-total').textContent = subtotal.toFixed(3);
      document.getElementById('total-discount').textContent = totalDiscount.toFixed(3);
      var svcSubtotal = 0; document.querySelectorAll('#services-body .service-row').forEach(function(row){ try{ svcSubtotal += parseFloat(row.querySelector('.service-amount').value) || 0; }catch(e){} });
      document.getElementById('services-sub-total').textContent = svcSubtotal.toFixed(3);
      var grand = (svcSubtotal + (subtotal - totalDiscount)).toFixed(3);
      document.getElementById('grand-total').textContent = grand;
      try{ var bottom = document.getElementById('bottom-total'); if(bottom) bottom.textContent = 'BHD ' + parseFloat(grand).toFixed(3); }catch(e){}
    }catch(e){ }
  };

  // create item row (parts)
  window.createItemRow = function(focus){ try{ if(!window._lastCreateItemRowAt) window._lastCreateItemRowAt = 0; var now = Date.now(); if(now - window._lastCreateItemRowAt < 250) return null; window._lastCreateItemRowAt = now; }catch(e){}
    var tbody = document.getElementById('items-body'); if(!tbody) return null; var tr = document.createElement('tr'); tr.className = 'item-row'; tr.innerHTML = "<td><input type='text' class='item-desc' value=''><div class='stock-display'></div></td><td><input type='number' class='item-qty' step='1' value='1'></td><td><input type='number' class='item-rate' step='0.001' value='0.000'></td><td><input type='number' class='item-discount' step='0.001' value='0.000'></td><td><input type='text' class='item-amount' value='0.000' readonly></td><td><button type="button" class='remove-row'>×</button></td>";
    tbody.appendChild(tr);
    try{ var inp = tr.querySelector('.item-desc'); if(inp && window.initInventoryAutocomplete) window.initInventoryAutocomplete(inp); if(focus!==false && inp) inp.focus(); }catch(e){}
    // attach remove handler
    tr.querySelector('.remove-row').addEventListener('click', function(){ try{ if(tr && tr.parentNode) tr.parentNode.removeChild(tr); window.recomputeTotals(); }catch(e){} });
    // qty input listener
    var qty = tr.querySelector('.item-qty'); if(qty){ qty.addEventListener('input', function(){ try{ window.updateRowAmount(tr); window.recomputeTotals(); }catch(e){} }); }
    return tr;
  };

  // create service row
  window.createServiceRow = function(focus){ var tbody = document.getElementById('services-body'); if(!tbody) return null; var tr = document.createElement('tr'); tr.className = 'service-row'; tr.innerHTML = "<td><input type='text' class='service-desc' value=''></td><td><input type='number' class='service-qty' step='1' value='1'></td><td><input type='number' class='service-rate' step='0.001' value='0.000'></td><td><input type='text' class='service-amount' value='0.000'></td><td><button type='button' class='remove-service'>×</button></td>"; tbody.appendChild(tr); try{ var desc = tr.querySelector('.service-desc'); if(desc && focus!==false) desc.focus(); }catch(e){} tr.querySelector('.remove-service').addEventListener('click', function(){ try{ if(tr && tr.parentNode) tr.parentNode.removeChild(tr); window.recomputeTotals(); }catch(e){} }); tr.querySelector('.service-qty').addEventListener('input', function(){ try{ var q = parseFloat(tr.querySelector('.service-qty').value)||0; var r = parseFloat(tr.querySelector('.service-rate').value)||0; tr.querySelector('.service-amount').value = (q*r).toFixed(3); window.recomputeTotals(); }catch(e){} }); tr.querySelector('.service-rate').addEventListener('input', function(){ try{ var q = parseFloat(tr.querySelector('.service-qty').value)||0; var r = parseFloat(tr.querySelector('.service-rate').value)||0; tr.querySelector('.service-amount').value = (q*r).toFixed(3); window.recomputeTotals(); }catch(e){} }); return tr; };

  // serialize maintenance items (services first then parts)
  // Serializer is provided by `static/js/line-items.core.js` (canonical implementation).

  // attach UI handlers (per-element, not global delegated click)
  try{
    var addRowBtn = document.getElementById('add-row'); if(addRowBtn) addRowBtn.addEventListener('click', function(e){ e.preventDefault(); window.createItemRow(true); });
    var addSvcBtn = document.getElementById('add-service-row'); if(addSvcBtn) addSvcBtn.addEventListener('click', function(e){ e.preventDefault(); window.createServiceRow(true); });
    // initialize existing inputs
    document.querySelectorAll('#items-body .item-desc').forEach(function(inp){ try{ window.initInventoryAutocomplete(inp); }catch(e){} });
    // submit serialization
    var form = document.getElementById('maintenance-form'); if(form){ form.addEventListener('submit', function(evt){ try{ if(!window.serializeMaintenanceItems()) evt.preventDefault(); }catch(e){} }); }
  }catch(e){}

  // initial state: ensure at least one service and one item row visible
  try{ if(document.querySelectorAll('#services-body .service-row').length === 0) window.createServiceRow(false); if(document.querySelectorAll('#items-body .item-row').length === 0) window.createItemRow(true); }catch(e){}

})();
