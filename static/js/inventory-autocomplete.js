(function(){
    // Lightweight inventory autocomplete helpers used by multiple templates.
    // Exposes: window.fetchInventory(q), window.lookupPartPrice(name), window.initInventoryAutocomplete(input)

    function fetcher(u){ return (window.fetchJson?window.fetchJson:function(url){ return fetch(url).then(function(r){ return r.json(); }); })(u); }

    window.fetchInventory = function(q){
        // fetch inventory and services in parallel and merge results
        var urlInv = '/inventory/json/?q=' + encodeURIComponent(q||'');
        // use the services autocomplete endpoint (match services-table)
        var urlSvc = '/services/autocomplete/?q=' + encodeURIComponent(q||'');
        return Promise.all([fetcher(urlInv).catch(function(){ return {results:[]}; }), fetcher(urlSvc).catch(function(){ return {results:[]}; })])
            .then(function(res){
                var inv = (res[0] && res[0].results)? res[0].results : [];
                var svc = (res[1] && res[1].results)? res[1].results : [];
                // normalize service items to inventory-like shape if needed
                var mappedSvc = svc.map(function(it){ return Object.assign({}, it, { name: it.name, sale_price: it.sale_price, code: it.code || '', track_stock: false, quantity: null }); });
                // merge by name, services appended after inventory but avoid duplicates by name
                var merged = inv.slice();
                var names = new Set(merged.map(function(i){ return (i.name||'').toLowerCase(); }));
                mappedSvc.forEach(function(s){ if(!names.has((s.name||'').toLowerCase())){ merged.push(s); names.add((s.name||'').toLowerCase()); } });
                return merged;
            }).catch(function(){ return []; });
    };

    // inventory only (parts) fetch - used by item inputs so services are not mixed into parts list
    window.fetchInventoryParts = function(q){
        var urlInv = '/inventory/json/?q=' + encodeURIComponent(q||'');
        return fetcher(urlInv).then(function(data){ return (data && data.results)? data.results : []; }).catch(function(){ return []; });
    };

    window.lookupPartPrice = function(name){
        if(!name) return Promise.resolve(null);
        return window.fetchInventory(name).then(function(list){
            if(!list || !list.length) return null;
            var match = list.find(function(it){ return (it.name||'').toLowerCase() === (name||'').toLowerCase(); }) || list[0];
            var price = (match && (match.sale_price!==undefined ? match.sale_price : (match.price!==undefined ? match.price : null)));
            return (price!==null && price!==undefined) ? parseFloat(price) : null;
        }).catch(function(){ return null; });
    };

    window.initInventoryAutocomplete = function(input){
        if(!input || input._invInit) return;
        // debug: log attempts to initialize inventory autocomplete
        try{ console.log('[inv] initInventoryAutocomplete for', input, 'dataset=', input && input.dataset); }catch(e){}
        // do not initialize inventory autocomplete on inputs explicitly marked for services
        try{ if(input.dataset && input.dataset.autocomplete === 'service'){ try{ console.log('[inv] skipped binding (service-marked input)'); }catch(e){} return; } }catch(e){}
        input._invInit = true;
        try{ console.log('[inv] bound inventory autocomplete to', input); }catch(e){}
        var dd = null, timer = null, onWindowChange = null;
        function close(){ if(dd){ try{ if(dd.parentNode) dd.parentNode.removeChild(dd); }catch(e){} dd = null; } if(onWindowChange){ window.removeEventListener('scroll', onWindowChange, true); window.removeEventListener('resize', onWindowChange); onWindowChange = null; } }
        function positionDropdown(){ if(!dd) return; try{ var rect = input.getBoundingClientRect(); dd.style.left = (rect.left + window.scrollX) + 'px'; dd.style.top = (rect.bottom + window.scrollY + 6) + 'px'; dd.style.width = rect.width + 'px'; }catch(e){} }
        function render(list){
            close();
            dd = document.createElement('div');
            dd.className = 'inventory-suggestions';
            dd.style.position = 'absolute';
            dd.style.zIndex = 9999;
            dd.style.boxSizing = 'border-box';
            dd.style.maxHeight = '260px';
            dd.style.overflow = 'auto';
            dd.style.border = '1px solid #e6e6e6';
            dd.style.background = '#fff';
            dd.style.borderRadius = '6px';
            dd.style.boxShadow = '0 8px 30px rgba(2,6,23,0.06)';
            dd.style.padding = '4px 0';

            if(!list || !list.length){
                var empty = document.createElement('div');
                empty.style.padding = '8px';
                empty.style.color = '#666';
                empty.textContent = 'No items';
                dd.appendChild(empty);
            } else {
                list.forEach(function(it){
                    var row = document.createElement('div');
                    row.className = 'item-row-suggest';
                    row.style.padding = '8px';
                    row.style.cursor = 'pointer';
                    row.style.borderBottom = '1px solid #f1f5f9';
                    var title = document.createElement('div');
                    title.style.fontWeight = '600';
                    var stockVal = (it.stock!==undefined && it.stock!==null) ? Number(it.stock) : (it.quantity!==undefined?Number(it.quantity):undefined);
                    var stockText = '';
                    if(it.track_stock){
                        if(stockVal === undefined){ stockText = ' (Stock: ? )'; }
                        else if(stockVal > 0){ stockText = ' (Stock: ' + stockVal + ')'; }
                        else { stockText = ' (Out of stock ⚠️)'; }
                    }
                    title.textContent = (it.name || (it.title||'')) + stockText;
                    var meta = document.createElement('div');
                    meta.style.fontSize = '13px';
                    meta.style.color = '#6b7280';
                    var parts = [];
                    if(it.code) parts.push('Code: '+it.code);
                    if(it.sku) parts.push('SKU: '+it.sku);
                    if(it.price!==undefined) parts.push('Price: '+parseFloat(it.price).toFixed(3));
                    if(stockVal!==undefined && stockVal!==null) parts.push('Available: '+String(stockVal));
                    meta.textContent = parts.join(' • ');
                    row.appendChild(title);
                    row.appendChild(meta);

                    if(it.track_stock && (stockVal===0 || (stockVal!==undefined && Number(stockVal) <= 0))){
                        row.classList.add('out-of-stock');
                    }

                    row.addEventListener('click', function(){
                        try{
                            var rowEl = input.closest('.item-row');
                            var requestedQty = 1;
                            try{ requestedQty = Number((rowEl && rowEl.querySelector('.item-qty'))?rowEl.querySelector('.item-qty').value:1)||1; }catch(e){}
                            var allowOut = false;
                            try{ if(input && input.dataset && input.dataset.allowOutOfStock==='true') allowOut = true; }catch(e){}
                            try{ if(window.inventory_allow_out_of_stock) allowOut = true; }catch(e){}

                            // prevent selection entirely if tracked and stock <= 0 (unless explicitly allowed)
                            if(it.track_stock && (stockVal===0 || (stockVal!==undefined && Number(stockVal) <= 0)) && !allowOut){
                                try{ if(window.showAvailabilityModal) window.showAvailabilityModal('هذه القطعة غير متوفرة'); else alert('هذه القطعة غير متوفرة'); }catch(e){}
                                return;
                            }

                            if(it.track_stock && it.quantity!==undefined && Number(it.quantity) < requestedQty && !allowOut){ try{ if(window.showAvailabilityModal) window.showAvailabilityModal('Insufficient stock: available '+(it.quantity||0)+' • requested '+requestedQty); }catch(e){} return; }

                            input.value = it.name;
                            if(rowEl){
                                rowEl.dataset.inventoryId = it.id;
                                rowEl.dataset.partId = it.id;
                                rowEl.dataset.selected = 'true';
                                if(it.quantity!==undefined) rowEl.dataset.inventoryQty = String(it.quantity);
                                if(it.track_stock!==undefined) rowEl.dataset.inventoryTrackStock = String(Boolean(it.track_stock));
                                var rateEl = rowEl.querySelector('.item-rate');
                                if(rateEl && it.price!==undefined) rateEl.value = parseFloat(it.price).toFixed(2);
                                try{ if(window.updateRowAmount) window.updateRowAmount(rowEl); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                            }
                        }catch(e){console.error(e);} 
                        close();
                        try{ var hasEmpty=false; document.querySelectorAll('#items-body .item-desc').forEach(function(d){ if((d.value||'').trim()==='') hasEmpty=true; }); if(!hasEmpty && window.createItemRow) window.createItemRow(false); }catch(e){}
                    });

                    dd.appendChild(row);
                });
            }
            document.body.appendChild(dd);
            positionDropdown();
            onWindowChange = function(){ positionDropdown(); };
            window.addEventListener('scroll', onWindowChange, true);
            window.addEventListener('resize', onWindowChange);
        }
        function fetchAndRender(q){
            // prefer inventory-only fetch for item inputs; fallback to merged fetchInventory if available
            var fetchFn = (window.fetchInventoryParts) ? window.fetchInventoryParts : ((window.fetchInventory) ? window.fetchInventory : function(u){ return fetcher('/inventory/json/?q=' + encodeURIComponent(u||'')).then(function(d){ return (d && d.results)? d.results : []; }); });
            var rawQ = (q||'')+''; rawQ = rawQ.replace(/\u00A0/g,' ').trim();
            fetchFn(rawQ).then(function(list){
                var mapped = (list||[]).map(function(it){
                    var qty = (it.stock!==undefined && it.stock!==null) ? Number(it.stock) : ((it.quantity!==undefined && it.quantity!==null) ? Number(it.quantity) : undefined);
                    return {
                        id: it.id,
                        name: it.name||it.title||'',
                        code: it.code||'',
                        sku: it.sku||'',
                        price: (it.sale_price!==undefined)?parseFloat(it.sale_price):(it.price!==undefined?parseFloat(it.price):undefined),
                        quantity: qty,
                        stock: qty,
                        track_stock: (it.track_stock!==undefined && it.track_stock!==null)?Boolean(it.track_stock):undefined
                    };
                });
                if((mapped||[]).length === 0 && rawQ !== ''){
                    // fallback: show full list if exact lookup failed (helps when server-rendered value has encoding differences)
                    fetchFn('').then(function(all){ var mappedAll = (all||[]).map(function(it){ var qty = (it.stock!==undefined && it.stock!==null) ? Number(it.stock) : ((it.quantity!==undefined && it.quantity!==null) ? Number(it.quantity) : undefined); return { id: it.id, name: it.name||it.title||'', code: it.code||'', sku: it.sku||'', price: (it.sale_price!==undefined)?parseFloat(it.sale_price):(it.price!==undefined?parseFloat(it.price):undefined), quantity: qty, stock: qty, track_stock: (it.track_stock!==undefined && it.track_stock!==null)?Boolean(it.track_stock):undefined }; }); render(mappedAll.slice(0,50)); }).catch(function(){ render(mapped.slice(0,50)); });
                } else {
                    render(mapped.slice(0,50));
                }
            }).catch(function(){ close(); });
        }
        input.addEventListener('input', function(){
            try{
                var tr = input.closest && input.closest('.item-row');
                if(tr){ tr.dataset.partId = ''; tr.dataset.selected = 'false'; }
            }catch(e){}
            var q = (input.value||'').trim();
            try{ console.log('[inv] input event on', input, 'value=', q); }catch(e){}
            if(timer) clearTimeout(timer);
            if(!q){ close(); return; }
            timer = setTimeout(function(){ fetchAndRender(q); }, 160);
        });
        // open suggestions on user click/focus or when there's existing content
        var _invPointerActivate = false;
        input.addEventListener('pointerdown', function(){ _invPointerActivate = true; setTimeout(function(){ _invPointerActivate = false; }, 250); });
        // On focus/click, prefer showing services if the current value matches a service
        function checkServicesThenInventory(q, allowEmpty){
            try{
                var qq = (q||'').trim();
                if(!qq && !allowEmpty) return fetchAndRender('');
                // query services endpoint quickly to see if there are matching services
                var svcUrl = '/services/autocomplete/?q=' + encodeURIComponent(qq||'');
                try{ fetcher(svcUrl).then(function(sd){ var sres = (sd && sd.results)? sd.results : []; if(sres && sres.length){ // prefer service behavior
                            try{ console.log('[inv] switching to service autocomplete for input', input, 'q=', qq); }catch(e){}
                            try{ if(input.dataset) input.dataset.autocomplete = 'service'; }catch(e){}
                            try{ if(window.initServiceAutocomplete) { window.initServiceAutocomplete(input); if(input._svcFetchAndRender) input._svcFetchAndRender(qq); } }catch(e){}
                            return; }
                        // no services; fallback to inventory
                        fetchAndRender(qq);
                    }).catch(function(){ fetchAndRender(qq); });
                }catch(e){ fetchAndRender(qq); }
            }catch(e){ fetchAndRender(q); }
        }
        input.addEventListener('focus', function(){ var q = (input.value||'').trim(); if(q || _invPointerActivate) checkServicesThenInventory(q, false); });
        // also open suggestions on user click when the field is empty (show full list)
        input.addEventListener('click', function(e){ var q = (input.value||'').trim(); if(!q){ checkServicesThenInventory('', true); } else { checkServicesThenInventory(q, false); } });
        input.addEventListener('blur', function(){ setTimeout(close,150); setTimeout(function(){ window.lookupPartPrice(input.value).then(function(price){ if(price!==null){ try{ var tr = input.closest('.item-row'); var rateEl = tr && tr.querySelector('.item-rate'); if(rateEl) { rateEl.value = parseFloat(price).toFixed(2); if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); } }catch(e){} } }); },180); });
    };
})();
