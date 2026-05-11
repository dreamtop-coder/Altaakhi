// Clean, well-indented maintenance inline script.
(function () {
    'use strict';

    function safeFetchJson(url) {
        try {
            if (typeof window.fetchJson === 'function') {
                return window.fetchJson(url);
            }
            return fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.json(); });
        } catch (e) {
            return Promise.reject(e);
        }
    }

    function clearSuggestions() {
        var c = document.getElementById('customer-suggestions');
        if (c) {
            c.innerHTML = '';
            c.style.display = 'none';
        }

        document.querySelectorAll('.customer-selector > [role="listbox"]').forEach(function (el) {
            if (el && el.parentNode) el.parentNode.removeChild(el);
        });

        var t = document.getElementById('customer-suggest-toggle');
        if (t) t.textContent = '∨';
    }

    function renderSuggestions(list) {
        if (!list || !list.length) {
            clearSuggestions();
            return;
        }

        var input = document.getElementById('customer-search');
        var container = (input && input.parentNode) ? input.parentNode : document.getElementById('customer-suggestions');
        if (!container) return;

        try { container.style.position = container.style.position || 'relative'; } catch (e) { }

        var box = document.createElement('div');
        box.setAttribute('role', 'listbox');
        box.style.position = 'absolute';
        box.style.zIndex = '500';
        box.style.background = '#fff';
        box.style.border = '1px solid #e6e6e6';
        box.style.width = '100%';
        box.style.borderRadius = '6px';
        box.style.top = '100%';
        box.style.left = '0';
        box.style.direction = 'ltr';

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

        var rows = document.createElement('div');

        function buildRows(src) {
            rows.innerHTML = '';

            src.forEach(function (it) {
                var row = document.createElement('div');
                row.style.padding = '8px';
                row.style.cursor = 'pointer';
                row.style.borderBottom = '1px solid #f1f5f9';

                var name = document.createElement('div');
                name.style.fontWeight = '600';
                name.style.direction = 'rtl';
                name.textContent = it.name || '';

                var sub = document.createElement('div');
                sub.className = 'small-muted';
                sub.style.direction = 'ltr';
                sub.style.fontSize = '13px';
                sub.textContent = (it.phone || '') + (it.plates && it.plates.length ? ' • ' + it.plates.join(', ') : '');

                row.appendChild(name);
                row.appendChild(sub);

                row.addEventListener('click', function (ev) {
                    ev.stopPropagation();

                    try {
                        var selClient = document.getElementById('selected_client_id');
                        if (selClient) selClient.value = it.id;
                    } catch (e) { }

                    var custInput = document.getElementById('customer-search');
                    if (custInput) custInput.value = it.name || '';

                    // populate plates or car selector
                    try {
                        var plateEl = document.getElementById('id_plate_number');
                        var showEl = document.getElementById('selected-plate');
                        var sel = document.getElementById('id_selected_client_car');
                        var wrapper = document.getElementById('client-car-select-wrapper');
                        var label = wrapper ? wrapper.querySelector('.maintenance-label') : null;
                        var carList = (it.cars && it.cars.length) ? it.cars : (it.plates || []).map(function (p) { return { id: null, plate: p }; });

                        if (carList.length === 1) {
                            // single car: show plate + MODEL, hide select and label
                            var only = carList[0];
                            if (plateEl) plateEl.value = only.plate || '';
                            if (showEl) {
                                var brRaw = (only.brand && (only.brand.name || only.brand)) || '';
                                var moRaw = (only.model && (only.model.name || only.model)) || '';
                                var yearRaw = only.year || only.year === 0 ? String(only.year) : '';
                                var parts = [];
                                if (brRaw) parts.push(String(brRaw).toUpperCase());
                                if (moRaw) parts.push(String(moRaw).toUpperCase());
                                if (yearRaw) parts.push(yearRaw);
                                var suffix = parts.join(' - ');
                                showEl.textContent = (only.plate || '') + (suffix ? (' ' + suffix) : '');
                            }
                            if (wrapper) wrapper.style.display = '';
                            if (label) try { label.style.display = 'none'; } catch (e) {}
                            try { var togBtn = wrapper ? wrapper.querySelector('.vehicle-select-toggle') : null; if (togBtn) togBtn.style.display = 'none'; } catch (e) {}
                            if (sel) try { sel.style.display = 'none'; sel.innerHTML = ''; } catch (e) {}
                            // set hidden selected id if available
                            try { var hid = document.getElementById('id_selected_client_car'); if (hid) hid.value = only.id || only.plate || ''; } catch (e) {}
                        } else if (carList.length > 1) {
                            // multiple cars: populate select so user can choose
                            if (plateEl) plateEl.value = '';
                            if (showEl) showEl.textContent = '';
                            if (wrapper) wrapper.style.display = '';
                            if (label) try { label.style.display = ''; } catch (e) {}
                            try { var togBtn2 = wrapper ? wrapper.querySelector('.vehicle-select-toggle') : null; if (togBtn2) togBtn2.style.display = ''; } catch (e) {}
                            if (sel) {
                                sel.innerHTML = '';
                                var ph = document.createElement('option');
                                ph.value = '';
                                ph.text = 'Select vehicle';
                                ph.selected = true;
                                ph.disabled = true;
                                sel.appendChild(ph);
                                carList.forEach(function (c) {
                                    var o = document.createElement('option');
                                    o.value = c.id || c.plate || '';
                                    o.setAttribute('data-plate', c.plate || '');
                                    var brandName = (c.brand && (c.brand.name || c.brand)) || '';
                                    var modelName = (c.model && (c.model.name || c.model)) || '';
                                    var yearVal = c.year || c.year === 0 ? String(c.year) : '';
                                    var parts = [];
                                    if (brandName) parts.push(String(brandName).toUpperCase());
                                    if (modelName) parts.push(String(modelName).toUpperCase());
                                    if (yearVal) parts.push(yearVal);
                                    var suffix = parts.join(' - ');
                                    var lbl = (c.plate || '');
                                    if (suffix) lbl = lbl + ' - ' + suffix;
                                    o.text = lbl;
                                    sel.appendChild(o);
                                });
                                try { sel.style.display = ''; } catch (e) {}
                            }
                        } else {
                            if (plateEl) plateEl.value = '';
                            if (showEl) showEl.textContent = '';
                            if (wrapper) wrapper.style.display = 'none';
                        }
                    } catch (e) { }

                    clearSuggestions();
                });

                rows.appendChild(row);
            });
        }

        var listToShow = (list || []).slice(0, 1000);
        buildRows(listToShow);

        localSearch.addEventListener('input', function () {
            var q = (localSearch.value || '').trim().toLowerCase();
            if (!q) {
                buildRows(listToShow);
                return;
            }

            var filtered = list.filter(function (it) {
                return (it.name || '').toLowerCase().indexOf(q) !== -1 || (it.phone || '').indexOf(q) !== -1 || (it.plates && it.plates.join(' ').toLowerCase().indexOf(q) !== -1);
            });

            buildRows(filtered.slice(0, 1000));
        });

        box.appendChild(rows);
        container.appendChild(box);

        try { localSearch.focus(); } catch (e) { }

        var t = document.getElementById('customer-suggest-toggle');
        if (t) t.textContent = '∧';
    }

    function showInlineSuggestions(q) {
        q = (q || '').trim();

        if (window.clients_sample && window.clients_sample.length) {
            if (!q) {
                return renderSuggestions(window.clients_sample.slice(0, 1000));
            }

            var f = window.clients_sample.filter(function (it) {
                return (it.name || '').toLowerCase().indexOf(q.toLowerCase()) !== -1 || (it.phone || '').indexOf(q) !== -1 || (it.plates && it.plates.join(' ').toLowerCase().indexOf(q.toLowerCase()) !== -1);
            });

            return renderSuggestions(f.slice(0, 1000));
        }

        safeFetchJson('/clients/search/?q=' + encodeURIComponent(q)).then(function (data) {
            renderSuggestions((data && data.results) ? data.results : []);
        }).catch(function (err) {
            console.error('clients search failed', err);
        });
    }

    function openCustomerModal(prefill) {
        var backdrop = document.getElementById('customer-modal-backdrop');
        if (!backdrop) return;

        var input = document.getElementById('modal-customer-query');
        var results = document.getElementById('modal-customer-results');
        if (input) input.value = prefill || '';
        backdrop.style.display = 'flex';
        if (results) {
            results.innerHTML = '<div style="padding:12px;color:#666">Type to search</div>';
        }
        if (input) try { input.focus(); } catch (e) { }
    }

    function closeCustomerModal() {
        var b = document.getElementById('customer-modal-backdrop');
        if (!b) return;
        b.style.display = 'none';
    }

    function performModalSearch(q) {
        var resultsBox = document.getElementById('modal-customer-results');
        if (!resultsBox) return;

        var qq = (q || '').trim();
        if (!qq) {
            resultsBox.innerHTML = '<div style="padding:12px;color:#666">Type to search</div>';
            return;
        }

        resultsBox.innerHTML = '<div style="padding:12px;color:#666">Searching...</div>';

        // If we have a local sample, perform client-side starts-with filtering for names,
        // and contains for phone/plates. Otherwise fallback to server search.
        if (window.clients_sample && window.clients_sample.length) {
            var qlow = qq.toLowerCase();
            var filtered = window.clients_sample.filter(function (it) {
                var name = (it.name || '').toLowerCase();
                var phone = (it.phone || '');
                var plates = (it.plates && it.plates.join(' ').toLowerCase()) || '';
                return name.indexOf(qlow) === 0 || phone.indexOf(qq) !== -1 || plates.indexOf(qlow) !== -1;
            }).slice(0, 1000);

            // simulate async
            setTimeout(function () { renderModalResults(filtered); }, 0);
            return;
        }

        safeFetchJson('/clients/search/?q=' + encodeURIComponent(qq)).then(function (data) {
            renderModalResults((data && data.results) ? data.results : []);
        }).catch(function (err) {
            resultsBox.innerHTML = '<div style="padding:12px;color:#c00">Search failed</div>';
            console.error('modal clients search failed', err);
        });
    }

    function renderModalResults(list) {
        var resultsBox = document.getElementById('modal-customer-results');
        if (!resultsBox) return;
        resultsBox.innerHTML = '';

        if (!list || !list.length) {
            resultsBox.innerHTML = '<div style="padding:12px;color:#666">No results</div>';
            return;
        }
        // create a scrollable container with a sticky header and hoverable rows
        var container = document.createElement('div');
        container.style.maxHeight = '360px';
        container.style.overflow = 'auto';
        container.style.border = '1px solid #e6e6e6';
        container.style.borderRadius = '6px';

        var tbl = document.createElement('table');
        tbl.style.width = '100%';
        tbl.style.borderCollapse = 'collapse';

        var thead = document.createElement('thead');
        thead.style.position = 'sticky';
        thead.style.top = '0';
        thead.style.background = '#fff';
        thead.style.zIndex = '10';
        thead.innerHTML = '<tr>' +
            '<th style="text-align:left;padding:8px;border-bottom:1px solid #eee">CUSTOMER NAME</th>' +
            '<th style="text-align:left;padding:8px;border-bottom:1px solid #eee">PHONE</th>' +
            '<th style="text-align:left;padding:8px;border-bottom:1px solid #eee">PLATES</th>' +
            '<th style="text-align:left;padding:8px;border-bottom:1px solid #eee">MODEL</th>' +
            '</tr>';
        tbl.appendChild(thead);

        var tbody = document.createElement('tbody');
        list.forEach(function (it) {
            var tr = document.createElement('tr');
            tr.style.cursor = 'pointer';
            tr.style.borderBottom = '1px solid #f1f5f9';
            tr.addEventListener('mouseover', function () { tr.style.background = '#f8fafc'; });
            tr.addEventListener('mouseout', function () { tr.style.background = ''; });

            var nameTd = document.createElement('td');
            nameTd.style.padding = '8px';
            nameTd.style.fontWeight = '600';
            nameTd.textContent = it.name || '';

            var phoneTd = document.createElement('td');
            phoneTd.style.padding = '8px';
            phoneTd.textContent = it.phone || '';

            var platesTd = document.createElement('td');
            platesTd.style.padding = '8px';
            platesTd.textContent = (it.plates && it.plates.length) ? it.plates.join(', ') : '';

            var modelTd = document.createElement('td');
            modelTd.style.padding = '8px';
            // compose MODEL as "BRAND - MODEL -YEAR" if available
            var modelLabel = '';
            if (it.cars && it.cars.length) {
                var c0 = it.cars[0];
                var br = (c0.brand && (c0.brand.name || c0.brand)) || c0.brand || '';
                var mo = (c0.model && (c0.model.name || c0.model)) || c0.model || '';
                var yr = c0.year || c0.year === 0 ? String(c0.year) : '';
                var parts = [];
                if (br) parts.push(String(br).toUpperCase());
                if (mo) parts.push(String(mo).toUpperCase());
                if (yr) parts.push(String(yr));
                modelLabel = parts.join(' - ');
            }
            modelTd.textContent = modelLabel;

            tr.addEventListener('click', function () { selectClientFromModal(it); });

            tr.appendChild(nameTd);
            tr.appendChild(phoneTd);
            tr.appendChild(platesTd);
            tr.appendChild(modelTd);
            tbody.appendChild(tr);
        });

        tbl.appendChild(tbody);
        container.appendChild(tbl);
        resultsBox.appendChild(container);
    }

    function selectClientFromModal(item) {
        try {
            var sel = document.getElementById('selected_client_id');
            if (sel) sel.value = item.id;

            var cust = document.getElementById('customer-search');
            if (cust) cust.value = item.name || '';

            var selectEl = document.getElementById('id_selected_client_car');
            var wrapper = document.getElementById('client-car-select-wrapper');

            if (selectEl) {
                selectEl.innerHTML = '';

                if (item.cars && item.cars.length) {
                    item.cars.forEach(function (c) {
                        var o = document.createElement('option');
                        o.value = c.id || c.plate || '';
                        o.setAttribute('data-plate', c.plate || '');
                        var label = (c.plate || '');
                        var brandName = (c.brand && (c.brand.name || c.brand)) || '';
                        var modelName = (c.model && (c.model.name || c.model)) || '';
                        var yearVal = c.year || c.year === 0 ? String(c.year) : '';
                        var parts = [];
                        if (brandName) parts.push(String(brandName).toUpperCase());
                        if (modelName) parts.push(String(modelName).toUpperCase());
                        if (yearVal) parts.push(yearVal);
                        var suffix = parts.join(' - ');
                        if (suffix) label = label + ' - ' + suffix;
                        o.text = label;
                        selectEl.appendChild(o);
                    });

                    if (item.cars.length === 1) {
                        try {
                            if (wrapper) wrapper.style.display = '';
                            // hide label for single-car and hide select
                            try { var lbl = wrapper ? wrapper.querySelector('.maintenance-label') : null; if (lbl) lbl.style.display = 'none'; } catch (e) {}
                            selectEl.style.display = 'none';
                            var only = item.cars[0];
                            var showEl = document.getElementById('selected-plate');
                            if (showEl) {
                                var plateVal = only.plate || '';
                                var brRaw = (only.brand && (only.brand.name || only.brand)) || '';
                                var moRaw = (only.model && (only.model.name || only.model)) || '';
                                var yearRaw = only.year || only.year === 0 ? String(only.year) : '';
                                var parts = [];
                                if (brRaw) parts.push(String(brRaw).toUpperCase());
                                if (moRaw) parts.push(String(moRaw).toUpperCase());
                                if (yearRaw) parts.push(yearRaw);
                                var suffix = parts.join(' - ');
                                var displayLabel = plateVal + (suffix ? ('\t' + suffix) : '');
                                showEl.textContent = displayLabel;
                                showEl.style.background = 'transparent';
                                showEl.style.border = '0';
                                showEl.style.padding = '0';
                            }
                        } catch (e) { }

                        try { selectEl.value = item.cars[0].id || item.cars[0].plate || ''; } catch (e) { }
                    } else {
                        try {
                            if (wrapper) wrapper.style.display = '';
                            // multiple cars: show label and the select so user can pick
                            try { var lbl2 = wrapper ? wrapper.querySelector('.maintenance-label') : null; if (lbl2) lbl2.style.display = ''; } catch (e) {}
                            try { var togBtn3 = wrapper ? wrapper.querySelector('.vehicle-select-toggle') : null; if (togBtn3) togBtn3.style.display = ''; } catch (e) {}
                            selectEl.style.display = '';
                            var showEl = document.getElementById('selected-plate');
                            if (showEl) showEl.textContent = '';
                        } catch (e) { }
                    }
                } else {
                    try {
                        if (wrapper) wrapper.style.display = 'none';
                        selectEl.style.display = 'none';
                    } catch (e) { }
                }
            }
        } catch (e) { }

        closeCustomerModal();
        clearSuggestions();
    }

    // expose functions
    window.showInlineSuggestions = showInlineSuggestions;
    window.openCustomerModal = openCustomerModal;
    window.clearSuggestions = clearSuggestions;

    // modal wiring: attach input handler (debounced) and backdrop close behavior
    document.addEventListener('DOMContentLoaded', function () {
        try {
            var debounce = function (fn, wait) {
                var t = null;
                return function () {
                    var args = arguments;
                    var ctx = this;
                    if (t) clearTimeout(t);
                    t = setTimeout(function () { fn.apply(ctx, args); }, wait || 250);
                };
            };

            var input = document.getElementById('modal-customer-query');
            var results = document.getElementById('modal-customer-results');
            var backdrop = document.getElementById('customer-modal-backdrop');

            if (input && results) {
                var debounced = debounce(function () {
                    var q = (input.value || '').trim();
                    if (!q) {
                        results.innerHTML = '<div style="padding:12px;color:#666">Type to search</div>';
                        return;
                    }
                    performModalSearch(q);
                }, 200);

                input.addEventListener('input', debounced);

                var btn = document.getElementById('modal-customer-search-btn');
                if (btn) btn.addEventListener('click', function (ev) {
                    ev && ev.preventDefault && ev.preventDefault();
                    performModalSearch(input.value || '');
                });
            }

            if (backdrop) {
                backdrop.addEventListener('click', function (ev) {
                    if (ev.target === backdrop) {
                        closeCustomerModal();
                    }
                });
            }

            document.addEventListener('keydown', function (ev) {
                if (ev.key === 'Escape') {
                    closeCustomerModal();
                }
            });

            // Hide vehicle-select-toggle for single-vehicle wrappers on initial load
            try {
                document.querySelectorAll('#client-car-select-wrapper').forEach(function (w) {
                    try {
                        var tog = w.querySelector('.vehicle-select-toggle');
                        var sel = w.querySelector('select[id^="id_selected_client_car"]');
                        // If select does not exist or has <=1 option, hide the toggle
                        if (tog) {
                            if (!sel || (sel.options && sel.options.length <= 1)) {
                                tog.style.display = 'none';
                            } else {
                                tog.style.display = '';
                            }
                        }
                    } catch (e) { }
                });
            } catch (e) { }
        } catch (e) { console.error('modal wiring failed', e); }
    });

    document.addEventListener('click', function (e) {
        var t = e.target;
        if (!t) return;
        if (t.closest && (t.closest('#customer-suggestions') || t.closest('.customer-selector'))) return;
        clearSuggestions();
    });

    window.toggleCustomerSuggestions = function () {
        var cs = document.getElementById('customer-suggestions');
        var tog = document.getElementById('customer-suggest-toggle');

        // Find any active suggestion listboxes either inside the dedicated
        // `#customer-suggestions` or appended directly to `.customer-selector`.
        var activeBox = document.querySelector('.customer-selector [role="listbox"]') || (cs ? cs.querySelector('[role="listbox"]') : null);

        if (activeBox) {
            // If a listbox exists, remove it (this covers both clicking the
            // toggle when it's showing `∧`, and other cases).
            try { activeBox.parentNode && activeBox.parentNode.removeChild(activeBox); } catch (e) {}
            try { if (cs) { cs.style.display = 'none'; cs.innerHTML = ''; } } catch (e) {}
            if (tog) tog.textContent = '∨';
            return;
        }

        // No active box — open suggestions.
        showInlineSuggestions('');
        try { if (cs) cs.style.display = 'block'; } catch (e) {}
        if (tog) tog.textContent = '∧';
    };

})();
