(function(){
    if(window.__serviceAutocompleteLoaded) return; window.__serviceAutocompleteLoaded = true;

    async function fetchJson(url){ try{ const r = await fetch(url); return await r.json(); }catch(e){ return { results: [] }; } }

    // very small dropdown renderer for services
    function makeDropdown(input, list){
        try{ if(!input) return; }catch(e){}
        // close existing
        try{ if(window.dropdownManager && typeof window.dropdownManager.closeOwner === 'function') window.dropdownManager.closeOwner('service', {force:true}); }catch(e){}
        var dd = document.createElement('div'); dd.className = 'service-dd'; dd.style.position = 'absolute'; dd.style.zIndex = 9999; dd.style.background = '#fff'; dd.style.border = '1px solid #ddd'; dd.style.maxHeight = '260px'; dd.style.overflowY = 'auto'; dd.style.boxSizing = 'border-box'; dd.style.width = input.offsetWidth + 'px';
        dd.addEventListener('pointerdown', function(ev){ ev.stopPropagation(); }, {passive:false});
        dd.addEventListener('mousedown', function(ev){ ev.stopPropagation(); }, {passive:false});
        list.forEach(function(it){
            var row = document.createElement('div'); row.style.padding = '8px'; row.style.cursor = 'pointer';
            var title = document.createElement('div'); title.style.fontWeight = '600'; title.textContent = it.name || it.title || '';
            var meta = document.createElement('div'); meta.style.fontSize = '13px'; meta.style.color = '#6b7280';
            var price = (it.sale_price!==undefined && it.sale_price!==null) ? parseFloat(it.sale_price).toFixed(3) : ((it.price!==undefined&&it.price!==null)?parseFloat(it.price).toFixed(3):'');
            meta.innerHTML = price ? ('Price: <strong>' + price + '</strong>') : '';
            row.appendChild(title); row.appendChild(meta);
            row.addEventListener('click', function(ev){ ev.preventDefault(); ev.stopPropagation();
                try{ input.value = it.name || it.title || ''; input._lastQuery = input.value || ''; }catch(e){}
                var tr = input.closest && input.closest('tr');
                if(tr){ try{ tr.dataset.type = 'service'; tr.dataset.serviceId = it.id; if(tr.querySelector){ var rateEl = tr.querySelector('.item-rate') || tr.querySelector('.service-rate'); if(rateEl && (it.sale_price!==undefined||it.price!==undefined)){ var pv = (it.sale_price!==undefined && it.sale_price!==null) ? it.sale_price : it.price; rateEl.value = parseFloat(pv||0).toFixed(3); } } }catch(e){} }
                try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                try{ if(window.dropdownManager && typeof window.dropdownManager.closeOwner === 'function') window.dropdownManager.closeOwner('service', {force:true}); }catch(e){}
            }, false);
            dd.appendChild(row);
        });
        try{ if(window.dropdownManager && typeof window.dropdownManager.open === 'function'){ dd.setAttribute('data-dropdown-owner','service'); window.dropdownManager.open(dd,'service'); } else { document.body.appendChild(dd); } }catch(e){ document.body.appendChild(dd); }
        try{ const rect = input.getBoundingClientRect(); dd.style.left = rect.left + window.scrollX + 'px'; dd.style.top = rect.bottom + window.scrollY + 'px'; }catch(e){}
    }

    window.initServiceAutocomplete = function(input){
        try{ if(!input) return; }catch(e){}
        if(input._svcBound) return; 
        // If the page allows both inventory and service, prefer the merged
        // dropdown implemented by `inventory-autocomplete`. In that mixed
        // mode we avoid attaching a separate service-only opener to prevent
        // competing dropdowns (which cause the "first click shows services,
        // second click shows parts" behavior).
        try{
            var allowedForPage = (typeof window.getAllowedTypes === 'function') ? window.getAllowedTypes() : ['inventory'];
            if(allowedForPage && allowedForPage.indexOf('service') !== -1 && allowedForPage.indexOf('inventory') !== -1){
                try{ input._svcBound = true; }catch(e){}
                return;
            }
        }catch(e){}
        input._svcBound = true;
        try{ input.addEventListener('pointerdown', function(ev){ ev.stopPropagation(); ev.preventDefault && ev.preventDefault(); // show list
            try{ var allowed = (typeof window.getAllowedTypes === 'function') ? window.getAllowedTypes() : ['inventory']; if(allowed.indexOf('service') === -1){ return; } }catch(e){}
            var q = (input.value||'').trim(); var url = '/services/autocomplete/?q=' + encodeURIComponent(q);
            fetchJson(url).then(function(d){ var list = (d && d.results) ? d.results : []; makeDropdown(input, list); }).catch(function(){ makeDropdown(input, []); });
        }, {passive:false}); }catch(e){}
        try{ input.addEventListener('input', function(ev){ try{ var allowed = (typeof window.getAllowedTypes === 'function') ? window.getAllowedTypes() : ['inventory']; if(allowed.indexOf('service') === -1){ return; } }catch(e){}
            var q = (input.value||'').trim(); var url = '/services/autocomplete/?q=' + encodeURIComponent(q); fetchJson(url).then(function(d){ var list = (d && d.results) ? d.results : []; // if q empty, still show
            try{ if(list && list.length) makeDropdown(input, list); else makeDropdown(input, []); }catch(e){} }).catch(function(){ makeDropdown(input, []); }); }, false); }catch(e){}
    };

})();
