// Simple global dropdown manager to avoid multiple handlers fighting over dropdowns
(function(){
    if (window.__dropdownManagerLoaded) return; window.__dropdownManagerLoaded = true;

    // Allow disabling at runtime
    if (window.__disableDropdownManager) {
        window.dropdownManager = {
            open: function(){ console.log('dropdownManager: DISABLED (open)'); },
            closeAllExcept: function(){},
            closeOwner: function(){},
            closeAll: function(){}
        };
        return;
    }

    var manager = {
        _justOpened: false,
        open: function(el, owner){
            try{
                if(!el) return;
                if(el && typeof el === 'object' && el.el && el.owner){ owner = el.owner; el = el.el; }
                // allow opening same element/owner again; do not block re-open
                try{ el.setAttribute && el.setAttribute('data-dropdown-owner', owner||'anon'); }catch(e){}
                try{ this.closeAllExcept(owner); }catch(e){}
                if (window.__disableDropdownManager) return;
                var container = (document.getElementById('dropdown-root') || document.body);
                try{ if(container && !container.contains(el)) container.appendChild(el); }catch(e){ console.error('dropdownManager: appendChild failed', e); }
                // stateless manager: do not retain references to dropdown elements
                this._justOpened = true; setTimeout(function(){ try{ manager._justOpened = false; }catch(e){} }, 160);
            }catch(e){ console.error('dropdownManager.open failed', e); }
        },
        closeAllExcept: function(owner){
            try{
                document.querySelectorAll('[data-dropdown-owner]').forEach(function(d){
                    try{ if(d && d.getAttribute && d.getAttribute('data-protected')) return; }catch(e){}
                    try{
                        var own = (d.getAttribute && d.getAttribute('data-dropdown-owner')) || (d.dataset && d.dataset.dropdownOwner) || null;
                        if(own !== (owner||'anon')){
                            try{ if(d && d.setAttribute) d.setAttribute('data-__closing','1'); }catch(e){}
                            try{ if(d && d.parentNode) d.parentNode.removeChild(d); else if(typeof d.remove === 'function') d.remove(); }catch(e){}
                        }
                    }catch(e){}
                });
                // stateless: nothing to keep here
            }catch(e){ console.error('dropdownManager.closeAllExcept failed', e); }
        },
        closeOwner: function(owner, opts){
            try{
                var force = (opts && opts.force) || (opts === true);
                if(!force) {
                    // no pointerdown anti-race guard; allow immediate forced closes
                }
                document.querySelectorAll('[data-dropdown-owner="'+owner+'"]').forEach(function(d){
                    try{ if(d && d.getAttribute && d.getAttribute('data-protected')) return; }catch(e){}
                    try{ if(d && d.setAttribute) d.setAttribute('data-__closing','1'); }catch(e){}
                    try{ if(d && d.parentNode) d.parentNode.removeChild(d); else if(typeof d.remove === 'function') d.remove(); }catch(e){}
                });
                // stateless: nothing to keep here
            }catch(e){ console.error('dropdownManager.closeOwner failed', e); }
        },
        closeAll: function(){
            try{
                document.querySelectorAll('[data-dropdown-owner]').forEach(function(d){
                    try{ if(d && d.getAttribute && d.getAttribute('data-protected')) return; }catch(e){}
                    try{ if(d && d.setAttribute) d.setAttribute('data-__closing','1'); }catch(e){}
                    try{ if(d && d.parentNode) d.parentNode.removeChild(d); else if(typeof d.remove === 'function') d.remove(); }catch(e){}
                });
                // stateless: nothing to keep here
            }catch(e){ console.error('dropdownManager.closeAll failed', e); }
        }
    };
    // no pointerdown capture guard: allow normal event ordering
    try{ document.addEventListener('click', function(ev){ try{ if(manager._justOpened) return; if(!ev || !ev.target) return; if(ev.target.closest && ev.target.closest('[data-dropdown-owner]')) return; try{ if(ev.target.closest && (ev.target.closest('.svc-dd') || ev.target.closest('.inventory-dd'))) return; }catch(e){} manager.closeAll(); }catch(e){} }); }catch(e){}

    window.dropdownManager = manager;
    try{ console.log('dropdown-manager: loaded'); }catch(e){}
})();
