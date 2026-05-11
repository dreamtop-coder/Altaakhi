;(function () {
    if (window.__inventoryAutocompleteLoaded) return;
    window.__inventoryAutocompleteLoaded = true;
    // Global guard: block automatic open for a short window after Add-row
    try{ window.__invBlockAutoOpenUntil = window.__invBlockAutoOpenUntil || 0; }catch(e){}

    function fetcher(url, opts) {
        try{
            if(window.fetchInventoryParts && String(url||'').indexOf('/inventory/json') === 0){
                var q = '';
                try{ var m = String(url).match(/[?&]q=([^&]*)/); if(m && m[1]) q = decodeURIComponent(m[1]); else if(String(url).indexOf('?all=1') !== -1) q = ''; }catch(e){}
                return Promise.resolve(window.fetchInventoryParts(q, opts)).then(function(results){ return { results: results }; });
            }
        }catch(e){}
        return fetch(url, opts).then(r => r.json());
    }

    // Per-input open intent: only open when the user interacted with the same field

    // Prefer central `window.fetchInventoryParts` provided by the API loader.
    if (typeof window.fetchInventoryParts === 'undefined') {
        window.fetchInventoryParts = function (q, opts) {
            q = (q === undefined || q === null) ? '' : (String(q).trim());
            const url = (q === '') ? '/inventory/json/?all=1' : ('/inventory/json/?q=' + encodeURIComponent(q));
            return fetcher(url, opts).then(r => { try{}catch(e){} return r.results || []; }).catch(() => ([]));
        };
    }

    // Initialize inventory autocomplete for a newly-created row element.
    // Uses a microtask delay to ensure row internals are present before binding.
    try{
        window.initInventoryRow = function(row){
            try{ if(!row) return; }catch(e){}
            try{
                setTimeout(function(){
                    try{
                        var inp = (row.querySelector && (row.querySelector('.item-desc') || row.querySelector('.service-desc'))) || null;
                        if(inp && typeof window.initInventoryAutocomplete === 'function'){
                            try{ window.initInventoryAutocomplete(inp); }catch(e){}
                        }
                    }catch(e){}
                }, 0);
            }catch(e){}
        };
    }catch(e){}

    window.fetchByType = function (q, type) {
        q = (q === undefined || q === null) ? '' : (String(q).trim());
        // Inventory-only system for bills: always return parts
        if (typeof window.fetchInventoryParts === 'function') return window.fetchInventoryParts(q);
        return fetcher('/inventory/json/?q=' + encodeURIComponent(q)).then(r => r.results || []);
    };

    window.lookupPartPrice = function (name) {
        if (!name) return Promise.resolve(null);
        if (typeof window.fetchInventoryParts === 'function') {
            return window.fetchInventoryParts(name).then(list => {
                if (!list || !list.length) return null;
                const match = list.find(it => (it.name || '').toLowerCase() === (name || '').toLowerCase()) || list[0];
                const price = (match && (match.sale_price !== undefined ? match.sale_price : (match.price !== undefined ? match.price : null)));
                return (price !== null && price !== undefined) ? parseFloat(price) : null;
            }).catch(() => null);
        }
        return Promise.resolve(null);
    };

    window.initInventoryAutocomplete = function (input) {
        try{}catch(e){}
        if (!input){ try{}catch(e){}; return; }
        // Strict binding guard: if already bound (attribute or property), return immediately
        // Additional global WeakSet guard to avoid double-binding in edge cases
        try{ window.__invBoundInputs = window.__invBoundInputs || (typeof WeakSet !== 'undefined' ? new WeakSet() : null); }catch(e){ window.__invBoundInputs = window.__invBoundInputs || null; }
        try{ if(window.__invBoundInputs && window.__invBoundInputs.has && window.__invBoundInputs.has(input)){ try{}catch(e){}; return; } }catch(e){}
        try{
            var hasAttrBound = false;
            try{ hasAttrBound = (input.getAttribute && input.getAttribute('data-inv-bound') === '1'); }catch(e){ hasAttrBound = false; }
                if (hasAttrBound || (input.dataset && input.dataset.invBound === '1') || input._invBound){ try{}catch(e){}; return; }
        }catch(e){}
        // mark as bound early via attribute so duplicate initializers see it
        try{ if(input.setAttribute) input.setAttribute('data-inv-bound','1'); else if(input.dataset) input.dataset.invBound = '1'; }catch(e){}
        input._invBound = true;
        // suppress immediate click/focus events caused by the same user click
        // that created this input (e.g. Add-row). Clear on next macrotask.
        try{ input._invSuppress = true; setTimeout(function(){ try{ input._invSuppress = false; }catch(e){} }, 0); }catch(e){}
        try{ if(window.__invBoundInputs && window.__invBoundInputs.add) window.__invBoundInputs.add(input); }catch(e){}
        // assign a short unique id for tracing across multiple handlers
        try{ if(!input._invId){ window.__invCounter = (window.__invCounter||0) + 1; input._invId = 'inv#' + window.__invCounter; } }catch(e){}
        try{}catch(e){}
        let dd = null, timer = null;
        // derive the enclosing row and ensure a stable row id so state is per-row
        var tr = null;
        try{ tr = input.closest && input.closest('.item-row'); }catch(e){ tr = null; }
        try{
            if(tr){ if(!tr.dataset || !tr.dataset.rowId){ window.__invRowCounter = (window.__invRowCounter||0) + 1; try{ if(!tr.dataset) tr.dataset = {}; }catch(e){}; tr.dataset.rowId = 'row_' + window.__invRowCounter; } }
        }catch(e){}
        var __rowId = (tr && tr.dataset && tr.dataset.rowId) ? tr.dataset.rowId : ((input.dataset && input.dataset.invId) || input._invId);
        // global per-row state store (keyed by rowId)
        try{ window.__invState = window.__invState || {}; if(!window.__invState[__rowId]) window.__invState[__rowId] = { opened: false, lastQuery: (input._lastQuery||''), locked: false, userInteracted: false, openSessionId: null }; }catch(e){}
        function _getState(){ try{ var id = __rowId; return (window.__invState && id) ? window.__invState[id] : null; }catch(e){ return null; } }
        function _markOpened(){ try{ var s = _getState(); if(s){ s.opened = true; s.locked = false; } }catch(e){} }
        function _markClosed(){ try{ var s = _getState(); if(s){ s.locked = true; } }catch(e){} }
        function _setLastQuery(q){ try{ var s = _getState(); if(s){ s.lastQuery = String(q||'').trim(); } }catch(e){} }
        // Prevent the global document click handler from immediately closing
        // dropdowns when the user clicks the input to open suggestions.
        try{
            input.addEventListener('pointerdown', function(ev){ try{ ev.stopPropagation(); }catch(e){} }, false);
            input.addEventListener('mousedown', function(ev){ try{ ev.stopPropagation(); }catch(e){} }, false);
        }catch(e){}

        // Use a per-input intent flag to avoid global false positives.
        // `allowOpen` is set when the user directly interacts with this input
        // (pointerdown / mousedown). Focus will only open the dropdown when
        // `allowOpen` is true and the input is the active element. This avoids
        // opening on unrelated page gestures.
        var allowOpen = false;
        // skipAutoOpen prevents the initial auto-open that can occur when a
        // newly-created input is immediately focused as part of Add-row flow.
        // It will be cleared either on user mousedown or after a short timeout.
        var skipAutoOpen = true;
        var inflight = null;
        var inflightQ = null;
        var openScheduled = false;
        var controller = null;
        // simple debounce to avoid multiple near-simultaneous scheduleOpen calls
        var _lastScheduleAt = 0;
        // time-based suppression so input events after scheduleOpen don't
        // trigger competing fetches
        var suppressInputUntil = 0;
        // short-term dedupe: remember last request for this input
        var __lastReq = { q: null, t: 0, promise: null, requestId: null };
        // programmatic change guard
        var isProgrammatic = false;
        // preserve last user query per-input so reopen uses it instead of falling back to all
        try{ if(input._lastQuery === undefined) input._lastQuery = ''; }catch(e){}
        try{
            input.addEventListener('pointerdown', function(ev){ try{ ev && ev.stopPropagation && ev.stopPropagation(); }catch(e){} }, false);
            input.addEventListener('mousedown', function(ev){ try{ ev && ev.stopPropagation && ev.stopPropagation(); }catch(e){} }, false);
        }catch(e){}

        function close() {
            try{
                try{}catch(e){}
                // No-op when already closed
                try{ if(!dd && !isOpen){ try{}catch(e){}; return; } }catch(e){}

                // Remove visual dropdown element and inform dropdownManager
                if (dd){
                    try{ dd.setAttribute && dd.setAttribute('data-__closing','1'); }catch(e){}
                    try{
                        if(window.dropdownManager && typeof window.dropdownManager.closeOwner === 'function'){
                            try{ window.dropdownManager.closeOwner('inventory', {force: true}); }catch(e){}
                            // best-effort: reset possible internal flags on manager
                            try{ if(window.dropdownManager._owner) delete window.dropdownManager._owner; }catch(e){}
                            try{ if(window.dropdownManager._currentOwner) delete window.dropdownManager._currentOwner; }catch(e){}
                            try{ if(window.dropdownManager.currentOwner !== undefined) window.dropdownManager.currentOwner = null; }catch(e){}
                        }
                        // ensure dd removed from DOM if still present
                        try{ if(dd.parentNode) dd.parentNode.removeChild(dd); }catch(e){}
                    }catch(e){}
                }

                // clear DOM reference and open flag
                dd = null;
                isOpen = false;

                // Reset per-row state fully so manager won't think it's still open
                try{
                    var st = _getState();
                    try{
                        if(q === '' && st && st.opened){ try{ if(window.__debugInventory) console.debug('[inv-autocomplete] skip fetchAll; already open for', input._invId); }catch(e){}; return (__lastReq && __lastReq.promise) ? __lastReq.promise : Promise.resolve([]); }
                    }catch(e){}
                    if(st){
                        st.opened = false;
                        st.locked = false;
                        st.inflight = false;
                        st.userInteracted = false;
                        st.lastRequestId = null;
                    }
                }catch(e){}

                // Reset any dataset locks on the row/input
                try{
                    if(tr && tr.dataset){ tr.dataset.locked = '0'; tr.dataset.suppressInput = '0'; }
                    if(input && input.dataset){ input.dataset.locked = '0'; input.dataset.suppressInput = '0'; }
                }catch(e){}

                // Clear local inflight/dedupe tracking
                try{ inflight = null; inflightQ = null; __lastReq.promise = null; __lastReq.requestId = null; }catch(e){}
                try{ if(controller){ try{ controller.abort(); }catch(e){} controller = null; } }catch(e){}
            }catch(e){}
        }

        function showPlaceholder(text){
            try{}catch(e){}
            try{ if(isOpen && dd){ try{ dd.textContent = text || 'Loading...'; const rect = input.getBoundingClientRect(); dd.style.left = rect.left + window.scrollX + 'px'; dd.style.top = rect.bottom + window.scrollY + 'px'; }catch(e){}; return; } }catch(e){}
            try{ close(); }catch(e){}
            dd = document.createElement('div'); dd.className = 'inventory-dd placeholder'; dd.style.position = 'absolute'; dd.style.zIndex = 9999; dd.style.background = '#fff'; dd.style.border = '1px solid #ddd';
            try{ dd.style.padding = '8px'; dd.style.color = '#6b7280'; }catch(e){}
            try{ dd.textContent = text || 'Loading...'; }catch(e){ dd.innerText = text || 'Loading...'; }
            try{ if(window.dropdownManager && typeof window.dropdownManager.open === 'function'){ dd.setAttribute('data-dropdown-owner','inventory'); window.dropdownManager.open(dd,'inventory'); } else { document.body.appendChild(dd); } }catch(e){ try{ document.body.appendChild(dd); }catch(e){} }
            try{ const rect = input.getBoundingClientRect(); dd.style.left = rect.left + window.scrollX + 'px'; dd.style.top = rect.bottom + window.scrollY + 'px'; }catch(e){}
        }

        function populateDropdown(list){
            try{ if(!dd) return; }catch(e){}
            try{ dd.innerHTML = ''; }catch(e){}
            const currentVal = ((input && input.value) ? (input.value||'').trim().toLowerCase() : '');
            const q = currentVal;
            var renderList = (list || []).slice();
            try{
                var allowed = (typeof window.getAllowedTypes === 'function') ? window.getAllowedTypes() : ['inventory'];
                renderList = renderList.filter(function(item){
                    var itype = item.type || ((item.track_stock) ? 'inventory' : 'service');
                    return allowed.indexOf(itype) !== -1;
                });
            }catch(e){}
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
                try{
                    const name = it.name || it.title || '';
                    var priceVal = null;
                    try{ if(it.sale_price!==undefined && it.sale_price!==null) priceVal = it.sale_price; }catch(e){}
                    try{ if(priceVal===null && it.price!==undefined && it.price!==null) priceVal = it.price; }catch(e){}
                    var qty = null;
                    try{ if(it.quantity!==undefined && it.quantity!==null) qty = String(it.quantity); }catch(e){}

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

                    row.innerHTML = '';
                    row.appendChild(titleDiv);
                    row.appendChild(metaDiv);
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
                    try{ // prevent programmatic assignment from retriggering input searches
                        try{ isProgrammatic = true; }catch(e){}
                        try{ if(tr && tr.dataset) tr.dataset.locked = '1'; else input.dataset && (input.dataset.locked = '1'); }catch(e){}
                        input.value = it.name || (it.title||'');
                        try{ input._lastQuery = (input.value||'').trim(); }catch(e){}
                        try{ _setLastQuery(input._lastQuery); }catch(e){}
                        try{ if(input && input.style) input.style.background = '#fff'; }catch(e){}
                        setTimeout(function(){ try{ isProgrammatic = false; }catch(e){} try{ if(tr && tr.dataset) tr.dataset.locked = '0'; else input.dataset && (input.dataset.locked = '0'); }catch(e){} }, 400);
                    }catch(e){}
                    const tr = input.closest && input.closest('.item-row');
                    if(tr){
                        var inferred = 'inventory';
                        try{ tr.dataset.type = 'inventory'; }catch(e){}
                        try{ tr.dataset.inventoryQty = (it.quantity!==undefined ? String(it.quantity) : '1'); }catch(e){}
                        try{ tr.dataset.inventoryTrackStock = (it.track_stock!==undefined ? String(Boolean(it.track_stock)) : 'false'); }catch(e){}
                        try{ tr.dataset.inventoryId = it.id; }catch(e){}
                        try{ tr.dataset.partId = it.id; }catch(e){}
                        try{ delete tr.dataset.serviceId; }catch(e){}
                        try{ var hh = tr.querySelector && tr.querySelector('.item-type-hidden'); if(hh) hh.value = 'inventory'; }catch(e){}
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
                    try{ setTimeout(function(){ close(); }, 0); }catch(e){}
                    try{ _markClosed(); }catch(e){}
                }
                row.addEventListener('mousedown', selectItemFromRow, false);
                row.addEventListener('touchstart', selectItemFromRow, {passive:false});
                dd.appendChild(row);
            });
            try{ const rect = input.getBoundingClientRect(); dd.style.left = rect.left + window.scrollX + 'px'; dd.style.top = rect.bottom + window.scrollY + 'px'; }catch(e){}
        }

        // render is now the single authority that decides whether to actually
        // draw/open the dropdown. It only renders when the requestId matches
        // the row's lastRequestId and the row state allows opening.
        function canRender(state, requestId){
            try{
                // Be permissive: allow render unless a different request clearly won.
                // Rationale: `locked` was causing renders to be blocked permanently
                // after a close/blur action. Use lastRequestId as the single authority.
                if(!state) return true;
                if(!requestId) return true;
                if(state.lastRequestId && state.lastRequestId !== requestId) return false;
                return true;
            }catch(e){ return true; }
        }

        function render(list, requestId) {
            try{}catch(e){}
            if(!list) list = [];
            var st = _getState();
            try{ if(st && st.lastOpenedRequest && st.lastOpenedRequest === requestId && isOpen){ try{ populateDropdown(list); }catch(e){}; return; } }catch(e){}
            // Ensure the row remembers this requestId so render can validate it
            try{ if(st && requestId && (!st.lastRequestId || st.lastRequestId !== requestId)){ st.lastRequestId = requestId; } }catch(e){}
            if(!canRender(st, requestId)){
                try{}catch(e){}
                return;
            }

            if(list.length === 0){ try{}catch(e){}; _markClosed(); close(); return; }

            // If dropdown already open, reuse it by repopulating content without
            // re-attaching or re-opening the manager (prevents duplicate OPENED logs).
            if(isOpen && dd){ try{ populateDropdown(list); return; }catch(e){} }

            // Not open: ensure previous state cleared then create and open
            try{ close(); }catch(e){}
            dd = document.createElement('div'); dd.className = 'inventory-dd'; dd.style.position = 'absolute'; dd.style.zIndex = 9999; dd.style.background = '#fff'; dd.style.border = '1px solid #ddd';
            // prevent clicks inside the dropdown from bubbling to global handlers
            try{ dd.addEventListener('pointerdown', function(ev){ try{ ev.stopPropagation(); }catch(e){} }, {passive:true}); }catch(e){}
            try{ dd.addEventListener('mousedown', function(ev){ try{ ev.stopPropagation(); }catch(e){} }, {passive:true}); }catch(e){}
            try{ dd.addEventListener('click', function(ev){ try{ ev.stopPropagation(); }catch(e){} }, false); }catch(e){}
            try{ dd.style.maxHeight = '240px'; dd.style.overflowY = 'auto'; dd.style.overflowX = 'hidden'; dd.style.boxSizing = 'border-box'; }catch(e){}
            try{ dd.style.width = input.offsetWidth + 'px'; }catch(e){}
            isOpen = true;
            try{ populateDropdown(list); }catch(e){}
            try{
                if(window.dropdownManager && typeof window.dropdownManager.open === 'function'){
                    dd.setAttribute('data-dropdown-owner','inventory');
                    window.dropdownManager.open(dd,'inventory');
                    try{ if(window.__debugInventory) console.debug('[inv-autocomplete] OPENED DD'); }catch(e){}
                    try{ if(st) st.lastOpenedRequest = requestId; }catch(e){}
                } else {
                    document.body.appendChild(dd);
                    try{ if(st) st.lastOpenedRequest = requestId; }catch(e){}
                }
            }catch(e){}
            try{ _markOpened(); }catch(e){}
            // Opening finished: clear transient opening flag but keep a short
            // suppression window so immediate subsequent input/clicks won't
            // trigger competing fetches that race with the just-opened list.
            try{
                var st2 = _getState();
                if(st2){
                    st2.opening = false;
                            try{ st2.suppressInputUntil = Math.max(st2.suppressInputUntil||0, Date.now() + 120); }catch(e){}
                }
            }catch(e){}
        }

        function fetchAndRender(q, requestId) {
            try{ if(window.__debugInventory) console.debug('[inv-autocomplete] fetchAndRender q=', q, 'for', input, 'id=', input._invId, 'req=', requestId); }catch(e){}
            // normalize query and treat special trigger '__ALL__' as empty
            q = (q === undefined || q === null) ? '' : String(q).trim();
            if (q === '__ALL__') q = '';
            // If this row is currently opening the full list, delay any
            // typed-query fetches until the opening completes to avoid the
            // race where `?all=1` is followed immediately by `?q=...` which
            // can shrink/close the dropdown prematurely.
            try{
                var stDelay = _getState();
                if(stDelay && stDelay.opening && q !== ''){
                    try{}catch(e){}
                    var waiter = (__lastReq && __lastReq.promise) ? __lastReq.promise : Promise.resolve([]);
                    return waiter.then(function(){ var nid = (Date.now()||0) + ':' + Math.random(); try{ var s = _getState(); if(s) s.lastRequestId = nid; }catch(e){} return fetchAndRender(q, nid); });
                }
            }catch(e){}
            try{ if(q !== '') _setLastQuery(q); }catch(e){}
            // show immediate feedback so the dropdown appears on click/focus
            try{ showPlaceholder('Loading...'); }catch(e){}
            var st = _getState();
            try {
                if (st && st.inflight) {
                    try{ if(window.__debugInventory) console.debug('[inv-autocomplete] reuse inflight for', input._invId); }catch(e){}
                    return (__lastReq && __lastReq.promise)
                        ? __lastReq.promise
                        : Promise.resolve([]);
                }
            } catch (e) {}
            // mark inflight so subsequent triggers don't start another fetch
            try { if (st) st.inflight = true; } catch (e) {}

                // short dedupe: if we requested the same q very recently, reuse promise
            try{
                var now = Date.now();
                if(__lastReq.q === q && (now - __lastReq.t) < 800 && __lastReq.promise && __lastReq.requestId === requestId){
                    try{}catch(e){}
                    return __lastReq.promise.then(function(){ /* nothing */ });
                }
            }catch(e){}
            // record request id for this fetch
            __lastReq.q = q; __lastReq.t = Date.now(); __lastReq.requestId = requestId;
            // abort previous fetch for this input (if any) and create a new controller
            try{ if(controller){ try{ controller.abort(); }catch(e){} controller = null; } controller = (typeof AbortController !== 'undefined') ? new AbortController() : null; }catch(e){}
            // If the input or its row explicitly requests inventory-only, use parts-only fetch
            try{
                var tr = input && input.closest ? input.closest('.item-row') : null;
                var inputFlag = input && input.dataset && input.dataset.autocomplete === 'inventory';
                var rowFlag = tr && (tr.dataset && (tr.dataset.type === 'inventory' || tr.dataset.type === 'part'));
                if(inputFlag || rowFlag){
                    // reuse inflight when same query and same requestId
                    if(inflight && inflightQ === q && __lastReq.requestId === requestId){ return inflight.then(function(res){ render(res||[], requestId); }).catch(function(){ try{ render([] , requestId); }catch(e){}; return []; }); }
                    inflightQ = q;
                    try{
                        var opts = controller ? { signal: controller.signal } : undefined;
                        var allowedTypes = (typeof window.getAllowedTypes === 'function') ? window.getAllowedTypes() : ['inventory'];
                        if(allowedTypes.indexOf('service') !== -1 && typeof window.fetchInventoryMerged === 'function'){
                            inflight = window.fetchInventoryMerged(q).then(function(res){ try{ render(res||[], requestId); }catch(e){}; return res; }).catch(function(err){ if(err && err.name === 'AbortError'){ try{}catch(e){}; } try{ render([] , requestId); }catch(e){}; return []; }).finally(function(){ try{ if(st) st.inflight = false; }catch(e){} inflight = null; inflightQ = null; });
                        } else {
                            inflight = window.fetchInventoryParts(q, opts).then(function(res){ try{ render(res||[], requestId); }catch(e){}; return res; }).catch(function(err){ if(err && err.name === 'AbortError'){ try{}catch(e){}; } try{ render([] , requestId); }catch(e){}; return []; }).finally(function(){ try{ if(st) st.inflight = false; }catch(e){} inflight = null; inflightQ = null; });
                        }
                    }catch(e){ inflight = Promise.resolve([]); }
                    __lastReq.promise = inflight;
                    return inflight;
                }
            }catch(e){ /* ignore and fall back */ }
            // inventory-only default (window.fetchInventory is now inventory-only)
            if(inflight && inflightQ === q && __lastReq.requestId === requestId){ return inflight.then(function(res){ render(res||[], requestId); }).catch(function(){ try{ render([] , requestId); }catch(e){}; return []; }); }
            inflightQ = q;
            try{
                var opts2 = controller ? { signal: controller.signal } : undefined;
                var allowedTypes2 = (typeof window.getAllowedTypes === 'function') ? window.getAllowedTypes() : ['inventory'];
                if(allowedTypes2.indexOf('service') !== -1 && typeof window.fetchInventoryMerged === 'function'){
                    inflight = window.fetchInventoryMerged(q).then(function(res){ try{ render(res||[], requestId); }catch(e){}; return res; }).catch(function(err){ if(err && err.name === 'AbortError'){ try{}catch(e){}; } try{ render([] , requestId); }catch(e){}; return []; }).finally(function(){ try{ if(st) st.inflight = false; }catch(e){} inflight = null; inflightQ = null; });
                } else {
                    inflight = window.fetchInventoryParts(q, opts2).then(function(res){ try{ render(res||[], requestId); }catch(e){}; return res; }).catch(function(err){ if(err && err.name === 'AbortError'){ try{}catch(e){}; } try{ render([] , requestId); }catch(e){}; return []; }).finally(function(){ try{ if(st) st.inflight = false; }catch(e){} inflight = null; inflightQ = null; });
                }
            }catch(e){ inflight = Promise.resolve([]); }
            __lastReq.promise = inflight;
            return inflight;
        }

        input.addEventListener('input', function(){
            try{ if(isProgrammatic) { try{}catch(e){}; return; } }catch(e){}
            try{ var sst = _getState(); if(sst && sst.suppressInputUntil && Date.now() < sst.suppressInputUntil){ try{}catch(e){}; return; } }catch(e){}
            try{ if(tr && tr.dataset && tr.dataset.suppressInput === '1'){ try{}catch(e){}; return; } }catch(e){}
            try{ if(tr && tr.dataset && tr.dataset.locked === '1'){ try{}catch(e){}; return; } }catch(e){}
            try{ clearTimeout(timer); }catch(e){}
            const q = (input.value||'').trim();
            try{}catch(e){}
            // create a request id for this keystroke and route via fetchAndRender
            timer = setTimeout(function(){ var requestId = (Date.now()||0) + ':' + Math.random(); try{ var s = _getState(); if(s) s.lastRequestId = requestId; }catch(e){} fetchAndRender(q, requestId); }, 150);
        });
        // scheduleOpen -> requestId -> fetchAndRender -> render decides opening
        function scheduleOpen(){
            try{}catch(e){}
            try{ clearTimeout(timer); }catch(e){}
            try{ if(Date.now() < (window.__invBlockAutoOpenUntil || 0)) { try{ if(window.__debugInventory) console.debug('[inv-autocomplete] blocked by global invBlockAutoOpenUntil'); }catch(e){}; return; } }catch(e){}
            var now = Date.now();
            // ignore repeated scheduleOpen within 400ms
            try{ if(_lastScheduleAt && (now - _lastScheduleAt) < 400){ try{}catch(e){}; return; } }catch(e){}
            _lastScheduleAt = now;
            try{ var _st_now = _getState(); if(_st_now && _st_now.opened){ try{}catch(e){}; return; } }catch(e){}
            if(openScheduled) return;
            // If dropdown is already visible, skip scheduling a new fetch
            try{ if(typeof isOpen !== 'undefined' && isOpen){ try{}catch(e){}; return; } }catch(e){}
            // Skip opens when selection/programmatic change is happening or the row/input is locked
            try{ if(isProgrammatic){ try{}catch(e){}; return; } }catch(e){}
            try{ if(window.__svcSelecting){ try{}catch(e){}; return; } }catch(e){}
            try{ if(tr && tr.dataset && tr.dataset.locked === '1'){ try{}catch(e){}; return; } }catch(e){}
            try{ if(input && input.dataset && input.dataset.locked === '1'){ try{}catch(e){}; return; } }catch(e){}
            openScheduled = true;
            // set opening/suppress flags immediately so input events fired
            // between the click and the delayed fetch are ignored.
            try{
                var s0 = _getState();
                var immediateSuppress = Date.now() + 120;
                try{ if(s0) { s0.suppressInputUntil = immediateSuppress; s0.opening = true; } }catch(e){}
                try{ if(tr && tr.dataset){ tr.dataset.suppressInput = '1'; setTimeout(function(){ try{ tr.dataset.suppressInput = '0'; }catch(e){} }, 120); } else { input.dataset && (input.dataset.suppressInput = '1'); setTimeout(function(){ try{ input.dataset && (input.dataset.suppressInput = '0'); }catch(e){} }, 120); } }catch(e){}
                suppressInputUntil = immediateSuppress;
            }catch(e){}
            setTimeout(function(){ try{ openScheduled = false;
                var st = _getState();
                try{ if(st) st.userInteracted = true; }catch(e){}
                // Always request the full list on open; typing will filter.
                var toFetch = '__ALL__';
                // If this row is already open, avoid re-fetching the full list.
                if(st && st.opened){ try{}catch(e){}; return; }
                var requestId = (Date.now()||0) + ':' + Math.random();
                try{ if(st) st.lastRequestId = requestId; }catch(e){}
                try{}catch(e){}
                fetchAndRender(toFetch, requestId);
            }catch(e){} }, 50);
        }
        input.addEventListener('focus', function(ev){ try{ if(input._invSuppress){ try{ input._invSuppress = false; }catch(e){}; return; } if(skipAutoOpen){ return; } ev && ev.stopPropagation && ev.stopPropagation(); if(document.activeElement !== input) return; try{ var s = _getState(); if(s) s.isFocused = true; }catch(e){}; scheduleOpen(); }catch(e){} });
        input.addEventListener('click', function(ev){ try{ if(input._invSuppress){ try{ input._invSuppress = false; }catch(e){}; return; } if(skipAutoOpen){ return; } ev && ev.stopPropagation && ev.stopPropagation(); allowOpen = true; try{ var s = _getState(); if(s) s.userInteracted = true; }catch(e){}; scheduleOpen(); }catch(e){} });
        try{ input.addEventListener('mousedown', function(){ try{ skipAutoOpen = false; allowOpen = true; }catch(e){} }, false); }catch(e){}
        // Allow tests to disable the auto-close behavior by setting
        // `window.__disableInventoryAutoClose = true` in the console.
        input.addEventListener('blur', function(){ try{ if(window.__disableInventoryAutoClose) return; }catch(e){}
            try{
                // delay closing slightly to allow focus to move to another input or into the dropdown
                setTimeout(function(){ try{ if(window.__disableInventoryAutoClose) return; try{ var active = document.activeElement; if(dd && (dd.contains(active) || active === input)){ try{}catch(e){}; return; } }catch(e){} _markClosed(); close(); }catch(e){} }, 150);
            }catch(e){}
        });
        // If we were bound as part of a click/focus cycle, the input may already
        // be focused. In that case open the suggestions immediately so the
        // original user interaction shows the dropdown instead of requiring
        // another click.
        try{
            setTimeout(function(){ try{ if(!skipAutoOpen && document.activeElement === input && allowOpen){ try{}catch(e){} scheduleOpen(); allowOpen = false; } }catch(e){} }, 0);
            setTimeout(function(){ try{ skipAutoOpen = false; }catch(e){} }, 300);
        }catch(e){}
    };

    // Auto-initialize inventory-only inputs for server-rendered rows on page load
    try{
        document.addEventListener('DOMContentLoaded', function(){
            try{
                var rows = document.querySelectorAll && document.querySelectorAll('.item-row');
                if(!rows || !rows.length) return;
                rows.forEach(function(tr){
                    try{
                        // determine if this row is inventory-only via dataset or hidden input
                        var rowType = tr.dataset && (tr.dataset.type || tr.dataset.autocomplete || null);
                        var hh = tr.querySelector && tr.querySelector('.item-type-hidden');
                        if(hh && hh.value && hh.value.trim() === 'inventory') rowType = 'inventory';
                        if(rowType === 'inventory' || rowType === 'part'){
                            var inp = tr.querySelector && tr.querySelector('.item-desc');
                            if(inp && window.initInventoryAutocomplete && !inp._invBound){
                                try{ window.initInventoryAutocomplete(inp); }catch(e){}
                            }
                        }
                    }catch(e){}
                });
            }catch(e){}
        });
    }catch(e){}

})();
