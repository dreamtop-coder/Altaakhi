(function(){
    // Item table helper for maintenance page
    // Exposes: window.createItemRow(), window.updateRowAmount(), window.serializeMaintenanceItems(), window.initItemsTable(), window.recomputeTotals()

    function toFixed3(v){ try{ return parseFloat(v||0).toFixed(3); }catch(e){ return '0.000'; } }

    // Normalize server-rendered rows: ensure dataset.type is present
    function normalizeServerRenderedRows(){
        try{
            // Mark any rows in #services-body as service
            try{ document.querySelectorAll('#services-body .service-row, #services-body tr').forEach(function(r){ try{ if(!r.dataset || !r.dataset.type) r.dataset.type = 'service'; if(!r.classList.contains('item-row')) r.classList.add('item-row'); }catch(e){} }); }catch(e){}

            // Remove server-rendered placeholder/empty rows that were previously saved
            // (no description, zero rate and zero amount, and no linked ids).
            try{
                var maybeEmpty = document.querySelectorAll('#items-body .item-row, #services-body .item-row');
                Array.prototype.forEach.call(maybeEmpty, function(r){ try{
                    var descEl = r.querySelector && (r.querySelector('.item-desc') || r.querySelector('.service-desc') || r.querySelector('.service-label'));
                    var desc = '';
                    try{ if(descEl) desc = (typeof descEl.value !== 'undefined') ? (descEl.value||'') : (descEl.textContent||''); }catch(e){}
                    desc = (desc||'').trim();
                    var rateEl = r.querySelector && (r.querySelector('.item-rate') || r.querySelector('.service-rate'));
                    var amtEl = r.querySelector && (r.querySelector('.item-amount') || r.querySelector('.service-amount'));
                    var rate = parseFloat(rateEl && rateEl.value ? rateEl.value : 0) || 0;
                    var amt = parseFloat(amtEl && amtEl.value ? amtEl.value : 0) || 0;
                    var hasId = false;
                    try{ if(r.dataset && (r.dataset.serviceId || r.dataset.partId || r.dataset.inventoryId || r.dataset.invoiceItemId)) hasId = true; }catch(e){}
                    if(!desc && rate === 0 && amt === 0 && !hasId){ try{ if(r.parentNode) r.parentNode.removeChild(r); else if(typeof r.remove === 'function') r.remove(); }catch(e){} }
                }catch(e){} });
            }catch(e){}

            // Ensure numeric inputs for inventory (part) rows are left-aligned
            try{
                var allRows = document.querySelectorAll('#items-body .item-row, #services-body .item-row');
                Array.prototype.forEach.call(allRows, function(r){ try{
                    var isInv = false;
                    try{ if(r.dataset && r.dataset.type === 'inventory') isInv = true; }catch(e){}
                    try{ if(r.dataset && (r.dataset.partId || r.dataset.inventoryId)) isInv = true; }catch(e){}
                    try{ var hh = r.querySelector && r.querySelector('.item-type-hidden'); if(hh && hh.value === 'inventory') isInv = true; }catch(e){}
                    if(isInv){
                        try{ var qEl = r.querySelector('.item-qty'); if(qEl) qEl.style.textAlign = 'left'; }catch(e){}
                        try{ var rateEl = r.querySelector('.item-rate'); if(rateEl) rateEl.style.textAlign = 'left'; }catch(e){}
                        try{ var discEl = r.querySelector('.item-discount'); if(discEl) discEl.style.textAlign = 'left'; }catch(e){}
                    }
                }catch(e){} });
            }catch(e){}

            window.createItemRow = function(focus){
                try{
                    // On maintenance pages the items table should create service rows,
                    // not plain inventory item rows. Redirect to createServiceRow when available.
                    try{ if(window.__isMaintenancePage){ if(typeof window.createServiceRow === 'function') return window.createServiceRow(focus); if(window.createServiceRow) return window.createServiceRow(focus); } }catch(e){}
                    var body = document.getElementById('items-body') || document.getElementById('items-body-view') || null;
                    if(!body){ try{ body = document.querySelector('tbody#items-body, tbody#items-body-view, tbody'); }catch(e){} }
                    if(!body) return null;
                    // Build a row that matches server-rendered inventory rows (no type selector)
                    var tr = document.createElement('tr'); tr.className = 'item-row';
                    try{ tr.dataset.type = 'inventory'; }catch(e){}
                    // Do not default new rows to 'inventory' — leave type unset so
                    // the autocomplete logic can show merged services+parts for
                    // freshly-added rows when the user clicks "Item Details".
                    tr.innerHTML = '\n        <td style="padding:8px 12px;"><input type="text" class="item-desc" value="" style="width:100%;padding:8px;border:1px solid #eee;border-radius:6px;" /></td>\n        <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-qty" value="1" min="0" step="1" style="width:90px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>\n        <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-rate" value="0.000" step="0.001" style="width:110px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>\n        <td style="padding:8px 12px;text-align:center;"><input type="number" class="item-discount" value="0.00" step="0.001" style="width:60px;padding:6px;border:1px solid #eee;border-radius:6px;text-align:center;" /></td>\n        <td style="padding:8px 18px 8px 12px;text-align:right;"><input type="text" class="item-amount" value="0.000" readonly style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;text-align:right;" /></td>\n        <td style="padding:8px 12px;text-align:center;"><button type="button" class="remove-item-row remove-row" style="background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;">×</button></td>';
                    try{ body.appendChild(tr); }catch(e){ try{ document.body.appendChild(tr); }catch(err){} }
                    try{
                        var desc = tr.querySelector('.item-desc');
                        try{
                            // default: mark new rows as inventory to avoid accidental service classification
                            try{ if(desc && desc.setAttribute) desc.setAttribute('data-autocomplete','inventory'); }catch(e){}
                            if(window.initInventoryAutocomplete) {
                                window.initInventoryAutocomplete(desc);
                                try{ desc.dataset.step = desc.dataset.step || 'view'; }catch(e){}
                            } else if(window.initServiceAutocomplete) {
                                window.initServiceAutocomplete(desc);
                            }
                        }catch(e){ console.warn('initInventoryAutocomplete failed (ignored)', e); }
                        var qty = tr.querySelector('.item-qty'); var rate = tr.querySelector('.item-rate'); var disc = tr.querySelector('.item-discount');
                        qty.addEventListener('input', function(){ window.updateRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                        rate.addEventListener('input', function(){ window.updateRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                        disc.addEventListener('input', function(){ window.updateRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                        if(focus!==false) desc.focus();
                    }catch(e){}
                    return tr;
                }catch(e){ console.error('createItemRow failed', e); return null; }
            };
        }catch(e){}
    }

    document.addEventListener('click', function(e){ try{ var btn = e.target && e.target.closest ? e.target.closest('.remove-row') : null; if(btn){ var r = (btn.closest && (btn.closest('.item-row') || btn.closest('.service-row') || btn.closest('tr')) ) || null; if(r){ try{ if(r.parentNode) r.parentNode.removeChild(r); else if(typeof r.remove === 'function') r.remove(); }catch(err){} try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} } } }catch(err){} });

    // Lightweight Item Details popover: delegated handler to show concise info
    (function(){
        var currentPopover = null;
        function removePopover(){ try{ if(currentPopover && currentPopover.parentNode) currentPopover.parentNode.removeChild(currentPopover); currentPopover = null; }catch(e){} }
        function buildPopover(content, rect){
            removePopover();
            var pop = document.createElement('div');
            pop.className = 'item-detail-popover';
            pop.style.position = 'absolute';
            pop.style.zIndex = 2000;
            pop.style.background = '#fff';
            pop.style.border = '1px solid #e0e0e0';
            pop.style.padding = '8px 10px';
            pop.style.borderRadius = '6px';
            pop.style.boxShadow = '0 6px 18px rgba(0,0,0,0.08)';
            pop.style.fontSize = '0.95em';
            pop.style.minWidth = '180px';
            pop.innerHTML = content;
            document.body.appendChild(pop);
            // position near rect (below if space)
            try{
                var top = rect.bottom + 6;
                var left = rect.left;
                if((top + pop.offsetHeight) > (window.innerHeight - 10)) top = rect.top - pop.offsetHeight - 6;
                if((left + pop.offsetWidth) > (window.innerWidth - 10)) left = Math.max(10, window.innerWidth - pop.offsetWidth - 10);
                pop.style.top = top + 'px'; pop.style.left = left + 'px';
            }catch(e){}
            currentPopover = pop;
            // clicking popover should not immediately close it
            pop.addEventListener('click', function(ev){ ev.stopPropagation(); });
        }

        document.addEventListener('click', function(ev){ try{
            try{ if(window.__debugInventory) console.debug('[items-table] click event', ev.target, 'target.tagName=' + (ev.target && ev.target.tagName)); }catch(e){}
            // any click outside closes popover
            if(currentPopover && !ev.target.closest('.item-detail-popover')) removePopover();
            var target = ev.target && (ev.target.closest ? ev.target.closest('.item-desc, .service-desc, .service-label, .item-desc-cell, .item-detail-trigger') : null);
            try{ if(window.__debugInventory) console.debug('[items-table] click matched target', target); }catch(e){}
            if(!target) return;
                // ensure autocomplete is initialized for the clicked row before we stop propagation
                try{
                    var row = target.closest && target.closest('tr');
                    var descInput = null;
                    try{
                        if(target.classList && (target.classList.contains('item-desc') || target.classList.contains('service-desc'))) descInput = target;
                    }catch(e){}
                    try{ if(!descInput && row) descInput = row.querySelector('.item-desc') || row.querySelector('.service-desc') || row.querySelector('.service-desc-edit'); }catch(e){}
                    try{ if(descInput && typeof window.initInventoryAutocomplete === 'function') window.initInventoryAutocomplete(descInput); }catch(e){}
                }catch(e){}
                ev.stopPropagation();
                // find row (ensure row variable exists below)
                var row = row || (target.closest && target.closest('tr'));
            if(!row) return;
            // derive name, price, qty
            var name = '';
            try{ if(target.value !== undefined) name = (target.value||'').trim(); else name = (target.textContent||'').trim(); }catch(e){}
            var price = '';
            try{ var rateEl = row.querySelector('.item-rate') || row.querySelector('.service-rate'); if(rateEl) price = toFixed3(parseFloat(rateEl.value||rateEl.textContent||0)||0); }catch(e){}
            var qty = '';
            try{ var qtyEl = row.querySelector('.item-qty'); if(qtyEl) qty = (parseFloat(qtyEl.value)||0); }catch(e){}
            // decide if service
            var isService = false;
            try{ if(row.classList && row.classList.contains && row.classList.contains('service-row')) isService = true; if(row.dataset && row.dataset.type === 'service') isService = true; if(target.dataset && target.dataset.autocomplete === 'service') isService = true; }catch(e){}
            // build content
            var html = '';
            html += '<div style="font-weight:600;margin-bottom:6px;">' + (name || '-') + '</div>';
            html += '<div style="color:#333;">price <strong style="float:right">' + (price || '0.000') + '</strong></div>';
            if(!isService){ html += '<div style="color:#333;margin-top:6px;">Quantity <strong style="float:right">' + (qty || 0) + '</strong></div>'; }
            buildPopover(html, target.getBoundingClientRect());
        }catch(e){} }, true);
    })();

    // Serializer is provided by `static/js/line-items.core.js` (canonical implementation).

    window.recomputeTotals = function(){
        try{
            // Sum services globally. Use defensive detection for rows missing dataset.type
            var svcTotal = 0;
            try{
                // Scan legacy service rows first
                document.querySelectorAll('.service-row').forEach(function(r){ try{ var el = r.querySelector('.service-amount') || r.querySelector('.item-amount'); var val = el ? parseFloat(el.value)||0 : 0; svcTotal += val; }catch(e){} });
                // Scan item rows and detect effective type
                document.querySelectorAll('#items-body .item-row').forEach(function(r){ try{
                    var effective = (r.dataset && r.dataset.type) ? r.dataset.type : null;
                    var descEl = r.querySelector && r.querySelector('.item-desc');
                    if(!effective){ try{ if(descEl && descEl.dataset && descEl.dataset.autocomplete === 'service') effective = 'service'; }catch(e){}
                    if(!effective){ try{ if(r.querySelector && r.querySelector('.service-label')) effective = 'service'; }catch(e){} }
                    if(effective === 'service'){
                        var el = r.querySelector('.service-amount') || r.querySelector('.item-amount'); var val = el ? parseFloat(el.value)||0 : 0; svcTotal += val;
                        try{ r.dataset.type = 'service'; }catch(e){}
                    }
                }catch(e){} });
            }catch(e){}
            try{ var elSvc = document.getElementById('services-sub-total'); if(elSvc) elSvc.textContent = toFixed3(svcTotal); }catch(e){}

            // Items subtotal should exclude service rows which may be present
            // inside the #items-body container.
            var sub = 0; var discTotal = 0;
            try{ document.querySelectorAll('#items-body .item-row').forEach(function(r){ try{ if(r.dataset && r.dataset.type === 'service') return; var q = parseFloat(r.querySelector('.item-qty').value)||0; var rate = parseFloat(r.querySelector('.item-rate').value)||0; var d = parseFloat(r.querySelector('.item-discount').value)||0; var lineTotal = q * rate; var lineNet = lineTotal * (1 - (d/100)); sub += lineTotal; discTotal += (lineTotal - lineNet); }catch(e){} }); }catch(e){}
            try{ var subEl = document.getElementById('sub-total'); if(subEl) subEl.textContent = toFixed3(sub); }catch(e){}
            try{ var discEl = document.getElementById('total-discount'); if(discEl) discEl.textContent = toFixed3(discTotal); }catch(e){}

            var grand = (sub - discTotal) + svcTotal;
            try{ var grandEl = document.getElementById('grand-total'); if(grandEl) grandEl.textContent = toFixed3(grand); }catch(e){}
            try{ var bottom = document.getElementById('bottom-total'); if(bottom) bottom.textContent = 'BHD ' + toFixed3(grand); }catch(e){}
            return true;
        }catch(e){ console.error('recomputeTotals failed', e); return false; }
    };

    window.initItemsTable = function(){ try{
        // Normalize any server-rendered rows so dataset.type is present
        try{ normalizeServerRenderedRows(); }catch(e){}
        // robust selector: try common ids/classes first, then fallback to button text
        var btn = document.querySelector('button[id="add-line-item"], button.add-line-item, #add-line-item, #add-row');
        if(!btn){
            // fallback: find a button whose text includes "Add Line Item"
            var allButtons = Array.prototype.slice.call(document.getElementsByTagName('button')||[]);
            for(var i=0;i<allButtons.length;i++){ try{ var t = (allButtons[i].textContent||'').trim(); if(t.indexOf('Add Line Item') !== -1){ btn = allButtons[i]; break; } }catch(e){} }
        }
        if(btn){
            try{ if(!(btn.dataset && btn.dataset.addlineBound === '1')){ btn.addEventListener('click', function(e){ e.preventDefault(); try{ createItemRow(true); }catch(err){ console.error('createItemRow failed', err); } }); try{ btn.dataset.addlineBound = '1'; }catch(e){} try{ window.__addLineHandlerInstalled = true; }catch(e){} } }catch(e){}
        }
        // Check both possible items containers before auto-adding a blank row.
        try{
            var count = 0;
            var bodyA = document.querySelector('#items-body');
            var bodyB = document.querySelector('#items-body-view');
            if(bodyA) count += (bodyA.querySelectorAll('.item-row') || []).length;
            if(bodyB) count += (bodyB.querySelectorAll('.item-row') || []).length;
            if(count === 0 && !window.__isMaintenancePage) createItemRow(false);
        }catch(e){ if(document.querySelectorAll('#items-body .item-row').length === 0 && !window.__isMaintenancePage) createItemRow(false); }
        // ensure totals update
        try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
        // Delegated input handler to keep amounts working for dynamically-created rows
        try{
            if(!window.__itemsDelegatedInputBound){
                window.__itemsDelegatedInputBound = true;
                document.addEventListener('input', function(e){
                    try{
                        if(!e || !e.target) return;
                        var row = e.target.closest && e.target.closest('tr');
                        if(!row) return;
                        // service rows may be classed or have dataset.type === 'service'
                        var isService = (row.classList && row.classList.contains && row.classList.contains('service-row')) || (row.dataset && row.dataset.type === 'service');
                        if(isService){ try{ if(window.updateServiceRowAmount) window.updateServiceRowAmount(row); }catch(err){} }
                        else { try{ if(window.updateRowAmount) window.updateRowAmount(row); }catch(err){} }
                        try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(err){}
                    }catch(err){}
                }, true);
            }
        }catch(e){}
    }catch(e){ console.error('initItemsTable failed', e); } };

    // initialize when DOM ready if called
    document.addEventListener('DOMContentLoaded', function(){ try{ if(window.initItemsTable) window.initItemsTable(); }catch(e){} });

// Robustly bind the Add Line Item button so it works even if the
// button is re-rendered or the DOM changes after initial load.
function bindAddButton(){
    try{
        if(window.__addLineHandlerInstalled) return;
        var btn = document.querySelector('#add-line-item, #add-row');
        if(!btn) return;
        try{ if(btn.dataset && btn.dataset.addlineBound === '1') return; }catch(e){}
        // Replace with a clone to remove stale listeners, then attach ours
        try{ var newBtn = btn.cloneNode(true); btn.parentNode.replaceChild(newBtn, btn); btn = newBtn; }catch(e){}
        try{ btn.dataset.addlineBound = '1'; }catch(e){}
        btn.addEventListener('click', function(e){ try{ e.preventDefault(); if(window.createItemRow) window.createItemRow(true); if(window.recomputeTotals) window.recomputeTotals(); }catch(err){} });
        try{ window.__addLineHandlerInstalled = true; }catch(e){}
    }catch(e){}
}

// Run immediately and a couple of retries to handle late-rendered buttons
try{ bindAddButton(); setTimeout(bindAddButton, 500); setTimeout(bindAddButton, 1500); }catch(e){}

})();
