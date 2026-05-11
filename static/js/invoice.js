(function(){
  if(window.__invoiceInit) return; window.__invoiceInit = true;
  try{ console.log('[LOAD]', 'invoice.js', 'PAGE_MODE=' + (window.PAGE_MODE||'unset')); }catch(e){}
  if(typeof window.PAGE_MODE === 'undefined' || window.PAGE_MODE !== 'invoice') return;
  function parseFloatSafe(v){ var n = parseFloat(v); return isNaN(n)?0:n; }

  // update row amount for invoice parts
  window.updateRowAmount = function(row){ try{ var q = parseFloatSafe(row.querySelector('.item-qty').value); var r = parseFloatSafe(row.querySelector('.item-rate').value); var d = parseFloatSafe(row.querySelector('.item-discount').value); var amt = q * r * (1 - d/100); var amtEl = row.querySelector('.item-amount'); if(amtEl) amtEl.value = amt.toFixed(3); return amt; }catch(e){return 0;} };

  window.recomputeTotals = function(){ try{ var subtotal = 0, totalDiscount = 0; document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var q = parseFloatSafe(row.querySelector('.item-qty').value); var r = parseFloatSafe(row.querySelector('.item-rate').value); var d = parseFloatSafe(row.querySelector('.item-discount').value); var line = q * r; var amt = window.updateRowAmount(row); subtotal += line; totalDiscount += (line - amt); }catch(e){} }); document.getElementById('sub-total').textContent = subtotal.toFixed(3); document.getElementById('total-discount').textContent = totalDiscount.toFixed(3); var grand = (subtotal - totalDiscount).toFixed(3); document.getElementById('grand-total').textContent = grand; try{ var bottom = document.getElementById('bottom-total'); if(bottom) bottom.textContent = 'BHD ' + parseFloat(grand).toFixed(3); }catch(e){} }catch(e){} };

  if (typeof window.createItemRow === 'undefined') {
    window.createItemRow = function(focus){ try{ if(!window._lastCreateItemRowAt) window._lastCreateItemRowAt = 0; var now = Date.now(); if(now - window._lastCreateItemRowAt < 250) return null; window._lastCreateItemRowAt = now; }catch(e){}
      var tbody = document.getElementById('items-body'); if(!tbody) return null; var tr = document.createElement('tr'); tr.className = 'item-row';
      tr.innerHTML = `
        <td style="padding:8px 12px;vertical-align:middle;">
            <input type="text" class="item-desc" value="" style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;box-sizing:border-box;min-height:36px;height:36px;line-height:20px;" />
            <input type="hidden" class="item-type-hidden" name="item_type[]" value="inventory" />
        </td>
        <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-qty" value="1" min="0" step="1" style="width:90px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>
        <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-rate" value="0.000" step="0.001" style="width:110px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>
        <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-discount" value="0.00" step="0.001" style="width:60px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>
        <td style="padding:8px 12px;text-align:right;"><input type="text" class="item-amount" value="0.000" readonly style="width:calc(100% - 12px);padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;text-align:right;box-sizing:border-box;" /></td>
        <td style="padding:8px 12px;text-align:center;"><button type="button" class="remove-item-row remove-row" style="background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;">×</button></td>
      `;
      tbody.appendChild(tr);
      try{ window.__invBlockAutoOpenUntil = Date.now() + 400; }catch(e){}
      try{ var inp = tr.querySelector('.item-desc'); try{ if(typeof window.initInventoryRow === 'function') window.initInventoryRow(tr); else if(inp && window.initInventoryAutocomplete) window.initInventoryAutocomplete(inp); }catch(e){} if(focus!==false && inp) inp.focus(); }catch(e){}
      tr.querySelector('.remove-row').addEventListener('click', function(){ try{ if(tr && tr.parentNode) tr.parentNode.removeChild(tr); window.recomputeTotals(); }catch(e){} });
      var qty = tr.querySelector('.item-qty'); if(qty){ qty.addEventListener('input', function(){ try{ window.updateRowAmount(tr); window.recomputeTotals(); }catch(e){} }); }
      var rate = tr.querySelector('.item-rate'); if(rate){ rate.addEventListener('input', function(){ try{ window.updateRowAmount(tr); window.recomputeTotals(); }catch(e){} }); }
      var disc = tr.querySelector('.item-discount'); if(disc){ disc.addEventListener('input', function(){ try{ window.updateRowAmount(tr); window.recomputeTotals(); }catch(e){} }); }
      try{ tr.dataset.type = 'inventory'; }catch(e){}
      return tr;
    };
  }

  window.serializeInvoiceItems = function(){ try{ window.recomputeTotals(); var items = []; document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var partId = row.dataset.partId || row.dataset.inventoryId || null; if(!partId) return; items.push({ part_id: partId, description: row.querySelector('.item-desc').value, qty: parseFloatSafe(row.querySelector('.item-qty').value)||0, rate: parseFloatSafe(row.querySelector('.item-rate').value)||0, discount: parseFloatSafe(row.querySelector('.item-discount').value)||0, amount: parseFloatSafe(row.querySelector('.item-amount').value)||0 }); }catch(e){} }); var el = document.getElementById('items_json'); if(el) el.value = JSON.stringify(items); return true; }catch(e){ return false; } };

  try{ var addRowBtn = document.getElementById('add-row'); if(addRowBtn) addRowBtn.addEventListener('click', function(e){ e.preventDefault(); window.createItemRow(true); }); document.querySelectorAll('#items-body .item-desc').forEach(function(inp){ try{ window.initInventoryAutocomplete(inp); }catch(e){} }); var form = document.getElementById('invoice-form'); if(form){ form.addEventListener('submit', function(evt){ try{ if(!window.serializeInvoiceItems()) evt.preventDefault(); }catch(e){} }); } }catch(e){}

  try{ if(document.querySelectorAll('#items-body .item-row').length === 0) window.createItemRow(false); }catch(e){}

})();

  // Normalize any server-rendered initial row (svc_...) into a JS-created row
  document.addEventListener('DOMContentLoaded', function(){
    try{
      var body = document.getElementById('items-body'); if(!body) return;
      var first = body.querySelector('tr.item-row'); if(!first) return;
      if(first.dataset && first.dataset.rowId && String(first.dataset.rowId).indexOf('svc_') === 0){
        try{
          var descEl = first.querySelector('.item-desc'); var qtyEl = first.querySelector('.item-qty'); var rateEl = first.querySelector('.item-rate'); var discEl = first.querySelector('.item-discount');
          var vals = { description: descEl ? (descEl.value||'') : '', qty: qtyEl ? (qtyEl.value||'1') : '1', rate: rateEl ? (rateEl.value||'0.000') : '0.000', discount: discEl ? (discEl.value||'0.000') : '0.000', inventoryId: (first.dataset && (first.dataset.inventoryId||first.dataset.partId)) || null };
          try{ first.parentNode.removeChild(first); }catch(e){}
          var newRow = null;
          try{ newRow = window.createItemRow(false); }catch(e){}
          if(!newRow) return;
          try{ var d = newRow.querySelector('.item-desc'); if(d) d.value = vals.description; var q = newRow.querySelector('.item-qty'); if(q) q.value = vals.qty; var r = newRow.querySelector('.item-rate'); if(r) r.value = parseFloat(vals.rate||0).toFixed(3); var di = newRow.querySelector('.item-discount'); if(di) di.value = parseFloat(vals.discount||0).toFixed(3); if(vals.inventoryId){ try{ newRow.dataset.inventoryId = vals.inventoryId; newRow.dataset.partId = vals.inventoryId; }catch(e){} } if(window.updateRowAmount) window.updateRowAmount(newRow); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
        }catch(e){}
      }
    }catch(e){}
  });
