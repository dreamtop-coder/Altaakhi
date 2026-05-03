 (function () {

    /* =========================
       BASE FETCH HELPER
    ========================== */
    async function fetchJson(url) {
        try {
            const res = await fetch(url);
            return await res.json();
        } catch (e) {
            console.error('[API ERROR]', url, e);
            return { results: [] };
        }
    }

    /* =========================
       FETCH INVENTORY + SERVICES
    ========================== */
    window.fetchInventory = async function (q = '') {

        const qq = (q||'')+''; if(!qq || !qq.trim()) return [];
        const urlInv = '/inventory/json/?q=' + encodeURIComponent(qq);
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
       INVENTORY ONLY (PARTS)
    ========================== */
    window.fetchInventoryParts = async function (q = '') {
        const qq = (q||'')+''; if(!qq || !qq.trim()) return [];
        const url = '/inventory/json/?q=' + encodeURIComponent(qq);
        const data = await fetchJson(url);
        return data.results || [];
    };

    /* =========================
       LOOKUP PRICE
    ========================== */
    window.lookupPartPrice = async function (name) {
        if (!name) return null;

        const list = await window.fetchInventory(name);

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
                    _loadScriptOnce('/static/js/dropdown-manager.js?v=1', function(){ _loadScriptOnce('/static/js/inventory-autocomplete.js?v=4', function(){ try{ if(typeof window.initInventoryAutocomplete === 'function' && window.initInventoryAutocomplete !== arguments.callee){ window.initInventoryAutocomplete(input); } }catch(e){} }); });
                    return;
                }
                // final fallback: no-op
            }catch(e){}
        };
    }

    // Service autocomplete loader stub
    if(typeof window.initServiceAutocomplete === 'undefined'){
        window.initServiceAutocomplete = function(input){
            try{
                if(typeof window._svcLoaderAttached === 'undefined'){
                    window._svcLoaderAttached = true;
                    // ensure dropdown manager is available. Do NOT auto-load legacy services-table.js
                    _loadScriptOnce('/static/js/dropdown-manager.js?v=1', function(){
                        // Legacy `services-table.js` is known-broken; do not load it automatically.
                        // If needed, load it manually for debugging by uncommenting the line below.
                        // _loadScriptOnce('/static/js/services-table.js?v=3', function(){ try{ if(typeof window.initServiceAutocomplete === 'function' && window.initServiceAutocomplete !== arguments.callee){ window.initServiceAutocomplete(input); } }catch(e){} });
                    });
                    return;
                }
            }catch(e){}
        };
    }

    // If this is a maintenance page, proactively load services-table so
    // service dropdowns and initServicesTable are available without user action.
    try{
        if(window.__isMaintenancePage){
            try{ if(window.__debugInventory) console.debug('line-items.api: maintenance page detected, preloading dropdown-manager.js (skipping legacy services-table.js)'); }catch(e){}
            // Load dropdown manager only; do not preload legacy services-table.js which contains a syntax error.
            _loadScriptOnce('/static/js/dropdown-manager.js?v=1', function(){});
        }
    }catch(e){}

})();
