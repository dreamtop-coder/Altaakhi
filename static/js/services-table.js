(function(){
    // Services table helper
    // Exposes: window.createServiceRow(), window.serializeServiceItems(), window.initServicesTable()
    function fetcher(u){ return (window.fetchJson?window.fetchJson:function(url){ return fetch(url).then(function(r){ return r.json(); }); })(u); }

    // lightweight debug helper - enable by setting `window.__svcDebug = true` in the console
    function svcDebug(msg){ try{ if(window && window.__svcDebug) console.log('[svc] '+msg); }catch(e){} }
    function initServiceAutocomplete(input){
        if(!input || input._svcInit) return; input._svcInit = true;
        var dd=null, timer=null;
        function close(){ if(dd){ try{ dd.parentNode.removeChild(dd); }catch(e){} dd=null; } }
        function position(){ if(!dd) return; try{ var rect = input.getBoundingClientRect(); dd.style.left = (rect.left + window.scrollX) + 'px'; dd.style.top = (rect.bottom + window.scrollY + 6) + 'px'; dd.style.width = rect.width + 'px'; }catch(e){} }
        function render(list){ close(); dd = document.createElement('div');
            // reuse inventory dropdown classes so services list looks identical to items autocomplete
            dd.className='inventory-suggestions'; dd.style.position='absolute'; dd.style.zIndex=9999; dd.style.maxHeight='260px'; dd.style.overflow='auto'; dd.style.border='1px solid #e6e6e6'; dd.style.background='#fff'; dd.style.padding='4px 0'; dd.style.borderRadius='6px'; dd.style.boxSizing='border-box'; dd.style.boxShadow='0 8px 30px rgba(2,6,23,0.06)';
            if(!list || !list.length){ var e = document.createElement('div'); e.style.padding='8px'; e.style.color='#666'; e.textContent='No services'; dd.appendChild(e); }
            else{ list.forEach(function(it){ var row = document.createElement('div'); row.className='item-row-suggest'; row.style.padding='8px'; row.style.cursor='pointer'; row.style.borderBottom='1px solid #f1f5f9'; var title = document.createElement('div'); title.style.fontWeight='600'; title.textContent = it.name || ''; var meta = document.createElement('div'); meta.style.fontSize='13px'; meta.style.color='#6b7280'; var metaParts = [];
                    if(it.code) metaParts.push('Code: '+it.code);
                    if(it.sale_price!==undefined) metaParts.push('Price: '+parseFloat(it.sale_price).toFixed(3));
                    meta.textContent = metaParts.join(' • ');
                    row.appendChild(title); row.appendChild(meta);
                    row.addEventListener('click', function(){ try{ var r = input.closest('.service-row'); input.value = it.name || ''; if(r){ r.dataset.serviceId = it.id; var rateEl = r.querySelector('.service-rate'); if(rateEl && it.sale_price!==undefined) rateEl.value = parseFloat(it.sale_price).toFixed(3); var qtyEl = r.querySelector('.service-qty'); if(qtyEl && !qtyEl.value) qtyEl.value = '1'; updateServiceRowAmount(r); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                                // fallback: if this row has a visible label and hidden input, update them directly
                                try{ var lbl = r.querySelector('.service-label'); var hidden = r.querySelector('.service-desc'); if(lbl) lbl.textContent = it.name || ''; if(hidden) hidden.value = it.name || ''; if(it.id) r.dataset.serviceId = it.id; }catch(e){}
                        }
                        // dispatch a custom event so callers can react to selection
                        try{ var ev = new CustomEvent('service-selected', { detail: it }); input.dispatchEvent(ev); }catch(e){}
                    }catch(err){ console.error(err); } close(); });
                    dd.appendChild(row);
                }); }
            // match inventory autocomplete visual behavior (box-sizing, shadow)
            dd.style.boxSizing = 'border-box';
            dd.style.boxShadow = '0 8px 30px rgba(2,6,23,0.06)';
            document.body.appendChild(dd); position(); window.addEventListener('scroll', position, true); window.addEventListener('resize', position);
        }
        function fetchAndRender(q){ var url = '/services/autocomplete/?q=' + encodeURIComponent(q||''); fetcher(url).then(function(data){ var list = (data && data.results)?data.results:[]; render(list.slice(0,50)); }).catch(function(){ close(); }); }
        // expose fetchAndRender on the input so callers can open suggestions programmatically
        try{ input._svcFetchAndRender = fetchAndRender; }catch(e){}
        input.addEventListener('input', function(){ var q = (input.value||'').trim(); if(timer) clearTimeout(timer); if(!q){ close(); return; } timer = setTimeout(function(){ fetchAndRender(q); }, 150); });
        input.addEventListener('blur', function(){ setTimeout(close,150); });
        input.addEventListener('click', function(){ var q = (input.value||'').trim(); if(!q) fetchAndRender(''); });
    }

    // NOTE: Removed the overly-broad document click fallback that created
    // service rows on any click inside the maintenance table. Row creation
    // must be driven by the Add Service button to avoid duplicate calls.

    function updateServiceRowAmount(row){ try{ var q = parseFloat(row.querySelector('.service-qty').value) || 0; var r = parseFloat(row.querySelector('.service-rate').value) || 0; var d = parseFloat(row.querySelector('.service-discount')? row.querySelector('.service-discount').value : 0) || 0; var amt = q * r * (1 - (d/100)); var amtEl = row.querySelector('.service-amount'); if(amtEl) amtEl.value = amt.toFixed(3); return amt; }catch(e){return 0;} }

        function createServiceRow(focus, attachToBody){ try{
                try{ if(window.__svcLogCreate) console.log('createServiceRow called', new Error().stack); }catch(e){}
                // strong re-entrancy guard to avoid concurrent creations from
                // multiple event sources. Tests can bypass by setting
                // `window.__svcAllowCreate`.
                if(window.__creatingServiceRow) return null;
                window.__creatingServiceRow = true;
                setTimeout(function(){ try{ window.__creatingServiceRow = false; }catch(e){} }, 300);
            // Only permit creating a new row appended to the services body when
            // the action was initiated by the Add Service button (which sets
            // `window._addingService`). Programmatic callers that do not want
            // an appended row should call with `attachToBody === false`.
            // Tests or special callers may temporarily set `window.__svcAllowCreate`.
            if (attachToBody !== false && !window._addingService && !window.__svcAllowCreate) {
                return null;
            }
            // prevent concurrent creations from multiple listeners/fires
            if(window._creatingServiceRow) return null;
            window._creatingServiceRow = true;
            setTimeout(function(){ try{ window._creatingServiceRow = false; }catch(e){} }, 300);
            if(!window._lastCreateServiceAt) window._lastCreateServiceAt = 0;
            var _now = Date.now();
            if(_now - window._lastCreateServiceAt < 300){ return null; }
            window._lastCreateServiceAt = _now;
            var body = document.getElementById('services-body');
            // if caller intends to attach to body, avoid adding a new empty row
            // when an empty service row already exists — focus and return it.
            if(attachToBody!==false && body){
                try{
                    // Prefer the existence flag when set (faster, and prevents
                    // DOM-based races). Fall back to DOM scan if flag not set.
                    
                    var existingEmpty = Array.prototype.slice.call(body.querySelectorAll('.service-row')).find(function(r){ try{ var lbl = r.querySelector('.service-label'); var txt = lbl ? (lbl.textContent||'').trim() : ''; return (!txt || txt === 'Click to add service'); }catch(e){ return false; } });
                    if(existingEmpty){ try{ var firstInput = existingEmpty.querySelector('.service-qty'); if(firstInput && focus!==false) firstInput.focus(); }catch(e){} return existingEmpty; }
                }catch(e){}
            }
            var tr = document.createElement('tr'); tr.className = 'service-row'; tr.innerHTML = '\
        <td style="padding:6px;vertical-align:middle;">\
              <div class="service-label" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;font-size:14px;color:#374151;font-weight:400;font-family:inherit;box-sizing:border-box;min-height:36px;height:36px;line-height:20px;display:block;background:#fff">&nbsp;</div>\
            <input type="hidden" class="service-desc" value=""/>\
        </td>\
        <td style="padding:6px;text-align:center;"><input type="number" class="service-qty" step="1" value="1" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;"/></td>\
        <td style="padding:6px;text-align:center;"><input type="number" class="service-rate" step="0.001" value="0.000" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;"/></td>\
        <td style="padding:6px;text-align:center;"><input type="number" class="service-discount" step="0.01" value="0.00" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;"/></td>\
        <td style="padding:6px;text-align:center;"><input type="text" class="service-amount" value="0.000" readonly style="width:100%;padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;"/></td>\
        <td style="padding:6px;text-align:center;"><button type="button" class="remove-service-row" style="background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;">×</button></td>'; 
            // append only if caller wants this row added to the services list
            if(attachToBody!==false){ if(!body) return null; body.appendChild(tr); }
            // mark: a service row was appended
        try{ var hiddenDesc = tr.querySelector('.service-desc'); var label = tr.querySelector('.service-label'); var qty = tr.querySelector('.service-qty'); var rate = tr.querySelector('.service-rate'); qty.addEventListener('input', function(){ updateServiceRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} }); rate.addEventListener('input', function(){ updateServiceRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
            // clicking the visible label opens an inline autocomplete input so user can pick a service
            if(label){ label.style.cursor = 'pointer';
                // placeholder style when empty
                if(!label.textContent || !label.textContent.trim() || label.textContent.trim()===''){
                    label.textContent = 'Click to add service'; label.style.color = '#6b7280';
                }
                label.addEventListener('click', function(){ try{ svcDebug('created-row: label clicked');
                    // if an edit input already exists, focus it
                    if(tr.querySelector('.service-desc-edit')){ tr.querySelector('.service-desc-edit').focus(); return; }
                    var inputEl = document.createElement('input'); inputEl.type = 'text'; inputEl.className = 'service-desc-edit'; inputEl.placeholder = 'Select service'; inputEl.style.width = '100%'; inputEl.style.padding = '6px'; inputEl.style.border = '1px solid #ddd'; inputEl.style.borderRadius = '6px';
                    inputEl.dataset.autocomplete = 'service';
                    // replace label with the inline input so layout/position matches item inputs
                    var originalLabel = label;
                    try{ label.parentNode.replaceChild(inputEl, label); }catch(e){ label.style.display = 'none'; label.parentNode.insertBefore(inputEl, label); }
                    // initialize autocomplete on this input
                    initServiceAutocomplete(inputEl);
                    // Ensure inventory autocomplete doesn't attach to this input and force service fetch on click
                    try{ inputEl._invInit = true; inputEl.setAttribute('autocomplete','off'); inputEl.addEventListener('click', function(ev){ ev.stopPropagation(); try{ if(inputEl._svcFetchAndRender) inputEl._svcFetchAndRender(''); }catch(e){} }); }catch(e){}
                    inputEl.focus();
                    // open suggestions immediately (use exposed function if available)
                    try{ setTimeout(function(){ try{ if(inputEl._svcFetchAndRender) inputEl._svcFetchAndRender(''); else inputEl.dispatchEvent(new MouseEvent('click', { bubbles: true })); }catch(e){} }, 40); }catch(e){}
                    // when a service is selected via autocomplete, copy value to hidden and restore label
                    function onSelected(ev){ try{ var it = ev && ev.detail ? ev.detail : null; var val = inputEl.value || (it && it.name) || ''; if(hiddenDesc) hiddenDesc.value = val; if(label) { label.textContent = val; label.style.color = '#374151'; } // set dataset if available
                                if(it && it.id) tr.dataset.serviceId = it.id; updateServiceRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} }catch(e){}
                        // cleanup - restore original label in place of the input
                        try{ inputEl.removeEventListener('service-selected', onSelected); }catch(e){};
                        try{ if(inputEl && inputEl.parentNode){ if(originalLabel){ inputEl.parentNode.replaceChild(originalLabel, inputEl); } else { inputEl.parentNode.removeChild(inputEl); } } }catch(e){};
                        try{ if(originalLabel) originalLabel.style.display = ''; }catch(e){};
                    }
                    inputEl.addEventListener('service-selected', onSelected);
                    // if user blurs without selecting, restore label and remove input
                    inputEl.addEventListener('blur', function(){ setTimeout(function(){ try{ // if suggestions are visible, keep the input so user can choose
                                if(document.querySelector && document.querySelector('.inventory-suggestions')) return; if(document.activeElement === inputEl) return; inputEl.removeEventListener('service-selected', onSelected); if(inputEl && inputEl.parentNode){ if(originalLabel) inputEl.parentNode.replaceChild(originalLabel, inputEl); else inputEl.parentNode.removeChild(inputEl); } if(originalLabel) originalLabel.style.display = ''; }catch(e){} }, 300); });
                }catch(e){} }); }
            if(focus!==false) { try{ var firstInput = tr.querySelector('.service-qty'); if(firstInput) firstInput.focus(); }catch(e){} }
        }catch(e){}
        return tr; }
        catch(e){ console.error('createServiceRow failed', e); return null; }
    }

    document.addEventListener('click', function(e){ try{ if(e.target && e.target.classList && e.target.classList.contains('remove-service-row')){ var r = e.target.closest('.service-row'); if(r) r.parentNode.removeChild(r); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} } }catch(err){}});
    // (no existence-flag cleanup needed)

    // attach behaviors to an existing service row (server-rendered)
    function attachServiceRowEvents(tr){
        try{
            if(!tr) return;
            var qty = tr.querySelector('.service-qty'); var rate = tr.querySelector('.service-rate');
            if(qty) qty.addEventListener('input', function(){ updateServiceRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
            if(rate) rate.addEventListener('input', function(){ updateServiceRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
            var label = tr.querySelector('.service-label'); var hiddenDesc = tr.querySelector('.service-desc');
            if(label){ label.style.cursor = 'pointer';
                label.addEventListener('click', function(){ try{ svcDebug('attach-row: label clicked (server-rendered)');
                    if(tr.querySelector('.service-desc-edit')){ tr.querySelector('.service-desc-edit').focus(); return; }
                    var inputEl = document.createElement('input'); inputEl.type = 'text'; inputEl.className = 'service-desc-edit'; inputEl.placeholder = 'Select service'; inputEl.style.width = '100%'; inputEl.style.padding = '6px'; inputEl.style.border = '1px solid #ddd'; inputEl.style.borderRadius = '6px';
                    inputEl.dataset.autocomplete = 'service';
                    var originalLabel = label;
                    try{ label.parentNode.replaceChild(inputEl, label); }catch(e){ label.style.display = 'none'; label.parentNode.insertBefore(inputEl, label); }
                    initServiceAutocomplete(inputEl);
                    // prevent inventory autocomplete from binding and force service suggestions
                    try{ inputEl._invInit = true; inputEl.setAttribute('autocomplete','off'); inputEl.addEventListener('click', function(ev){ ev.stopPropagation(); try{ if(inputEl._svcFetchAndRender) inputEl._svcFetchAndRender(''); }catch(e){} }); }catch(e){}
                    inputEl.focus();
                    try{ setTimeout(function(){ try{ if(inputEl._svcFetchAndRender) inputEl._svcFetchAndRender(''); else inputEl.dispatchEvent(new MouseEvent('click', { bubbles: true })); }catch(e){} }, 40); }catch(e){}
                    function onSelected(ev){ try{ var it = ev && ev.detail ? ev.detail : null; var val = inputEl.value || (it && it.name) || ''; if(hiddenDesc) hiddenDesc.value = val; if(label) { label.textContent = val; label.style.color = '#374151'; } if(it && it.id) tr.dataset.serviceId = it.id; updateServiceRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} }catch(e){}
                        try{ inputEl.removeEventListener('service-selected', onSelected); }catch(e){};
                        try{ if(inputEl && inputEl.parentNode){ if(originalLabel){ inputEl.parentNode.replaceChild(originalLabel, inputEl); } else { inputEl.parentNode.removeChild(inputEl); } } }catch(e){};
                        try{ if(originalLabel) originalLabel.style.display = ''; }catch(e){};
                    }
                    inputEl.addEventListener('service-selected', onSelected);
                    inputEl.addEventListener('blur', function(){ setTimeout(function(){ try{ if(document.querySelector && document.querySelector('.inventory-suggestions')) return; if(document.activeElement === inputEl) return; inputEl.removeEventListener('service-selected', onSelected); if(inputEl && inputEl.parentNode){ if(originalLabel) inputEl.parentNode.replaceChild(originalLabel, inputEl); else inputEl.parentNode.removeChild(inputEl); } if(originalLabel) originalLabel.style.display = ''; }catch(e){} }, 300); });
                }catch(e){} });
            }
        }catch(e){}
    }

    // delegated handler: ensure clicks on any `.service-label` open service autocomplete
    document.addEventListener('click', function(e){
        try{
            var t = e.target;
            if(!t || !t.classList) return;
            if(t.classList.contains('service-label')){
                svcDebug('delegated: service-label clicked');
                // if this label is already inside a service-row, attachServiceRowEvents should have set behavior
                var tr = t.closest('.service-row');
                if(tr) return; // already handled elsewhere
                // fallback: replace the label with an inline input and open service suggestions
                try{
                    if(t.querySelector && t.querySelector('.service-desc-edit')) return;
                    var inputEl = document.createElement('input');
                    inputEl.type = 'text'; inputEl.className = 'service-desc-edit'; inputEl.placeholder = 'Select service';
                    inputEl.style.width = '100%'; inputEl.style.padding = '6px'; inputEl.style.border = '1px solid #ddd'; inputEl.style.borderRadius = '6px';
                    inputEl.dataset.autocomplete = 'service';
                    var originalLabel = t;
                    try{ originalLabel.parentNode.replaceChild(inputEl, originalLabel); }catch(err){ originalLabel.style.display = 'none'; originalLabel.parentNode.insertBefore(inputEl, originalLabel); }
                    initServiceAutocomplete(inputEl);
                    try{ inputEl._invInit = true; inputEl.setAttribute('autocomplete','off'); inputEl.addEventListener('click', function(ev){ ev.stopPropagation(); try{ if(inputEl._svcFetchAndRender) inputEl._svcFetchAndRender(''); }catch(e){} }); }catch(e){}
                    inputEl.focus();
                    // Try to open suggestions immediately and again shortly after to avoid races
                    try{ if(inputEl._svcFetchAndRender) { try{ inputEl._svcFetchAndRender(''); }catch(e){} } else { try{ inputEl.dispatchEvent(new MouseEvent('click', { bubbles: true })); }catch(e){} } }catch(e){}
                    try{ setTimeout(function(){ try{ if(inputEl._svcFetchAndRender) inputEl._svcFetchAndRender(''); else inputEl.dispatchEvent(new MouseEvent('click', { bubbles: true })); }catch(e){} }, 180); }catch(e){}
                    // restore label on blur
                    inputEl.addEventListener('blur', function(){ setTimeout(function(){ try{ if(document.querySelector && document.querySelector('.inventory-suggestions')) return; if(document.activeElement === inputEl) return; if(inputEl && inputEl.parentNode){ inputEl.parentNode.replaceChild(originalLabel, inputEl); } if(originalLabel) originalLabel.style.display = ''; }catch(e){} }, 300); });
                }catch(err){}
            }
        }catch(e){}
    });

    window.createServiceRow = createServiceRow;
        window.serializeServiceItems = function(){ var out = []; document.querySelectorAll('.service-row').forEach(function(row){ try{ var svcId = row.dataset.serviceId ? parseInt(row.dataset.serviceId,10) : null; var desc = '';
            var hidden = row.querySelector('.service-desc'); if(hidden) desc = hidden.value || '';
            var label = row.querySelector('.service-label'); if(!desc && label) desc = label.textContent.trim();
            var qty = parseFloat(row.querySelector('.service-qty').value) || 0; var rate = parseFloat(row.querySelector('.service-rate').value) || 0; var discount = parseFloat(row.querySelector('.service-discount')? row.querySelector('.service-discount').value : 0) || 0; var amount = parseFloat(row.querySelector('.service-amount').value) || 0; var obj = { description: desc, qty: qty, rate: rate, discount: discount, amount: amount }; if(svcId) obj.service_id = svcId; out.push(obj); }catch(e){} }); return out; };

    window.initServicesTable = function(){ try{
        var btn = document.getElementById('add-service');
        // Prefer per-element dataset binding marker instead of a global boolean
        // so re-rendered DOM elements won't accidentally accumulate handlers.
        if(btn){
            try{
                if(btn.dataset.bound !== '1'){
                    btn.dataset.bound = '1';
                    // bind on the capture phase on the button so this handler runs
                    // before any other target/bubble listeners that may be added
                    // by other scripts. This ensures the Add button is the
                    // authoritative creator of service rows.
                    btn.addEventListener('click', function _svc_addServiceClick(e){
                        e.preventDefault();
                        e.stopPropagation();
                        try{ e.stopImmediatePropagation(); }catch(err){}
                        // simple per-button lock to stop multiple bound handlers from
                        // all executing their create logic on the same click.
                        if(btn.dataset.lock === '1') return;
                        btn.dataset.lock = '1';
                            try{
                                // set the older flag expected by createServiceRow so
                                // it allows an appended row when the Add button is used.
                                try{ window._addingService = true; }catch(e){}
                                try{ createServiceRow(true); }catch(err){}
                            }finally{
                                setTimeout(function(){ try{ window._addingService = false; }catch(e){} try{ delete btn.dataset.lock; }catch(e){} }, 300);
                            }
                    }, true);
                }
            }catch(e){}
        }
        // NOTE: Removed capture-phase guard — it interfered with the button's
        // own click handler by stopping propagation before target listeners run.
        // We rely on the Add button's handler calling stopImmediatePropagation()
        // to protect against other document-level listeners.
        // create initial row if none
        // initialize existing server-rendered service rows so their labels are editable
        try{ document.querySelectorAll('#services-body .service-row').forEach(function(r){ attachServiceRowEvents(r); }); }catch(e){}
        // debug: list server-rendered rows when debug enabled
        try{ svcDebug('initServicesTable: found ' + (document.querySelectorAll('#services-body .service-row').length) + ' service-row(s)'); document.querySelectorAll('#services-body .service-row').forEach(function(r,i){ try{ var lbl = r.querySelector('.service-label'); var hid = r.querySelector('.service-desc'); svcDebug('row['+i+'] dataset.serviceId='+(r.dataset.serviceId||'')+' labelExists='+(lbl?1:0)+' hiddenDesc='+(hid?hid.value:'(none)')); }catch(e){} }); }catch(e){}
        // defensive dedupe: remove duplicate visible `.service-label` elements not inside `#services-body`
        try{
            var seen = new Set();
            var serviceBodyIds = new Set(Array.from(document.querySelectorAll('#services-body .service-row')).map(function(r){ return r.dataset.serviceId || ''; }));
            document.querySelectorAll('.service-label').forEach(function(lbl){
                try{
                    var txt = (lbl.textContent||'').trim();
                    var tr = lbl.closest('tr');
                    var sid = tr && tr.dataset ? (tr.dataset.serviceId || '') : '';
                    var key = sid || txt;
                    if(sid && serviceBodyIds.has(sid)){
                        // we already have this service in the services tbody; remove duplicated label outside
                        if(!tr || !tr.classList.contains('service-row')){ svcDebug('dedupe: removing duplicate label for serviceId='+sid); if(lbl.parentNode) lbl.parentNode.removeChild(lbl); }
                    } else {
                        if(seen.has(key)){
                            svcDebug('dedupe: removing duplicate label for key='+key); if(lbl.parentNode) lbl.parentNode.removeChild(lbl);
                        } else {
                            seen.add(key);
                        }
                    }
                }catch(e){}
            });
        }catch(e){}
        // Ensure there is at least one service row on page load so the user
        // sees the `Service` row immediately when opening the add page.
        // Use the transient `_addingService` flag so `createServiceRow` permits
        // the append without relying on DOM-based existence checks.
        try{
            var _bodyInit = document.getElementById('services-body');
            if(_bodyInit && _bodyInit.querySelectorAll('.service-row').length === 0){
                try{ window._addingService = true; }catch(e){}
                try{ createServiceRow(true); }catch(e){}
                setTimeout(function(){ try{ window._addingService = false; }catch(e){} }, 200);
            }
        }catch(e){}
    }catch(e){ console.error('initServicesTable failed', e); } };

})();
