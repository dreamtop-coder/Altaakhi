(function(){
    if(window.__servicesTableLoaded) return;
    window.__servicesTableLoaded = true;
    try{ console.warn('[LOAD] services-table.js stub - neutralized due to legacy syntax error.'); }catch(e){}

    // Provide minimal no-op shims so other code can safely call legacy APIs.
    window.attachServiceRowEvents = window.attachServiceRowEvents || function(row){};
    window.onServiceSelected = window.onServiceSelected || function(row, item){};
    window.initServicesTable = window.initServicesTable || function(){};
    window.createServiceRow = window.createServiceRow || function(){ return null; };
})();

(function () {
    if (window.__servicesTableLoaded) return;
    window.__servicesTableLoaded = true;

    // lightweight dropdown lock
    if (!window.__svcDropdownLock) window.__svcDropdownLock = { state: 'closed', rowId: null };

    function canOpen(id) { try{ return window.__svcDropdownLock.state !== 'opening'; }catch(e){return true;} }
    function lock(id) { try{ window.__svcDropdownLock = { state: 'opening', rowId: id }; }catch(e){} }
    // ensure lock is reset after open/close operations

    function unlock(){ try{ window.__svcDropdownLock = { state: 'closed', rowId: null }; }catch(e){} }

    // helper to close service dropdowns via manager when possible
