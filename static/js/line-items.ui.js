(function(){
    // UI: DOM row creation and init
    window.createItemRow = function(typeOrFocus, focus){
        try{
            try{ if(window.__creatingItemRow) return null; window.__creatingItemRow = true; }catch(e){}
            try{
                if(window.__logCreateItemRow){
                    try{
                        window.__createItemRowCalls = (window.__createItemRowCalls||0) + 1;
                        console.log('createItemRow called', window.__createItemRowCalls, Date.now());
                        console.trace();
                    }catch(err){}
                }
            }catch(err){}
            try{
                // debounce rapid createItemRow calls (increase window to avoid duplicates)
                if(window.__lastCreateItemRowAt && (Date.now() - window.__lastCreateItemRowAt) < 800){ return null; }
                window.__lastCreateItemRowAt = Date.now();
            }catch(e){}
            // By default leave new rows untyped so Add Line Item opens merged
            // suggestions (services + inventory). Callers may pass a string
            // to force a specific type ('inventory'|'service').
            var itemType;
            if(typeof typeOrFocus === 'string') itemType = typeOrFocus;
            else if(typeof typeOrFocus === 'boolean') { focus = typeOrFocus; }
            // If this call is the automatic initial row creation (focus===false),
            // ensure we only do it once across all scripts.
            try{
                if(focus === false){
                    if(window.__initialRowCreated) { try{ window.__creatingItemRow = false; }catch(e){} return null; }
                    try{ window.__initialRowCreated = true; }catch(e){}
                }
            }catch(e){}
            // Honor a page-requested initial item type (e.g. invoices/add wants inventory-only)
            try{
                if(!itemType && focus === false && typeof window.__initialItemType !== 'undefined' && window.__initialItemType){
                    itemType = window.__initialItemType;
                }
            }catch(e){}
            var body = document.getElementById('items-body') || document.getElementById('items-body-view') || null;
            if(!body){
                try{
                    // Prefer a tbody that already looks like the items table (contains item inputs)
                    var tbodies = Array.prototype.slice.call(document.querySelectorAll('tbody'));
                    for(var i=0;i<tbodies.length;i++){
                        var b = tbodies[i];
                        try{
                            if(b.querySelector && (b.querySelector('.item-desc') || b.querySelector('.item-type-hidden') || b.querySelector('input[name="item_type[]"]'))){ body = b; break; }
                        }catch(e){}
                    }
                    // fallback to explicit ids only (avoid generic single 'tbody' which may be services table)
                    if(!body) body = document.querySelector('tbody#items-body, tbody#items-body-view');
                }catch(e){}
            }
            if(!body){ try{ window.__creatingItemRow = false; }catch(e){} return null; }
            // If there's already an empty item-desc row, avoid creating another duplicate
            // Exception: when caller explicitly asked to focus (user Add button), allow creating additional rows.
            try{
                try{
                    var existingEmpty = false;
                    (body.querySelectorAll('.item-row')||[]).forEach(function(r){ try{ var d = r.querySelector && (r.querySelector('.item-desc') || r.querySelector('.service-desc')); if(d && ((d.value||'').trim()==='')) existingEmpty = true; }catch(e){} });
                    if(existingEmpty && focus !== true){ try{ window.__creatingItemRow = false; }catch(e){} return null; }
                }catch(e){}
            }catch(e){}
            var tr = document.createElement('tr'); tr.className = 'item-row';
            try{ if(itemType) { tr.setAttribute('data-type', itemType); tr.dataset.type = itemType; } }catch(e){}
            tr.innerHTML = '\n                <td style="padding:8px 12px;vertical-align:middle;">\n                    <input type="text" class="item-desc" value="" style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;box-sizing:border-box;min-height:36px;height:36px;line-height:20px;" data-bound="true" />\n                    <input type="hidden" class="item-type-hidden" name="item_type[]" value="" />\n                </td>\n                <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-qty" value="1" min="0" step="1" style="width:90px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>\n                <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-rate" value="0.000" step="0.001" style="width:110px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>\n                <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-discount" value="0.00" step="0.001" style="width:60px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>\n                <td style="padding:8px 12px;text-align:right;"><input type="text" class="item-amount" value="0.000" readonly style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;text-align:right;" /></td>\n                <td style="padding:8px 12px;text-align:center;"><button type="button" class="remove-item-row remove-row" style="background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;">×</button></td>';
            try{ body.appendChild(tr); }catch(e){ try{ document.body.appendChild(tr); }catch(err){} }
            // mark creation time early so other initializers can detect "new" rows
            try{ tr.dataset.__createdAt = Date.now(); }catch(e){}
            try{
                // ensure hidden input and dataset reflect requested item type (only if explicitly provided)
                try{ if(itemType){ tr.setAttribute('data-type', itemType); tr.dataset.type = itemType; } }catch(e){}
                try{ var hh_init = tr.querySelector('.item-type-hidden'); if(hh_init && itemType) hh_init.value = itemType; }catch(e){}
            }catch(e){}
            try{
                var desc = tr.querySelector('.item-desc');
                        try{
                            // Default all new rows to inventory-only
                            try{ desc.dataset.autocomplete = 'inventory'; }catch(e){}
                            try{ if(typeof window.initInventoryAutocomplete === 'function') window.initInventoryAutocomplete(desc); }catch(e){}
                        }catch(e){}
                    // listen for explicit service selection events and forward to service handler
                    try{ desc.addEventListener && desc.addEventListener('service-selected', function(ev){ try{ if(!window._servicesTableInit && window.onServiceSelected) window.onServiceSelected(tr, ev.detail); }catch(e){} }); }catch(e){}
                    // No mutation observer needed in inventory-only mode
                }catch(e){}
                // Type selector removed in inventory-only mode; ensure hidden input present and set
                try{
                    var hh = tr.querySelector('.item-type-hidden'); if(hh) hh.value = 'inventory';
                    try{ tr.dataset.type = 'inventory'; }catch(e){}
                }catch(e){}
                var qty = tr.querySelector('.item-qty'); var rate = tr.querySelector('.item-rate'); var disc = tr.querySelector('.item-discount');
                qty.addEventListener('input', function(){ try{ if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                rate.addEventListener('input', function(){ try{ if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                disc.addEventListener('input', function(){ try{ if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                if(focus!==false) desc.focus();
            }catch(e){}
            try{ 
                try{ tr.dataset.__createdAt = Date.now(); }catch(e){}
                try{ var __s = (new Error().stack||'').split('\n')[1] || ''; tr.dataset.__createdBy = __s.trim(); }catch(e){}
                // dedupe: remove rapid duplicate rows that have identical descriptions
                try{
                    var runDedupe = function(){
                        try{
                            var rows = Array.prototype.slice.call((body.querySelectorAll('.item-row')||[]));
                            var groups = {};
                            rows.forEach(function(r){
                                try{
                                    var key = '';
                                    var d = r.querySelector && r.querySelector('.item-desc');
                                    if(d && (d.value||'').trim() !== '') key = (d.value||'').trim();
                                    else {
                                        var sl = r.querySelector && r.querySelector('.service-label');
                                        if(sl && (sl.textContent||'').trim() !== '') key = (sl.textContent||'').trim();
                                    }
                                    if(!key) return;
                                    var t = parseInt(r.dataset.__createdAt||0,10) || 0;
                                    groups[key] = groups[key] || [];
                                    groups[key].push({row:r, time:t});
                                }catch(e){}
                            });
                            Object.keys(groups).forEach(function(k){
                                try{
                                    var arr = groups[k];
                                    if(arr.length < 2) return;
                                    arr.sort(function(a,b){ return a.time - b.time; });
                                    // keep earliest, remove others that were created recently
                                    for(var i=1;i<arr.length;i++){
                                        try{
                                            var age = Date.now() - (arr[i].time||0);
                                            if(age < 2500){ // 2.5s window
                                                try{ console.log('Dedup: removing duplicate row', {key:k, createdBy: arr[i].row.dataset && arr[i].row.dataset.__createdBy, age: age, createdAt: arr[i].time}); }catch(e){}
                                                if(arr[i].row && arr[i].row.parentNode) arr[i].row.parentNode.removeChild(arr[i].row);
                                            }
                                        }catch(e){}
                                    }
                                }catch(e){}
                            });
                        }catch(e){}
                    };
                    try{ setTimeout(runDedupe, 80); }catch(e){}
                    try{ setTimeout(runDedupe, 700); }catch(e){}
                    try{ setTimeout(runDedupe, 1500); }catch(e){}
                }catch(e){}
            }catch(e){}
            try{ window.__creatingItemRow = false; }catch(e){}
            return tr;
        }catch(e){ console.error('createItemRow failed', e); try{ window.__creatingItemRow = false; }catch(err){} return null; }
    };

    // attach delegated remove handler (robust to text-node targets)
    document.addEventListener('click', function(e){ try{ var btn = e.target && e.target.closest ? e.target.closest('.remove-row') : null; if(btn){ var r = (btn.closest && (btn.closest('.item-row') || btn.closest('.service-row') || btn.closest('tr'))) || null; if(r){ try{ if(r.parentNode) r.parentNode.removeChild(r); else if(typeof r.remove === 'function') r.remove(); }catch(err){} try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} } } }catch(err){} });

    // Keep `onServiceSelected` as a no-op wrapper to avoid flipping rows to 'service'
    try{
        (function(){
            var _orig = window.onServiceSelected || function(row,item){};
            window.onServiceSelected = function(row,item){
                try{ _orig(row,item); }catch(e){}
            };
        })();
    }catch(e){}

    // minimal createServiceRow delegator: will use canonical implementation if provided
    window.createServiceRow = window.createServiceRow || function(focus, attachToBody){ try{ if(window.__creatingServiceRow) return null; if(attachToBody !== false && !window._addingService && !window.__svcAllowCreate){ /*guard*/ } // fall back to a simple service row
            var body = document.getElementById('services-body') || document.body;
            var tr = document.createElement('tr'); tr.className='item-row'; try{ tr.setAttribute('data-type','service'); }catch(e){} tr.innerHTML = '\
        <td style="padding:8px 12px;vertical-align:middle;">\
              <div class="service-label" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;font-size:14px;color:#374151;font-weight:400;box-sizing:border-box;min-height:36px;height:36px;line-height:20px;display:block;background:#fff">&nbsp;</div>\
            <input type="hidden" class="service-desc" value=""/>\
        </td>\
        <td style="padding:8px 12px;text-align:center;"><input type="number" class="service-qty" step="1" value="1" style="width:90px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;"/></td>\
        <td style="padding:8px 12px;text-align:center;"><input type="number" class="service-rate" step="0.001" value="0.000" style="width:110px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;"/></td>\
        <td style="padding:8px 12px;text-align:center;"><input type="number" class="service-discount" step="0.01" value="0.00" style="width:60px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;"/></td>\
        <td style="padding:8px 12px;text-align:right;"><input type="text" class="service-amount" value="0.000" readonly style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;text-align:right;"/></td>\
        <td style="padding:8px 12px;text-align:center;"><button type="button" class="remove-service-row remove-row" style="background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;">×</button></td>';
            if(body) body.appendChild(tr); return tr; }catch(e){ console.error(e); return null; } };

    // bind add buttons (items + services)
    window.initItemsTable = window.initItemsTable || function(){ try{ if(window.__addLineHandlerInstalled){} else { var btn = document.querySelector('button[id="add-line-item"], button.add-line-item, #add-line-item, #add-row'); if(btn && !(btn.dataset && btn.dataset.addlineBound === '1')){ btn.addEventListener('click', function(e){ e.preventDefault(); try{ createItemRow(true); if(window.recomputeTotals) window.recomputeTotals(); }catch(err){ console.error(err); } }); try{ btn.dataset.addlineBound = '1'; }catch(e){} try{ window.__addLineHandlerInstalled = true; }catch(e){} } } if(document.querySelectorAll('#items-body .item-row').length === 0 && !window.__isMaintenancePage) createItemRow(false); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} }catch(e){} };

        // Fallback: delegated click handler to catch any "Add Line Item" button
        // even if its listeners were removed or the element was re-rendered.
        document.addEventListener('click', function(e){
            try{
                var t = e.target;
                var btn = t && t.closest ? t.closest('button, a') : null;
                if(!btn) return;
                    try{ if(window.__addLineHandlerInstalled) return; }catch(e){}
                var txt = (btn.textContent||'').trim();
                if(btn.id === 'add-line-item' || btn.classList.contains('add-line-item') || txt.indexOf('Add Line Item') !== -1){
                    try{ e.preventDefault(); }catch(err){}
                    try{ /* prevent other click handlers (target/bubble) from also running */ e.stopImmediatePropagation(); }catch(err){}
                    try{ try{ window.__addLineHandlerInstalled = true; }catch(e){} if(window.createItemRow) window.createItemRow(true); }catch(err){}
                    try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(err){}
                }
            }catch(err){}
        }, true);

    window.initServicesTable = window.initServicesTable || function(){ try{ window._servicesTableInit = true; var btn = document.getElementById('add-service'); if(btn && btn.dataset.bound !== '1'){ btn.dataset.bound = '1'; btn.addEventListener('click', function(e){ e.preventDefault(); e.stopPropagation(); if(btn.dataset.lock === '1') return; btn.dataset.lock = '1'; try{ window._addingService = true; createServiceRow(true); }catch(err){} finally{ setTimeout(function(){ try{ window._addingService = false; }catch(e){} try{ delete btn.dataset.lock; }catch(e){} }, 300); } }, true); } try{ document.querySelectorAll('#services-body .service-row, #services-body .item-row[data-type="service"]').forEach(function(r){ try{ if(window.updateServiceRowAmount) window.updateServiceRowAmount(r); }catch(e){} }); }catch(e){} }catch(e){ console.error('initServicesTable failed', e); } };

    // Only load/initialize services-table on maintenance pages.
    try{
        var __pageInvoiceType = (document && document.body && document.body.dataset && document.body.dataset.invoiceType) ? document.body.dataset.invoiceType : null;
        if(__pageInvoiceType === 'maintenance'){
            try{
                if(typeof window.initServiceAutocomplete === 'function' && !window.__svcLoaderKicked){
                    window.__svcLoaderKicked = true;
                    try{ var _tmp = document.createElement('input'); _tmp.type = 'text'; try{ window.initServiceAutocomplete(_tmp); }catch(e){} }catch(e){}
                    setTimeout(function(){ try{ if(window.initServicesTable) window.initServicesTable(); }catch(e){} }, 350);
                }
            }catch(e){}
        }
    }catch(e){}

    document.addEventListener('DOMContentLoaded', function(){ try{ if(window.initItemsTable) window.initItemsTable(); }catch(e){} try{ var __pageInvoiceType = (document && document.body && document.body.dataset && document.body.dataset.invoiceType) ? document.body.dataset.invoiceType : null; if(__pageInvoiceType === 'maintenance'){ try{ if(window.initServicesTable) window.initServicesTable(); }catch(e){} } }catch(e){} });

// canonical serializer now lives in `static/js/line-items.core.js`.
// Do not redefine `window.serializeMaintenanceItems` here to avoid
// conflicting implementations; the core file provides the canonical
// implementation and should be loaded before other UI modules.

    // Direct binding: ensure any `#add-line-item` button calls `createItemRow`.
    document.addEventListener('DOMContentLoaded', function(){
        try{
            var btn = document.getElementById('add-line-item');
            if(!btn) return;
            try{ btn.style.cursor = 'pointer'; }catch(e){}
            // If another module already bound the Add Line Item handler,
            // avoid adding a second listener. Respect `data-addline-bound`
            // and the global `__addLineHandlerInstalled` flag.
            try{ if((btn.dataset && btn.dataset.addlineBound === '1') || window.__addLineHandlerInstalled) return; }catch(e){}
            try{ if(btn.dataset) btn.dataset.directBound = '1'; }catch(e){}
            try{ window.__addLineHandlerInstalled = true; }catch(e){}
            btn.addEventListener('click', function(e){
                try{ e.preventDefault(); }catch(err){}
                try{
                    var created = null;
                    try{ if(window.createItemRow) created = window.createItemRow(true); }catch(err){ created = null; }
                    if(!created){
                        try{ if(window.__lastCreateItemRowAt && (Date.now() - window.__lastCreateItemRowAt) < 220){ /* another handler already created a row; skip fallback */ created = null; } }catch(e){}
                    }
                    if(!created){
                        // simple safe fallback: append minimal row and init inventory autocomplete if available
                        try{
                            var body = document.getElementById('items-body') || document.getElementById('items-body-view') || document.querySelector('tbody#items-body, tbody#items-body-view, tbody');
                            if(body){
                                var tr = document.createElement('tr'); tr.className = 'item-row';
                                tr.innerHTML = '\n                <td style="padding:8px 12px;vertical-align:middle;">\n                    <input type="text" class="item-desc" value="" style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;box-sizing:border-box;min-height:36px;height:36px;line-height:20px;" />\n                    <input type="hidden" class="item-type-hidden" name="item_type[]" value="" />\n                </td>\n                <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-qty" value="1" min="0" step="1" style="width:90px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>\n                <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-rate" value="0.000" step="0.001" style="width:110px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>\n                <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-discount" value="0.00" step="0.001" style="width:60px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>\n                <td style="padding:8px 18px 8px 12px;text-align:right;"><input type="text" class="item-amount" value="0.000" readonly style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;text-align:right;" /></td>\n                <td style="padding:8px 12px;text-align:center;"><button type="button" class="remove-item-row remove-row" style="background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;">×</button></td>';
                                try{ body.appendChild(tr); }catch(e){ document.body.appendChild(tr); }
                                try{ tr.dataset.__createdAt = Date.now(); }catch(e){}
                                try{ var desc = tr.querySelector && tr.querySelector('.item-desc'); if(desc && typeof window.initInventoryAutocomplete === 'function') window.initInventoryAutocomplete(desc); }catch(e){}
                            }
                        }catch(e){ console.error('fallback create row failed', e); }
                    }
                    try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(err){}
                }catch(e){}
            }, false);
        }catch(e){}
    });

    // Delegated handler: when any autocomplete selection occurs on an item input,
    // ensure the row is converted to a service if appropriate.
    try{
        document.addEventListener('autocomplete:selected', function(ev){
            try{
                var input = ev && ev.target ? ev.target : null; var detail = ev && ev.detail ? ev.detail : null;
                if(!input) return;
                try{ if(input._svcHasLocalHandler) return; }catch(e){}
                var row = input.closest && input.closest('.item-row') ? input.closest('.item-row') : null;
                if(!row) return;
                try{
                    var it = detail || null;
                    var inferred = it && it.type ? it.type : (it && (it.track_stock===false || it.sale_price!==undefined) ? 'service' : null);
                    if(inferred === 'service'){
                        try{ if(!window._servicesTableInit && window.onServiceSelected) window.onServiceSelected(row, it); }catch(e){}
                    } else if(inferred === null){
                        // if the detail lacks type, but row.dataset was set by autocomplete
                        try{ if(row.dataset && row.dataset.type === 'service') { if(!window._servicesTableInit && window.onServiceSelected) window.onServiceSelected(row, it||{}); } }catch(e){}
                    }
                }catch(e){}
            }catch(e){}
        }, true);
    }catch(e){}

    try{
        document.addEventListener('service-selected', function(ev){
            try{
                var input = ev && ev.target ? ev.target : null; var detail = ev && ev.detail ? ev.detail : null;
                if(!input) return; 
                // if this input has its own local handler, skip global handling
                try{ if(input._svcHasLocalHandler) return; }catch(e){}
                var row = input.closest && input.closest('.item-row') ? input.closest('.item-row') : null; if(!row) return;
                try{ if(!window._servicesTableInit && window.onServiceSelected) window.onServiceSelected(row, detail); }catch(e){}
            }catch(e){}
        }, true);
    }catch(e){}

    // Ensure inventory autocomplete initialized for any pre-rendered item inputs
    (function(){
        function bindUnboundItems(){
            try{
                var inputs = document.querySelectorAll('.item-desc');
                if(!inputs) return;
                Array.prototype.forEach.call(inputs, function(input){
                    try{
                        if(!input._invBound){
                            if(typeof window.initInventoryAutocomplete === 'function'){
                                try{ window.initInventoryAutocomplete(input); }catch(e){}
                            }
                        }
                    }catch(e){}
                });
            }catch(e){}
        }
        // three safe hooks: DOM ready, fallback delayed scan, and final window.load
        try{ document.addEventListener('DOMContentLoaded', bindUnboundItems); }catch(e){}
        try{ setTimeout(bindUnboundItems, 500); }catch(e){}
        try{ window.addEventListener('load', bindUnboundItems); }catch(e){}
    })();

    // Normalize pre-rendered rows: ensure hidden item_type[], bind autocomplete, and try to resolve existing descriptions
    document.addEventListener('DOMContentLoaded', function(){
        try{
            document.querySelectorAll('#items-body .item-row').forEach(function(row){
                try{
                    // ensure hidden type input exists
                    if(!row.querySelector('.item-type-hidden')){
                        var h = document.createElement('input'); h.type = 'hidden'; h.name = 'item_type[]'; h.className = 'item-type-hidden'; h.value = 'inventory';
                        // try to place it in first cell
                        try{ var c = row.querySelector('td'); if(c) c.appendChild(h); else row.appendChild(h); }catch(e){ row.appendChild(h); }
                    }
                    // normalize any existing select or hidden inputs to expected values
                    try{
                        var sel = row.querySelector('.item-type');
                        var hh = row.querySelector('.item-type-hidden');
                        function normalizeAndApply(v){
                            if(!v) return 'inventory';
                            var lv = (v+'').toLowerCase();
                            if(lv === 'part' || lv === 'parts' || lv === 'inventory') return 'inventory';
                            if(lv === 'service' || lv === 'services') return 'service';
                            return lv;
                        }
                        if(sel && (typeof sel.value !== 'undefined')){
                            var mapped = normalizeAndApply(sel.value);
                            try{ if(hh) hh.value = (mapped === 'inventory' ? 'inventory' : 'service'); }catch(e){}
                            try{ row.dataset.type = mapped; }catch(e){}
                        } else if(hh && (typeof hh.value !== 'undefined')){
                            var mapped2 = normalizeAndApply(hh.value);
                            try{ if(mapped2 === 'part') mapped2 = 'inventory'; }catch(e){}
                            try{ row.dataset.type = mapped2; }catch(e){}
                        } else {
                            try{ if(!row.dataset.type) row.dataset.type = 'inventory'; }catch(e){}
                        }

                        // attach change handler for server-rendered select so switching type updates row dataset and autocomplete
                        try{
                            if(sel && !sel._typeBound){
                                sel._typeBound = true;
                                sel.addEventListener('change', function(){
                                    try{
                                        var val = sel.value; var mapped = normalizeAndApply(val);
                                        try{ if(hh) hh.value = (mapped === 'inventory' ? 'inventory' : 'service'); }catch(e){}
                                        try{ row.dataset.type = mapped; }catch(e){}
                                        var desc = row.querySelector('.item-desc');
                                        if(mapped === 'inventory'){
                                            try{ if(desc) desc.dataset.autocomplete = 'inventory'; }catch(e){}
                                            try{ if(typeof window.initInventoryAutocomplete === 'function' && desc) window.initInventoryAutocomplete(desc); }catch(e){}
                                        } else {
                                            try{ if(desc) desc.dataset.autocomplete = 'service'; }catch(e){}
                                            try{ if(typeof window.initServiceAutocomplete === 'function' && desc) window.initServiceAutocomplete(desc); }catch(e){}
                                        }
                                        try{ delete row.dataset.partId; delete row.dataset.inventoryId; delete row.dataset.serviceId; }catch(e){}
                                    }catch(e){}
                                });
                            }
                        }catch(e){}
                    }catch(e){}
                    // If user types a name and blurs without picking suggestion,
                    // attempt an exact-name lookup and convert to service if matched.
                    try{
                        if(desc){
                            desc.addEventListener('blur', function(){
                                try{
                                    var v = (desc.value||'').trim(); if(!v) return;
                                    // try to resolve via fetchInventory (merged services+parts)
                                    try{
                                        if(typeof window.fetchInventory === 'function'){
                                            window.fetchInventory(v).then(function(list){
                                                try{
                                                    if(!list || !list.length) return;
                                                    var match = list.find(function(it){ return (it.name||'').toLowerCase() === v.toLowerCase(); }) || null;
                                                    if(!match) return;
                                                    // if matched item is service, convert row
                                                    var inferred = match.type || ((match.track_stock) ? 'inventory' : 'service');
                                                    if(inferred === 'service'){
                                                        try{ if(!window._servicesTableInit && window.onServiceSelected) window.onServiceSelected(tr, match); }catch(e){}
                                                        try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                                                        try{ if(window.serializeMaintenanceItems) window.serializeMaintenanceItems(); }catch(e){}
                                                    } else {
                                                        // mark as inventory selection
                                                        try{ tr.dataset.inventoryId = match.id; tr.dataset.partId = match.id; }catch(e){}
                                                        try{ tr.dataset.type = 'inventory'; }catch(e){}
                                                        try{ var hh2 = tr.querySelector && tr.querySelector('.item-type-hidden'); if(hh2) hh2.value = 'inventory'; }catch(e){}
                                                        try{ if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                                                        try{ var descEl = tr.querySelector && tr.querySelector('.item-desc'); if(descEl && descEl.style) descEl.style.background = '#fff'; }catch(e){}
                                                    }
                                                }catch(e){}
                                            }).catch(function(){});
                                        }
                                    }catch(e){}
                                }catch(e){}
                            });
                        }
                    }catch(e){}

                    // bind autocomplete to desc
                    var desc = row.querySelector('.item-desc');
                    if(desc){
                        try{
                            // ensure description input has correct autocomplete marker for its row type
                            try{ if(row.dataset && row.dataset.type === 'service') desc.dataset.autocomplete = 'service'; else desc.dataset.autocomplete = 'inventory'; }catch(e){}
                        }catch(e){}
                        try{
                            try{ if(typeof window.initInventoryAutocomplete === 'function') window.initInventoryAutocomplete(desc); }catch(e){}
                            try{ if(typeof window.initServiceAutocomplete === 'function') window.initServiceAutocomplete(desc); }catch(e){}
                            try{ desc.addEventListener && desc.addEventListener('service-selected', function(ev){ try{ if(!window._servicesTableInit && window.onServiceSelected) window.onServiceSelected(row, ev.detail); }catch(e){} }); }catch(e){}
                        }catch(e){}
                        // if value present, try to lookup and annotate the row with ids/prices
                        var val = (desc.value||'').trim();
                        if(val){
                            try{
                                if(typeof window.fetchInventory === 'function'){
                                    window.fetchInventory(val).then(function(list){
                                        try{
                                            if(list && list.length){
                                                var match = list.find(function(it){ return (it.name||'').toLowerCase() === val.toLowerCase(); }) || list[0];
                                                if(match){
                                                    if(match.id) { row.dataset.partId = match.id; row.dataset.inventoryId = match.id; }
                                                    if(match.track_stock!==undefined) row.dataset.inventoryTrackStock = String(Boolean(match.track_stock));
                                                    var rateEl = row.querySelector('.item-rate'); if(rateEl && (match.sale_price!==undefined || match.price!==undefined)){
                                                        var p = (match.sale_price!==undefined?match.sale_price:(match.price!==undefined?match.price:null)); if(p!==null && p!==undefined) rateEl.value = parseFloat(p).toFixed(3);
                                                    }
                                                    try{ if(window.updateRowAmount) window.updateRowAmount(row); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                                                }
                                            }
                                        }catch(e){}
                                    }).catch(function(){});
                                }
                            }catch(e){}
                        }
                    }
                }catch(e){}
            });
        }catch(e){}
    });

    // Ensure form submission serializes items_json for invoice forms
    document.addEventListener('submit', function(e){
        try{
            var form = e.target;
            if(!form) return;
            // If this form is the invoice form or contains the items_json hidden input, serialize
            if(form.id === 'invoice-form' || (form.querySelector && form.querySelector('#items_json'))){
                try{ if(window.serializeMaintenanceItems) window.serializeMaintenanceItems(); }catch(err){}
            }
        }catch(err){}
    }, true);

    // Also ensure items_json is populated after all inits run
    try{
        function ensureSerializeOnReady(){ try{ if(window.serializeMaintenanceItems) window.serializeMaintenanceItems(); }catch(e){} }
        // run shortly after DOMContentLoaded in case inits run asynchronously
        document.addEventListener('DOMContentLoaded', function(){ try{ setTimeout(ensureSerializeOnReady, 120); }catch(e){} });
        // and again on window.load to catch late-loaded scripts
        window.addEventListener('load', function(){ try{ setTimeout(ensureSerializeOnReady, 80); }catch(e){} });
    }catch(e){}

    // Post-load normalization: ensure rows that match services are marked correctly
    try{
        document.addEventListener('DOMContentLoaded', function(){
            try{
                setTimeout(function(){
                    try{
                        var rows = Array.prototype.slice.call(document.querySelectorAll('#items-body .item-row'));
                        rows.forEach(function(r){
                            try{
                                var desc = r.querySelector && (r.querySelector('.item-desc')||r.querySelector('.service-desc'));
                                if(!desc) return;
                                var val = (desc.value||'').trim(); if(!val) return;
                                if(typeof window.fetchInventory === 'function'){
                                    window.fetchInventory(val).then(function(list){
                                        try{
                                            if(!list || !list.length) return;
                                            var match = list.find(function(it){ return (it.name||'').toLowerCase() === val.toLowerCase(); }) || list[0];
                                            if(!match) return;
                                            var inferred = match.type || ((match.track_stock) ? 'inventory' : 'service');
                                                                    // Treat matched item as inventory (purchase bills are inventory-only)
                                                                    try{ var hh2 = r.querySelector && r.querySelector('.item-type-hidden'); if(hh2) hh2.value = 'inventory'; }catch(e){}
                                                                    try{ r.dataset.type = 'inventory'; }catch(e){}
                                                                    try{ if(match.id) { r.dataset.partId = match.id; r.dataset.inventoryId = match.id; } }catch(e){}
                                                                    try{ if(match.track_stock!==undefined) r.dataset.inventoryTrackStock = String(Boolean(match.track_stock)); }catch(e){}
                                                                    try{
                                                                        var rateEl = r.querySelector && r.querySelector('.item-rate');
                                                                        var p = (match.sale_price!==undefined?match.sale_price:(match.price!==undefined?match.price:null));
                                                                        if(rateEl && p!==null && p!==undefined) rateEl.value = parseFloat(p).toFixed(3);
                                                                    }catch(e){}
                                                                    try{ var descEl = r.querySelector && r.querySelector('.item-desc'); if(descEl && descEl.style) descEl.style.background = '#fff'; }catch(e){}
                                                                    try{ if(window.updateRowAmount) window.updateRowAmount(r); }catch(e){}
                                                                    try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                                        }catch(e){}
                                    }).catch(function(){});
                                }
                            }catch(e){}
                        });
                    }catch(e){}
                }, 250);
            }catch(e){}
        });
    }catch(e){}

    // Initialize service inputs to use the merged inventory autocomplete
    // This wires `.service-desc` inputs to the unified fetch/autocomplete so
    // services appear without the legacy services-table.js.
    document.addEventListener('DOMContentLoaded', function(){
        try{
            // Attach merged autocomplete to any pre-rendered service inputs
            document.querySelectorAll('.service-desc, input.service-desc').forEach(function(input){
                try{
                    if(!input) return;
                    try{ if(input.dataset) input.dataset.autocomplete = 'service'; }catch(e){}
                    if(typeof window.initInventoryAutocomplete === 'function'){
                        try{ window.initInventoryAutocomplete(input); }catch(e){}
                    }
                }catch(e){}
            });

            // Make clicking a visible .service-label focus the hidden input and open suggestions
            document.querySelectorAll('.service-label').forEach(function(lbl){
    // Fallback: ensure any remaining unbound `.item-desc` inputs get initialized
    try{
        setTimeout(function(){
            try{
                document.querySelectorAll('#items-body .item-desc, .item-desc').forEach(function(el){
                    try{ if(!el._invBound && typeof window.initInventoryAutocomplete === 'function'){ window.initInventoryAutocomplete(el); } }catch(e){}
                });
            }catch(e){}
        }, 60);
    }catch(e){}
                try{
                    lbl.style.cursor = lbl.style.cursor || 'pointer';
                    lbl.addEventListener('click', function(){
                        try{
                                try{ if(window.__debugInventory) console.debug('[line-items.ui] service-label clicked', lbl); }catch(e){}
                            var row = lbl.closest && lbl.closest('tr'); if(!row) return;
                            // prefer a visible editable input; if only a hidden .service-desc exists, create a temporary editor
                            var hidden = row.querySelector('.service-desc');
                            try{ if(window.__debugInventory) console.debug('[line-items.ui] found hidden,visible inputs', !!hidden, !!row.querySelector('.item-desc')); }catch(e){}
                            var visible = row.querySelector('.item-desc');
                            var edit = null;
                            if(hidden && hidden.tagName === 'INPUT' && hidden.type === 'hidden'){
                                try{ if(window.__debugInventory) console.debug('[line-items.ui] creating temporary editor for hidden service-desc'); }catch(e){}
                                // create temporary visible input to edit service description
                                edit = document.createElement('input');
                                edit.type = 'text';
                                edit.className = 'service-desc-edit';
                                edit.value = (hidden.value || (lbl.textContent||'')).trim();
                                // copy basic styles from .service-label for consistency
                                try{ edit.style.width = '100%'; edit.style.padding = '6px'; edit.style.border = '1px solid #eee'; edit.style.borderRadius = '6px'; edit.style.boxSizing = 'border-box'; edit.style.minHeight = '36px'; edit.style.height = '36px'; }catch(e){}
                                // insert editor before the label and hide label
                                try{ lbl.parentNode.insertBefore(edit, lbl); lbl.style.display = 'none'; }catch(e){}
                                // when editor loses focus, restore label and copy value back to hidden
                                var cleanup = function(){ try{
                                    var v = (edit.value||'').trim();
                                    if(hidden) hidden.value = v;
                                    lbl.textContent = v || lbl.textContent;
                                    try{ if(edit && edit.parentNode) edit.parentNode.removeChild(edit); }catch(e){}
                                    try{ lbl.style.display = ''; }catch(e){}
                                }catch(err){}
                                };
                                edit.addEventListener('blur', function(){ setTimeout(cleanup, 120); });
                                edit.addEventListener('keydown', function(ev){ if(ev.key === 'Escape'){ try{ if(edit && edit.parentNode) edit.parentNode.removeChild(edit); lbl.style.display = ''; }catch(e){} } if(ev.key === 'Enter'){ try{ edit.blur(); }catch(e){} } });
                                // ensure autocomplete is initialized on the editor
                                try{ if(typeof window.initInventoryAutocomplete === 'function') window.initInventoryAutocomplete(edit); }catch(e){}
                                try{ edit.focus(); }catch(e){}
                                return;
                            }
                            // fallback: focus existing visible description input
                            var inp = visible || hidden || row.querySelector('.item-desc');
                            if(!inp) return;
                            try{ if(inp.focus) inp.focus(); }catch(e){}
                            if(typeof window.initInventoryAutocomplete === 'function'){
                                try{ window.initInventoryAutocomplete(inp); }catch(e){}
                            }
                        }catch(e){}
                    });
                }catch(e){}
            });
        }catch(e){}
    });
})();