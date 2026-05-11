
    // Plate lookup removed: page no longer includes `id_plate_number` and `car-info-box`.
    // Previous code caused `Cannot read properties of null (reading 'addEventListener')`
    // which stopped all JS execution. Removed to keep autocomplete and buttons working.

    // --- Customer autocomplete ---
    var custInput = document.getElementById('customer-search');
    var custSuggestions = document.getElementById('customer-suggestions');
    var custTimer = null;
    function clearSuggestions(){
        try{
            try{ if(window.__suppressClearSuggestions){ try{ window.__suppressClearSuggestions = false; }catch(e){}; return; } }catch(e){}
            if(custSuggestions){ custSuggestions.innerHTML=''; custSuggestions.style.display = 'none'; }
        }catch(e){}
        try{
            // remove any inline suggestion boxes appended to .customer-selector containers
            document.querySelectorAll('.customer-selector > [role="listbox"]').forEach(function(el){ if(el && el.parentNode) el.parentNode.removeChild(el); });
        }catch(e){}
        var t = document.getElementById('customer-suggest-toggle'); if(t) t.textContent = '∨';
    }
    function renderSuggestions(list){
        try{
            try{ console.debug && console.debug('renderSuggestions called, items=', (list && list.length) || 0); }catch(e){}
            clearSuggestions();
            if(!list || !list.length) return;
            // determine live input and container: prefer the input's parent (.customer-selector)
            var liveInput = document.getElementById('customer-search');
            var container = (liveInput && liveInput.parentNode) ? liveInput.parentNode : custSuggestions;
            if(!container) return;
            try{ container.style.position = container.style.position || 'relative'; }catch(e){}

            var box = document.createElement('div');
            box.setAttribute('role','listbox');
            box.style.position='absolute';
            box.style.zIndex=500;
            box.style.background='#fff';
            box.style.border='1px solid #e6e6e6';
            box.style.width='100%';
            box.style.borderRadius='6px';
            box.style.top='100%';
            box.style.left='0';
            box.style.direction='ltr';

            // inline search box at top of suggestions
            var searchWrapper = document.createElement('div');
            searchWrapper.style.padding = '8px';
            var localSearch = document.createElement('input');
            localSearch.type = 'search';
            localSearch.placeholder = 'Search';
            localSearch.style.width = '100%';
            localSearch.style.boxSizing = 'border-box';
            localSearch.style.padding = '8px';
            localSearch.style.border = '1px solid #e6e6e6';
            localSearch.style.borderRadius = '6px';
            localSearch.style.fontSize = '14px';
            searchWrapper.appendChild(localSearch);
            box.appendChild(searchWrapper);

            var rowsContainer = document.createElement('div');
            function buildRows(sourceList){
                rowsContainer.innerHTML = '';
                sourceList.forEach(function(item){
                    var row = document.createElement('div');
                    row.style.padding='8px'; row.style.cursor='pointer'; row.style.borderBottom='1px solid #f1f5f9';
                    var nameDiv = document.createElement('div');
                    nameDiv.style.fontWeight = '600';
                    nameDiv.style.direction = 'rtl';
                    nameDiv.textContent = item.name;
                    var subDiv = document.createElement('div');
                    subDiv.className = 'small-muted';
                    subDiv.style.direction = 'ltr';
                    subDiv.style.fontSize = '13px';
                    subDiv.textContent = (item.phone||'') + (item.plates && item.plates.length ? ' • '+item.plates.join(', ') : '');
                    row.appendChild(nameDiv);
                    row.appendChild(subDiv);
                    row.addEventListener('click', function(e){
                        e.stopPropagation();
                        try{ document.getElementById('selected_client_id').value = item.id; }catch(ex){}
                        try{ var live = document.getElementById('customer-search'); if(live) live.value = item.name; }catch(ex){}
                        try{ console.debug && console.debug('customer selected (renderSuggestions):', item && (item.id||item.phone||item.name), item); }catch(ex){}
                        // if plates available, set the hidden plate_number and show it visibly
                        try{
                            var plateEl = document.getElementById('id_plate_number');
                            var showEl = document.getElementById('selected-plate');
                                if(item.plates && item.plates.length){
                                // if exactly one plate, set it; if multiple, show chooser to force explicit pick
                                if(item.plates.length === 1){
                                    var singlePlate = item.plates[0];
                                    if(plateEl) plateEl.value = singlePlate;
                                    // try to find matching car object for richer label
                                    var richLabel = singlePlate;
                                    if(item.cars && item.cars.length){
                                        for(var ii=0; ii<item.cars.length; ii++){
                                            var cc = item.cars[ii];
                                            if(cc.plate === singlePlate){
                                                var brRaw = (cc.brand && (cc.brand.name || cc.brand)) || '';
                                                var moRaw = (cc.model && (cc.model.name || cc.model)) || '';
                                                var br = (brRaw || '').toUpperCase();
                                                var mo = (moRaw || '').toUpperCase();
                                                var sfx = ((br? (br + ' '): '') + (mo || '')).trim();
                                                if(sfx) richLabel = singlePlate + ' - ' + sfx;
                                                break;
                                            }
                                        }
                                    }
                                    if(showEl){
                                        showEl.textContent = richLabel;
                                        showEl.style.background = 'transparent';
                                        showEl.style.border = '0';
                                        showEl.style.padding = '0';
                                    }
                                }
                                // if multiple plates, populate the `id_selected_client_car` select so the user chooses from a dropdown
                                if(item.plates.length > 1){
                                    try{
                                        var selectEl2 = document.getElementById('id_selected_client_car');
                                        var wrapper = document.getElementById('client-car-select-wrapper');
                                        if(selectEl2){
                                            selectEl2.innerHTML = '';
                                            // placeholder so user must choose explicitly
                                            var ph = document.createElement('option'); ph.value = ''; ph.text = 'Select vehicle'; ph.selected = true; ph.disabled = true; selectEl2.appendChild(ph);
                                            var carList = (item.cars && item.cars.length) ? item.cars : item.plates.map(function(p, idx){ return {id: null, plate: p}; });
                                            carList.forEach(function(c){
                                                var opt = document.createElement('option');
                                                opt.value = c.id || c.plate || '';
                                                var brandName = (c.brand && (c.brand.name || c.brand)) || '';
                                                var modelName = (c.model && (c.model.name || c.model)) || '';
                                                opt.setAttribute('data-plate', c.plate || '');
                                                opt.setAttribute('data-brand', brandName);
                                                opt.setAttribute('data-model', modelName);
                                                var label = (c.plate || '');
                                                var suffix = ((brandName? (brandName + ' ') : '') + (modelName || '')).trim();
                                                if(suffix) label = label + ' - ' + suffix;
                                                opt.text = label;
                                                selectEl2.appendChild(opt);
                                            });
                                            // show wrapper and focus select for user choice
                                            try{ if(wrapper) wrapper.style.display = ''; selectEl2.style.display = 'none'; var showEl = document.getElementById('selected-plate'); if(showEl) showEl.textContent = 'selection';
                                                // show vehicle toggle buttons when multiple plates
                                                try{ document.querySelectorAll('.vehicle-select-toggle').forEach(function(b){ b.style.display = ''; }); }catch(e){}
                                            }catch(e){}
                                        }
                                    }catch(e){ console.error('populate select error', e); }
                                    // remove any old chooser buttons if present
                                    var old = document.getElementById('plate-chooser'); if(old) old.parentNode.removeChild(old);
                                } else {
                                    // single plate: ensure wrapper visible and show plate text, hide select
                                    try{
                                        var wrapper = document.getElementById('client-car-select-wrapper');
                                        if(wrapper){ wrapper.style.display = ''; }
                                        var selectEl2 = document.getElementById('id_selected_client_car');
                                        if(selectEl2){ selectEl2.style.display = 'none'; }
                                        // hide vehicle toggle buttons for single plate
                                        try{ document.querySelectorAll('.vehicle-select-toggle').forEach(function(b){ b.style.display = 'none'; }); }catch(e){}
                                    }catch(e){}
                                    var old = document.getElementById('plate-chooser'); if(old) old.parentNode.removeChild(old);
                                }
                            } else {
                                if(plateEl) plateEl.value = '';
                                if(showEl) showEl.textContent = '';
                            }
                            // populate selected_client_car select if present
                            try{
                                var selectEl = document.getElementById('id_selected_client_car');
                                if(selectEl){
                                    // clear existing options
                                    selectEl.innerHTML = '';
                                    if(item.cars && item.cars.length){
                                        // placeholder option to force explicit selection
                                        var ph = document.createElement('option'); ph.value = ''; ph.text = 'Select vehicle'; ph.selected = true; ph.disabled = true; selectEl.appendChild(ph);
                                        item.cars.forEach(function(c){
                                            var opt = document.createElement('option'); opt.value = c.id || c.plate || '';
                                            var brandName = (c.brand && (c.brand.name || c.brand)) || '';
                                            var modelName = (c.model && (c.model.name || c.model)) || '';
                                            opt.setAttribute('data-plate', c.plate || '');
                                            opt.setAttribute('data-brand', brandName);
                                            opt.setAttribute('data-model', modelName);
                                            var label = (c.plate || '');
                                            var suffix = ((brandName? (brandName + ' ') : '') + (modelName || '')).trim();
                                            if(suffix) label = label + ' - ' + suffix;
                                            opt.text = label;
                                            selectEl.appendChild(opt);
                                        });
                                        // if exactly one car, hide the select and show plain text under the label
                                            if(item.cars.length === 1){
                                            try{ selectEl.style.display = 'none'; }catch(e){}
                                            try{ var only = item.cars[0]; var showEl = document.getElementById('selected-plate'); if(showEl){ var plateVal = only.plate || ''; var brRaw = (only.brand && (only.brand.name || only.brand)) || ''; var moRaw = (only.model && (only.model.name || only.model)) || ''; var br = (brRaw || '').toUpperCase(); var mo = (moRaw || '').toUpperCase(); var suffix = ''; if(br && mo){ suffix = br + ' - ' + mo; } else if(br){ suffix = br; } else if(mo){ suffix = mo; } var displayLabel = plateVal + (suffix? ('\t' + suffix) : ''); showEl.textContent = displayLabel; showEl.style.background = 'transparent'; showEl.style.border = '0'; showEl.style.padding = '0'; } }catch(e){}
                                            // hide toggle buttons for single-car case
                                            try{ document.querySelectorAll('.vehicle-select-toggle').forEach(function(b){ b.style.display = 'none'; }); }catch(e){}
                                            // also set the select's value for form submission (even if hidden)
                                            try{ selectEl.value = item.cars[0].id || item.cars[0].plate || ''; }catch(e){}
                                            } else {
                                                try{ selectEl.style.display = 'none'; var showEl = document.getElementById('selected-plate'); if(showEl) showEl.textContent = 'selection'; }catch(e){}
                                        }
                                    } else {
                                        try{ selectEl.style.display = 'none'; }catch(e){}
                                    }
                                }
                            }catch(ex){}
                        }catch(ex){}
                        clearSuggestions();
                    });
                    rowsContainer.appendChild(row);
                });
            }

            // initial fill (show many items; adjust limit if dataset is huge)
            var displayList = (list || []).slice(0,1000);
            buildRows(displayList);

            // filtering from search input
            localSearch.addEventListener('input', function(){
                var q = (localSearch.value||'').trim().toLowerCase();
                if(!q){ buildRows(displayList); return; }
                var filtered = list.filter(function(it){
                    return (it.name||'').toLowerCase().indexOf(q)!==-1 || (it.phone||'').indexOf(q)!==-1 || (it.plates && it.plates.join(' ').toLowerCase().indexOf(q)!==-1);
                });
                buildRows(filtered.slice(0,1000));
            });

            // prevent clicks inside box from bubbling to document click handler
            box.addEventListener('click', function(ev){ ev.stopPropagation(); });
            box.appendChild(rowsContainer);
            // append to the input's container so it visually sits below the input
            container.appendChild(box);
            // focus the inline search box
            try{ localSearch.focus(); }catch(e){}
            var t = document.getElementById('customer-suggest-toggle'); if(t) t.textContent = '∧';
        }catch(err){ console.error('renderSuggestions error', err); }
    }

    // showInlineSuggestions: used by the arrow toggle to show inline suggestions
    function showInlineSuggestions(q){
        try{ console.debug && console.debug('showInlineSuggestions called, q=', q, 'custSuggestions exists=', !!custSuggestions); }catch(e){}
        q = (q || '').trim();

        // if we have preloaded clients, filter locally
            if(window.clients_sample && window.clients_sample.length){
            if(!q){
                renderSuggestions(window.clients_sample.slice(0,1000));
            } else {
                var filtered = window.clients_sample.filter(function(it){
                    return (it.name||'').toLowerCase().indexOf(q.toLowerCase())!==-1 ||
                           (it.phone||'').indexOf(q)!==-1 ||
                           (it.plates && it.plates.join(' ').toLowerCase().indexOf(q.toLowerCase())!==-1);
                });
                renderSuggestions(filtered.slice(0,1000));
            }
            return;
        }

        // fallback: query server — use global `fetchJson` if available, otherwise use native fetch
        try{
            var __custFetcher = (typeof window.fetchJson === 'function') ? window.fetchJson : function(url){ return fetch(url, {credentials:'same-origin'}).then(function(r){ return r.json(); }); };
            __custFetcher('/clients/search/?q=' + encodeURIComponent(q)).then(function(data){ try{ console.debug && console.debug('showInlineSuggestions fetched', data); }catch(e){}; renderSuggestions(data.results||[]); }).catch(function(err){ console.error('clients search failed', err); });
        }catch(err){ try{ console.error('clients search failed', err); }catch(e){} }
    }
    if(custInput){
        // prevent direct typing into the main customer input; clicking/focusing it opens the dropdown
        document.addEventListener('click', function(e){
            var id = e.target && e.target.id;
            // ignore clicks inside the suggestions box or inside the selector controls
            if(e.target.closest && (e.target.closest('#customer-suggestions') || e.target.closest('.customer-selector'))) return;
            clearSuggestions();
        });
    }
    // hide client-car wrapper initially if no client selected
    try{
        var clientWrapper = document.getElementById('client-car-select-wrapper');
        var selectedClientId = (document.getElementById('selected_client_id') && document.getElementById('selected_client_id').value) || '';
        if(clientWrapper && !selectedClientId){ clientWrapper.style.display = 'none'; var sel = document.getElementById('id_selected_client_car'); if(sel) sel.style.display = 'none'; var sp = document.getElementById('selected-plate'); if(sp) sp.textContent = ''; }
        // if client exists but select is empty, leave the wrapper visible but keep select hidden until user toggles
        if(clientWrapper && selectedClientId){ try{ clientWrapper.style.display = ''; var sel = document.getElementById('id_selected_client_car'); if(sel && sel.options && sel.options.length<=1){ sel.style.display = 'none'; } }catch(e){} }
    }catch(e){}
    // magnifier button: show suggestions or open advanced modal
    var custBtn = document.getElementById('customer-search-btn');
    if(window.DEBUG) console.log('customer search elements:', {custBtnExists: !!custBtn, custInputExists: !!custInput, custSuggestionsExists: !!custSuggestions});
        // magnifier should open advanced modal
        if(custBtn){
                custBtn.addEventListener('click', function(e){
                if(window.DEBUG) console.log('customer-search-btn (magnifier) clicked');
                openCustomerModal(custInput ? custInput.value : '');
            });
            // fallback: make sure a direct onclick works even if event listeners are blocked
            custBtn.onclick = function(){ try{ openCustomerModal(custInput ? custInput.value : ''); }catch(err){ console.error(err); } };
        } else {
            console.warn('customer-search-btn not found — cannot attach click handler');
        }
        // arrow toggle: show inline suggestions
        var custToggle = document.getElementById('customer-suggest-toggle');
            if(custToggle){
                custToggle.addEventListener('click', function(e){
                e.stopPropagation();
                try{ window.__suppressClearSuggestions = true; }catch(e){}
                if(window.DEBUG) console.log('customer-suggest-toggle clicked');
                try{ window.toggleCustomerSuggestions(); }catch(err){ console.error(err); }
            });
            // fallback onclick to call the same toggle helper
            custToggle.onclick = function(e){ try{ e && e.stopPropagation(); window.toggleCustomerSuggestions(); }catch(err){ console.error(err); } };
        }

        // expose functions globally for debugging / inline onclick fallback
        try{ window.showInlineSuggestions = showInlineSuggestions; window.openCustomerModal = openCustomerModal; window.clearSuggestions = clearSuggestions; }catch(e){ /* ignore */ }

    // show inline suggestions on input focus
    if(custInput){
        custInput.addEventListener('focus', function(){
            try{ window.__suppressClearSuggestions = true; }catch(e){}
            try{ showInlineSuggestions(''); }catch(err){ console.error('showInlineSuggestions error', err); }
        });
        // also show suggestions when clicking the input (useful for clicking the caret)
        custInput.addEventListener('click', function(e){
            try{ window.__suppressClearSuggestions = true; }catch(e){}
            try{ showInlineSuggestions(''); }catch(err){ console.error('showInlineSuggestions error', err); }
        });
        // show suggestions on typing
        custInput.addEventListener('input', function(e){
            try{ showInlineSuggestions(e.target && e.target.value ? e.target.value : ''); }catch(err){ console.error('showInlineSuggestions error', err); }
        });
        // also open suggestions when clicking anywhere in the selector wrapper
        try{
            var custWrapperClick = document.querySelector('.customer-selector');
            if(custWrapperClick){
                custWrapperClick.addEventListener('click', function(e){
                    try{ window.__suppressClearSuggestions = true; }catch(err){}
                    try{ e && e.stopPropagation(); if(custInput) { try{ custInput.focus(); }catch(err){} } showInlineSuggestions(''); }catch(err){}
                });
                // keyboard accessibility: Enter or Space opens suggestions
                custWrapperClick.addEventListener('keydown', function(e){ try{ if(e.key === 'Enter' || e.key === ' ') { e.preventDefault(); if(custInput) custInput.focus(); showInlineSuggestions(''); } }catch(err){} });
            }
        }catch(e){}
    }

    // Toggle helper for inline onclick on the caret button
    try{
        window.toggleCustomerSuggestions = function(){
            try{
                if(!custSuggestions) return;
                var custToggle = document.getElementById('customer-suggest-toggle');
                var isOpen = (custSuggestions.style.display === 'block');
                if(isOpen){
                    // hide
                    custSuggestions.style.display = 'none';
                    custSuggestions.innerHTML = '';
                    if(custToggle) custToggle.textContent = '∨';
                } else {
                    // show full list (open unfiltered)
                    showInlineSuggestions('');
                    try{ custSuggestions.style.display = 'block'; }catch(e){}
                    if(custToggle) custToggle.textContent = '∧';
                }
            }catch(err){ console.error('toggleCustomerSuggestions error', err); }
        };
    }catch(e){ /* ignore */ }

    // --- Advanced modal search implementation ---
    function openCustomerModal(prefill){
        var backdrop = document.getElementById('customer-modal-backdrop');
        if(!backdrop) return;
        var input = document.getElementById('modal-customer-query');
        var resultsBox = document.getElementById('modal-customer-results');
        input.value = prefill || '';
        backdrop.style.display = 'flex';
        input.focus();
        performModalSearch(input.value||'');
        // attach handlers
        var closeBtn = backdrop.querySelector('.modal-close');
        if(closeBtn) closeBtn.onclick = closeCustomerModal;
        backdrop.onclick = function(e){ if(e.target === backdrop) closeCustomerModal(); };
        document.getElementById('modal-customer-search-btn').onclick = function(){ performModalSearch(document.getElementById('modal-customer-query').value||''); };
    }
    function closeCustomerModal(){
        var backdrop = document.getElementById('customer-modal-backdrop'); if(!backdrop) return; backdrop.style.display='none';
    }
    function performModalSearch(q){
        var resultsBox = document.getElementById('modal-customer-results');
        if(!resultsBox) return;
        resultsBox.innerHTML = '<div style="padding:12px;color:#666">Searching...</div>';
        try{
            var __modalFetcher = (typeof window.fetchJson === 'function') ? window.fetchJson : function(url){ return fetch(url, {credentials:'same-origin'}).then(function(r){ return r.json(); }); };
            __modalFetcher('/clients/search/?q=' + encodeURIComponent(q)).then(function(data){ renderModalResults(data.results || []); }).catch(function(err){ resultsBox.innerHTML = '<div style="padding:12px;color:#c00">Search failed</div>'; console.error('modal clients search failed', err); });
        }catch(e){ resultsBox.innerHTML = '<div style="padding:12px;color:#c00">Search failed</div>'; console.error('modal clients search failed', e); }
    }
    function renderModalResults(list){
        var resultsBox = document.getElementById('modal-customer-results'); if(!resultsBox) return; resultsBox.innerHTML = '';
        if(!list.length){ resultsBox.innerHTML = '<div style="padding:12px;color:#666">No results</div>'; return; }
        var tbl = document.createElement('table');
        var thead = document.createElement('thead'); thead.innerHTML = '<tr><th>CUSTOMER NAME</th><th>PHONE</th><th>PLATES</th></tr>'; tbl.appendChild(thead);
        var tbody = document.createElement('tbody');
        list.forEach(function(it){
            var tr = document.createElement('tr'); tr.style.cursor='pointer';
            var phones = it.phone || '';
            var plates = (it.plates && it.plates.length)? it.plates.join(', ') : '';
            tr.innerHTML = '<td style="color:#1976d2;font-weight:600">'+it.name+'</td><td>'+phones+'</td><td>'+plates+'</td>';
            tr.addEventListener('click', function(){ selectClientFromModal(it); });
            tbody.appendChild(tr);
            try{ window.__invBlockAutoOpenUntil = Date.now() + 400; }catch(e){}
        });
        tbl.appendChild(tbody); resultsBox.appendChild(tbl);
    }
    function selectClientFromModal(item){
        document.getElementById('selected_client_id').value = item.id;
        custInput.value = item.name;
        // populate select with car ids
        try{
            var selectEl = document.getElementById('id_selected_client_car');
            var wrapper = document.getElementById('client-car-select-wrapper');
            if(selectEl){
                selectEl.innerHTML = '';
                if(item.cars && item.cars.length){
                    item.cars.forEach(function(c){ var opt = document.createElement('option'); opt.value = c.id || c.plate || ''; var brandName = (c.brand && (c.brand.name || c.brand)) || ''; var modelName = (c.model && (c.model.name || c.model)) || ''; opt.setAttribute('data-plate', c.plate || ''); opt.setAttribute('data-brand', brandName); opt.setAttribute('data-model', modelName); var label = (c.plate||''); var suffix = ((brandName? (brandName + ' '):'') + (modelName||'')).trim(); if(suffix) label = label + ' - ' + suffix; opt.text = label; selectEl.appendChild(opt); });
                    if(item.cars.length === 1){
                        // single car: hide select, show plate text
                        try{ if(wrapper) wrapper.style.display = ''; selectEl.style.display = 'none'; var only = item.cars[0]; var showEl = document.getElementById('selected-plate'); if(showEl){ var plateVal = only.plate || ''; var brRaw = (only.brand && (only.brand.name || only.brand)) || ''; var moRaw = (only.model && (only.model.name || only.model)) || ''; var br = (brRaw || '').toUpperCase(); var mo = (moRaw || '').toUpperCase(); var suffix = ''; if(br && mo){ suffix = br + ' - ' + mo; } else if(br){ suffix = br; } else if(mo){ suffix = mo; } var displayLabel = plateVal + (suffix? ('\t' + suffix) : ''); showEl.textContent = displayLabel; showEl.style.background = 'transparent'; showEl.style.border = '0'; showEl.style.padding = '0'; } }catch(e){}
                        try{ selectEl.value = item.cars[0].id || item.cars[0].plate || ''; }catch(e){}
                    } else {
                        // multiple cars: show select and focus, show placeholder label
                        try{ if(wrapper) wrapper.style.display = ''; selectEl.style.display = 'none'; var showEl = document.getElementById('selected-plate'); if(showEl) showEl.textContent = 'selection'; }catch(e){}
                    }
                } else {
                    try{ if(wrapper) wrapper.style.display = 'none'; selectEl.style.display = 'none'; }catch(e){}
                }
            }
        }catch(e){}
        closeCustomerModal(); clearSuggestions();
    }

    // --- Items table logic ---
    function parseFloatSafe(v){ var n = parseFloat(v); return isNaN(n)?0:n; }
    function updateRowAmount(row){
        var q = parseFloatSafe(row.querySelector('.item-qty').value);
        var r = parseFloatSafe(row.querySelector('.item-rate').value);
        var d = parseFloatSafe(row.querySelector('.item-discount').value);
        var amt = q * r * (1 - d/100);
        row.querySelector('.item-amount').value = amt.toFixed(3);
        return amt;
    }
    function recomputeTotals(){
        var rows = document.querySelectorAll('#items-body .item-row');
        var subtotal = 0; var totalDiscount = 0;
        rows.forEach(function(row){
            var q = parseFloatSafe(row.querySelector('.item-qty').value);
            var r = parseFloatSafe(row.querySelector('.item-rate').value);
            var d = parseFloatSafe(row.querySelector('.item-discount').value);
            var line = q * r;
            var amt = updateRowAmount(row);
            subtotal += line;
            totalDiscount += (line - amt);
        });
        document.getElementById('sub-total').textContent = subtotal.toFixed(3);
        document.getElementById('total-discount').textContent = totalDiscount.toFixed(3);
        // services subtotal: sum any item-rows marked as service
        var svcSubtotal = 0;
        document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var isSvc = (row.dataset && row.dataset.type === 'service') || (row.querySelector && row.querySelector('.service-amount')); if(isSvc){ var el = row.querySelector('.service-amount') || row.querySelector('.item-amount'); svcSubtotal += parseFloat(el && el.value ? el.value : 0) || 0; } }catch(e){} });
        document.getElementById('services-sub-total').textContent = svcSubtotal.toFixed(3);
        var grand = (svcSubtotal + (subtotal - totalDiscount)).toFixed(3);
        document.getElementById('grand-total').textContent = grand;
        // update bottom total display (visible sticky bar)
        try{ var bottom = document.getElementById('bottom-total'); if(bottom) bottom.textContent = 'BHD ' + parseFloat(grand).toFixed(3); }catch(e){}
    }
    var __itemsBodyEl = document.getElementById('items-body');
    if(__itemsBodyEl){
        __itemsBodyEl.addEventListener('click', function(e){
            if(e.target && e.target.classList && e.target.classList.contains('remove-row')){
                var row = e.target.closest('.item-row');
                if(row && row.parentNode) row.parentNode.removeChild(row);
                try{ recomputeTotals(); }catch(e){}
            }
        });
        __itemsBodyEl.addEventListener('input', function(e){
            var el = e.target;
            if(!el) return;
            if(el.classList && (el.classList.contains('item-qty') || el.classList.contains('item-rate') || el.classList.contains('item-discount'))){
                var row = el.closest && el.closest('.item-row');
                try{ if(row) updateRowAmount(row); }catch(err){}
                try{ recomputeTotals(); }catch(err){}
                try{
                    if(el.classList.contains('item-qty')){
                        var avail = row && row.dataset && row.dataset.inventoryQty ? Number(row.dataset.inventoryQty) : undefined;
                        var trackStock = row && row.dataset && (row.dataset.inventoryTrackStock!==undefined) ? (row.dataset.inventoryTrackStock === 'true') : undefined;
                        var req = Number(el.value) || 0;
                        if(trackStock && avail !== undefined && !isNaN(avail) && req > avail){
                            try{ showAvailabilityModal('Insufficient stock: available ' + avail + ' • requested ' + req); }catch(ex){}
                        }
                    }
                }catch(ex){}
            }
        });
    }
    // helper: create and append a new item row, return the new row element
    // Prefer the canonical window.createItemRow when available to avoid dual factories
    var createItemRow = (function(){
        if(typeof window.createItemRow !== 'undefined'){
            return function(focus){ try{ return window.createItemRow(focus); }catch(e){ return null; } };
        }
        // Fallback inline factory (only used if canonical factory is not present)
        return function(focus){
            try{
                var _ctx = (window && window.ITEM_CONTEXT) ? window.ITEM_CONTEXT : (window.__isMaintenancePage ? 'maintenance' : 'invoice');
                if(_ctx === 'maintenance'){
                    // Legacy createServiceRow early-return removed to ensure
                    // the canonical createItemRow path is used for the first row.
                    try{
                        // fallthrough to unified factory below
                    }catch(e){}
                    try{
                        // Manual fallback replaced: prefer canonical factory and
                        // always append to the unified `#items-body` so the new
                        // `item-row` initialization path is used.
                        var itemsBody = document.getElementById('items-body') || document.getElementById('items-body-view') || document.body;
                        if(typeof window.createItemRow === 'function'){
                            try{
                                var newRow = window.createItemRow(focus===false?false:true);
                                if(newRow && itemsBody && newRow.parentNode !== itemsBody){ try{ itemsBody.appendChild(newRow); }catch(e){} }
                                return newRow;
                            }catch(e){}
                        }
                        // If canonical factory isn't available, fall through to the
                        // existing items-body inline fallback below (inventory-style row).
                    }catch(e){}
                }
            }catch(e){}
            try{ if(!window._lastCreateItemRowAt) window._lastCreateItemRowAt = 0; var now = Date.now(); if(now - window._lastCreateItemRowAt < 250){ return null; } window._lastCreateItemRowAt = now; }catch(e){}
            var tbody = document.getElementById('items-body');
            var tr = document.createElement('tr'); tr.className='item-row';
            try{ tr.dataset.rowId = 'row_' + Date.now() + '_' + Math.floor(Math.random()*1000); }catch(e){}
            tr.innerHTML = '' +
                '<td style="padding:6px;"><input type="text" class="item-desc" value="" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;"/> <div class="stock-display" style="margin-top:6px;color:#16a34a;font-weight:600;font-size:13px;"></div></td>' +
                '<td style="padding:6px;"><input type="number" class="item-qty" step="1" value="1" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;"/></td>' +
                '<td style="padding:6px;"><input type="number" class="item-rate" step="0.001" value="0.000" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;"/></td>' +
                '<td style="padding:6px;"><input type="number" class="item-discount" step="0.001" value="0.000" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;"/></td>' +
                '<td style="padding:6px 12px 6px 6px;"><input type="text" class="item-amount" value="0.000" readonly style="width:calc(100% - 12px);padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;box-sizing:border-box;"/></td>' +
                '<td style="padding:6px;text-align:center;"><button type="button" class="remove-row" style="background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;">×</button></td>';
            var inheritType;

            try{
                if(window.__lastCreatedFromRow){
                    try{
                        var src = window.__lastCreatedFromRow;

                        if(src && src.dataset && src.dataset.type === 'service'){
                            inheritType = 'service';
                        }
                    }catch(e){}

                    try{
                        window.__lastCreatedFromRow = null;
                    }catch(e){}
                }
            }catch(e){}

            try{
                if(inheritType){
                    tr.dataset.type = inheritType;
                }
            }catch(e){}
            tbody.appendChild(tr);
            try{ tr.dataset.__createdAt = Date.now(); }catch(e){}
            try{ var newInput = tr.querySelector('.item-desc'); if(newInput){ try{ if(tr && tr.dataset && tr.dataset.type === 'service') newInput.dataset.autocomplete = 'service'; }catch(e){} try{ if(!newInput.dataset.step) newInput.dataset.step = 'view'; }catch(e){} try{ if(typeof window.initInventoryRow === 'function') window.initInventoryRow(tr); else if(window.initInventoryAutocomplete) window.initInventoryAutocomplete(newInput); }catch(e){} if(focus!==false) newInput.focus(); } }catch(e){}
            try{ var qtyEl = tr.querySelector('.item-qty'); var stockEl = tr.querySelector('.stock-display'); if(qtyEl){ qtyEl.addEventListener('input', function(){ try{ var rowStock = tr.dataset.inventoryQty ? Number(tr.dataset.inventoryQty) : (tr.dataset.stock ? Number(tr.dataset.stock) : null); if(rowStock !== null && rowStock !== undefined && tr.dataset.inventoryTrackStock === 'true'){ var v = Number(qtyEl.value) || 0; if(v > rowStock){ try{ alert('⚠️ الكمية أكبر من المتوفر في المخزون'); }catch(e){} qtyEl.value = rowStock; try{ if(window.updateRowAmount) window.updateRowAmount(tr); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} } } }catch(e){} }); } }catch(e){}
            return tr;
        };
    })();

    var __addRowBtn = document.getElementById('add-row');
    if(__addRowBtn){ __addRowBtn.addEventListener('click', function(e){ try{ e.preventDefault(); e.stopPropagation(); }catch(ex){} try{ createItemRow(true); }catch(err){} }); try{ __addRowBtn.dataset.addlineBound = '1'; }catch(e){} }

    // --- Inventory autocomplete for Item Details ---
    var invTimer = null;
    function closeInventorySuggestionsFor(input){
        try{ var box = input.parentNode.querySelector('.inventory-suggestions'); if(box) box.parentNode.removeChild(box); }catch(e){}
    }
    function renderInventorySuggestionsFor(input, list){
        closeInventorySuggestionsFor(input);
        if(!list || !list.length) return;
        var wrapper = input.parentNode; // td
        try{ wrapper.style.position = wrapper.style.position || 'relative'; }catch(e){}
        var box = document.createElement('div');
        box.className = 'inventory-suggestions';
        // position the suggestions box below the input and allow scrolling
        try{
            box.style.position = 'absolute';
            box.style.left = '0px';
            box.style.right = '0px';
            box.style.top = (input.offsetHeight + 6) + 'px';
            box.style.zIndex = 1200;
            box.style.background = '#fff';
            box.style.border = '1px solid #e6e6e6';
            box.style.boxSizing = 'border-box';
            box.style.maxHeight = '220px';
            box.style.overflow = 'auto';
            box.style.borderRadius = '6px';
            box.style.boxShadow = '0 8px 30px rgba(2,6,23,0.06)';
            box.style.padding = '4px 0';
            box.style.width = '100%';
        }catch(e){ }
        list.forEach(function(it){
            var row = document.createElement('div'); row.className = 'item-row-suggest';
            row.style.padding = '8px';
            row.style.borderBottom = '1px solid #f1f5f9';
            // Title line with optional out-of-stock badge
            var title = document.createElement('div'); title.style.fontWeight='600'; title.style.marginBottom='4px';
            var nameText = it.name || (it.title||'');
            try{
                if(it.track_stock === true && (it.quantity===0 || it.quantity==='0')){
                    title.innerHTML = (nameText || '') + ' <span style="color:#b91c1c;font-weight:600;margin-left:6px;font-size:12px;">(Out of stock ⚠️)</span>';
                } else {
                    title.textContent = nameText;
                }
            }catch(e){ title.textContent = nameText; }
            // Meta line: Price and Available
            var meta = document.createElement('div'); meta.style.fontSize='13px'; meta.style.color='#6b7280';
            var _dispPrice = (it.price!==undefined) ? it.price : (it.sale_price!==undefined ? it.sale_price : undefined);
            var qty = (it.quantity!==undefined && it.quantity!==null) ? String(it.quantity) : null;
            var parts = [];
            if(_dispPrice!==undefined && _dispPrice!==null) parts.push('Price: <strong>' + parseFloat(_dispPrice).toFixed(3) + '</strong>');
            if(qty !== null) parts.push('Available: <strong>' + qty + '</strong>');
            meta.innerHTML = parts.join(' &nbsp;•&nbsp; ');
            row.appendChild(title); row.appendChild(meta);
            row.addEventListener('click', function(e){
                try{
                    if(!it || !it.name) return;
                    // Check availability if server provided `quantity`
                    var rowEl = input.closest('.item-row');
                    var requestedQty = 1;
                    try{ requestedQty = Number((rowEl && rowEl.querySelector('.item-qty')) ? rowEl.querySelector('.item-qty').value : 1) || 1; }catch(ex){}
                    // only enforce availability when the part explicitly tracks stock
                    if(it.track_stock === true && it.quantity !== undefined && Number(it.quantity) < requestedQty){
                        // show shortage modal and prevent selection
                        try{ showAvailabilityModal('Insufficient stock: available ' + (it.quantity||0) + ' • requested ' + requestedQty); }catch(ex){ console.error(ex); }
                        return;
                    }
                    input.value = it.name;
                    if(rowEl){
                        rowEl.dataset.inventoryId = it.id;
                        if(it.quantity!==undefined && it.quantity!==null) rowEl.dataset.inventoryQty = String(it.quantity);
                        if(it.track_stock!==undefined && it.track_stock!==null) rowEl.dataset.inventoryTrackStock = String(Boolean(it.track_stock));
                        var rateEl = rowEl.querySelector('.item-rate'); var _rateVal = (it.price!==undefined) ? it.price : (it.sale_price!==undefined ? it.sale_price : undefined); if(rateEl && _rateVal!==undefined) rateEl.value = parseFloat(_rateVal).toFixed(3);
                        // set stock display inside the row
                        try{
                            var stockEl = rowEl.querySelector('.stock-display');
                            if(stockEl){
                                if(it.track_stock){
                                    stockEl.innerText = 'Stock: ' + (it.quantity!==undefined && it.quantity!==null ? String(it.quantity) : '?');
                                    stockEl.style.color = (it.quantity!==undefined && it.quantity!==null && Number(it.quantity) > 0) ? '#16a34a' : '#b91c1c';
                                } else {
                                    stockEl.innerText = '';
                                }
                            }
                        }catch(ex){}
                        updateRowAmount(rowEl); recomputeTotals();
                        // attach qty clamp if needed
                        try{
                            var qtyEl = rowEl.querySelector('.item-qty');
                            if(qtyEl){
                                qtyEl.addEventListener('input', function(){
                                    try{
                                        var rowStock = rowEl.dataset.inventoryQty ? Number(rowEl.dataset.inventoryQty) : (rowEl.dataset.stock ? Number(rowEl.dataset.stock) : null);
                                        if(rowStock !== null && rowStock !== undefined && rowEl.dataset.inventoryTrackStock === 'true'){
                                            var v = Number(qtyEl.value) || 0;
                                            if(v > rowStock){
                                                try{ alert('⚠️ الكمية أكبر من المتوفر في المخزون'); }catch(e){}
                                                qtyEl.value = rowStock;
                                                try{ if(window.updateRowAmount) window.updateRowAmount(rowEl); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                                            }
                                        }
                                    }catch(e){}
                                });
                            }
                        }catch(ex){}
                    }
                }catch(err){console.error(err);} 
                // defer closing to allow selection side-effects to run first
                try{ setTimeout(function(){ try{ closeInventorySuggestionsFor(input); }catch(e){} }, 0); }catch(e){}
                // ensure there's always an empty row available: add one if none
                try{
                    var hasEmpty = false;
                    document.querySelectorAll('#items-body .item-desc').forEach(function(d){ if((d.value||'').trim()==='') hasEmpty = true; });
                    if(!hasEmpty){ try{ window.__lastCreatedFromRow = input.closest('.item-row') || null; }catch(e){} try{ createItemRow(true); }catch(e){} }
                }catch(ex){ /* ignore */ }
            });
            box.appendChild(row);
        });
        wrapper.appendChild(box);
    }

    // Compact, shared inventory autocomplete initializer
    (function(){
        function initInventoryAutocomplete(input){
            if(!input || input._invInit) return; input._invInit = true; try{ input._invBound = true; }catch(e){}
            var dd = null, timer = null, onWindowChange = null;
            var wrapper = input.parentNode; try{ wrapper.style.position = wrapper.style.position || 'relative'; }catch(e){}
            function close(){ if(dd){ try{ if(dd.parentNode) dd.parentNode.removeChild(dd); }catch(e){} dd = null; } if(onWindowChange){ window.removeEventListener('scroll', onWindowChange, true); window.removeEventListener('resize', onWindowChange); onWindowChange = null; } }
            function positionDropdown(){ if(!dd) return; try{ var rect = input.getBoundingClientRect(); dd.style.left = (rect.left + window.scrollX) + 'px'; dd.style.top = (rect.bottom + window.scrollY + 6) + 'px'; dd.style.width = rect.width + 'px'; }catch(e){}
            }
            function render(list){ close();
                dd = document.createElement('div'); dd.className='inventory-suggestions'; dd.style.position = 'absolute'; dd.style.zIndex = 9999; dd.style.boxSizing = 'border-box'; dd.style.maxHeight = '260px'; dd.style.overflow = 'auto'; dd.style.border = '1px solid #e6e6e6'; dd.style.background = '#fff'; dd.style.borderRadius = '6px'; dd.style.boxShadow = '0 8px 30px rgba(2,6,23,0.06)'; dd.style.padding = '4px 0';
                if(!list || !list.length){ var empty = document.createElement('div'); empty.style.padding='8px'; empty.style.color='#666'; empty.textContent = 'No items'; dd.appendChild(empty); }
                else{
                    list.forEach(function(it){
                        var row = document.createElement('div'); row.className='item-row-suggest'; row.style.padding='8px'; row.style.cursor='pointer'; row.style.borderBottom='1px solid #f1f5f9';
                        var title = document.createElement('div'); title.style.fontWeight='600'; title.textContent = it.name || (it.title||'');
                        var meta = document.createElement('div'); meta.style.fontSize='13px'; meta.style.color='#6b7280';
                        var parts = [];
                        if(it.code) parts.push('Code: '+it.code);
                        if(it.sku) parts.push('SKU: '+it.sku);
                        var _dispPrice2 = (it.price!==undefined) ? it.price : (it.sale_price!==undefined ? it.sale_price : undefined);
                        if(_dispPrice2!==undefined) parts.push('Price: '+parseFloat(_dispPrice2).toFixed(3));
                        if(it.quantity!==undefined && it.quantity!==null) parts.push('Available: '+String(it.quantity));
                        meta.textContent = parts.join(' • ');
                        row.appendChild(title); row.appendChild(meta);
                        row.addEventListener('click', function(e){
                            e.stopPropagation();
                            try{
                                var idCandidate = item.id || item.pk || item.client_id || item.clientId || item._id || '';
                                try{ var selEl = document.getElementById('selected_client_id'); if(selEl) selEl.value = idCandidate; }catch(ex){}
                                try{ window.currentCustomerId = idCandidate; }catch(ex){}
                                try{ console.debug && console.debug('customer selected (renderSuggestions):', idCandidate, item); }catch(ex){}
                            }catch(e){}
                            try{ var live = document.getElementById('customer-search'); if(live) live.value = item.name; }catch(ex){}
                            // if plates available, set the hidden plate_number and show it visibly
                                try{ requestedQty = Number((rowEl && rowEl.querySelector('.item-qty'))?rowEl.querySelector('.item-qty').value:1)||1; }catch(e){}
                                if(it.track_stock === true && it.quantity!==undefined && Number(it.quantity) < requestedQty){ showAvailabilityModal('Insufficient stock: available '+(it.quantity||0)+' • requested '+requestedQty); return; }
                                input.value = it.name;
                                if(rowEl){ rowEl.dataset.inventoryId = it.id; if(it.quantity!==undefined) rowEl.dataset.inventoryQty = String(it.quantity); if(it.track_stock!==undefined) rowEl.dataset.inventoryTrackStock = String(Boolean(it.track_stock)); var rateEl = rowEl.querySelector('.item-rate'); var _rv = (it.price!==undefined) ? it.price : (it.sale_price!==undefined ? it.sale_price : undefined); if(rateEl && _rv!==undefined) rateEl.value = parseFloat(_rv).toFixed(3); updateRowAmount(rowEl); recomputeTotals(); }
                            }catch(e){ console.error(e); }
                            try{ setTimeout(function(){ try{ close(); }catch(e){} }, 0); }catch(e){}
                            try{ var hasEmpty=false; document.querySelectorAll('#items-body .item-desc').forEach(function(d){ if((d.value||'').trim()==='') hasEmpty=true; }); if(!hasEmpty){ try{ window.__lastCreatedFromRow = rowEl || null; }catch(e){} try{ createItemRow(true); }catch(e){} } }catch(e){}
                        });
                        dd.appendChild(row);
                    });
                }
                // append to body (or use dropdown manager) so it's not clipped by table overflow
                try{ if(window.dropdownManager && typeof window.dropdownManager.open === 'function'){ dd.setAttribute('data-dropdown-owner','inventory'); window.dropdownManager.open(dd,'inventory'); } else { document.body.appendChild(dd); } }catch(e){}
                positionDropdown();
                onWindowChange = function(){ positionDropdown(); };
                window.addEventListener('scroll', onWindowChange, true);
                window.addEventListener('resize', onWindowChange);
            }
            function fetchAndRender(q){
                var fetchFn = (window.fetchInventory) ? window.fetchInventory : function(u){
                    var fetcher = (window.fetchJson)?window.fetchJson:function(url){ return fetch(url).then(function(r){ return r.json(); }); };
                    // If query is empty, request the server endpoint without the q param
                    // so the backend can return a default/popular list. Otherwise use q.
                    try{
                        if(!u || (typeof u === 'string' && u.trim() === '')){
                            return fetcher('/inventory/json/').then(function(d){ return (d && d.results)? d.results : []; });
                        }
                    }catch(e){}
                    return fetcher('/inventory/json/?q=' + encodeURIComponent(u||'')).then(function(d){ return (d && d.results)? d.results : []; });
                };
                return fetchFn(q).then(function(list){
                    var mapped = (list||[]).map(function(it){ return { id: it.id, name: it.name||it.title||'', code: it.code||'', sku: it.sku||'', price: (it.sale_price!==undefined)?parseFloat(it.sale_price):(it.price!==undefined?parseFloat(it.price):undefined), quantity: (it.quantity!==undefined && it.quantity!==null)?Number(it.quantity):undefined, track_stock: (it.track_stock!==undefined && it.track_stock!==null)?Boolean(it.track_stock):undefined }; });
                    render(mapped.slice(0,50));
                }).catch(function(){ close(); });
            }
                input.addEventListener('input', function(){ var q = (input.value||'').trim(); if(timer) clearTimeout(timer); if(!q){ // allow empty query to show default list
                    timer = setTimeout(function(){ fetchAndRender(''); }, 160); return; } timer = setTimeout(function(){ fetchAndRender(q); }, 160); });
                // ensure focus and click open the dropdown even without typing
                try{ input.addEventListener('focus', function(){ try{ if(timer) clearTimeout(timer); timer = setTimeout(function(){ fetchAndRender((input.value||'').trim()||''); }, 40); }catch(e){} }); }catch(e){}
                try{ input.addEventListener('click', function(){ try{ if(timer) clearTimeout(timer); timer = setTimeout(function(){ fetchAndRender((input.value||'').trim()||''); }, 40); }catch(e){} }); }catch(e){}
            // open suggestions on user click/focus or when there's existing content
            var _invPointerActivate = false;
            input.addEventListener('pointerdown', function(){ _invPointerActivate = true; setTimeout(function(){ _invPointerActivate = false; }, 250); });
            input.addEventListener('focus', function(){ try{ fetchAndRender((input.value||'').trim() || ''); }catch(e){} });
            // also open suggestions on user click when the field is empty
            input.addEventListener('click', function(e){ try{ fetchAndRender((input.value||'').trim() || ''); }catch(e){} });
            input.addEventListener('blur', function(){ setTimeout(close,150); setTimeout(function(){ lookupPartPrice(input.value).then(function(price){ if(price!==null){ try{ var tr = input.closest('.item-row'); var rateEl = tr && tr.querySelector('.item-rate'); if(rateEl) { rateEl.value = parseFloat(price).toFixed(3); updateRowAmount(tr); recomputeTotals(); } }catch(e){} } }); },180); });
        }
        if(typeof window.initInventoryAutocomplete === 'undefined'){
            window.initInventoryAutocomplete = initInventoryAutocomplete;
        }
    })();

    // attach to any existing item-desc inputs
    // if there are no rows yet, create an initial empty row (skip on maintenance page)
    if(document.querySelectorAll('#items-body .item-row').length === 0 && !window.__isMaintenancePage){ createItemRow(false); }
    document.querySelectorAll('#items-body .item-desc').forEach(function(inp){ try{ window.initInventoryAutocomplete(inp); }catch(e){} });
    // ensure totals and bottom total reflect any server-rendered rows
    try{ recomputeTotals(); }catch(e){}

    // close inventory suggestions when clicking elsewhere (do not close merged svc dropdowns)
    document.addEventListener('click', function(ev){
        try{
            // keep dropdown open when interacting with the input or the dropdown itself
            if(ev.target && ev.target.closest && (ev.target.closest('.inventory-suggestions') || ev.target.closest('.svc-dd') || ev.target.closest('.item-desc'))) return;
            // remove all inventory suggestion boxes
            document.querySelectorAll('.inventory-suggestions').forEach(function(b){ b.parentNode && b.parentNode.removeChild(b); });
        }catch(e){}
    });

    // When the user changes the vehicle select, update the hidden plate and visible label
    try{
        var carSelect = document.getElementById('id_selected_client_car');
        if(carSelect){
            carSelect.addEventListener('change', function(){
                try{
                    var opt = this.options[this.selectedIndex];
                    var plate = (opt && opt.getAttribute) ? (opt.getAttribute('data-plate') || opt.value) : (opt ? opt.value : '');
                    var plateField = document.getElementById('id_plate_number'); if(plateField) plateField.value = plate;
                    var showEl = document.getElementById('selected-plate'); if(showEl){ var plateVal = (opt && opt.getAttribute) ? (opt.getAttribute('data-plate') || opt.value) : (opt ? opt.value : ''); var br = ((opt && opt.getAttribute) ? (opt.getAttribute('data-brand') || '') : '') .toUpperCase(); var mo = ((opt && opt.getAttribute) ? (opt.getAttribute('data-model') || '') : '') .toUpperCase(); var suffix = ''; if(br && mo){ suffix = br + ' - ' + mo; } else if(br){ suffix = br; } else if(mo){ suffix = mo; } var displayLabel = plateVal + (suffix? ('\t' + suffix) : ''); showEl.textContent = displayLabel; showEl.style.background = 'transparent'; showEl.style.border = '0'; showEl.style.padding = '0'; }
                }catch(e){/* ignore */}
            });
        }
    }catch(e){/* ignore */}

    // Toggle the vehicle select when the user clicks any small arrow button
    try{
        var vehToggles = document.querySelectorAll('.vehicle-select-toggle');
        if(vehToggles && vehToggles.length){
            vehToggles.forEach(function(btn){
                btn.addEventListener('click', function(){
                    try{
                        var sel = document.getElementById('id_selected_client_car');
                        if(!sel) return;
                        // Always show the select (do not fallback to modal). User expects the dropdown.
                        if(!sel.style.display || sel.style.display === 'none'){
                            sel.style.display = '';
                            try{ sel.focus(); }catch(e){}
                        } else {
                            sel.style.display = 'none';
                        }
                    }catch(e){/* ignore */}
                });
            });
        }
    }catch(e){}

    // allow clicking the visible plate label to open the select for multi-car clients
    try{
        var sp = document.getElementById('selected-plate');
        if(sp){
            sp.style.cursor = 'pointer';
            sp.addEventListener('click', function(){
                try{
                    var sel = document.getElementById('id_selected_client_car');
                    if(!sel) return;
                    if(sel.options && sel.options.length > 1){ sel.style.display = ''; try{ sel.focus(); }catch(e){} }
                }catch(e){}
            });
        }
    }catch(e){}

    // Availability modal helper
    function showAvailabilityModal(message){
        try{
            var mb = document.getElementById('availability-modal-backdrop');
            if(!mb){
                mb = document.createElement('div'); mb.id = 'availability-modal-backdrop'; mb.style.position='fixed'; mb.style.left='0'; mb.style.top='0'; mb.style.right='0'; mb.style.bottom='0'; mb.style.background='rgba(0,0,0,0.5)'; mb.style.display='flex'; mb.style.alignItems='center'; mb.style.justifyContent='center'; mb.style.zIndex=2000;
                var card = document.createElement('div'); card.style.background='#fff'; card.style.padding='18px'; card.style.borderRadius='8px'; card.style.maxWidth='560px'; card.style.width='90%'; card.style.boxShadow='0 8px 30px rgba(2,6,23,0.2)';
                var h = document.createElement('div'); h.style.fontWeight='700'; h.style.marginBottom='8px'; h.textContent = 'Stock Alert';
                var p = document.createElement('div'); p.id='availability-modal-message'; p.style.marginBottom='12px'; p.style.color='#111';
                var btn = document.createElement('button'); btn.textContent='Close'; btn.style.padding='8px 12px'; btn.style.border='none'; btn.style.background='#1976d2'; btn.style.color='#fff'; btn.style.borderRadius='6px'; btn.style.cursor='pointer';
                btn.onclick = function(){ try{ mb.style.display='none'; }catch(e){} };
                card.appendChild(h); card.appendChild(p); card.appendChild(btn); mb.appendChild(card); document.body.appendChild(mb);
            }
            var msgEl = document.getElementById('availability-modal-message'); if(msgEl) msgEl.textContent = message || '';
            mb.style.display = 'flex';
        }catch(e){ console.error('showAvailabilityModal failed', e); }
    }

    // serialize items into hidden input on submit
    document.getElementById('maintenance-form').addEventListener('submit', function(e){
        // Require explicit vehicle selection for clients with multiple cars
        try{
            var sel = document.getElementById('id_selected_client_car');
            var selectedClientId = document.getElementById('selected_client_id') && document.getElementById('selected_client_id').value;
            if(sel && selectedClientId){
                // if there are real options (more than the placeholder) and no selection
                var realOptions = Array.prototype.slice.call(sel.options).filter(function(o){ return o.value && !o.disabled; });
                if(realOptions.length > 1 && (!sel.value || sel.value === '')){
                    // show inline error near selector instead of alert
                    e.preventDefault();
                    try{
                        var warn = document.getElementById('vehicle-select-warning');
                        if(!warn){ warn = document.createElement('div'); warn.id = 'vehicle-select-warning'; warn.style.color = '#b71c1c'; warn.style.marginTop = '6px'; warn.style.fontWeight = '600'; warn.textContent = 'Please select a vehicle for the chosen customer.'; var wrapper = document.getElementById('client-car-select-wrapper'); if(wrapper) wrapper.appendChild(warn); }
                        // open and focus select
                        sel.style.display = '';
                        try{ sel.focus(); }catch(e){}
                    }catch(err){}
                    return;
                }
            }
        }catch(err){}
        recomputeTotals();
        var items = [];
        // include services first (mark with service_id when available)
        try{
            if(window.serializeServiceItems){
                var svcs = window.serializeServiceItems();
                svcs.forEach(function(it){ items.push(it); });
            } else {
                // fallback: read any service-typed rows inside the unified items table
                document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var isSvc = (row.dataset && row.dataset.type === 'service') || (row.querySelector && row.querySelector('.service-amount')); if(isSvc){ items.push({ description: (row.querySelector('.item-desc') && row.querySelector('.item-desc').value) || (row.querySelector('.service-desc') && row.querySelector('.service-desc').value) || '', qty: parseFloatSafe((row.querySelector('.item-qty') || row.querySelector('.service-qty')) ? ((row.querySelector('.item-qty')||row.querySelector('.service-qty')).value) : 0), rate: parseFloatSafe((row.querySelector('.item-rate') || row.querySelector('.service-rate')) ? ((row.querySelector('.item-rate')||row.querySelector('.service-rate')).value) : 0), discount: parseFloatSafe((row.querySelector('.item-discount') || row.querySelector('.service-discount')) ? ((row.querySelector('.item-discount')||row.querySelector('.service-discount')).value) : 0), amount: parseFloatSafe((row.querySelector('.item-amount') || row.querySelector('.service-amount')) ? ((row.querySelector('.item-amount')||row.querySelector('.service-amount')).value) : 0), service_id: row.dataset && row.dataset.serviceId ? parseInt(row.dataset.serviceId,10) : null }); } }catch(e){} });
            }
        }catch(e){}
        // then include parts items (require part_id)
        document.querySelectorAll('#items-body .item-row').forEach(function(row){
            try{
                var partId = row.dataset.partId || row.dataset.inventoryId || null;
                var rowType = (row.dataset && row.dataset.type) ? row.dataset.type : null;
                // If this row was marked as a service (some service selections
                // are created inside the items table), serialize it as a service
                // entry instead of enforcing a part_id.
                if(rowType === 'service'){
                    try{
                        items.push({
                            service_id: row.dataset && row.dataset.serviceId ? parseInt(row.dataset.serviceId,10) : null,
                            description: row.querySelector('.item-desc') ? (row.querySelector('.item-desc').value||'') : '',
                            qty: parseFloatSafe(row.querySelector('.item-qty') ? row.querySelector('.item-qty').value : 0),
                            rate: parseFloatSafe(row.querySelector('.item-rate') ? row.querySelector('.item-rate').value : 0),
                            discount: parseFloatSafe(row.querySelector('.item-discount') ? row.querySelector('.item-discount').value : 0),
                            amount: parseFloatSafe(row.querySelector('.item-amount') ? row.querySelector('.item-amount').value : 0)
                        });
                    }catch(e){}
                    return;
                }
                // For regular part rows, require a linked part id to avoid
                // ambiguous free-text entries.
                if(!partId) return; // skip rows without linked part
                items.push({
                    part_id: partId,
                    description: row.querySelector('.item-desc').value,
                    qty: parseFloatSafe(row.querySelector('.item-qty').value),
                    rate: parseFloatSafe(row.querySelector('.item-rate').value),
                    discount: parseFloatSafe(row.querySelector('.item-discount').value),
                    amount: parseFloatSafe(row.querySelector('.item-amount').value)
                });
            }catch(e){}
        });
        document.getElementById('items_json').value = JSON.stringify(items);
    });
    // Serializer is provided by `static/js/line-items.core.js` (canonical implementation);
    // inline duplicate removed to ensure single source of truth.

    // Expose helpers globally so fallback handlers can call them if needed
    try{
        if(typeof window.createItemRow === 'undefined'){
            window.createItemRow = createItemRow;
        }
        // ensure both old and new global names point to the same initializer
        try{ window.initInventoryAutocomplete = window.initInventoryAutocomplete || initInventoryAutocomplete; }catch(e){}
        // showInlineSuggestions and openCustomerModal are also exposed earlier
    }catch(e){ console.error('expose helpers failed', e); }

    // Ensure serialization runs just before any form submit as a safety net
    try{
        var _form = document.getElementById('maintenance-form');
        if(_form){
            _form.addEventListener('submit', function(evt){
                try{ if(window.serializeMaintenanceItems) window.serializeMaintenanceItems(); }catch(err){}
            }, false);
        }
    }catch(e){}

    // Delegated click fallback: handle clicks on controls even if their
    // original listeners failed to attach (safety net for broken/aborted scripts)
    document.addEventListener('click', function(e){
        try{
            var t = e.target;
            if(!t) return;
            // Add New Row
            if(t.id === 'add-row' || (t.closest && t.closest('#add-row'))){
                e.preventDefault();
                try{ if(window.createItemRow) window.createItemRow(true); }catch(err){ console.error('createItemRow failed', err); }
                return;
            }
            // Magnifier: open advanced customer modal
            if(t.id === 'customer-search-btn' || (t.closest && t.closest('#customer-search-btn'))){
                e.preventDefault();
                try{ if(window.openCustomerModal) window.openCustomerModal((document.getElementById('customer-search')||{}).value||''); }catch(err){ console.error('openCustomerModal failed', err); }
                return;
            }
            // Caret toggle: show inline suggestions
            if(t.id === 'customer-suggest-toggle' || (t.closest && t.closest('#customer-suggest-toggle'))){
                e.preventDefault();
                try{ if(window.toggleCustomerSuggestions) window.toggleCustomerSuggestions(); else if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(err){ console.error('toggleCustomerSuggestions/showInlineSuggestions failed', err); }
                return;
            }
            // Click on the main customer input should show inline suggestions
            if(t.id === 'customer-search' || (t.closest && t.closest('#customer-search'))){
                try{ if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(err){}
                return;
            }
        }catch(e){ console.error('delegated click handler error', e); }
    });
    // Ensure the visible selected-plate includes brand/model when available
    try{
        var sp = document.getElementById('selected-plate');
        if(sp && sp.textContent && sp.textContent.trim()){
            var text = sp.textContent.trim();
            // if already contains a dash, likely includes brand/model
            if(text.indexOf('-') === -1){
                var brand = '';
                var model = '';
                var wrapper = document.getElementById('client-car-select-wrapper');
                if(wrapper){ brand = wrapper.getAttribute('data-brand') || wrapper.dataset.brand || ''; model = wrapper.getAttribute('data-model') || wrapper.dataset.model || ''; }
                // try select option
                if((!brand && !model)){
                    var sel = document.getElementById('id_selected_client_car');
                    if(sel && sel.options && sel.options.length){ var opt = sel.options[sel.selectedIndex] || sel.options[0]; if(opt){ brand = opt.getAttribute('data-brand') || opt.dataset.brand || ''; model = opt.getAttribute('data-model') || opt.dataset.model || ''; } }
                }
                // try clients_sample fallback
                if((!brand && !model) && window.clients_sample && window.clients_sample.length){
                    try{
                        var cid = (document.getElementById('selected_client_id') && document.getElementById('selected_client_id').value) || '';
                        if(cid){
                            var clientObj = window.clients_sample.find(function(c){ return String(c.id) === String(cid); });
                            if(clientObj && clientObj.cars && clientObj.cars.length){
                                var plateOnly = text.split(/\s+/)[0];
                                for(var i=0;i<clientObj.cars.length;i++){ var cc = clientObj.cars[i]; if((cc.plate||'') === plateOnly){ brand = (cc.brand && (cc.brand.name || cc.brand)) || ''; model = (cc.model && (cc.model.name || cc.model)) || ''; break; } }
                            }
                        }
                    }catch(e){}
                }
                if(brand || model){ var br = (brand||'').toUpperCase(); var mo = (model||'').toUpperCase(); var suffix = ''; if(br && mo) suffix = ' ' + br + ' - ' + mo; else if(br) suffix = ' ' + br; else if(mo) suffix = ' ' + mo; sp.textContent = text + suffix; }
            }
        }
    }catch(e){}
});
    // Fallback initializer: ensure customer-search is editable and has handlers
    try{
        (function(){
            var el = document.getElementById('customer-search');
            var btn = document.getElementById('customer-search-btn');
            var tog = document.getElementById('customer-suggest-toggle');
            if(el){
                try{ el.readOnly = false; el.removeAttribute && el.removeAttribute('readonly'); el.disabled = false; el.style.pointerEvents = 'auto'; }catch(e){}
                if(!el._custFallbackBound){
                    el.addEventListener('click', function(ev){ try{ ev && ev.stopPropagation && ev.stopPropagation(); if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(e){} });
                    el.addEventListener('focus', function(ev){ try{ if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(e){} });
                    el._custFallbackBound = true;
                }
            }
            if(btn && !btn._custFallback){
                btn.addEventListener('click', function(ev){ try{ ev && ev.preventDefault && ev.preventDefault(); if(window.openCustomerModal) window.openCustomerModal(el?el.value:''); else { var bd = document.getElementById('customer-modal-backdrop'); if(bd){ bd.style.display='flex'; var minp = document.getElementById('modal-customer-query'); if(minp){ minp.value = (el && el.value) || ''; minp.focus(); } try{ if(typeof performModalSearch === 'function') performModalSearch(minp?minp.value:''); }catch(e){} } } }catch(e){} });
                btn._custFallback = true;
            }
            if(tog && !tog._custFallback){
                tog.addEventListener('click', function(ev){ try{ ev && ev.stopPropagation && ev.stopPropagation(); if(window.toggleCustomerSuggestions) window.toggleCustomerSuggestions(); else if(window.showInlineSuggestions) window.showInlineSuggestions(''); }catch(e){} });
                tog._custFallback = true;
            }
        })();
    }catch(e){}
