(function(){
    // UI: DOM row creation and init
    window.createItemRow = function(typeOrFocus, focus){
        try{
            try{ if(window.__creatingItemRow) return null; window.__creatingItemRow = true; }catch(e){}
            try{ /* global short lock to avoid duplicate creates from multiple handlers */ if(window.__addRowInProgress){ try{ if(window.__debugLineItems) console.debug('[line-items] createItemRow ignored due to addRowInProgress', Date.now()); }catch(e){} return null; } window.__addRowInProgress = true; setTimeout(function(){ try{ window.__addRowInProgress = false; }catch(e){} }, 1200); }catch(e){}
            try{ if(window.__debugLineItems) console.debug('[line-items] createItemRow start', Date.now(), {typeOrFocus:typeOrFocus, focus:focus}); }catch(e){}
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
            // If this is the automatic initial row creation on a maintenance
            // page, do NOT short-circuit to legacy `createServiceRow`.
            // Prefer the unified item-row creation and initialization below.
            try{
                if(!itemType && focus === false && (window && window.ITEM_CONTEXT && String(window.ITEM_CONTEXT).trim() === 'maintenance')){
                    // fallthrough to unified factory below
                }
            }catch(e){}
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
            tr.innerHTML = `
                <td style="padding:8px 12px;vertical-align:middle;">
                    <input type="text" class="item-desc" value="" style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;box-sizing:border-box;min-height:36px;height:36px;line-height:20px;" data-bound="true" />
                    <input type="hidden" class="item-type-hidden" name="item_type[]" value="" />
                </td>
                <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-qty" value="1" min="0" step="1" style="width:90px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>
                <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-rate" value="0.000" step="0.001" style="width:110px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>
                <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-discount" value="0.00" step="0.001" style="width:60px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>
                <td style="padding:8px 12px;text-align:right;"><input type="text" class="item-amount" value="0.000" readonly style="width:calc(100% - 12px);padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;text-align:right;box-sizing:border-box;" /></td>
                <td style="padding:8px 12px;text-align:center;"><button type="button" class="remove-item-row remove-row" style="background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;">×</button></td>
            `;
            try{ body.appendChild(tr); }catch(e){ try{ document.body.appendChild(tr); }catch(err){} }
            try{ window.__invBlockAutoOpenUntil = Date.now() + 400; }catch(e){}
            // mark creation time early so other initializers can detect "new" rows
            try{ tr.dataset.__createdAt = Date.now(); }catch(e){}
            try{
                // ensure hidden input and dataset reflect requested item type (only if explicitly provided)
                try{ if(itemType){ tr.setAttribute('data-type', itemType); tr.dataset.type = itemType; } }catch(e){}
                try{ var hh_init = tr.querySelector('.item-type-hidden'); if(hh_init && itemType) hh_init.value = itemType; }catch(e){}
            }catch(e){}
                try {
                    var desc = tr.querySelector('.item-desc');
                    if (desc) {
                        try{
                            var allowed = (typeof window.getAllowedTypes === 'function') ? window.getAllowedTypes() : ['inventory'];
                        }catch(e){ var allowed = ['inventory']; }
                        // If caller explicitly requested inventory, or the page only allows inventory,
                        // bind inventory autocomplete and mark row as inventory. Otherwise leave row untyped
                        // so merged suggestions (inventory+service) are available.
                        try{
                            if(itemType === 'inventory' || (allowed.length === 1 && allowed[0] === 'inventory')){
                                try{ desc.dataset.autocomplete = 'inventory'; }catch(e){}
                                try { if (typeof window.initInventoryRow === 'function') window.initInventoryRow(tr); else if (typeof window.initInventoryAutocomplete === 'function') window.initInventoryAutocomplete(desc); }catch(e){}
                                try{ desc.addEventListener && desc.addEventListener('service-selected', function(ev){ try{ if(!window._servicesTableInit && window.onServiceSelected) window.onServiceSelected(tr, ev.detail); }catch(e){} }); }catch(e){}
                                try{ var hh_bind = tr.querySelector('.item-type-hidden'); if(hh_bind) hh_bind.value = 'inventory'; }catch(e){}
                                try{ tr.dataset.type = 'inventory'; }catch(e){}
                            } else {
                                // Mixed mode: initialize inventory binding (so parts are suggested),
                                // but do not force the row type to inventory so services remain available.
                                try { if (typeof window.initInventoryRow === 'function') window.initInventoryRow(tr); else if (typeof window.initInventoryAutocomplete === 'function') window.initInventoryAutocomplete(desc); }catch(e){}
                                // Also bind service autocomplete so this input can show services too
                                try{ if (typeof window.initServiceAutocomplete === 'function') window.initServiceAutocomplete(desc); }catch(e){}
                                try{ desc.addEventListener && desc.addEventListener('service-selected', function(ev){ try{ if(!window._servicesTableInit && window.onServiceSelected) window.onServiceSelected(tr, ev.detail); }catch(e){} }); }catch(e){}
                            }
                        }catch(e){}
                    }
                } catch(e) {}
                var qty = tr.querySelector('.item-qty'); var rate = tr.querySelector('.item-rate'); var disc = tr.querySelector('.item-discount');
                qty.addEventListener('input', function(){ try{ if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                rate.addEventListener('input', function(){ try{ if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                disc.addEventListener('input', function(){ try{ if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                if(focus!==false) desc.focus();
            }catch(e){}
            try{
                try{ tr.dataset.__createdAt = Date.now(); }catch(e){}
                try{
                    var __s = (new Error().stack||'').split('\n')[1] || '';
                    tr.dataset.__createdBy = __s.trim();
                }catch(e){}

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
                                    // treat empty descriptions as a special blank key so
                                    // rapid duplicate empty rows are also de-duped
                                    if(!key) {
                                        key = '__BLANK__' + (r.dataset && r.dataset.type ? (':' + r.dataset.type) : '');
                                    }
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
                    // Temporarily disable dedupe timers while debugging duplicate
                    // creation sources. Re-enable these timers once initialization

                        // Remove any legacy service rows found anywhere in the document
                        // (not relying on `#services-body`) and create a unified first
                        // `item-row` inside `#items-body` if needed.
                        try{
                            function removeLegacyServiceRowsAndCreateUnified(){
                                try{
                                    if(window.__legacyRowsRemoved) return;
                                    var ib = document.getElementById('items-body');
                                    var all = Array.prototype.slice.call(document.querySelectorAll('tr')) || [];
                                    var legacyRows = all.filter(function(r){ try{ if(!r) return false; if(r.closest && r.closest('#items-body')) return false; return Boolean(r.querySelector('.service-desc') || r.querySelector('.service-qty') || r.classList.contains('service-row')); }catch(e){return false;} });
                                    if(!legacyRows || legacyRows.length === 0) return;
                                    // Remove legacy rows
                                    legacyRows.forEach(function(r){ try{ if(r && r.parentNode) r.parentNode.removeChild(r); }catch(e){} });
                                    try{ console.log('[line-items] removed legacy service rows:', legacyRows.length); }catch(e){}
                                    window.__legacyRowsRemoved = true;
                                    // Create a unified initial item row (items-body) if the unified factory exists
                                    try{
                                        if(typeof window.createItemRow === 'function' && ib){
                                            try{ window.createItemRow(false); }catch(e){}
                                            try{ console.log('[line-items] created unified initial item row'); }catch(e){}
                                        }
                                    }catch(e){}
                                }catch(e){}
                            }
                            try{ document.addEventListener('DOMContentLoaded', removeLegacyServiceRowsAndCreateUnified); }catch(e){}
                            try{ window.addEventListener('load', removeLegacyServiceRowsAndCreateUnified); }catch(e){}
                            try{ setTimeout(removeLegacyServiceRowsAndCreateUnified, 400); }catch(e){}
                        }catch(e){}

    // Ensure customer-search has basic bindings if the template fallback didn't run
    try{
        function __bindCustomerFallback(){
            try{
                var el = document.getElementById('customer-search');
                if(!el || el._custFallbackBound) return;
                try{ el.readOnly = false; el.removeAttribute && el.removeAttribute('readonly'); el.disabled = false; el.style.pointerEvents = 'auto'; }catch(e){}
                var handler = function(ev){ try{ ev && ev.stopPropagation && ev.stopPropagation(); if(window.showInlineSuggestions) return window.showInlineSuggestions(''); if(window.toggleCustomerSuggestions) return window.toggleCustomerSuggestions(); }catch(e){} };
                try{ el.addEventListener('click', handler); el.addEventListener('focus', handler); }catch(e){}
                try{ el.addEventListener('input', function(ev){ try{ if(window.showInlineSuggestions) window.showInlineSuggestions(ev.target && ev.target.value ? ev.target.value : ''); }catch(e){} }); }catch(e){}
                el._custFallbackBound = true;
                var btn = document.getElementById('customer-search-btn');
                if(btn && !btn._custFallback){
                    try{ btn.addEventListener('click', function(ev){ try{ ev && ev.preventDefault && ev.preventDefault(); if(window.openCustomerModal) window.openCustomerModal(el?el.value:''); else { var bd = document.getElementById('customer-modal-backdrop'); if(bd){ bd.style.display='flex'; var minp = document.getElementById('modal-customer-query'); if(minp){ minp.value = (el && el.value) || ''; minp.focus(); } try{ if(typeof performModalSearch === 'function') performModalSearch(minp?minp.value:''); }catch(e){} } } }catch(e){} }); }catch(e){}
                    btn._custFallback = true;
                }
            }catch(e){}
        }
        try{ document.addEventListener('DOMContentLoaded', __bindCustomerFallback); }catch(e){}
        try{ window.addEventListener('load', __bindCustomerFallback); }catch(e){}
        try{ setTimeout(__bindCustomerFallback, 600); }catch(e){}
    }catch(e){}
    // Also observe DOM mutations to re-bind if the input is re-rendered dynamically
    try{
        (function(){
            var mo = null;
            function startObs(){
                try{
                    if(typeof MutationObserver === 'undefined') return;
                    if(mo) return;
                    mo = new MutationObserver(function(muts){
                        try{
                            muts.forEach(function(m){
                                try{
                                    if(!m.addedNodes) return;
                                    for(var i=0;i<m.addedNodes.length;i++){
                                        var n = m.addedNodes[i];
                                        try{
                                            if(n && n.querySelector && n.querySelector('#customer-search')){ __bindCustomerFallback(); return; }
                                            if(n && n.id === 'customer-search'){ __bindCustomerFallback(); return; }
                                        }catch(e){}
                                    }
                                }catch(e){}
                            });
                        }catch(e){}
                    });
                    try{ mo.observe(document.body, {childList:true, subtree:true}); }catch(e){}
                }catch(e){}
            }
            try{ if(document.readyState === 'complete' || document.readyState === 'interactive') startObs(); else document.addEventListener('DOMContentLoaded', startObs); }catch(e){}
            try{ setTimeout(startObs, 1200); }catch(e){}
        })();
    }catch(e){}

                            // More robust startup: in case other scripts re-insert legacy rows or items-body
                            // is rendered late, retry a few times to ensure unified rows are present.
                            try{
                                function robustEnsureUnifiedRows(){
                                    try{
                                        var attempts = 0;
                                        var maxAttempts = 8;
                                        var iv = setInterval(function(){
                                            try{
                                                attempts++;
                                                var ib = document.getElementById('items-body');
                                                // remove any legacy rows found outside of #items-body
                                                try{
                                                    var all = Array.prototype.slice.call(document.querySelectorAll('tr')) || [];
                                                    var legacy = all.filter(function(r){ try{ if(!r) return false; if(r.closest && r.closest('#items-body')) return false; return Boolean(r.querySelector('.service-desc') || r.querySelector('.service-qty') || r.classList.contains('service-row')); }catch(e){return false;} });
                                                    if(legacy && legacy.length){
                                                        legacy.forEach(function(r){ try{ r.parentNode && r.parentNode.removeChild(r); }catch(e){} });
                                                        try{ console.log('[line-items] robust: removed legacy service rows', legacy.length); }catch(e){}
                                                    }
                                                }catch(e){}
                                                // ensure at least one item-row exists
                                                var hasItem = ib && ib.querySelector && ib.querySelector('.item-row');
                                                if(!hasItem && typeof window.createItemRow === 'function' && ib){
                                                    try{ window.createItemRow(false); }catch(e){}
                                                    try{ console.log('[line-items] robust: created unified item-row'); }catch(e){}
                                                }
                                                // if items exist and no legacy rows remain, stop
                                                var stillLegacy = Array.prototype.slice.call(document.querySelectorAll('tr')).filter(function(r){ try{ return (r.closest && !r.closest('#items-body')) && (r.querySelector('.service-desc') || r.querySelector('.service-qty') || r.classList.contains('service-row')); }catch(e){return false;} }).length || 0;
                                                var itemsNow = (document.querySelectorAll && document.querySelectorAll('#items-body .item-row').length) || 0;
                                                if((itemsNow>0) && (stillLegacy===0)){
                                                    try{ clearInterval(iv); }catch(e){}
                                                    return;
                                                }
                                                if(attempts >= maxAttempts){ try{ clearInterval(iv); }catch(e){} }
                                            }catch(e){}
                                        }, 180);
                                    }catch(e){}
                                }
                                try{ window.addEventListener && window.addEventListener('load', robustEnsureUnifiedRows); }catch(e){}
                                try{ setTimeout(robustEnsureUnifiedRows, 600); }catch(e){}
                            }catch(e){}
                    // is stable.
                    // try{ setTimeout(runDedupe, 80); }catch(e){}
                    // try{ setTimeout(runDedupe, 700); }catch(e){}
                    // try{
                    //     setTimeout(function(){
                    //         try{ runDedupe(); }catch(e){}
                    //     }, 1500);
                    // }catch(e){}
                }catch(e){}
            }catch(e){}
            try{ window.__creatingItemRow = false; }catch(e){}
            return tr;
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
            // Append service rows as unified `item-row` in `#items-body` so they
            // participate in the unified totals/serialization flow.
            var body = document.getElementById('items-body') || document.body;
            var tr = document.createElement('tr'); tr.className='item-row'; try{ tr.setAttribute('data-type','service'); tr.dataset.type = 'service'; }catch(e){}
            tr.innerHTML = `
        <td style="padding:8px 12px;vertical-align:middle;">
              <input type="text" class="service-desc item-desc" value="" style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;box-sizing:border-box;min-height:36px;height:36px;line-height:20px;background:#fff;" />
              <input type="hidden" class="item-type-hidden" name="item_type[]" value="service" />
        </td>
        <td style="padding:8px 12px;text-align:center;"><input type="number" class="service-qty item-qty" step="1" value="1" style="width:90px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;"/></td>
        <td style="padding:8px 12px;text-align:center;"><input type="number" class="service-rate item-rate" step="0.001" value="0.000" style="width:110px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;"/></td>
        <td style="padding:8px 12px;text-align:center;"><input type="number" class="service-discount item-discount" step="0.01" value="0.00" style="width:60px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;"/></td>
        <td style="padding:8px 12px;text-align:right;"><input type="text" class="service-amount item-amount" value="0.000" readonly style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;text-align:right;"/></td>
        <td style="padding:8px 12px;text-align:center;"><button type="button" class="remove-service-row remove-row" style="background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;">×</button></td>`;
            if(body) body.appendChild(tr);
            try{
                var svcInput = tr.querySelector && tr.querySelector('.service-desc');
                if(svcInput){
                    try{ if(svcInput.dataset) svcInput.dataset.autocomplete = 'service'; }catch(e){}
                    try{ if(!svcInput._svcBound) svcInput._svcBound = true; }catch(e){}
                    try{ if(typeof window.initServiceAutocomplete === 'function') window.initServiceAutocomplete(svcInput); }catch(e){}
                }
            }catch(e){}
            return tr; }catch(e){ console.error(e); return null; } };

    // Aggressive normalization: replace any pre-rendered rows inside #services-body
    // with canonical rows created by `createServiceRow`, preserving visible values.
    // This strips legacy event listeners and ensures consistent classnames/handlers.
    (function normalizeServicesBody(){
        try{
            function run(){
                try{
                    var all = Array.prototype.slice.call(document.querySelectorAll('tr')) || [];
                    var rows = all.filter(function(orig){ try{ if(!orig) return false; if(orig.closest && orig.closest('#items-body')) return false; return Boolean(orig.querySelector('.service-desc') || orig.querySelector('.service-qty') || orig.classList.contains('service-row')); }catch(e){return false;} });
                    rows.forEach(function(orig){ try{
                        if(!orig) return;
                        // Skip rows already normalized
                        if(orig.dataset && orig.dataset.__normalized === '1') return;
                        // collect visible values
                        var desc = orig.querySelector && (orig.querySelector('.service-desc') || orig.querySelector('.item-desc'));
                        var qty = orig.querySelector && (orig.querySelector('.service-qty') || orig.querySelector('.item-qty'));
                        var rate = orig.querySelector && (orig.querySelector('.service-rate') || orig.querySelector('.item-rate'));
                        var disc = orig.querySelector && (orig.querySelector('.service-discount') || orig.querySelector('.item-discount'));
                        var amt = orig.querySelector && (orig.querySelector('.service-amount') || orig.querySelector('.item-amount'));
                        var vals = { description: desc ? (desc.value||'') : '', qty: qty ? (qty.value||'1') : '1', rate: rate ? (rate.value||'0.000') : '0.000', discount: disc ? (disc.value||'0.00') : '0.00', amount: amt ? (amt.value||'0.000') : '0.000' };
                        // create canonical row
                        var newRow = null;
                        try{ newRow = window.createServiceRow(false); }catch(e){}
                        if(!newRow) return;
                        try{
                            var d = newRow.querySelector('.service-desc') || newRow.querySelector('.item-desc'); if(d) d.value = vals.description;
                            var qEl = newRow.querySelector('.service-qty') || newRow.querySelector('.item-qty'); if(qEl) qEl.value = vals.qty;
                            var rEl = newRow.querySelector('.service-rate') || newRow.querySelector('.item-rate'); if(rEl) rEl.value = parseFloat(vals.rate||0).toFixed(3);
                            var diEl = newRow.querySelector('.service-discount') || newRow.querySelector('.item-discount'); if(diEl) diEl.value = parseFloat(vals.discount||0).toFixed(3);
                            var aEl = newRow.querySelector('.service-amount') || newRow.querySelector('.item-amount'); if(aEl) aEl.value = parseFloat(vals.amount||0).toFixed(3);
                            try{ newRow.dataset.__normalized = '1'; }catch(e){}
                        }catch(e){}
                            // remove original legacy row (newRow was appended into #items-body)
                            try{ orig.parentNode && orig.parentNode.removeChild(orig); }catch(e){}
                    }catch(e){} });
                }catch(e){}
            }
            try{ document.addEventListener('DOMContentLoaded', run); }catch(e){}
            try{ setTimeout(run, 300); }catch(e){}
        }catch(e){}

// Delegate customer-search events at document level so replacements still work
try{
    document.addEventListener('input', function(e){
        try{
            var t = e.target;
            if(!t) return;
            if(t.id === 'customer-search'){
                try{
                    if(window.showInlineSuggestions){ window.showInlineSuggestions(t.value||''); return; }
                    try{ window.__suppressClearSuggestions = true; }catch(e){}
                    // fallback: perform simple fetch + inline render when template helpers are absent
                    (function(q, inputEl){
                        try{
                            q = (q||'').trim();
                            var fetcher = (typeof window.fetchJson === 'function') ? window.fetchJson : function(url){ return fetch(url, {credentials:'same-origin'}).then(function(r){ return r.json(); }); };
                            fetcher('/clients/search/?q=' + encodeURIComponent(q)).then(function(data){
                                try{ console.debug && console.debug('customer fallback fetched', data); var results = (data && data.results) ? data.results : [];
                                    // render simple inline box
                                    try{ var live = document.getElementById('customer-search'); var parent = live && live.parentNode ? live.parentNode : document.body; 
                                        // remove any existing fallback box
                                        var old = parent.querySelector && parent.querySelector('[data-cust-fallback]'); if(old && old.parentNode) old.parentNode.removeChild(old);
                                        if(!results || results.length===0) return;
                                        var box = document.createElement('div'); box.setAttribute('data-cust-fallback','1'); box.style.position='absolute'; box.style.zIndex=600; box.style.background='#fff'; box.style.border='1px solid #ddd'; box.style.width='100%'; box.style.maxHeight='240px'; box.style.overflow='auto'; box.style.top = (live ? (live.offsetHeight + 'px') : '100%'); box.style.left='0'; box.style.boxSizing='border-box';
                                        results.forEach(function(item){ try{ var row = document.createElement('div'); row.style.padding='8px'; row.style.cursor='pointer'; row.style.borderBottom='1px solid #f3f3f3'; row.textContent = item.name + (item.phone ? (' — ' + item.phone) : ''); row.addEventListener('click', function(ev){ ev && ev.stopPropagation && ev.stopPropagation(); try{ var idCandidate = item.id || item.pk || item.client_id || item.clientId || item._id || ''; try{ var sel = document.getElementById('selected_client_id'); if(sel) sel.value = idCandidate; }catch(e){} try{ window.currentCustomerId = idCandidate; }catch(e){} try{ console.debug && console.debug('customer selected (fallback):', idCandidate, item); }catch(e){} try{ var live2 = document.getElementById('customer-search'); if(live2) live2.value = item.name; }catch(e){} try{ var sp = document.getElementById('selected-plate'); if(sp) sp.textContent = (item.plates && item.plates.length) ? item.plates.join(', ') : ''; }catch(e){} try{ if(typeof window.loadCustomerVehicles === 'function') window.loadCustomerVehicles(idCandidate); }catch(e){} }catch(e){} try{ if(box && box.parentNode) box.parentNode.removeChild(box); }catch(e){} }); box.appendChild(row);}catch(e){} });
                                        try{ parent.style.position = parent.style.position || 'relative'; parent.appendChild(box); }catch(e){}
                                    }catch(e){}
                                }catch(e){}
                            }).catch(function(){/* ignore */});
                        }catch(e){}
                    })(t.value||'', t);
                }catch(err){}
            }
        }catch(err){}
    }, true);

    document.addEventListener('click', function(e){
        try{
            var t = e.target;
            if(!t) return;
            // clicks on the customer input -> open inline suggestions
            if(t.id === 'customer-search' || (t.closest && t.closest('#customer-search'))){
                try{ if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(err){}
                return;
            }
            // clicks on magnifier button -> open modal
            var mag = t.closest && t.closest('#customer-search-btn');
            if(mag){ try{ if(window.openCustomerModal) window.openCustomerModal((document.getElementById('customer-search')||{}).value||''); }catch(err){} }
        }catch(err){}
    }, true);

    // mousedown listener (capture) — runs earlier than click and helps when other handlers
    // or CSS prevent default on click. Ensure input receives focus and suggestions open.
    document.addEventListener('mousedown', function(e){
        try{
            var t = e.target;
            if(!t) return;
            if(t.id === 'customer-search' || (t.closest && t.closest('#customer-search'))){
                try{ var inp = document.getElementById('customer-search'); if(inp && typeof inp.focus === 'function') inp.focus(); if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(err){}
                return;
            }
            var mag = t.closest && t.closest('#customer-search-btn');
            if(mag){ try{ if(window.openCustomerModal) window.openCustomerModal((document.getElementById('customer-search')||{}).value||''); }catch(err){} }
        }catch(err){}
    }, true);

    document.addEventListener('keydown', function(e){
        try{
            var t = e.target;
            if(!t) return;
            if(t.id === 'customer-search'){
                if(e.key === 'Enter' || e.key === ' '){
                    try{ e.preventDefault(); if(window.toggleCustomerSuggestions) window.toggleCustomerSuggestions(); else if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(err){}
                }
            }
        }catch(err){}
    }, true);
}catch(e){}
    })();

    // bind add buttons (items + services)
    (function(){
        function bindAddLineButton(){
            try{
                var btn = document.querySelector('#add-line-item') || document.querySelector('button.add-line-item') || document.querySelector('button[id*="add"], a[id*="add"], button[id*="add-row"], #add-row');
                if(!btn) return;
                try{ if(btn.dataset && btn.dataset.addlineBound === '1') return; }catch(e){}
                try{ btn.dataset.addlineBound = '1'; }catch(e){}
                try{ btn.style.cursor = 'pointer'; }catch(e){}
                try{ btn.addEventListener('click', function(e){ try{ e.preventDefault(); }catch(err){} try{ if(window.createItemRow) window.createItemRow(true); }catch(err){} try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(err){} }, false); }catch(e){}
                try{ window.__addLineHandlerInstalled = true; }catch(e){}
            }catch(e){}
        }

        // schedule binding attempts to catch buttons that are rendered later
        try{ document.addEventListener('DOMContentLoaded', bindAddLineButton); }catch(e){}
        try{ setTimeout(bindAddLineButton, 300); }catch(e){}
        try{ setTimeout(bindAddLineButton, 1200); }catch(e){}

        // expose for manual invocation/tests
        try{ window.bindAddLineButton = bindAddLineButton; }catch(e){}

        // Watch for late-inserted buttons (frameworks/templates that render after initial load)
        try{
            if(window.MutationObserver){
                var mo = new MutationObserver(function(muts){ try{ for(var i=0;i<muts.length;i++){ var added = muts[i].addedNodes || []; for(var j=0;j<added.length;j++){ try{ var n = added[j]; if(n && n.querySelector){ if(n.querySelector('#add-line-item, .add-line-item, #add-row')){ try{ bindAddLineButton(); }catch(e){} } } else if(n && n.id && (n.id === 'add-line-item' || n.id === 'add-row')){ try{ bindAddLineButton(); }catch(e){} } }catch(e){} } } }catch(e){} });
                try{ mo.observe(document.body, {childList:true, subtree:true}); }catch(e){}
            }
        }catch(e){}

        window.initItemsTable = window.initItemsTable || function(){
            try{ if(window.__itemsTableInitialized) return; window.__itemsTableInitialized = true; }catch(e){}
            try{ bindAddLineButton(); }catch(e){}
            try{ if(!window.__initialRowCreated) window.__initialRowCreated = true; }catch(e){}
            try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
        };
    })();

        // Fallback: delegated click handler to catch any "Add Line Item" button
        // even if its listeners were removed or the element was re-rendered.
        document.addEventListener('click', function(e){
            try{
                var t = e.target;
                var btn = t && t.closest ? t.closest('button, a') : null;
                if(!btn) return;
                    // allow delegated handler to run even if a binding flag exists;
                    // createItemRow is debounce-protected so duplicates are safe.
                var txt = (btn.textContent||'').trim();
                // always allow delegated handling for Add Line Item clicks
                if(btn.id === 'add-line-item' || btn.classList.contains('add-line-item') || txt.indexOf('Add Line Item') !== -1){
                    try{ e.preventDefault(); }catch(err){}
                    try{ /* prevent other click handlers (target/bubble) from also running */ e.stopImmediatePropagation(); }catch(err){}
                    try{ try{ window.__addLineHandlerInstalled = true; }catch(e){} try{ if(window.__debugLineItems) console.debug('[line-items] delegated click -> createItemRow', Date.now()); }catch(e){} if(window.createItemRow) window.createItemRow(true); }catch(err){}
                    try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(err){}
                }
            }catch(err){}
        }, true);

    window.initServicesTable = window.initServicesTable || function(){
        try{
            window._servicesTableInit = true;
            // bind to either legacy 'add-service' or template 'add-service-row'
            var btn = document.getElementById('add-service') || document.getElementById('add-service-row');
            if(btn && btn.dataset.bound !== '1'){
                btn.dataset.bound = '1';
                btn.addEventListener('click', function(e){
                    try{ e.preventDefault(); e.stopPropagation(); }catch(err){}
                    try{ if(btn.dataset.lock === '1') return; btn.dataset.lock = '1'; }catch(e){}
                    try{ window._addingService = true; createServiceRow(true); }catch(err){}
                    finally{ setTimeout(function(){ try{ window._addingService = false; }catch(e){} try{ delete btn.dataset.lock; }catch(e){} }, 300); }
                }, true);
            }
            // ensure existing service rows are normalized (now in #items-body)
            try{ document.querySelectorAll('#items-body .service-row, #items-body .item-row[data-type="service"]').forEach(function(r){ try{ if(window.updateServiceRowAmount) window.updateServiceRowAmount(r); }catch(e){} }); }catch(e){}
            // If we're on a maintenance page and there are no service rows, create one
            try{
                var isMaint = (window && window.ITEM_CONTEXT && String(window.ITEM_CONTEXT).trim() === 'maintenance') || window.__isMaintenancePage;
                if(isMaint){
                    var hasSvc = (document.querySelectorAll('#items-body .service-row').length || document.querySelectorAll('#items-body .item-row[data-type="service"]').length) > 0;
                    if(!hasSvc){ try{ createServiceRow(false); }catch(e){} }
                }
            }catch(e){}
        }catch(e){ console.error('initServicesTable failed', e); }
    };

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

    // Defer calling `initItemsTable` until the core signals readiness to avoid
    // race conditions where UI runs before core has initialized.
    try{
        function safeInitItemsTable(){
            try{
                if(window.__lineItemsReady){
                    try{ if(window.initItemsTable) window.initItemsTable(); }catch(e){}
                    try{ var __pageInvoiceType = (document && document.body && document.body.dataset && document.body.dataset.invoiceType) ? document.body.dataset.invoiceType : null; if(__pageInvoiceType === 'maintenance'){ try{ if(window.initServicesTable) window.initServicesTable(); }catch(e){} } }catch(e){}
                    return;
                }
            }catch(e){}
            // listen once for readiness; also poll as a fallback
            try{ if(window.addEventListener){ window.addEventListener('line-items-ready', function onLI(){ try{ if(window.initItemsTable) window.initItemsTable(); }catch(e){} try{ var __pageInvoiceType = (document && document.body && document.body.dataset && document.body.dataset.invoiceType) ? document.body.dataset.invoiceType : null; if(__pageInvoiceType === 'maintenance'){ try{ if(window.initServicesTable) window.initServicesTable(); }catch(e){} } }catch(e){} }); } }catch(e){}
            try{ setTimeout(safeInitItemsTable, 120); }catch(e){}
        }
        try{ document.addEventListener('DOMContentLoaded', safeInitItemsTable); }catch(e){}
        try{ setTimeout(safeInitItemsTable, 200); }catch(e){}
    }catch(e){}

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
            try{ if(btn.dataset) btn.dataset.addlineBound = '1'; }catch(e){}
            try{ window.__addLineHandlerInstalled = true; }catch(e){}
                btn.addEventListener('click', function(e){
                    try{ e.preventDefault(); }catch(err){}
                    try{
                        if(window.createItemRow) window.createItemRow(false);
                        if(window.recomputeTotals) window.recomputeTotals();
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
                        // Ensure the canonical initializer runs for any input that
                        // hasn't been initialized yet. Use `_invInit` as the
                        // authoritative guard so re-initialization is safe.
                        try{
                            if(typeof window.initInventoryAutocomplete === 'function' && !input._invInit){
                                try{ window.initInventoryAutocomplete(input); }catch(e){}
                            }
                        }catch(e){}
                        // Ensure focus/click open suggestions even if user doesn't type
                        try{
                            if(!input._invFocusBound){
                                input.addEventListener('focus', function(){ try{ input.dispatchEvent(new Event('input',{bubbles:true})); }catch(e){} });
                                input.addEventListener('click', function(){ try{ input.dispatchEvent(new Event('input',{bubbles:true})); }catch(e){} });
                                input._invFocusBound = true;
                            }
                        }catch(e){}
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
                        try{ var c = row.querySelector('td'); if(c) c.appendChild(h); else row.appendChild(h); }catch(e){ row.appendChild(h); }
                    }
                    try{
                        var desc = row.querySelector && (row.querySelector('.item-desc')||row.querySelector('.service-desc'));
                        if(!desc) return;
                        var val = (desc.value||'').trim();
                        if(!val) return;

                        if(typeof window.fetchInventory === 'function'){
                            window.fetchInventory(val).then(function(list){
                                try{
                                    if(!list || !list.length) return;
                                    var match = list.find(function(it){ return (it.name||'').toLowerCase() === val.toLowerCase(); }) || list[0];

                                    if(!match) return;

                                    var inferred = match.type || ((match.track_stock) ? 'inventory' : 'service');

                                    try{ var hh2 = row.querySelector('.item-type-hidden'); if(hh2) hh2.value = 'inventory'; }catch(e){}

                                    try{ row.dataset.type = 'inventory'; }catch(e){}

                                    try{ if(match.id) { row.dataset.partId = match.id; row.dataset.inventoryId = match.id; } }catch(e){}

                                    try{
                                        var rateEl = row.querySelector && row.querySelector('.item-rate');
                                        var p = (match.sale_price!==undefined ? match.sale_price : (match.price!==undefined ? match.price : null));

                                        if(rateEl && p!==null && p!==undefined){
                                            rateEl.value = parseFloat(p).toFixed(3);
                                        }
                                    }catch(e){}

                                    try{
                                        if(window.updateRowAmount) window.updateRowAmount(row);
                                        if(window.recomputeTotals) window.recomputeTotals();
                                    }catch(e){}
                                }catch(e){}
                            }).catch(function(){});
                        }
                    }catch(e){}
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
                    // Prefer service-specific initializer when available
                    if(typeof window.initServiceAutocomplete === 'function'){
                        try{ window.initServiceAutocomplete(input); }catch(e){}
                    } else if(typeof window.initInventoryAutocomplete === 'function'){
                        try{ window.initInventoryAutocomplete(input); }catch(e){}
                    }
                }catch(e){}
            });

            // Make clicking a visible .service-label focus the hidden input and open suggestions
            document.querySelectorAll('.service-label').forEach(function(lbl){
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
                                // ensure autocomplete is initialized on the editor (service-specific)
                                try{ if(typeof window.initServiceAutocomplete === 'function') window.initServiceAutocomplete(edit); else if(typeof window.initInventoryAutocomplete === 'function') window.initInventoryAutocomplete(edit); }catch(e){}
                                try{ edit.focus(); }catch(e){}
                                return;
                            }
                            // fallback: focus existing visible description input
                            var inp = visible || hidden || row.querySelector('.item-desc');
                            if(!inp) return;
                            try{ if(inp.focus) inp.focus(); }catch(e){}
                            // Initialize the appropriate autocomplete for this input
                            try{
                                var isService = false;
                                try{ isService = (row && row.dataset && row.dataset.type === 'service') || (inp.classList && inp.classList.contains('service-desc')); }catch(e){}
                                if(isService && typeof window.initServiceAutocomplete === 'function'){
                                    try{ window.initServiceAutocomplete(inp); }catch(e){}
                                } else if(typeof window.initInventoryAutocomplete === 'function'){
                                    try{ window.initInventoryAutocomplete(inp); }catch(e){}
                                }
                            }catch(e){}
                        }catch(e){}
                    });
                }catch(e){}
            });

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
            }catch(e){}
            });
})();

(function(){
    function ensureRecompute(){
        try{
            if(typeof window.recomputeTotals === 'function'){
                try{ window.recomputeTotals(); }catch(e){}
            } else {
                setTimeout(ensureRecompute, 50);
            }
        }catch(e){}
    }
    try{ window.addEventListener && window.addEventListener('core-ready', function(){ try{ if(typeof window.recomputeTotals === 'function') window.recomputeTotals(); else setTimeout(ensureRecompute,50); }catch(e){} }); }catch(e){}
    try{ ensureRecompute(); }catch(e){}
})();

// Delegate customer-search events at document level so replacements still work
try{
    document.addEventListener('input', function(e){
        try{
            var t = e.target;
            if(!t) return;
            if(t.id === 'customer-search'){
                try{ if(window.showInlineSuggestions) window.showInlineSuggestions(t.value||''); }catch(err){}
            }
        }catch(err){}
    }, true);

    document.addEventListener('click', function(e){
        try{
            var t = e.target;
            if(!t) return;
            // clicks on the customer input -> open inline suggestions
            if(t.id === 'customer-search' || (t.closest && t.closest('#customer-search'))){
                try{ if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(err){}
                return;
            }
            // clicks on magnifier button -> open modal
            var mag = t.closest && t.closest('#customer-search-btn');
            if(mag){ try{ if(window.openCustomerModal) window.openCustomerModal((document.getElementById('customer-search')||{}).value||''); }catch(err){} }
        }catch(err){}
    }, true);

    document.addEventListener('keydown', function(e){
        try{
            var t = e.target;
            if(!t) return;
            if(t.id === 'customer-search'){
                if(e.key === 'Enter' || e.key === ' '){
                    try{ e.preventDefault(); if(window.toggleCustomerSuggestions) window.toggleCustomerSuggestions(); else if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(err){}
                }
            }
        }catch(err){}
    }, true);
}catch(e){}

(function(){
    // Normalize server-rendered rows: replace any `svc_...` prefilled row
    // with a JS-created row so all rows share the same factory/behavior.
    document.addEventListener('DOMContentLoaded', function(){
        try{
            var body = document.getElementById('items-body'); if(!body) return;
            var first = body.querySelector('tr.item-row'); if(!first) return;
            try{
                var isServerRow = false;
                if(first.dataset && first.dataset.rowId && String(first.dataset.rowId).indexOf('svc_') === 0) isServerRow = true;
                if(!isServerRow) return;
                // extract visible values to preserve prefills
                var descEl = first.querySelector('.item-desc'); var qtyEl = first.querySelector('.item-qty'); var rateEl = first.querySelector('.item-rate'); var discEl = first.querySelector('.item-discount');
                var vals = { description: descEl ? (descEl.value||'') : '', qty: qtyEl ? (qtyEl.value||'1') : '1', rate: rateEl ? (rateEl.value||'0.000') : '0.000', discount: discEl ? (discEl.value||'0.000') : '0.000', inventoryId: (first.dataset && (first.dataset.inventoryId||first.dataset.partId)) || null };
                try{ first.parentNode.removeChild(first); }catch(e){}
                // create canonical JS row
                var newRow = null;
                try{ if(typeof window.createItemRow === 'function') newRow = window.createItemRow(false); }catch(e){}
                if(!newRow) return;
                try{
                    var d = newRow.querySelector('.item-desc'); if(d) d.value = vals.description;
                    var q = newRow.querySelector('.item-qty'); if(q) q.value = vals.qty;
                    var r = newRow.querySelector('.item-rate'); if(r) r.value = parseFloat(vals.rate||0).toFixed(3);
                    var di = newRow.querySelector('.item-discount'); if(di) di.value = parseFloat(vals.discount||0).toFixed(3);
                    if(vals.inventoryId){ try{ newRow.dataset.inventoryId = vals.inventoryId; newRow.dataset.partId = vals.inventoryId; }catch(e){} }
                    try{ if(window.updateRowAmount) window.updateRowAmount(newRow); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                }catch(e){}
            }catch(e){}
        }catch(e){}
    });
})();

// Normalize any pre-rendered rows (services or items) by running the
// canonical initializers on them. This ensures server-rendered rows use the
// same factory/handlers as dynamic rows without relying on cloning hacks.
(function(){
    function normalizeRow(row){
        try{
            if(!row) return;
            if(row.dataset && row.dataset.__normalized === '1') return;
            var svcInput = row.querySelector && row.querySelector('.service-desc');
            var itemInput = row.querySelector && row.querySelector('.item-desc');
            try{
                if(itemInput){
                    if(typeof window.initInventoryRow === 'function'){
                        try{ window.initInventoryRow(row); }catch(e){}
                    } else if(typeof window.initInventoryAutocomplete === 'function'){
                        try{ window.initInventoryAutocomplete(itemInput); }catch(e){}
                    }
                }
            }catch(e){}
            try{
                if(svcInput){
                    if(typeof window.initServiceAutocomplete === 'function'){
                        try{ window.initServiceAutocomplete(svcInput); }catch(e){}
                    } else if(typeof window.initInventoryAutocomplete === 'function'){
                        try{ window.initInventoryAutocomplete(svcInput); }catch(e){}
                    }
                }
            }catch(e){}
            try{ if(row.dataset) row.dataset.__normalized = '1'; }catch(e){}
        }catch(e){}
    }

    function runNormalize(){
        try{
            // Normalize any legacy service rows found outside #items-body
            try{
                var all = Array.prototype.slice.call(document.querySelectorAll('tr')) || [];
                var legacy = all.filter(function(r){ try{ if(!r) return false; if(r.closest && r.closest('#items-body')) return false; return Boolean(r.querySelector('.service-desc') || r.querySelector('.service-qty') || r.classList.contains('service-row')); }catch(e){return false;} });
                legacy.forEach(function(r){ try{ normalizeRow(r); }catch(e){} });
            }catch(e){}
            var ib = document.getElementById('items-body');
            if(ib){ Array.prototype.slice.call(ib.querySelectorAll('.item-row')).forEach(normalizeRow); }
        }catch(e){}
    }

    try{ document.addEventListener('DOMContentLoaded', runNormalize); }catch(e){}
    try{ setTimeout(runNormalize, 300); }catch(e){}
    try{ window.addEventListener('load', runNormalize); }catch(e){}
})();

// Ensure the first service input on the page is explicitly initialized
// after all scripts and elements have loaded. This guarantees server-
// rendered first rows receive the same autocomplete handlers as dynamic rows.
    try{
    window.addEventListener('load', function(){
        try{
            var inp = document.querySelector('#items-body .item-row[data-type="service"] .service-desc') || document.querySelector('.service-desc');
            if(!inp) return;
            try{ if(inp.dataset && inp.dataset.autocompleteInitialized === '1') return; }catch(e){}
            if(typeof window.initServiceAutocomplete === 'function'){
                try{ window.initServiceAutocomplete(inp); }catch(e){}
            } else if(typeof window.initInventoryAutocomplete === 'function'){
                try{ window.initInventoryAutocomplete(inp); }catch(e){}
            }
            try{ if(inp.dataset) inp.dataset.autocompleteInitialized = '1'; }catch(e){}
            try{ console.log('[line-items] first service row autocomplete initialized'); }catch(e){}
        }catch(e){}
    }, false);
}catch(e){}