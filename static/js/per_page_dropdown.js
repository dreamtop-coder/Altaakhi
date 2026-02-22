window.initPerPageDropdown = function(btnSelector, menuSelector) {
  const btn = document.querySelector(btnSelector);
  const menu = document.querySelector(menuSelector);
  if (!btn || !menu) return;
  let appended=false, originalParent=menu.parentElement;
  function openMenu(){
    if (!appended){ document.body.appendChild(menu); appended=true; }
    menu.style.display='block'; menu.style.position='fixed'; menu.style.visibility='visible';
    const btnRect = btn.getBoundingClientRect();
    const footer = btn.closest('.table-footer') || btn.parentElement;
    const footerInner = footer ? footer.querySelector('div[style*="box-shadow"]') || footer : null;
    const containerRect = footerInner ? footerInner.getBoundingClientRect() : (btn.parentElement ? btn.parentElement.getBoundingClientRect() : null);
    let width = Math.round(btnRect.width);
    if (containerRect) width = Math.max(width, Math.round(containerRect.width - 16));
    menu.style.width = width + 'px';
    const menuRect = menu.getBoundingClientRect();
    const spaceBelow = window.innerHeight - btnRect.bottom;
    const spaceAbove = btnRect.top;
    let top = (spaceBelow < menuRect.height + 8 && spaceAbove > menuRect.height + 8) ? (btnRect.top - 6 - menuRect.height) : (btnRect.bottom + 6);
    let left = btnRect.left + (btnRect.width - menuRect.width)/2;
    if (containerRect) {
      left = Math.max(8, Math.min(Math.round(containerRect.left + 8) - 4, window.innerWidth - menuRect.width - 8));
    } else {
      left = Math.max(8, Math.min(left, window.innerWidth - menuRect.width - 8));
    }
    // small visual nudge left
    left = left - 4;
    menu.style.left = Math.round(left) + 'px';
    menu.style.top = Math.round(top) + 'px';
    btn.setAttribute('aria-expanded','true'); btn.style.opacity='0.5';
  }
  function closeMenu(){ btn.setAttribute('aria-expanded','false'); btn.style.opacity=''; menu.style.display='none'; if (appended){ originalParent.appendChild(menu); appended=false; } }
  btn.addEventListener('click', function(e){ e.stopPropagation(); if (menu.style.display==='block') closeMenu(); else openMenu(); });
  menu.addEventListener('click', function(e){ const li = e.target.closest('li[role="option"]'); if (!li) return; const val = li.dataset.value; const params = new URLSearchParams(window.location.search); if (val === 'all') params.set('per_page','all'); else params.set('per_page', val); params.set('page','1'); window.location.search = params.toString(); });
  document.addEventListener('click', function(){ closeMenu(); });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeMenu(); });
};

// Auto-init when this script is loaded and DOM is ready
function _autoInitPerPage(){
  try{
    if(typeof initPerPageDropdown === 'function'){
      initPerPageDropdown('#perPageBtn','#perPageMenu');
    }
  }catch(e){ console.error('perPageDropdown auto-init failed', e); }
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', _autoInitPerPage);
} else {
  // DOM already ready — initialize immediately
  _autoInitPerPage();
}
