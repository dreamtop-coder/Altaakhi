;(function () {
    if (window.__inventoryAutocompleteLoaded) return;
    window.__inventoryAutocompleteLoaded = true;

    const FetchCache = {};

    function fetcher(url, opts) {
        if (FetchCache[url]) return FetchCache[url];
        const p = (window.fetchJson ? window.fetchJson(url) : fetch(url, opts).then(r => r.json())).finally(() => { try{ delete FetchCache[url]; }catch(e){} });
        FetchCache[url] = p;
        return p;
    }

    window.fetchInventory = function (q) {
        q = (q || '').trim();
        // Always perform merged fetch even for empty query so clicking empty inputs shows defaults
        const invUrl = '/inventory/json/?q=' + encodeURIComponent(q);
        const svcUrl = '/services/autocomplete/?q=' + encodeURIComponent(q);
        // If on the sales-invoice page, return only inventory (no services)
        try{ var pageFlag = (document && document.body && document.body.dataset && document.body.dataset.page) ? document.body.dataset.page : null; }catch(e){ var pageFlag = null; }
        if(pageFlag === 'sales-invoice'){
            return fetcher(invUrl).then(r => (r.results || [])).catch(() => ([]));
        }
        // default: merged inventory + services suggestions
        return Promise.all([fetcher(invUrl).catch(() => ({ results: [] })), fetcher(svcUrl).catch(() => ({ results: [] }))])
            .then(([inv, svc]) => {
                const invList = inv.results || [];
                const svcList = svc.results || [];
                const mappedSvc = svcList.map(s => ({ ...s, type: 'service', track_stock: false }));
                const names = new Set(invList.map(i => (i.name || '').toLowerCase()));
                const merged = invList.slice();
                mappedSvc.forEach(s => { if (!names.has((s.name || '').toLowerCase())) merged.push(s); });
                return merged;
            });
    };

    window.fetchInventoryParts = function (q) {
        q = (q || '').trim();
        if (!q) return Promise.resolve([]);
        return fetcher('/inventory/json/?q=' + encodeURIComponent(q)).then(r => r.results || []);
    };

    window.fetchByType = function (q, type) {
        q = (q || '').trim();
        if (!q) return Promise.resolve([]);
        if (type === 'service') return fetcher('/services/autocomplete/?q=' + encodeURIComponent(q)).then(r => r.results || []);
        return fetcher('/inventory/json/?q=' + encodeURIComponent(q)).then(r => r.results || []);
    };

    window.lookupPartPrice = function (name) {
        if (!name) return Promise.resolve(null);
        return window.fetchInventory(name).then(list => {
            if (!list || !list.length) return null;
            const match = list.find(it => (it.name || '').toLowerCase() === (name || '').toLowerCase()) || list[0];
            const price = (match && (match.sale_price !== undefined ? match.sale_price : (match.price !== undefined ? match.price : null)));
            return (price !== null && price !== undefined) ? parseFloat(price) : null;
        }).catch(() => null);
    };

    window.initInventoryAutocomplete = function (input) {
        try{ if(window.__debugInventory) console.debug('[inv-autocomplete] init called for', input, '._invBound=', input && input._invBound); }catch(e){}
        if (!input){ try{ if(window.__debugInventory) console.debug('[inv-autocomplete] init aborted: no input'); }catch(e){}; return; }
        if (input._invBound){ try{ if(window.__debugInventory) console.debug('[inv-autocomplete] init aborted: already bound', input); }catch(e){}; return; }
        input._invBound = true;
        try{ if(window.__debugInventory) console.debug('[inv-autocomplete] bound input', input); }catch(e){}
        let dd = null, timer = null;

        function close() { try{
            if (dd){ try{ dd.setAttribute && dd.setAttribute('data-__closing','1'); }catch(e){}
                if(window.dropdownManager && typeof window.dropdownManager.closeOwner === 'function'){
                    try{ window.dropdownManager.closeOwner('inventory', {force: true}); }catch(e){}
                } else {
                    try{ if(dd.style) dd.style.display = 'none'; if(dd.classList && (dd.classList.contains('inventory-dd')||dd.classList.contains('svc-dd'))) try{ dd.innerHTML = ''; }catch(e){} }catch(e){}
                }
            }
        }catch(e){} dd = null; }

        function render(list) {
            try{ if(window.__debugInventory) console.debug('[inv-autocomplete] render items=', (list && list.length) || 0, 'for', input); }catch(e){}
            close();
            dd = document.createElement('div'); dd.className = 'inventory-dd'; dd.style.position = 'absolute'; dd.style.zIndex = 9999; dd.style.background = '#fff'; dd.style.border = '1px solid #ddd';
            // constrain height and show scrollbar when list is long
            try{ dd.style.maxHeight = '240px'; dd.style.overflowY = 'auto'; dd.style.overflowX = 'hidden'; dd.style.boxSizing = 'border-box'; }catch(e){}
            try{ dd.style.width = input.offsetWidth + 'px'; }catch(e){}
                const currentVal = ((input && input.value) ? (input.value||'').trim().toLowerCase() : '');
                // Move exact match to top when opening full list and highlight it
                const q = currentVal;
                var renderList = (list || []).slice();
                try{
                    if(q){
                        var ix = renderList.findIndex(function(itm){ var n = (itm.name||itm.title||''); return n && n.toLowerCase() === q; });
                        if(ix > 0){ var ex = renderList.splice(ix,1)[0]; renderList.unshift(ex); }
                    }
                }catch(e){}

                (renderList || []).forEach(it => {
                    const row = document.createElement('div');
                    row.style.padding = '6px 8px';
                    row.style.cursor = 'pointer';
                    row.style.pointerEvents = 'auto';
                    row.style.position = 'relative';
                    row.style.zIndex = 10003;
                    // Render name left, and price/quantity details on the right when available
                    try{
                        const name = it.name || it.title || '';
                        var priceVal = null;
                        try{ if(it.sale_price!==undefined && it.sale_price!==null) priceVal = it.sale_price; }catch(e){}
                        try{ if(priceVal===null && it.price!==undefined && it.price!==null) priceVal = it.price; }catch(e){}
                        var qty = null;
                        try{ if(it.quantity!==undefined && it.quantity!==null) qty = String(it.quantity); }catch(e){}

                        // build two-line layout: title (with out-of-stock) and meta line
                        var titleDiv = document.createElement('div');
                        titleDiv.style.fontWeight = '600';
                        titleDiv.style.marginBottom = '4px';
                        try{
                            if(it.track_stock === true && (qty === '0' || qty === 0)){
                                titleDiv.innerHTML = (name || '') + ' <span style="color:#b91c1c;font-weight:600;margin-left:6px;font-size:12px;">(Out of stock ⚠️)</span>';
                            } else {
                                titleDiv.textContent = name;
                            }
                        }catch(e){ titleDiv.textContent = name; }

                        var metaDiv = document.createElement('div');
                        metaDiv.style.fontSize = '13px';
                        metaDiv.style.color = '#6b7280';
                        var metaParts = [];
                        if(priceVal !== null && priceVal !== undefined) metaParts.push('Price: <strong>' + parseFloat(priceVal).toFixed(3) + '</strong>');
                        if(qty !== null) metaParts.push('Available: <strong>' + qty + '</strong>');
                        metaDiv.innerHTML = metaParts.join(' &nbsp;•&nbsp; ');

                        // clear previous content and append
                        row.innerHTML = '';
                        row.appendChild(titleDiv);
                        row.appendChild(metaDiv);
                        // highlight exact match when opening full list on focus/click
                        try{
                            var nm = (name||'').toLowerCase();
                            if(currentVal && nm === currentVal){
                                row.style.background = '#f3f4f6';
                                try{ row.scrollIntoView && row.scrollIntoView({block:'nearest'}); }catch(e){}
                            }
                        }catch(e){}
                    }catch(e){ row.textContent = it.name || it.title || ''; }
                    function selectItemFromRow(ev){
                        try{ ev && ev.preventDefault && ev.preventDefault(); }catch(e){}
                        try{ ev && ev.stopPropagation && ev.stopPropagation(); }catch(e){}
                        try{ window.__svcSelecting = true; setTimeout(function(){ try{ window.__svcSelecting = false; }catch(e){} }, 250); }catch(e){}
                        // set value first
                        try{ input.value = it.name || (it.title||''); }catch(e){}
                        // update row dataset, hidden inputs and UI
                        const tr = input.closest && input.closest('.item-row');
                        if(tr){
                            // infer type when not explicitly present
                            var inferred = (it && it.type) ? it.type : ((it && it.track_stock) ? 'inventory' : 'service');
                            try{ tr.dataset.type = inferred || 'inventory'; }catch(e){}
                            try{ tr.dataset.inventoryQty = (it.quantity!==undefined ? String(it.quantity) : '1'); }catch(e){}
                            try{ tr.dataset.inventoryTrackStock = (it.track_stock!==undefined ? String(Boolean(it.track_stock)) : 'false'); }catch(e){}
                            // update id fields depending on inferred type
                            try{
                                if(inferred === 'service'){
                                    try{ tr.dataset.serviceId = it.id; }catch(e){}
                                    try{ delete tr.dataset.inventoryId; delete tr.dataset.partId; }catch(e){}
                                } else {
                                    try{ tr.dataset.inventoryId = it.id; }catch(e){}
                                    try{ tr.dataset.partId = it.id; }catch(e){}
                                    try{ delete tr.dataset.serviceId; }catch(e){}
                                }
                            }catch(e){}
                            // set hidden input for server serialization
                            try{ var hh = tr.querySelector && tr.querySelector('.item-type-hidden'); if(hh) hh.value = (inferred === 'service' ? 'service' : 'inventory'); }catch(e){}
                            try{
                                var rateEl = tr.querySelector && tr.querySelector('.item-rate');
                                var priceVal = null;
                                try{ if(it.sale_price!==undefined) priceVal = it.sale_price; }catch(e){}
                                try{ if(priceVal===null && it.price!==undefined) priceVal = it.price; }catch(e){}
                                try{ if(priceVal===null && it.rate!==undefined) priceVal = it.rate; }catch(e){}
                                if(rateEl && priceVal!==null && priceVal!==undefined){ rateEl.value = parseFloat(priceVal).toFixed(3); }
                            }catch(e){}
                            try{ if(window.updateRowAmount) window.updateRowAmount(tr); }catch(e){}
                            try{ if(inferred === 'service'){ if(window.recomputeTotals) window.recomputeTotals(); try{ if(!window._servicesTableInit && window.onServiceSelected) window.onServiceSelected(tr, it); }catch(e){} } else { if(window.recomputeTotals) window.recomputeTotals(); } }catch(e){}
                        }
                        // close after updates
                        try{ setTimeout(function(){ close(); }, 0); }catch(e){}
                    }
                    row.addEventListener('mousedown', selectItemFromRow, false);
                    row.addEventListener('touchstart', selectItemFromRow, {passive:false});
                dd.appendChild(row);
            });
            try{
                    if(window.dropdownManager && typeof window.dropdownManager.open === 'function'){
                    dd.setAttribute('data-dropdown-owner','inventory');
                    window.dropdownManager.open(dd,'inventory');
                    try{ if(window.__debugInventory) console.debug('[inv-autocomplete] OPENED DD'); }catch(e){}
                } else {
                    document.body.appendChild(dd);
                }
                const rect = input.getBoundingClientRect();
                dd.style.left = rect.left + window.scrollX + 'px';
                dd.style.top = rect.bottom + window.scrollY + 'px';
            }catch(e){}
        }

        function fetchAndRender(q) { try{ if(window.__debugInventory) console.debug('[inv-autocomplete] fetchAndRender q=', q, 'for', input); }catch(e){} return window.fetchInventory(q).then(render).catch(() => render([])); }

        input.addEventListener('input', function(){ try{ clearTimeout(timer); }catch(e){} const q = (input.value||'').trim(); if(!q){ try{ fetchAndRender(''); }catch(e){}; return; } timer = setTimeout(function(){ fetchAndRender(q); }, 150); });
        // always open suggestions on focus/click and show full list; typing will filter
        input.addEventListener('focus', function(){ try{ fetchAndRender(''); }catch(e){} });
        input.addEventListener('click', function(){ try{ fetchAndRender(''); }catch(e){} });
        // Allow tests to disable the auto-close behavior by setting
        // `window.__disableInventoryAutoClose = true` in the console.
        input.addEventListener('blur', function(){ try{ if(window.__disableInventoryAutoClose) return; }catch(e){}
            try{
                // delay closing slightly to allow focus to move to another input in the table
                setTimeout(function(){ try{ if(window.__disableInventoryAutoClose) return; close(); }catch(e){} }, 150);
            }catch(e){}
        });
    };

})();
