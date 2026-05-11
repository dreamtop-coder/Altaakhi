(function(){
    'use strict';

    function initLineItems() {
        try {
            if (window.initItemsTable) window.initItemsTable();
            if (window.recomputeTotals) window.recomputeTotals();
            if (window.initServicesTable) window.initServicesTable();

            // Ensure first row is created by JS (keep #items-body empty in template)
            try {
                var itemsBody = document.getElementById('items-body');
                if (itemsBody && itemsBody.children.length === 0) {
                    if (typeof window.createItemRow === 'function') {
                        window.createItemRow();
                    } else if (typeof window.createItemRowFallback === 'function') {
                        window.createItemRowFallback();
                    }
                }
            } catch (e) { console.warn('create initial item row failed', e); }
        } catch (e) { console.warn('initLineItems error', e); }
    }

    function onReady() {
        // attach change vehicle button
        try {
            var btn = document.getElementById('change-vehicle-btn');
            if (btn && !btn.__wired) {
                btn.addEventListener('click', function(){
                    try{ window.location = window.location.pathname; }catch(e){ window.location.href = window.location.pathname; }
                });
                btn.__wired = true;
            }
        } catch (e) { }

        // attach customer quick controls
        try {
            var suggestToggle = document.getElementById('customer-suggest-toggle');
            if (suggestToggle && !suggestToggle.__wired) {
                suggestToggle.addEventListener('click', function(){ try{ (window.toggleCustomerSuggestions||function(){})(); }catch(e){} });
                suggestToggle.__wired = true;
            }
            var searchBtn = document.getElementById('customer-search-btn');
            if (searchBtn && !searchBtn.__wired) {
                searchBtn.addEventListener('click', function(){ try{ (window.openCustomerModal||function(){})(); }catch(e){} });
                searchBtn.__wired = true;
            }
        } catch (e) { }

        // minimal fallback for createItemRow
        try{ window.createItemRow = window.createItemRow || (window.createItemRowFallback || null); }catch(e){}
    }

    // Wait for line-items scripts to be ready, otherwise init once DOM is loaded
    if (window.__lineItemsReady) {
        initLineItems();
    } else {
        window.addEventListener('line-items-ready', function(){ initLineItems(); });
        document.addEventListener('DOMContentLoaded', function(){
            // small delay to let line-items loader bind if it's about to
            setTimeout(function(){ initLineItems(); onReady(); }, 40);
        });
    }

    // also wire immediately for progressive enhancement
    try { document.addEventListener('DOMContentLoaded', onReady); } catch (e) {}

})();
