 (function () {

    /* =========================
       BASE FETCH HELPER
    ========================== */
    async function fetchJson(url, opts) {
        try {
            const res = await fetch(url, opts);
            return await res.json();
        } catch (e) {
            console.error('[API ERROR]', url, e);
            return { results: [] };
        }
    }

    /* =========================
       FETCH INVENTORY + SERVICES
    ========================== */
    // Inventory-only: return parts (no services). Use `fetchInventoryMerged` when
    // a merged inventory+services list is explicitly required.
    // Short-lived global cache + in-flight dedupe for the full-list `?all=1` request
    // Backwards-compatible alias that delegates to the canonical parts API.
    window.fetchInventory = function(q = '', opts){
        if (typeof window.fetchInventoryParts === 'function') return window.fetchInventoryParts(q, opts);
        return fetchJson('/inventory/json/?q=' + encodeURIComponent((q||'').trim()), opts).then(d => (d && d.results) ? d.results : []);
    };

    // Explicit merged fetch: inventory + services deduped by name.
    window.fetchInventoryMerged = async function (q = '') {
        const qq = (q || '').trim();
        const urlInv = (qq === '') ? '/inventory/json/?all=1' : ('/inventory/json/?q=' + encodeURIComponent(qq));
        const urlSvc = '/services/autocomplete/?q=' + encodeURIComponent(qq);

        const [invRes, svcRes] = await Promise.all([
            fetchJson(urlInv),
            fetchJson(urlSvc)
        ]);

        const inventory = invRes.results || [];
        const services = svcRes.results || [];

        const mappedServices = services.map(s => ({
            ...s,
            type: 'service',
            track_stock: false,
            quantity: null
        }));

        const merged = [...inventory];

        const names = new Set(
            merged.map(i => (i.name || '').toLowerCase())
        );

        for (const s of mappedServices) {
            const key = (s.name || '').toLowerCase();
            if (!names.has(key)) {
                merged.push(s);
                names.add(key);
            }
        }

        return merged;
    };

    /* =========================
       INVENTORY ONLY (PARTS) - Single Source Cache
    ========================== */
    window.__inventoryCache = window.__inventoryCache || { all: null, allPromise: null, ts: 0 };
    window.fetchInventoryParts = function (q = '', opts) {
        const qq = (q || '').trim();
        const cache = window.__inventoryCache;

        // ALL case - use shared cache + in-flight dedupe
        if (qq === '') {
            if (cache.all) return Promise.resolve(cache.all);
            if (!cache.allPromise) {
                cache.allPromise = fetchJson('/inventory/json/?all=1', opts)
                    .then(d => {
                        cache.all = (d && d.results) ? d.results : [];
                        cache.ts = Date.now();
                        return cache.all;
                    })
                    .finally(() => { cache.allPromise = null; });
            }
            return cache.allPromise;
        }

        // Search mode - no cache
        return fetchJson('/inventory/json/?q=' + encodeURIComponent(qq), opts)
            .then(d => (d && d.results) ? d.results : []);
    };

    // Prefetch full list on DOMContentLoaded to warm shared cache (best-effort)
    try{
        document.addEventListener('DOMContentLoaded', function(){ try{ if(window.fetchInventoryParts) window.fetchInventoryParts(''); }catch(e){} });
    }catch(e){}

    /* =========================
       LOOKUP PRICE
    ========================== */
    window.lookupPartPrice = async function (name) {
        if (!name) return null;

        // Use inventory-only lookup to avoid service entries interfering
        const list = await window.fetchInventoryParts(name);

        if (!list.length) return null;

        const match =
            list.find(i => (i.name || '').toLowerCase() === name.toLowerCase())
            || list[0];

        const price =
            match.sale_price ??
            match.price ??
            null;

        return price !== null ? parseFloat(price) : null;
    };

    /* =========================
       PAGE CONTEXT / TYPE HELPERS
    ========================== */
    window.getAllowedTypes = function(){
        try{
            var t = '';
            try{ if(window && window.ITEM_CONTEXT) t = String(window.ITEM_CONTEXT).trim(); }catch(e){}
            if(!t) t = (document && document.body && document.body.dataset && document.body.dataset.pageType) ? String(document.body.dataset.pageType).trim() : '';
            if(t === 'bills' || t === 'invoices') return ['inventory'];
            if(t === 'maintenance') return ['inventory','service'];
            return ['inventory'];
        }catch(e){ return ['inventory']; }
    };

    try{
        // Initialize a stable page-level context. Prefer explicit `body.dataset.pageType` or
        // `body.dataset.invoiceType` (set by templates). Fall back to allowed types detection.
        if(!window.ITEM_CONTEXT){
            var pt = (document && document.body && document.body.dataset) ? (document.body.dataset.pageType || document.body.dataset.invoiceType || '') : '';
            pt = (pt || '').toString().trim();
            if(!pt){
                try{ pt = (window.getAllowedTypes && window.getAllowedTypes().indexOf('service') !== -1) ? 'maintenance' : 'invoice'; }catch(e){}
            }
            window.ITEM_CONTEXT = pt || 'invoice';
        }
        // Backwards-compat flag used elsewhere in the codebase
        window.__isMaintenancePage = (window.ITEM_CONTEXT === 'maintenance') || (window.getAllowedTypes && window.getAllowedTypes().indexOf('service') !== -1);
    }catch(e){}

    /* =========================
       Backwards-compatible autoloaders for legacy autocomplete
       If the legacy functions are not present on the page, dynamically
       load the older scripts so templates that rely on them still work.
    ========================== */
    function _loadScriptOnce(url, cb){
        try{
            if(!url) return cb && cb();
            if(document.querySelector('script[src="' + url + '"]')){ return cb && cb(); }
            var s = document.createElement('script'); s.src = url; s.async = false; s.onload = function(){ try{ cb && cb(); }catch(e){} }; s.onerror = function(){ try{ cb && cb(); }catch(e){} }; document.head.appendChild(s);
        }catch(e){ try{ cb && cb(); }catch(err){} }
    }

    // Inventory autocomplete loader stub
    if(typeof window.initInventoryAutocomplete === 'undefined'){
        window.initInventoryAutocomplete = function(input){
            try{
                if(typeof window._invLoaderAttached === 'undefined'){
                    window._invLoaderAttached = true;
                    // ensure dropdown manager is available before loading autocomplete
                    _loadScriptOnce('/static/js/dropdown-manager.js?v=1', function(){ _loadScriptOnce('/static/js/inventory-autocomplete.js?v=9', function(){ try{ if(typeof window.initInventoryAutocomplete === 'function' && window.initInventoryAutocomplete !== arguments.callee){ window.initInventoryAutocomplete(input); } }catch(e){} }); });
                    return;
                }
                // final fallback: no-op
            }catch(e){}
        };
    }

    // Service autocomplete loader stub - load lightweight service-autocomplete
    if(typeof window.initServiceAutocomplete === 'undefined'){
        window.initServiceAutocomplete = function(input){
            try{
                if(typeof window._svcLoaderAttached === 'undefined'){
                    window._svcLoaderAttached = true;
                    // ensure dropdown manager is available then load our lightweight service autocomplete
                    _loadScriptOnce('/static/js/dropdown-manager.js?v=1', function(){ _loadScriptOnce('/static/js/service-autocomplete.js?v=1', function(){ try{ if(typeof window.initServiceAutocomplete === 'function' && window.initServiceAutocomplete !== arguments.callee){ window.initServiceAutocomplete(input); } }catch(e){} }); });
                    return;
                }
            }catch(e){}
        };
    }

    // If this is a maintenance page, proactively load services-table so
    // service dropdowns and initServicesTable are available without user action.
    try{
        var __isMaint = (window.ITEM_CONTEXT === 'maintenance') || window.__isMaintenancePage;
        if(__isMaint){
            try{ if(window.__debugInventory) console.debug('line-items.api: maintenance page detected, preloading dropdown-manager.js (skipping legacy services-table.js)'); }catch(e){}
            _loadScriptOnce('/static/js/dropdown-manager.js?v=1', function(){});
        }
    }catch(e){}

})();
