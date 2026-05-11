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
      var partsTotal = 0, totalDiscount = 0;
      // Sum parts (inventory) from #items-body rows that are not services
        document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{
          // robustly detect service rows so parts subtotal skips them
          var dtype = '';
          try{ dtype = (row.dataset && (row.dataset.type || row.getAttribute && row.getAttribute('data-type'))) || ''; }catch(e){}
          dtype = (dtype+'').toLowerCase();
          var hasServiceId = false;
          try{ hasServiceId = Boolean((row.dataset && (row.dataset.serviceId)) || (row.getAttribute && row.getAttribute('data-service-id'))); }catch(e){}
          var isService = (row.classList && row.classList.contains('service-row')) || (dtype === 'service') || !!hasServiceId || !!(row.querySelector && (row.querySelector('.service-desc') || row.querySelector('.service-qty') || row.querySelector('.service-amount')));
          if(isService) return;
          var qtyEl = row.querySelector('.item-qty'); var rateEl = row.querySelector('.item-rate'); var discEl = row.querySelector('.item-discount');
          var q = parseFloatSafe(qtyEl && qtyEl.value ? qtyEl.value : 0);
          var r = parseFloatSafe(rateEl && rateEl.value ? rateEl.value : 0);
          var d = parseFloatSafe(discEl && discEl.value ? discEl.value : 0);
          var line = q * r;
          var amt = (row.querySelector('.item-amount') && parseFloat(row.querySelector('.item-amount').value)) || 0;
          partsTotal += amt;
          totalDiscount += (line - amt);
        }catch(e){} });
      document.getElementById('sub-total').textContent = partsTotal.toFixed(3);
      document.getElementById('total-discount').textContent = totalDiscount.toFixed(3);
      // Sum services only from item rows marked as service
      var svcSubtotal = 0;
      try{ document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{
        var dtype2 = '';
        try{ dtype2 = (row.dataset && (row.dataset.type || row.getAttribute && row.getAttribute('data-type'))) || ''; }catch(e){}
        dtype2 = (dtype2+'').toLowerCase();
        var hasServiceId2 = false;
        try{ hasServiceId2 = Boolean((row.dataset && (row.dataset.serviceId)) || (row.getAttribute && row.getAttribute('data-service-id'))); }catch(e){}
        var isSvc = (row.classList && row.classList.contains('service-row')) || (dtype2 === 'service') || !!hasServiceId2 || !!(row.querySelector && (row.querySelector('.service-desc') || row.querySelector('.service-qty') || row.querySelector('.service-amount')));
        if(isSvc){ var el = row.querySelector('.service-amount') || row.querySelector('.item-amount'); svcSubtotal += parseFloat(el && el.value ? el.value : 0) || 0; }
        }catch(e){} }); }catch(e){}
      document.getElementById('services-sub-total').textContent = svcSubtotal.toFixed(3);
      var grand = (svcSubtotal + partsTotal).toFixed(3);
      document.getElementById('grand-total').textContent = grand;
      try{ var bottom = document.getElementById('bottom-total'); if(bottom) bottom.textContent = 'BHD ' + parseFloat(grand).toFixed(3); }catch(e){}
    }catch(e){ }
  };

  // create item row (parts)
  window.createItemRow = function(focus){ try{ if(!window._lastCreateItemRowAt) window._lastCreateItemRowAt = 0; var now = Date.now(); if(now - window._lastCreateItemRowAt < 250) return null; window._lastCreateItemRowAt = now; }catch(e){}
    var tbody = document.getElementById('items-body'); if(!tbody) return null; var tr = document.createElement('tr'); tr.className = 'item-row'; tr.innerHTML = "<td><input type='text' class='item-desc' value=''><div class='stock-display'></div></td><td><input type='number' class='item-qty' step='1' value='1'></td><td><input type='number' class='item-rate' step='0.001' value='0.000'></td><td><input type='number' class='item-discount' step='0.001' value='0.000'></td><td><input type='text' class='item-amount' value='0.000' readonly></td><td><button type="button" class='remove-row'>×</button></td>";
    tbody.appendChild(tr);
    try{ window.__invBlockAutoOpenUntil = Date.now() + 400; }catch(e){}
    try{ var inp = tr.querySelector('.item-desc'); try{ if(typeof window.initInventoryRow === 'function') window.initInventoryRow(tr); else if(inp && window.initInventoryAutocomplete) window.initInventoryAutocomplete(inp); }catch(e){} if(focus!==false && inp) inp.focus(); }catch(e){}
    // attach remove handler
    tr.querySelector('.remove-row').addEventListener('click', function(){ try{ if(tr && tr.parentNode) tr.parentNode.removeChild(tr); window.recomputeTotals(); }catch(e){} });
    // qty input listener
    var qty = tr.querySelector('.item-qty'); if(qty){ qty.addEventListener('input', function(){ try{ window.updateRowAmount(tr); window.recomputeTotals(); }catch(e){} }); }
    return tr;
  };

  // create service row (append as unified item-row with data-type=service)
  window.createServiceRow = function(focus){ var tbody = document.getElementById('items-body'); if(!tbody) return null; var tr = document.createElement('tr'); tr.className = 'item-row'; try{ tr.setAttribute('data-type','service'); tr.dataset.type = 'service'; }catch(e){} tr.innerHTML = "<td><input type='text' class='service-desc item-desc' value=''><input type='hidden' class='item-type-hidden' name='item_type[]' value='service' /></td><td><input type='number' class='service-qty item-qty' step='1' value='1'></td><td><input type='number' class='service-rate item-rate' step='0.001' value='0.000'></td><td><input type='text' class='service-amount item-amount' value='0.000' readonly></td><td><button type='button' class='remove-service remove-row'>×</button></td>"; tbody.appendChild(tr); try{ var desc = tr.querySelector('.service-desc'); if(desc && focus!==false) desc.focus(); }catch(e){} tr.querySelector('.remove-service').addEventListener('click', function(){ try{ if(tr && tr.parentNode) tr.parentNode.removeChild(tr); window.recomputeTotals(); }catch(e){} }); tr.querySelector('.service-qty').addEventListener('input', function(){ try{ var q = parseFloat(tr.querySelector('.service-qty').value)||0; var r = parseFloat(tr.querySelector('.service-rate').value)||0; tr.querySelector('.service-amount').value = (q*r).toFixed(3); window.recomputeTotals(); }catch(e){} }); tr.querySelector('.service-rate').addEventListener('input', function(){ try{ var q = parseFloat(tr.querySelector('.service-qty').value)||0; var r = parseFloat(tr.querySelector('.service-rate').value)||0; tr.querySelector('.service-amount').value = (q*r).toFixed(3); window.recomputeTotals(); }catch(e){} }); return tr; };

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

  // initial state: ensure at least one item row exists; services are unified as item rows
  try{ if(document.querySelectorAll('#items-body .item-row').length === 0) window.createItemRow(false); }catch(e){}

})();
