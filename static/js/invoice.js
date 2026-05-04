(function(){
  if(window.__invoiceInit) return; window.__invoiceInit = true;
  try{ console.log('[LOAD]', 'invoice.js', 'PAGE_MODE=' + (window.PAGE_MODE||'unset')); }catch(e){}
  if(typeof window.PAGE_MODE === 'undefined' || window.PAGE_MODE !== 'invoice') return;
  function parseFloatSafe(v){ var n = parseFloat(v); return isNaN(n)?0:n; }

  // update row amount for invoice parts
  window.updateRowAmount = function(row){ try{ var q = parseFloatSafe(row.querySelector('.item-qty').value); var r = parseFloatSafe(row.querySelector('.item-rate').value); var d = parseFloatSafe(row.querySelector('.item-discount').value); var amt = q * r * (1 - d/100); var amtEl = row.querySelector('.item-amount'); if(amtEl) amtEl.value = amt.toFixed(3); return amt; }catch(e){return 0;} };

  window.recomputeTotals = function(){ try{ var subtotal = 0, totalDiscount = 0; document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var q = parseFloatSafe(row.querySelector('.item-qty').value); var r = parseFloatSafe(row.querySelector('.item-rate').value); var d = parseFloatSafe(row.querySelector('.item-discount').value); var line = q * r; var amt = window.updateRowAmount(row); subtotal += line; totalDiscount += (line - amt); }catch(e){} }); document.getElementById('sub-total').textContent = subtotal.toFixed(3); document.getElementById('total-discount').textContent = totalDiscount.toFixed(3); var grand = (subtotal - totalDiscount).toFixed(3); document.getElementById('grand-total').textContent = grand; try{ var bottom = document.getElementById('bottom-total'); if(bottom) bottom.textContent = 'BHD ' + parseFloat(grand).toFixed(3); }catch(e){} }catch(e){} };

  window.createItemRow = function(focus){ try{ if(!window._lastCreateItemRowAt) window._lastCreateItemRowAt = 0; var now = Date.now(); if(now - window._lastCreateItemRowAt < 250) return null; window._lastCreateItemRowAt = now; }catch(e){}
    var tbody = document.getElementById('items-body'); if(!tbody) return null; var tr = document.createElement('tr'); tr.className = 'item-row'; tr.innerHTML = "<td><input type='text' class='item-desc' value=''><div class='stock-display'></div></td><td><input type='number' class='item-qty' step='1' value='1'></td><td><input type='number' class='item-rate' step='0.001' value='0.000'></td><td><input type='number' class='item-discount' step='0.001' value='0.000'></td><td><input type='text' class='item-amount' value='0.000' readonly></td><td><button type="button" class='remove-row'>×</button></td>";
    tbody.appendChild(tr);
    try{ var inp = tr.querySelector('.item-desc'); if(inp && window.initInventoryAutocomplete) window.initInventoryAutocomplete(inp); if(focus!==false && inp) inp.focus(); }catch(e){}
    tr.querySelector('.remove-row').addEventListener('click', function(){ try{ if(tr && tr.parentNode) tr.parentNode.removeChild(tr); window.recomputeTotals(); }catch(e){} });
    var qty = tr.querySelector('.item-qty'); if(qty){ qty.addEventListener('input', function(){ try{ window.updateRowAmount(tr); window.recomputeTotals(); }catch(e){} }); }
    return tr;
  };

  window.serializeInvoiceItems = function(){ try{ window.recomputeTotals(); var items = []; document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var partId = row.dataset.partId || row.dataset.inventoryId || null; if(!partId) return; items.push({ part_id: partId, description: row.querySelector('.item-desc').value, qty: parseFloatSafe(row.querySelector('.item-qty').value)||0, rate: parseFloatSafe(row.querySelector('.item-rate').value)||0, discount: parseFloatSafe(row.querySelector('.item-discount').value)||0, amount: parseFloatSafe(row.querySelector('.item-amount').value)||0 }); }catch(e){} }); var el = document.getElementById('items_json'); if(el) el.value = JSON.stringify(items); return true; }catch(e){ return false; } };

  try{ var addRowBtn = document.getElementById('add-row'); if(addRowBtn) addRowBtn.addEventListener('click', function(e){ e.preventDefault(); window.createItemRow(true); }); document.querySelectorAll('#items-body .item-desc').forEach(function(inp){ try{ window.initInventoryAutocomplete(inp); }catch(e){} }); var form = document.getElementById('invoice-form'); if(form){ form.addEventListener('submit', function(evt){ try{ if(!window.serializeInvoiceItems()) evt.preventDefault(); }catch(e){} }); } }catch(e){}

  try{ if(document.querySelectorAll('#items-body .item-row').length === 0) window.createItemRow(true); }catch(e){}

})();
