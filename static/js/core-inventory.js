(function(){
  if(window.__coreInventoryInit) return; window.__coreInventoryInit = true;
  // If the newer inventory-autocomplete implementation is loaded, skip
  // defining the legacy initializer to avoid duplicate bindings and fetches.
  try{ if(window.__inventoryAutocompleteLoaded){ try{ console.debug('[core-inventory] skipping legacy init (new autocomplete present)'); }catch(e){}; return; } }catch(e){}
  try{ console.log('[LOAD]', 'core-inventory.js'); }catch(e){}

  // Fetch inventory results; fall back to fetch if fetchJson not present
  window.fetchInventory = function(q){
    var fetcher = (window.fetchJson) ? window.fetchJson : function(url){ return fetch(url).then(function(r){ return r.json(); }); };
    var qq = (q || '').trim();
    var url = (qq === '') ? '/inventory/json/?all=1' : '/inventory/json/?q=' + encodeURIComponent(qq);
    return fetcher(url).then(function(d){ return (d && d.results) ? d.results : []; });
  };

  // Lookup part price by name (server endpoint optional)
  window.lookupPartPrice = function(name){
    if(!name) return Promise.resolve(null);
    var fetcher = (window.fetchJson) ? window.fetchJson : function(url){ return fetch(url).then(function(r){ return r.json(); }); };
    return fetcher('/inventory/lookup_price/?q=' + encodeURIComponent(name)).then(function(d){ return (d && d.price !== undefined) ? parseFloat(d.price) : null; }).catch(function(){ return null; });
  };

  // Simple shared inventory autocomplete initializer
  window.initInventoryAutocomplete = function(input){
    if(!input || input._invInit) return; input._invInit = true;
    var dd = null, timer = null, onWindowChange = null;
    function close(){ if(dd && dd.parentNode) dd.parentNode.removeChild(dd); dd = null; if(onWindowChange){ window.removeEventListener('scroll', onWindowChange, true); window.removeEventListener('resize', onWindowChange); onWindowChange = null; } }
    function positionDropdown(){ if(!dd) return; try{ var rect = input.getBoundingClientRect(); dd.style.left = (rect.left + window.scrollX) + 'px'; dd.style.top = (rect.bottom + window.scrollY + 6) + 'px'; dd.style.width = rect.width + 'px'; }catch(e){} }

    function render(list){ close(); dd = document.createElement('div'); dd.className = 'inventory-suggestions'; dd.style.position = 'absolute'; dd.style.zIndex = 9999; dd.style.boxSizing = 'border-box'; dd.style.maxHeight = '260px'; dd.style.overflow = 'auto'; dd.style.border = '1px solid #e6e6e6'; dd.style.background = '#fff'; dd.style.borderRadius = '6px'; dd.style.boxShadow = '0 8px 30px rgba(2,6,23,0.06)'; dd.style.padding = '4px 0';
      if(!list || !list.length){ var empty = document.createElement('div'); empty.style.padding='8px'; empty.style.color='#666'; empty.textContent = 'No items'; dd.appendChild(empty); }
      else{ list.forEach(function(it){ var row = document.createElement('div'); row.className='item-row-suggest'; row.style.padding='8px'; row.style.cursor='pointer'; row.style.borderBottom='1px solid #f1f5f9'; var title = document.createElement('div'); title.style.fontWeight='600'; title.textContent = it.name || it.title || ''; var meta = document.createElement('div'); meta.style.fontSize='13px'; meta.style.color='#6b7280'; var parts = []; if(it.code) parts.push('Code: '+it.code); if(it.sku) parts.push('SKU: '+it.sku); var _p = (it.price!==undefined)?it.price:((it.sale_price!==undefined)?it.sale_price:undefined); if(_p!==undefined) parts.push('Price: '+parseFloat(_p).toFixed(3)); if(it.quantity!==undefined && it.quantity!==null) parts.push('Available: '+String(it.quantity)); meta.textContent = parts.join(' • '); row.appendChild(title); row.appendChild(meta);
            row.addEventListener('click', function(ev){
              try{
                try{ ev && ev.stopPropagation && ev.stopPropagation(); }catch(e){}
                var rowEl = input.closest && input.closest('.item-row');
                // 1) set visible value
                try{ input.value = it.name || (it.title||''); }catch(e){}
                // 2) bind dataset and update UI
                if(rowEl){
                    try{ rowEl.dataset.inventoryId = it.id; }catch(e){}
                    try{ rowEl.dataset.partId = it.id; }catch(e){}
                    try{ 
                      // normalize server-provided types to canonical frontend values
                      var itType = it && it.type ? (''+it.type).toLowerCase() : 'inventory';
                      if(itType === 'inventory' || itType === 'part' || itType === 'parts') rowEl.dataset.type = 'part';
                      else if(itType === 'service' || itType === 'services') rowEl.dataset.type = 'service';
                      else rowEl.dataset.type = itType;
                    }catch(e){}
                    try{ if(it.quantity!==undefined) rowEl.dataset.inventoryQty = String(it.quantity); }catch(e){}
                    try{ if(it.track_stock!==undefined) rowEl.dataset.inventoryTrackStock = String(Boolean(it.track_stock)); }catch(e){}
                    try{ var rateEl = rowEl.querySelector && rowEl.querySelector('.item-rate'); var _rv = (it.price!==undefined)?it.price:((it.sale_price!==undefined)?it.sale_price:undefined); if(rateEl && _rv!==undefined) rateEl.value = parseFloat(_rv).toFixed(3); }catch(e){}
                    try{ if(window.updateRowAmount) window.updateRowAmount(rowEl); }catch(e){}
                    try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                }
                // 3) close after updates
                try{ setTimeout(function(){ close(); }, 0); }catch(e){}
              }catch(e){ console.error(e); }
            });
            dd.appendChild(row);
      }); }
      try{ if(window.dropdownManager && typeof window.dropdownManager.open === 'function'){ dd.setAttribute('data-dropdown-owner','inventory'); window.dropdownManager.open(dd,'inventory'); } else { document.body.appendChild(dd); } }catch(e){ document.body.appendChild(dd); }
      positionDropdown(); onWindowChange = function(){ positionDropdown(); }; window.addEventListener('scroll', onWindowChange, true); window.addEventListener('resize', onWindowChange);
    }

    function fetchAndRender(q){ return window.fetchInventory(q).then(function(list){ render((list||[]).slice(0,50)); }).catch(function(){ close(); }); }

    input.addEventListener('input', function(){ var q = (input.value||'').trim(); if(timer) clearTimeout(timer); if(!q){ close(); return; } timer = setTimeout(function(){ fetchAndRender(q); }, 160); });
    var _invPointerActivate = false; input.addEventListener('pointerdown', function(){ _invPointerActivate = true; setTimeout(function(){ _invPointerActivate = false; }, 250); });
    // Always open suggestions on focus or click so empty Service fields show merged results
    input.addEventListener('focus', function(){ try{ fetchAndRender((input.value||'').trim() || ''); }catch(e){} });
    input.addEventListener('click', function(e){ try{ fetchAndRender((input.value||'').trim() || ''); }catch(e){} });
    input.addEventListener('blur', function(){ setTimeout(function(){ close(); }, 150); setTimeout(function(){ window.lookupPartPrice(input.value).then(function(price){ if(price!==null){ try{ var tr = input.closest && input.closest('.item-row'); var rateEl = tr && tr.querySelector('.item-rate'); if(rateEl){ rateEl.value = parseFloat(price).toFixed(3); if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); } }catch(e){} } }); }, 260); });
})();

  // Delegated initializer: if user clicks an uninitialized `.item-desc`, ensure
  // the autocomplete is initialized and the input is focused so the dropdown opens.
  (function(){
    try{
      document.addEventListener('click', function(ev){
        try{
          var t = ev.target || null;
          if(!t || !t.closest) return;
          var inp = t.closest('.item-desc');
          if(!inp) return;
          // ensure autocomplete is initialized
          try{ if(typeof window.initInventoryAutocomplete === 'function' && !inp._invBound){ window.initInventoryAutocomplete(inp); } }catch(e){}
          // focus to trigger dropdown open handlers
          try{ if(document.activeElement !== inp) inp.focus(); }catch(e){}
        }catch(e){}
      }, true);
    }catch(e){}
  })();
