(function(){
    // Item table helper for maintenance page
    // Exposes: window.createItemRow(), window.updateRowAmount(), window.serializeMaintenanceItems(), window.initItemsTable(), window.recomputeTotals()

    function toFixed3(v){ try{ return parseFloat(v||0).toFixed(3); }catch(e){ return '0.000'; } }

    window.updateRowAmount = function(row){
        try{
            var q = parseFloat(row.querySelector('.item-qty').value) || 0;
            var r = parseFloat(row.querySelector('.item-rate').value) || 0;
            var d = parseFloat(row.querySelector('.item-discount').value) || 0;
            var amt = q * r * (1 - (d/100));
            var amtEl = row.querySelector('.item-amount');
            if(amtEl) amtEl.value = toFixed3(amt);
            return amt;
        }catch(e){ return 0; }
    };

    window.createItemRow = function(focus){
        try{
            var body = document.getElementById('items-body'); if(!body) return null;
            var tr = document.createElement('tr'); tr.className = 'item-row';
            // cell: description
            var tdDesc = document.createElement('td'); tdDesc.style.padding = '6px';
            var inpDesc = document.createElement('input'); inpDesc.type = 'text'; inpDesc.className = 'item-desc'; inpDesc.placeholder = 'Item details'; inpDesc.style.cssText = 'width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;font-size:14px;color:#374151;font-weight:400;font-family:inherit;box-sizing:border-box;min-height:36px;height:36px;line-height:20px;';
            inpDesc.dataset.autocomplete = 'inventory';
            tdDesc.appendChild(inpDesc);
            // cell: qty
            var tdQty = document.createElement('td'); tdQty.style.padding = '6px'; tdQty.style.textAlign = 'center';
            var inpQty = document.createElement('input'); inpQty.type = 'number'; inpQty.className = 'item-qty'; inpQty.step = '1'; inpQty.value = '1'; inpQty.style.cssText = 'width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;';
            tdQty.appendChild(inpQty);
            // cell: rate
            var tdRate = document.createElement('td'); tdRate.style.padding = '6px'; tdRate.style.textAlign = 'center';
            var inpRate = document.createElement('input'); inpRate.type = 'number'; inpRate.className = 'item-rate'; inpRate.step = '0.001'; inpRate.value = '0.000'; inpRate.style.cssText = 'width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;';
            tdRate.appendChild(inpRate);
            // cell: discount
            var tdDisc = document.createElement('td'); tdDisc.style.padding = '6px'; tdDisc.style.textAlign = 'center';
            var inpDisc = document.createElement('input'); inpDisc.type = 'number'; inpDisc.className = 'item-discount'; inpDisc.step = '0.01'; inpDisc.value = '0.00'; inpDisc.style.cssText = 'width:100%;padding:6px;border:1px solid #ddd;border-radius:6px;';
            tdDisc.appendChild(inpDisc);
            // cell: amount
            var tdAmount = document.createElement('td'); tdAmount.style.padding = '6px'; tdAmount.style.textAlign = 'center';
            var inpAmount = document.createElement('input'); inpAmount.type = 'text'; inpAmount.className = 'item-amount'; inpAmount.value = '0.000'; inpAmount.readOnly = true; inpAmount.style.cssText = 'width:100%;padding:6px;border:1px solid #eee;border-radius:6px;background:#fafafa;';
            tdAmount.appendChild(inpAmount);
            // cell: remove
            var tdRemove = document.createElement('td'); tdRemove.style.padding = '6px'; tdRemove.style.textAlign = 'center';
            var btnRemove = document.createElement('button'); btnRemove.type = 'button'; btnRemove.className = 'remove-item-row'; btnRemove.style.cssText = 'background:#ff5252;color:#fff;border:none;padding:6px 8px;border-radius:6px;cursor:pointer;'; btnRemove.textContent = '×';
            tdRemove.appendChild(btnRemove);
            tr.appendChild(tdDesc); tr.appendChild(tdQty); tr.appendChild(tdRate); tr.appendChild(tdDisc); tr.appendChild(tdAmount); tr.appendChild(tdRemove);
            body.appendChild(tr);
            try{
                var desc = tr.querySelector('.item-desc');
                if(desc) desc.dataset.autocomplete = 'inventory';
                if(window.initInventoryAutocomplete) window.initInventoryAutocomplete(desc);
                var qty = tr.querySelector('.item-qty'); var rate = tr.querySelector('.item-rate'); var disc = tr.querySelector('.item-discount');
                qty.addEventListener('input', function(){ window.updateRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                rate.addEventListener('input', function(){ window.updateRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                disc.addEventListener('input', function(){ window.updateRowAmount(tr); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                if(focus!==false) desc.focus();
            }catch(e){}
            return tr;
        }catch(e){ console.error('createItemRow failed', e); return null; }
    };

    document.addEventListener('click', function(e){ try{ if(e.target && e.target.classList && e.target.classList.contains('remove-item-row')){ var r = e.target.closest('.item-row'); if(r) r.parentNode.removeChild(r); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} } }catch(err){} });

    window.serializeMaintenanceItems = function(){
        try{
            var services = (window.serializeServiceItems? window.serializeServiceItems() : []);
            var items = [];
            document.querySelectorAll('#items-body .item-row').forEach(function(row){ try{ var desc = row.querySelector('.item-desc')? row.querySelector('.item-desc').value : ''; var qty = parseFloat(row.querySelector('.item-qty').value)||0; var rate = parseFloat(row.querySelector('.item-rate').value)||0; var disc = parseFloat(row.querySelector('.item-discount').value)||0; var amt = parseFloat(row.querySelector('.item-amount').value)||0; if((desc||'').trim()==='' && qty===0) return; items.push({ description: desc, qty: qty, rate: rate, discount: disc, amount: amt }); }catch(e){} });
            var combined = services.concat(items);
            var hidden = document.getElementById('items_json');
            if(hidden) hidden.value = JSON.stringify(combined);
            return true;
        }catch(e){ console.error('serializeMaintenanceItems failed', e); return false; }
    };

    window.recomputeTotals = function(){
        try{
            // services total (count service rows anywhere on the page)
            var svcTotal = 0;
            document.querySelectorAll('.service-row').forEach(function(r){ try{ var val = parseFloat(r.querySelector('.service-amount').value)||0; svcTotal += val; }catch(e){} });
            document.getElementById('services-sub-total').textContent = toFixed3(svcTotal);

            // items subtotal and discount
            var sub = 0; var discTotal = 0;
            document.querySelectorAll('#items-body .item-row').forEach(function(r){ try{ var q = parseFloat(r.querySelector('.item-qty').value)||0; var rate = parseFloat(r.querySelector('.item-rate').value)||0; var d = parseFloat(r.querySelector('.item-discount').value)||0; var lineTotal = q * rate; var lineNet = lineTotal * (1 - (d/100)); sub += lineTotal; discTotal += (lineTotal - lineNet); }catch(e){} });
            document.getElementById('sub-total').textContent = toFixed3(sub);
            document.getElementById('total-discount').textContent = toFixed3(discTotal);

            var grand = (sub - discTotal) + svcTotal;
            document.getElementById('grand-total').textContent = toFixed3(grand);
            var bottom = document.getElementById('bottom-total'); if(bottom) bottom.textContent = 'BHD ' + toFixed3(grand);
            return true;
        }catch(e){ console.error('recomputeTotals failed', e); return false; }
    };

    window.initItemsTable = function(){ try{ var btn = document.getElementById('add-row'); if(btn) btn.addEventListener('click', function(e){ e.preventDefault(); createItemRow(true); }); if(document.querySelectorAll('#items-body .item-row').length === 0) createItemRow(false); // ensure totals update
        // initialize existing server-rendered rows so their inputs get autocomplete and event handlers
        try{
            document.querySelectorAll('#items-body .item-row').forEach(function(row){
                try{
                    var desc = row.querySelector('.item-desc'); if(desc){ desc.dataset.autocomplete = 'inventory'; if(window.initInventoryAutocomplete) window.initInventoryAutocomplete(desc); }
                    var qty = row.querySelector('.item-qty'); var rate = row.querySelector('.item-rate'); var disc = row.querySelector('.item-discount');
                    if(qty) qty.addEventListener('input', function(){ window.updateRowAmount(row); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                    if(rate) rate.addEventListener('input', function(){ window.updateRowAmount(row); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });
                    if(disc) disc.addEventListener('input', function(){ window.updateRowAmount(row); try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} });

                    // If this server-rendered row's description matches a service name, convert it into a service-row
                    try{
                        var val = (desc && desc.value) ? (desc.value+'').trim() : '';
                        if(val){
                            // query services autocomplete for this exact name
                            var svcUrl = '/services/autocomplete/?q=' + encodeURIComponent(val);
                            (window.fetchJson? window.fetchJson(svcUrl) : fetch(svcUrl).then(function(r){ return r.json(); })).then(function(data){
                                try{
                                    var results = (data && data.results)? data.results : [];
                                    var match = results.find(function(it){ return (it.name||'').trim().toLowerCase() === val.toLowerCase(); });
                                    if(match && window.createServiceRow){
                                        // build a service row and copy values
                                        // create the row but do NOT attach it to the main services list —
                                        // we'll replace this item-row in-place with the new service-row
                                        var newTr = window.createServiceRow(false, false);
                                        if(!newTr) return;
                                        newTr.dataset.serviceId = match.id;
                                        var lbl = newTr.querySelector('.service-label'); var hidden = newTr.querySelector('.service-desc');
                                        if(lbl) lbl.textContent = match.name || val; if(hidden) hidden.value = match.name || val;
                                        var qEl = newTr.querySelector('.service-qty'); var rEl = newTr.querySelector('.service-rate'); var dEl = newTr.querySelector('.service-discount'); var aEl = newTr.querySelector('.service-amount');
                                        try{ if(qEl) qEl.value = (row.querySelector('.item-qty') && row.querySelector('.item-qty').value) || qEl.value; }catch(e){}
                                        try{ if(rEl) rEl.value = (row.querySelector('.item-rate') && row.querySelector('.item-rate').value) || rEl.value; }catch(e){}
                                        try{ if(dEl) dEl.value = (row.querySelector('.item-discount') && row.querySelector('.item-discount').value) || dEl.value; }catch(e){}
                                        try{ if(aEl) aEl.value = (row.querySelector('.item-amount') && row.querySelector('.item-amount').value) || aEl.value; }catch(e){}
                                        // replace old row with new service row
                                        row.parentNode.replaceChild(newTr, row);
                                        try{ if(window.initServicesTable) window.initServicesTable(); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
                                    }
                                }catch(e){}
                            }).catch(function(){ /* ignore */ });
                        }
                    }catch(e){}
                }catch(e){}
            });
        }catch(e){}
        try{ if(window.recomputeTotals) window.recomputeTotals(); }catch(e){}
    }catch(e){ console.error('initItemsTable failed', e); } };

    // initialize when DOM ready if called
    document.addEventListener('DOMContentLoaded', function(){ try{ if(window.initItemsTable) window.initItemsTable(); }catch(e){} });

})();