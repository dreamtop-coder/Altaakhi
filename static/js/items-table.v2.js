(function(){
    // Item table helper for maintenance page
    // Exposes: window.createItemRow(), window.updateRowAmount(), window.serializeMaintenanceItems(), window.initItemsTable(), window.recomputeTotals()

    function toFixed3(v){ try{ return parseFloat(v||0).toFixed(3); }catch(e){ return '0.000'; } }

    window.updateRowAmount = function(row){
        try{
            var q = parseFloat(row.querySelector('.item-qty').value) || 0;
            var r = parseFloat(row.querySelector('.item-rate').value) || 0;
            var d = parseFloat(row.querySelector('.item-discount').value) || 0;
            var amt = q * r * (1 - (d/100));
            var amtEl = row.querySelector('.item-amount');
            if(amtEl) amtEl.value = toFixed3(amt);
            return amt;
        }catch(e){ return 0; }
    };

    window.createItemRow = function(focus){
        try{
            var body = document.getElementById('items-body'); if(!body) return null;
            var tr = document.createElement('tr'); tr.className = 'item-row';
            // cell: description
            var tdDesc = document.createElement('td'); tdDesc.style.padding = '6px';
            var inpDesc = document.createElement('input'); inpDesc.type = 'text'; inpDesc.className = 'item-desc'; inpDesc.placeholder = 'Service'; inpDesc.style.cssText = 'width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;font-size:14px;color:#374151;font-weight:400;font-family:inherit;box-sizing:border-box;min-height:36px;height:36px;line-height:20px;';
            inpDesc.dataset.autocomplete = 'inventory';
            tdDesc.appendChild(inpDesc);
            // cell: qty
            var tdQty = document.createElement('td'); tdQty.style.padding = '6px'; tdQty.style.textAlign = 'center';
            var inpQty = document.createElement('input'); inpQty.type = 'number'; inpQty.className = 'item-qty'; inpQty.step = '1'; inpQty.value = '1'; inpQty.style.cssText = 'width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;';
            tdQty.appendChild(inpQty);
            // cell: rate
            var tdRate = document.createElement('td'); tdRate.style.padding = '6px'; tdRate.style.textAlign = 'center';
            var inpRate = document.createElement('input'); inpRate.type = 'number'; inpRate.className = 'item-rate'; inpRate.step = '0.001'; inpRate.value = '0.000'; inpRate.style.cssText = 'width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;';
            tdRate.appendChild(inpRate);
            // cell: discount
            var tdDisc = document.createElement('td'); tdDisc.style.padding = '6px'; tdDisc.style.textAlign = 'center';
            var inpDisc = document.createElement('input'); inpDisc.type = 'number'; inpDisc.className = 'item-discount'; inpDisc.step = '0.01'; inpDisc.value = '0.00'; inpDisc.style.cssText = 'width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;';
            tdDisc.appendChild(inpDisc);
            // cell: amount
            var tdAmount = document.createElement('td'); tdAmount.style.padding = '6px'; tdAmount.style.textAlign = 'center';
            var inpAmount = document.createElement('input'); inpAmount.type = 'text'; inpAmount.className = 'item-amount'; inpAmount.value = '0.000'; inpAmount.readOnly = true; inpAmount.style.cssText = 'width:100%;padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;';
            tdAmount.appendChild(inpAmount);
            // cell: remove
            var tdRemove = document.createElement('td'); tdRemove.style.padding = '6px'; tdRemove.style.textAlign = 'center';
            var btnRemove = document.createElement('button'); btnRemove.type = 'button'; btnRemove.className = 'remove-item-row'; btnRemove.style.cssText = 'background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;'; btnRemove.textContent = '×';
            tdRemove.appendChild(btnRemove);
            tr.appendChild(tdDesc); tr.appendChild(tdQty); tr.appendChild(tdRate); tr.appendChild(tdDisc); tr.appendChild(tdAmount); tr.appendChild(tdRemove);
            body.appendChild(tr);
            try{
                var desc = tr.querySelector('.item-desc');
                if(desc) desc.dataset.autocomplete = 'inventory';
                if(window.initInventoryAutocomplete) window.initInventoryAutocomplete(desc);
                var qty = tr.querySelector('.item-qty'); var rate = tr.querySelector('.item-rate'); var disc = tr.querySelector('.item-discount');
                qty.addEventListener('input', function(){ window.updateRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                rate.addEventListener('input', function(){ window.updateRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                disc.addEventListener('input', function(){ window.updateRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                if(focus!==false) desc.focus();
            }catch(e){}
            return tr;
        }catch(e){ console.error('createItemRow failed', e); return null; }
    };

    document.addEventListener('click', function(e){ try{ if(e.target && e.target.classList && e.target.classList.contains('remove-item-row')){ var r = e.target.closest('.item-row'); if(r) r.parentNode.removeChild(r); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} } }catch(err){} });

    window.serializeMaintenanceItems = function(){
        try{
            // allow toggling via window.DEBUG_ITEMS for quick debugging
            if(typeof window.DEBUG_ITEMS === 'undefined') window.DEBUG_ITEMS = false;
            // ensure every row (service or item) has a client-side id so the server
            // can distinguish intentional duplicates from accidental ones
            try{ document.querySelectorAll('.service-row').forEach(function(r){ try{ if(!r.getAttribute('data-client-row-id')){ var _cid = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : ('c' + Date.now() + Math.floor(Math.random()*1000000)); r.setAttribute('data-client-row-id', _cid); } }catch(e){} }); }catch(e){}
            try{ document.querySelectorAll('#items-body .item-row').forEach(function(r){ try{ if(!r.getAttribute('data-client-row-id')){ var _cid2 = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : ('c' + Date.now() + Math.floor(Math.random()*1000000)); r.setAttribute('data-client-row-id', _cid2); } }catch(e){} }); }catch(e){}

            var services = (window.serializeServiceItems? window.serializeServiceItems() : []);
            var items = [];
            document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var desc = row.querySelector('.item-desc')? row.querySelector('.item-desc').value : ''; var qty = parseFloat(row.querySelector('.item-qty').value)||0; var rate = parseFloat(row.querySelector('.item-rate').value)||0; var disc = parseFloat(row.querySelector('.item-discount').value)||0; var amt = parseFloat(row.querySelector('.item-amount').value)||0; if((desc||'').trim()==='' && qty===0) return; var obj = { description: desc, qty: qty, rate: rate, disc: disc, discount: disc, amount: amt }; var iid = row.dataset && row.dataset.invoiceItemId ? parseInt(row.dataset.invoiceItemId,10) : null; if(iid) obj.invoice_item_id = iid; try{ var cid = row.getAttribute && row.getAttribute('data-client-row-id'); if(cid) obj.client_row_id = cid; }catch(e){} items.push(obj); }catch(e){} });
            var combined = services.concat(items);
            // If the UI recorded removed service/invoice-item markers, include
            // them as deleted entries so the server can remove them on save.
            try{
                if(window.__removedServiceMarkers && window.__removedServiceMarkers.length){
                    window.__removedServiceMarkers.forEach(function(m){ try{ combined.push(m); }catch(e){} });
                }
                // legacy support: numeric ids previously stored in __removedServiceIds
                if(!window.__removedServiceIds) window.__removedServiceIds = [];
                if(window.__removedServiceIds && window.__removedServiceIds.length){
                    window.__removedServiceIds.forEach(function(rid){ try{ var n = parseInt(rid); if(!isNaN(n)) combined.push({ service_id: n, _deleted: true }); }catch(e){} });
                }
            }catch(e){}
            var hidden = document.getElementById('items_json');
            if(!hidden){
                // create hidden input if missing so server receives payload
                try{ hidden = document.createElement('input'); hidden.type = 'hidden'; hidden.id = 'items_json'; hidden.name = 'items_json'; var f = document.getElementById('invoice-form'); if(f) f.appendChild(hidden); }catch(e){}
            }
            if(hidden) hidden.value = JSON.stringify(combined);
            if(window.DEBUG_ITEMS) console.log('serializeMaintenanceItems -> items_json length=', hidden && hidden.value ? hidden.value.length : 0, 'rows=', combined.length);
            return true;
        }catch(e){ console.error('serializeMaintenanceItems failed', e); return false; }
    };

    window.recomputeTotals = function(){
        try{
            // services total (count service rows anywhere on the page)
            var svcTotal = 0;
            document.querySelectorAll('.service-row').forEach(function(r){ try{ var val = parseFloat(r.querySelector('.service-amount').value)||0; svcTotal += val; }catch(e){} });
            document.getElementById('services-sub-total').textContent = toFixed3(svcTotal);

            // items subtotal and discount
            var sub = 0; var discTotal = 0;
            document.querySelectorAll('#items-body .item-row').forEach(function(r){ try{ var q = parseFloat(r.querySelector('.item-qty').value)||0; var rate = parseFloat(r.querySelector('.item-rate').value)||0; var d = parseFloat(r.querySelector('.item-discount').value)||0; var lineTotal = q * rate; var lineNet = lineTotal * (1 - (d/100)); sub += lineTotal; discTotal += (lineTotal - lineNet); }catch(e){} });
            document.getElementById('sub-total').textContent = toFixed3(sub);
            document.getElementById('total-discount').textContent = toFixed3(discTotal);

            var grand = (sub - discTotal) + svcTotal;
            document.getElementById('grand-total').textContent = toFixed3(grand);
            var bottom = document.getElementById('bottom-total'); if(bottom) bottom.textContent = 'BHD ' + toFixed3(grand);
            // keep the hidden form amount in sync with the computed total so
            // client-side changes (add/remove rows) reflect in the form value
            // even before the user explicitly submits. The server-side saved
            // invoice.amount will still reflect persisted data until Save.
            try{ var fa = document.getElementById('form-amount'); if(fa) fa.value = toFixed3(grand); }catch(e){}
            return true;
        }catch(e){ console.error('recomputeTotals failed', e); return false; }
    };

    window.initItemsTable = function(){ try{ var btn = document.getElementById('add-row'); if(btn) btn.addEventListener('click', function(e){ e.preventDefault(); createItemRow(true); }); try{ var isMaintenancePage = !!(window.__isMaintenancePage); if(!isMaintenancePage){ if(document.querySelectorAll('#items-body .item-row').length === 0) createItemRow(false); } }catch(e){ if(document.querySelectorAll('#items-body .item-row').length === 0) createItemRow(false); } // ensure totals update
        // initialize existing server-rendered rows so their inputs get autocomplete and event handlers
        try{
            document.querySelectorAll('#items-body .item-row').forEach(function(row){
                try{
                    var desc = row.querySelector('.item-desc'); if(desc){ desc.dataset.autocomplete = 'inventory'; if(window.initInventoryAutocomplete) window.initInventoryAutocomplete(desc); }
                    var qty = row.querySelector('.item-qty'); var rate = row.querySelector('.item-rate'); var disc = row.querySelector('.item-discount');
                    if(qty) qty.addEventListener('input', function(){ window.updateRowAmount(row); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                    if(rate) rate.addEventListener('input', function(){ window.updateRowAmount(row); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                    if(disc) disc.addEventListener('input', function(){ window.updateRowAmount(row); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });

                    // If this server-rendered row's description matches a service name, convert it into a service-row
                    try{
                        var val = (desc && desc.value) ? (desc.value+'').trim() : '';
                        if(val){
                            // query services autocomplete for this exact name
                            var svcUrl = '/services/autocomplete/?q=' + encodeURIComponent(val);
                            (window.fetchJson? window.fetchJson(svcUrl) : fetch(svcUrl).then(function(r){ return r.json(); })).then(function(data){
                                try{
                                    var results = (data && data.results)? data.results : [];
                                    var match = results.find(function(it){ return (it.name||'').trim().toLowerCase() === val.toLowerCase(); });
                                    if(match && window.createServiceRow){
                                        // build a service row and copy values
                                        // create the row but do NOT attach it to the main services list —
                                        // we'll replace this item-row in-place with the new service-row
                                        var newTr = window.createServiceRow(false, false);
                                        if(!newTr) return;
                                        newTr.dataset.serviceId = match.id;
                                        var lbl = newTr.querySelector('.service-label'); var hidden = newTr.querySelector('.service-desc');
                                        if(lbl) lbl.textContent = match.name || val; if(hidden) hidden.value = match.name || val;
                                        var qEl = newTr.querySelector('.service-qty'); var rEl = newTr.querySelector('.service-rate'); var dEl = newTr.querySelector('.service-discount'); var aEl = newTr.querySelector('.service-amount');
                                        try{ if(qEl) qEl.value = (row.querySelector('.item-qty') && row.querySelector('.item-qty').value) || qEl.value; }catch(e){}
                                        try{ if(rEl) rEl.value = (row.querySelector('.item-rate') && row.querySelector('.item-rate').value) || rEl.value; }catch(e){}
                                        try{ if(dEl) dEl.value = (row.querySelector('.item-discount') && row.querySelector('.item-discount').value) || dEl.value; }catch(e){}
                                        try{ if(aEl) aEl.value = (row.querySelector('.item-amount') && row.querySelector('.item-amount').value) || aEl.value; }catch(e){}
                                        // insert the new service row into the services tbody so it
                                        // is treated as a service (not an item). Removing the old
                                        // item-row keeps the DOM structure correct and ensures
                                        // serialization picks up the service on save.
                                        try{
                                            var svcBody = document.getElementById('services-body');
                                            if(svcBody){
                                                svcBody.appendChild(newTr);
                                                try{ if(window.attachServiceRowEvents) attachServiceRowEvents(newTr); }catch(e){}
                                                // remove the original item-row from items tbody
                                                try{ if(row && row.parentNode) row.parentNode.removeChild(row); }catch(e){}
                                            } else {
                                                // fallback: replace in-place
                                                row.parentNode.replaceChild(newTr, row);
                                            }
                                        }catch(e){ try{ row.parentNode.replaceChild(newTr, row); }catch(err){} }
                                        try{ if(window.initServicesTable) window.initServicesTable(); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                                    }
                                }catch(e){}
                            }).catch(function(){ /* ignore */ });
                        }
                    }catch(e){}
                }catch(e){}
            });
        }catch(e){}
        try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
    }catch(e){ console.error('initItemsTable failed', e); } };

    // initialize when DOM ready if called
    function attachFormSubmit(){
        try{
            var form = document.getElementById('invoice-form');
            if(!form) return;
            if(form._serializeAttached) return; form._serializeAttached = true;
            // per-form submitting lock to prevent double-submit
            if(typeof form._submitting === 'undefined') form._submitting = false;
            form.addEventListener('submit', function(e){
                try{
                    if(form._submitting){
                        if(window.DEBUG_ITEMS) console.log('submit blocked: already submitting');
                        e.preventDefault();
                        return false;
                    }
                    // mark as submitting early to prevent duplicate submissions
                    form._submitting = true;
                    // ensure totals are up-to-date before serializing and submitting
                    try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                    // attempt standard serialization
                    var ok = true;
                    try{ ok = !!(window.serializeMaintenanceItems && window.serializeMaintenanceItems()); }catch(err){ ok = false; }
                    // defensive fallback: if hidden field is empty, build combined payload synchronously
                    try{
                        var hidden = document.getElementById('items_json');
                        if(!hidden || !(hidden.value && hidden.value.trim())){
                            if(window.DEBUG_ITEMS) console.log('Serialize fallback triggered: building items_json');
                            var combined = [];
                            try{ if(window.serializeServiceItems) { combined = combined.concat(window.serializeServiceItems()); } }catch(e){}
                            try{ document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var desc = row.querySelector('.item-desc')? row.querySelector('.item-desc').value : ''; var qty = parseFloat(row.querySelector('.item-qty').value)||0; var rate = parseFloat(row.querySelector('.item-rate').value)||0; var disc = parseFloat(row.querySelector('.item-discount').value)||0; var amt = parseFloat(row.querySelector('.item-amount').value)||0; if((desc||'').trim()==='' && qty===0) return; var obj = { description: desc, qty: qty, rate: rate, disc: disc, discount: disc, amount: amt }; var iid = row.dataset && row.dataset.invoiceItemId ? parseInt(row.dataset.invoiceItemId,10) : null; if(iid) obj.invoice_item_id = iid; try{ var cid = row.getAttribute && row.getAttribute('data-client-row-id'); if(!cid){ cid = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : ('c' + Date.now() + Math.floor(Math.random()*1000000)); row.setAttribute('data-client-row-id', cid); } if(cid) obj.client_row_id = cid; }catch(e){} combined.push(obj); }catch(e){} }); }catch(e){}
                            try{ if(window.__removedServiceMarkers && window.__removedServiceMarkers.length){ window.__removedServiceMarkers.forEach(function(m){ try{ combined.push(m); }catch(e){} }); } }catch(e){}
                            if(!hidden){ hidden = document.createElement('input'); hidden.type='hidden'; hidden.id='items_json'; hidden.name='items_json'; var f = document.getElementById('invoice-form'); if(f) f.appendChild(hidden); }
                            hidden.value = JSON.stringify(combined);
                            if(window.DEBUG_ITEMS) console.log('Serialize fallback produced items_json length=', hidden.value.length);
                        }
                    }catch(err){ if(window.DEBUG_ITEMS) console.error('serialize fallback error', err); }
                    // if still empty but there are visible rows, block submit so data isn't lost
                    try{
                        var hiddenNow = document.getElementById('items_json');
                        var hasVisible = (document.querySelectorAll('.service-row').length + document.querySelectorAll('#items-body .item-row').length) > 0;
                        if(hasVisible && (!hiddenNow || !(hiddenNow.value && hiddenNow.value.trim()))){
                            e.preventDefault();
                            form._submitting = false; // release lock
                            try{ alert('Failed to prepare invoice items for saving. Please try again or reload the page.'); }catch(ai){}
                            return false;
                        }
                    }catch(err){ if(window.DEBUG_ITEMS) console.error('post-serialize check failed', err); }
                    // allow submit to proceed (form._submitting remains true until navigation)
                }catch(err){ if(window.DEBUG_ITEMS) console.error('submit handler error', err); form._submitting = false; }
            });
                    // update hidden amount field from computed grand-total and
                    // sanitize to a numeric string to avoid server-side parsing issues
                    var grandText = (document.getElementById('grand-total') && document.getElementById('grand-total').textContent) ? document.getElementById('grand-total').textContent : '';
                    var numeric = (grandText+"").replace(/[^0-9.\-]/g,'');
                    var fa = document.getElementById('form-amount');
                    if(fa){ fa.value = (numeric !== '') ? (parseFloat(numeric).toFixed(3)) : '0.000'; }
                }catch(err){}
            });
        }catch(e){}
    }

    document.addEventListener('DOMContentLoaded', function(){ try{ if(window.initItemsTable) window.initItemsTable(); }catch(e){}
        try{ attachFormSubmit(); }catch(e){}
    });

    // If scripts run after DOMContentLoaded, ensure the submit handler is still attached
    try{ if(document.readyState && document.readyState !== 'loading'){ try{ if(window.initItemsTable) window.initItemsTable(); }catch(e){} try{ attachFormSubmit(); }catch(e){} } }catch(e){}

})();