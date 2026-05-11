// Temporary runtime marker: set `window.__coreLoaded = true` when executed
// Remove this marker after verifying the core script is loaded in the browser.
(function(){
    try{ console.log('CORE LOADED: line-items.core.js'); window.__coreLoaded = true; }catch(e){}
    // Core: calculations and serializers
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

    window.updateServiceRowAmount = function(row){
        try{
            var q = parseFloat(row.querySelector('.service-qty').value) || 0;
            var r = parseFloat(row.querySelector('.service-rate').value) || 0;
            var d = parseFloat(row.querySelector('.service-discount')? row.querySelector('.service-discount').value : 0) || 0;
            var amt = q * r * (1 - (d/100));
            var amtEl = row.querySelector('.service-amount'); if(amtEl) amtEl.value = toFixed3(amt); return amt;
        }catch(e){return 0;}
    };

    window.serializeServiceItems = function(){ var out = []; document.querySelectorAll('.service-row, .item-row[data-type="service"]').forEach(function(row){ try{ var svcId = row.dataset.serviceId ? parseInt(row.dataset.serviceId,10) : null; var invoiceItemId = row.dataset.invoiceItemId ? parseInt(row.dataset.invoiceItemId,10) : null; var desc = ''; var hidden = row.querySelector('.service-desc') || row.querySelector('.item-desc'); if(hidden) desc = hidden.value || ''; var label = row.querySelector('.service-label') || row.querySelector('.item-desc'); if(!desc && label) desc = (label.textContent||label.value||'').trim(); var qtyEl = row.querySelector('.service-qty') || row.querySelector('.item-qty'); var rateEl = row.querySelector('.service-rate') || row.querySelector('.item-rate'); var discEl = row.querySelector('.service-discount') || row.querySelector('.item-discount'); var amtEl = row.querySelector('.service-amount') || row.querySelector('.item-amount'); var qty = parseFloat(qtyEl && qtyEl.value ? qtyEl.value : 0) || 0; var rate = parseFloat(rateEl && rateEl.value ? rateEl.value : 0) || 0; var discount = parseFloat(discEl && discEl.value ? discEl.value : 0) || 0; var amount = parseFloat(amtEl && amtEl.value ? amtEl.value : 0) || 0; var obj = { description: desc, qty: qty, rate: rate, discount: discount, amount: amount }; if(svcId) obj.service_id = svcId; if(invoiceItemId) obj.invoice_item_id = invoiceItemId; try{ var cid = row.getAttribute && row.getAttribute('data-client-row-id'); if(cid) obj.client_row_id = cid; }catch(e){} out.push(obj); }catch(e){} }); return out; };

    window.serializeMaintenanceItems = function(){
            try{
                // Collect rows only from the unified items container; service rows
                // should be present as `.item-row[data-type="service"]`.
                var rows = Array.prototype.slice.call(document.querySelectorAll('#items-body .item-row')) || [];
                var items = [];
                rows.forEach(function(row){ try{
                    // Determine row type robustly. Normalize legacy values like
                    // 'inventory' to canonical 'part' so backend and JS agree.
                    var rawType = null;
                    try{ rawType = (row.dataset && (row.dataset.type || row.getAttribute && row.getAttribute('data-type'))) || null; }catch(e){}
                    // prefer explicit hidden input if present
                    try{ var hhType = row.querySelector && row.querySelector('.item-type-hidden'); if(hhType && (typeof hhType.value !== 'undefined' && hhType.value !== '')) rawType = hhType.value; }catch(e){}
                    var normalizedType = null;
                    try{
                        if(!rawType) normalizedType = null;
                        else {
                            var lt = (rawType+'').toLowerCase();
                            if(lt === 'service' || lt === 'services') normalizedType = 'service';
                            else if(lt === 'part' || lt === 'parts' || lt === 'inventory' || lt === 'item' ) normalizedType = 'part';
                            else normalizedType = lt;
                        }
                    }catch(e){ normalizedType = rawType; }
                    var isService = (row.classList && row.classList.contains('service-row')) || (normalizedType === 'service');
                    // description: prefer item-desc, then service-desc, then visible service-label
                    var descEl = row.querySelector && (row.querySelector('.item-desc') || row.querySelector('.service-desc') || row.querySelector('.service-label'));
                    var desc = '';
                    try{ if(descEl){ desc = (typeof descEl.value !== 'undefined') ? (descEl.value||'') : (descEl.textContent||''); } }catch(e){}
                    desc = (desc||'').trim();
                    var qty = parseFloat((row.querySelector('.item-qty') || row.querySelector('.service-qty') || { value: 1 }).value) || 0;
                    var rate = parseFloat((row.querySelector('.item-rate') || row.querySelector('.service-rate') || { value: 0 }).value) || 0;
                    var disc = parseFloat((row.querySelector('.item-discount') || row.querySelector('.service-discount') || { value: 0 }).value) || 0;
                    var amt = parseFloat((row.querySelector('.item-amount') || row.querySelector('.service-amount') || { value: 0 }).value) || 0;
                    // skip placeholder/empty rows: no description and no meaningful values
                    // (some rows default qty to 1 before user edits; ignore those if they
                    // have no description and no rate/amount to avoid saving blank lines)
                    if(!desc && rate === 0 && amt === 0) return;
                    var obj = {
                        // canonical item type used across frontend <-> backend
                        // ensure we always send 'service' or 'part' (not 'inventory')
                        type: isService ? 'service' : 'part',
                        item_type: isService ? 'service' : 'part',
                        description: desc,
                        qty: qty,
                        rate: rate,
                        discount: disc,
                        amount: amt
                    };
                    try{ if(row.dataset && row.dataset.serviceId) obj.service_id = row.dataset.serviceId; }catch(e){}
                    try{ if(row.dataset && (row.dataset.partId || row.dataset.inventoryId)) obj.part_id = (row.dataset.partId || row.dataset.inventoryId); }catch(e){}
                    try{ if(row.dataset && row.dataset.invoiceItemId) obj.invoice_item_id = row.dataset.invoiceItemId; }catch(e){}
                    try{ var cid = row.getAttribute && row.getAttribute('data-client-row-id'); if(cid) obj.client_row_id = cid; }catch(e){}
                    items.push(obj);
                }catch(e){} });
                var hidden = document.getElementById('items_json');
                if(hidden){ hidden.value = JSON.stringify(items); }
                else { try{ console.warn('[serialize] items_json hidden input not found'); }catch(e){} }
                return true;
            }catch(e){ console.error('serializeMaintenanceItems failed', e); return false; }
    };

    // Track whether we've applied server-provided initial totals yet
    window.__initialTotalsApplied = window.__initialTotalsApplied || false;
    window.recomputeTotals = function(){
        try{
            // If server provided totals exist and we haven't applied them yet,
            // prefer showing the server values on first paint to avoid a brief
            // flicker where client recompute reports different breakdown.
            if(!window.__initialTotalsApplied){
                try{
                    var ssv = document.getElementById('server-services-total');
                    var spv = document.getElementById('server-parts-total');
                    var applied = false;
                    if(ssv){ var elSvc = document.getElementById('services-sub-total'); if(elSvc){ elSvc.textContent = ssv.value; applied = true; } }
                    if(spv){ var subEl = document.getElementById('sub-total'); if(subEl){ subEl.textContent = spv.value; applied = true; } }
                    if(applied){
                        // also set grand and bottom totals consistently
                        try{ var g = document.getElementById('grand-total'); if(g){ var svc = parseFloat((ssv && ssv.value) || 0)||0; var parts = parseFloat((spv && spv.value) || 0)||0; g.textContent = toFixed3(svc + parts); } }catch(e){}
                        try{ var bottom = document.getElementById('bottom-total'); if(bottom){ bottom.textContent = 'BHD ' + toFixed3((parseFloat((ssv && ssv.value)||0)||0) + (parseFloat((spv && spv.value)||0)||0)); } }catch(e){}
                        window.__initialTotalsApplied = true;
                        return true;
                    }
                }catch(e){}
            }
            // Sum services only from unified item rows marked as service.
            var svcTotal = 0;
            try{
                var allRows = document.querySelectorAll('#items-body .item-row');
                Array.prototype.forEach.call(allRows, function(r){
                    try{
                        var dtype = '';
                        try{ dtype = (r.dataset && (r.dataset.type || r.getAttribute && r.getAttribute('data-type'))) || ''; }catch(e){}
                        dtype = (dtype+'').toLowerCase();
                        var hasServiceId = false;
                        try{ hasServiceId = Boolean((r.dataset && (r.dataset.serviceId)) || (r.getAttribute && r.getAttribute('data-service-id'))); }catch(e){}
                        var isServiceRow = (r.classList && r.classList.contains('service-row')) || (dtype === 'service') || !!hasServiceId || !!(r.querySelector && (r.querySelector('.service-desc') || r.querySelector('.service-qty')));
                        if(!isServiceRow) return;
                        var el = r.querySelector('.service-amount') || r.querySelector('.item-amount');
                        var val = el ? parseFloat(el.value)||0 : 0;
                        svcTotal += val;
                    }catch(e){}
                });
            }catch(e){}
            // If client computes zero services but server provided a subtotal, prefer server value
            try{
                var ssv = document.getElementById('server-services-total');
                if((!svcTotal || svcTotal === 0) && ssv && ssv.value){
                    svcTotal = parseFloat(ssv.value) || 0;
                }
            }catch(e){}
            try{ var elSvc = document.getElementById('services-sub-total'); if(elSvc) elSvc.textContent = toFixed3(svcTotal); }catch(e){}

            // Items subtotal should exclude any service rows that may live inside
            // the `#items-body` container (those are counted as services above).
            var sub = 0; var discTotal = 0;
            try{
                var itemRows = document.querySelectorAll('#items-body .item-row');
                Array.prototype.forEach.call(itemRows, function(r){
                    try{
                        // Determine row type robustly: prefer explicit dataset.type,
                        // but also treat rows with a linked service id as service rows.
                        var dtype = '';
                        try{ dtype = (r.dataset && (r.dataset.type || r.getAttribute && r.getAttribute('data-type'))) || ''; }catch(e){}
                        dtype = (dtype+'').toLowerCase();
                        var hasServiceId = false;
                        try{ hasServiceId = Boolean((r.dataset && (r.dataset.serviceId)) || (r.getAttribute && r.getAttribute('data-service-id'))); }catch(e){}
                        var isServiceRow = (r.classList && r.classList.contains('service-row')) || (dtype === 'service') || !!hasServiceId || !!(r.querySelector && (r.querySelector('.service-desc') || r.querySelector('.service-qty')));
                        if(isServiceRow) return; // skip service rows when summing parts
                        var q = parseFloat(r.querySelector('.item-qty').value)||0;
                        var rate = parseFloat(r.querySelector('.item-rate').value)||0;
                        var d = parseFloat(r.querySelector('.item-discount').value)||0;
                        var lineTotal = q * rate;
                        var lineNet = lineTotal * (1 - (d/100));
                        sub += lineTotal;
                        discTotal += (lineTotal - lineNet);
                    }catch(e){}
                });
            }catch(e){}
            // If client computes zero parts but server provided a parts subtotal, prefer server value
            try{
                var spv = document.getElementById('server-parts-total');
                if((!sub || sub === 0) && spv && spv.value){
                    sub = parseFloat(spv.value) || 0;
                }
            }catch(e){}
            try{ var subEl=document.getElementById('sub-total'); if(subEl) subEl.textContent=toFixed3(sub); }catch(e){}
            try{ var discEl=document.getElementById('total-discount'); if(discEl) discEl.textContent=toFixed3(discTotal); }catch(e){}

            var grand = (sub - discTotal) + svcTotal;
            try{ var grandEl = document.getElementById('grand-total'); if(grandEl) grandEl.textContent = toFixed3(grand); }catch(e){}
            try{ var bottom = document.getElementById('bottom-total'); if(bottom) bottom.textContent = 'BHD ' + toFixed3(grand); }catch(e){}
            return true;
        }catch(e){ console.error('recomputeTotals failed', e); return false; }
    };
    try{ window.dispatchEvent && window.dispatchEvent(new Event('core-ready')); }catch(e){}
    // Signal that line-items core is fully initialized so UI modules may safely run
    try{ window.__lineItemsReady = true; window.dispatchEvent && window.dispatchEvent(new Event('line-items-ready')); }catch(e){}

})();
// Ensure hidden `items_json` is populated before any form submit and once on load
try{
    document.addEventListener('submit', function(e){
        try{
            if(e && e.target && (e.target.id === 'invoice-form' || e.target.matches && e.target.matches('#invoice-form'))){
                var form = e.target;
                try{
                    var active = document.activeElement;
                    // If user is still focused in an item-desc, blur and delay submission
                    // slightly to allow async autocomplete/lookup to finish and convert rows.
                    if(active && active.classList && active.classList.contains('item-desc')){
                        try{ e.preventDefault(); }catch(err){}
                        try{ active.blur(); }catch(err){}
                        setTimeout(function(){ try{ if(window.serializeMaintenanceItems) window.serializeMaintenanceItems(); }catch(err){} try{ form.submit(); }catch(e){} }, 180);
                        return;
                    }
                }catch(err){}
                try{ if(window.serializeMaintenanceItems) window.serializeMaintenanceItems(); }catch(err){}
            }
        }catch(err){}
    }, true);
    // populate on load so server sees existing state if needed
    try{ if(document.readyState === 'complete' || document.readyState === 'interactive'){ if(window.serializeMaintenanceItems) setTimeout(window.serializeMaintenanceItems, 40); } else { window.addEventListener('load', function(){ try{ if(window.serializeMaintenanceItems) window.serializeMaintenanceItems(); }catch(e){} }); } }catch(e){}
}catch(e){}