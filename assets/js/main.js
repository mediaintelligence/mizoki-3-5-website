(function(){
  const menuBtn = document.querySelector('[data-menu-btn]');
  const navLinks = document.querySelector('[data-navlinks]');
  if(menuBtn && navLinks){
    menuBtn.addEventListener('click', ()=> navLinks.classList.toggle('open'));
  }

  // Active link highlight
  const path = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  document.querySelectorAll('.navlinks a').forEach(a=>{
    const href = (a.getAttribute('href')||'').toLowerCase();
    if(href === path){ a.classList.add('active'); }
  });

  // Footer year
  const yearEl = document.querySelector('[data-year]');
  if(yearEl){ yearEl.textContent = new Date().getFullYear(); }
})();
