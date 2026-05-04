(function(){
    'use strict';
    // items-table.v2.js shim
    // This minimal wrapper delegates to the primary `items-table.js` implementation
    // to avoid parse-time syntax errors while preserving expected globals.

    function delegate(name, fallback){
        try{ if(window && typeof window[name] === 'function') return window[name]; }catch(e){}
        return fallback || function(){ return null; };
    }

    // Do not override existing globals. This shim only avoids parse errors
    // and will not assign stub functions to `window.*` which can mask the
    // real implementation when the main script loads. Callers should use
    // the real functions from `items-table.js` when available.

    // if primary script already loaded, call its init
    try{ if(typeof window.initItemsTable === 'function') window.initItemsTable(); }catch(e){}
})();
