/* nav-mobile.js — shared mobile/iPad navigation for MIZ OKI 3.5
 *
 * Drops a hamburger button + slide-down sheet onto any page that has a
 * `.nav-links` list. Designed to be safe to include twice (idempotent),
 * style-isolated (injects its own <style>), and theme-agnostic
 * (works on both dark `index.html` and light `theme-light` pages).
 *
 * Usage:  <script src="/assets/js/nav-mobile.js" defer></script>
 */
(function () {
  if (window.__mizokiNavMobileLoaded) return;
  window.__mizokiNavMobileLoaded = true;

  function init() {
    var navLinks = document.querySelector('.nav-links');
    if (!navLinks) return; // page has no primary nav (e.g. login.html)

    // Skip if a hamburger from this script is already present.
    if (document.querySelector('.mz-nav-toggle')) return;

    injectStyles();

    // 1. Build the toggle button
    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'mz-nav-toggle';
    toggle.setAttribute('aria-label', 'Open menu');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-controls', 'mz-mobile-sheet');
    toggle.innerHTML = '<span></span><span></span><span></span>';

    // 2. Find the best place to mount the toggle
    //    Priority: .nav-right > .nav-actions > .hamburger parent > nav-links parent
    var mount =
      document.querySelector('.nav-right') ||
      document.querySelector('.nav-actions');

    if (!mount) {
      var existingHamb = document.querySelector('.hamburger');
      mount = existingHamb ? existingHamb.parentElement : navLinks.parentElement;
    }

    // Hide any pre-existing decorative .hamburger (e.g. platform.html)
    document.querySelectorAll('.hamburger').forEach(function (h) {
      h.style.display = 'none';
    });

    mount.appendChild(toggle);

    // 3. Build the slide-down sheet by cloning the existing nav-links
    var sheet = document.createElement('nav');
    sheet.id = 'mz-mobile-sheet';
    sheet.className = 'mz-mobile-sheet';
    sheet.setAttribute('aria-hidden', 'true');
    sheet.setAttribute('aria-label', 'Mobile navigation');

    var list = document.createElement('ul');
    navLinks.querySelectorAll('a').forEach(function (a) {
      var li = document.createElement('li');
      var clone = a.cloneNode(true);
      // Strip caret decorations so they don't render weirdly
      clone.querySelectorAll('.caret, .arr').forEach(function (n) { n.remove(); });
      li.appendChild(clone);
      list.appendChild(li);
    });

    // Also surface key actions from .nav-right / .nav-actions (CTA, sign-in, login)
    var actionEls = document.querySelectorAll(
      '.nav-right a, .nav-actions a'
    );
    actionEls.forEach(function (a) {
      // Skip the toggle button or anything inside the sheet itself
      if (a.closest('.mz-mobile-sheet')) return;
      var li = document.createElement('li');
      li.className = 'mz-mobile-action';
      var clone = a.cloneNode(true);
      clone.querySelectorAll('.caret, .arr').forEach(function (n) { n.remove(); });
      li.appendChild(clone);
      list.appendChild(li);
    });

    sheet.appendChild(list);
    document.body.appendChild(sheet);

    // 4. Open/close logic
    function setOpen(open) {
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      sheet.setAttribute('aria-hidden', String(!open));
      sheet.classList.toggle('open', open);
      document.body.classList.toggle('mz-menu-open', open);
    }

    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    sheet.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { setOpen(false); });
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
      }
    });

    // Auto-close when viewport widens back to desktop
    var mq = window.matchMedia('(min-width: 1181px)');
    var handle = function (e) { if (e.matches) setOpen(false); };
    if (mq.addEventListener) mq.addEventListener('change', handle);
    else mq.addListener(handle); // older Safari
  }

  function injectStyles() {
    if (document.getElementById('mz-nav-mobile-styles')) return;
    var s = document.createElement('style');
    s.id = 'mz-nav-mobile-styles';
    s.textContent = [
      /* Hamburger button */
      '.mz-nav-toggle{',
      '  display:none;',
      '  width:44px;height:44px;padding:0;margin-left:10px;',
      '  background:transparent;border:1px solid currentColor;',
      '  border-radius:6px;cursor:pointer;color:inherit;',
      '  align-items:center;justify-content:center;',
      '  -webkit-tap-highlight-color:transparent;opacity:.85;',
      '}',
      '.mz-nav-toggle:hover{opacity:1;}',
      '.mz-nav-toggle:focus-visible{outline:2px solid #7c5cff;outline-offset:2px;}',
      '.mz-nav-toggle span{',
      '  display:block;width:18px;height:2px;background:currentColor;',
      '  margin:3px 0;border-radius:2px;',
      '  transition:transform .25s ease,opacity .2s ease;',
      '}',
      '.mz-nav-toggle[aria-expanded="true"] span:nth-child(1){transform:translateY(5px) rotate(45deg);}',
      '.mz-nav-toggle[aria-expanded="true"] span:nth-child(2){opacity:0;}',
      '.mz-nav-toggle[aria-expanded="true"] span:nth-child(3){transform:translateY(-5px) rotate(-45deg);}',

      /* Slide-down sheet (works on both dark and light themes) */
      '.mz-mobile-sheet{',
      '  position:fixed;left:0;right:0;top:64px;bottom:0;',
      '  background:rgba(8,10,16,.97);color:#fff;',
      '  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);',
      '  transform:translateY(-110%);transition:transform .35s ease;',
      '  z-index:9000;padding:20px 22px 40px;overflow-y:auto;',
      '  border-top:1px solid rgba(255,255,255,.08);',
      '}',
      'body.theme-light .mz-mobile-sheet{',
      '  background:rgba(255,255,255,.98);color:#0f172a;',
      '  border-top-color:#e2e8f0;',
      '}',
      '.mz-mobile-sheet.open{transform:translateY(0);}',
      '.mz-mobile-sheet ul{list-style:none;padding:0;margin:0;}',
      '.mz-mobile-sheet li{border-bottom:1px solid rgba(255,255,255,.08);}',
      'body.theme-light .mz-mobile-sheet li{border-bottom-color:#e2e8f0;}',
      '.mz-mobile-sheet a{',
      '  display:flex;align-items:center;min-height:48px;',
      '  padding:14px 4px;font-size:1.02rem;',
      '  color:inherit;text-decoration:none;font-weight:500;',
      '}',
      '.mz-mobile-sheet a:active{opacity:.6;}',
      '.mz-mobile-sheet .mz-mobile-action{border-bottom:none;}',
      '.mz-mobile-sheet .mz-mobile-action a{',
      '  margin-top:6px;padding:14px 16px;border-radius:8px;',
      '  background:rgba(124,92,255,.18);justify-content:center;',
      '}',

      /* Body scroll-lock while menu open */
      'body.mz-menu-open{overflow:hidden;}',

      /* Show the hamburger when nav-links are hidden (≤1180px) */
      '@media (max-width:1180px){',
      '  .nav-links{display:none !important;}',
      '  .mz-nav-toggle{display:inline-flex;}',
      '}',

      /* Touch devices: kill sticky :hover transforms */
      '@media (hover: none){',
      '  .card:hover,.div-card:hover,.btn-primary:hover,.btn:hover{',
      '    transform:none !important;box-shadow:none !important;',
      '  }',
      '}',

      /* Universal tap-target floor on primary CTAs */
      '.btn-primary,.btn{min-height:44px;}',
    ].join('\n');
    document.head.appendChild(s);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
