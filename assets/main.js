/* Real Marco – návrh webu. Bez knihoven: nativní scroll, IntersectionObserver, CSS scroll-driven animace. */
(() => {
  const d = document, root = d.documentElement;
  root.classList.add('js');
  const $ = (s, c = d) => c.querySelector(s);
  const $$ = (s, c = d) => [...c.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- navigace ---------- */
  const nav = $('#nav'), burger = $('#burger'), menu = $('#menu');
  const solidAlways = !d.body.classList.contains('home');
  let lastY = scrollY, ticking = false;
  const onScroll = () => {
    const y = scrollY;
    nav.classList.toggle('solid', solidAlways || y > 40);
    if (!nav.classList.contains('menu-open')) nav.classList.toggle('hide', y > 500 && y > lastY + 4);
    if (y < lastY - 4 || y < 500) nav.classList.remove('hide');
    lastY = y; ticking = false;
  };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();
  if (burger) burger.addEventListener('click', () => {
    const open = burger.getAttribute('aria-expanded') !== 'true';
    burger.setAttribute('aria-expanded', open);
    burger.setAttribute('aria-label', open ? 'Zavřít menu' : 'Otevřít menu');
    menu.classList.toggle('open', open);
    nav.classList.toggle('menu-open', open);
    d.body.style.overflow = open ? 'hidden' : '';
  });
  $$('#menu a').forEach(a => a.addEventListener('click', () => {
    if (burger && burger.getAttribute('aria-expanded') === 'true') burger.click();
  }));

  /* ---------- reveal ---------- */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { rootMargin: '0px 0px -8% 0px', threshold: .08 });
  $$('.rv, .clip').forEach(el => io.observe(el));

  /* ---------- čísla ---------- */
  const cio = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    cio.unobserve(e.target);
    const el = e.target, to = +el.dataset.count;
    if (reduce) return;
    const t0 = performance.now(), dur = 1600;
    const step = t => {
      const p = Math.min(1, (t - t0) / dur), v = Math.round(to * (1 - Math.pow(1 - p, 3)));
      el.textContent = v;
      if (p < 1) requestAnimationFrame(step);
    };
    el.textContent = '0';
    requestAnimationFrame(step);
  }), { threshold: .6 });
  $$('[data-count]').forEach(el => cio.observe(el));

  /* ---------- služby: náhled fotky u kurzoru ---------- */
  const prev = $('.srv-prev');
  if (prev && matchMedia('(hover: hover) and (pointer: fine)').matches) {
    const img = $('img', prev);
    let x = 0, y = 0, cx = 0, cy = 0, raf = 0, on = false;
    const loop = () => {
      cx += (x - cx) * .18; cy += (y - cy) * .18;
      prev.style.transform = `translate3d(${cx + 28}px, ${cy - 110}px, 0)`;
      if (on || Math.abs(x - cx) > .5) raf = requestAnimationFrame(loop); else raf = 0;
    };
    $$('.srv[data-img]').forEach(row => {
      const pre = new Image(); pre.src = row.dataset.img;
      row.addEventListener('mouseenter', e => {
        img.src = row.dataset.img; on = true; x = cx = e.clientX; y = cy = e.clientY;
        prev.classList.add('on'); if (!raf) raf = requestAnimationFrame(loop);
      });
      row.addEventListener('mousemove', e => { x = e.clientX; y = e.clientY; });
      row.addEventListener('mouseleave', () => { on = false; prev.classList.remove('on'); });
    });
  }

  /* ---------- formuláře (návrh – neodesílají) ---------- */
  $$('[data-form]').forEach(f => f.addEventListener('submit', e => {
    e.preventDefault();
    const ok = $('.form-ok', f); if (ok) ok.hidden = false;
    $$('input, textarea', f).forEach(i => { if (i.type !== 'radio') i.value = ''; });
  }));

  /* ---------- nabídka: filtry ---------- */
  const grid = $('#grid');
  if (grid && d.body.classList.contains('offer')) {
    const cards = $$('.card', grid);
    const state = { typ: '', kat: '', lok: '', cena: '', plocha: '', razeni: '' };
    const qs = new URLSearchParams(location.search);
    Object.keys(state).forEach(k => { if (qs.get(k)) state[k] = qs.get(k); });
    const priceSel = $('select[data-f="cena"]');
    const priceOpts = {
      prodej: [3e6, 5e6, 7e6, 9e6, 12e6], pronajem: [20e3, 30e3, 45e3, 70e3],
      '': [3e6, 5e6, 7e6, 9e6, 12e6]
    };
    const fmt = v => v >= 1e6 ? (v / 1e6).toLocaleString('cs-CZ') + ' mil. Kč' : (v / 1e3).toLocaleString('cs-CZ') + ' tis. Kč';
    const fillPrice = () => {
      const keep = state.cena;
      priceSel.innerHTML = '<option value="">Neomezeně</option>' + priceOpts[state.typ].map(v => `<option value="${v}">${fmt(v)}</option>`).join('');
      priceSel.value = priceOpts[state.typ].includes(+keep) ? keep : '';
      state.cena = priceSel.value;
    };
    const out = $('[data-count-out]'), empty = $('.empty'), reset = $('[data-reset]'), badge = $('.f-badge');
    const apply = (anim = true) => {
      let n = 0;
      const vis = [];
      cards.forEach(c => {
        const ds = c.dataset, price = +ds.price, area = +ds.area;
        const ok = (!state.typ || ds.kind === state.typ) && (!state.kat || ds.cat === state.kat) && (!state.lok || ds.reg === state.lok)
          && (!state.cena || (price > 0 && price <= +state.cena)) && (!state.plocha || area >= +state.plocha);
        c.classList.toggle('is-out', !ok);
        if (ok) { n++; vis.push(c); }
      });
      const s = state.razeni;
      const key = c => s.startsWith('cena') ? (+c.dataset.price || (s === 'cena-asc' ? 1e12 : 0)) : s === 'plocha-desc' ? +c.dataset.area : c.dataset.date;
      const sorted = [...cards].sort((a, b) => {
        const ka = key(a), kb = key(b);
        if (!s) return ka < kb ? 1 : -1;
        return s === 'cena-asc' ? ka - kb : kb - ka;
      });
      sorted.forEach(c => grid.appendChild(c));
      if (anim && !reduce) vis.forEach((c, i) => { c.classList.remove('pop'); void c.offsetWidth; c.style.animationDelay = Math.min(i, 8) * 40 + 'ms'; c.classList.add('pop'); c.classList.add('in'); });
      out.textContent = n;
      empty.hidden = n > 0;
      const active = Object.entries(state).filter(([k, v]) => v && k !== 'razeni').length;
      reset.hidden = !active;
      if (badge) { badge.hidden = !active; badge.textContent = active; }
      $$('[data-f="typ"]').forEach(b => b.setAttribute('aria-pressed', b.dataset.v === state.typ));
      $$('[data-f="kat"]').forEach(b => b.setAttribute('aria-pressed', b.dataset.v === state.kat));
      $$('select[data-f]').forEach(sel => { sel.value = state[sel.dataset.f]; });
      const p = new URLSearchParams(Object.entries(state).filter(([, v]) => v));
      history.replaceState(null, '', location.pathname + (p.toString() ? '?' + p : ''));
    };
    $$('button[data-f]').forEach(b => b.addEventListener('click', () => {
      const f = b.dataset.f;
      state[f] = (f === 'kat' && state.kat === b.dataset.v) ? '' : b.dataset.v;
      if (f === 'typ') fillPrice();
      apply();
    }));
    $$('select[data-f]').forEach(s => s.addEventListener('change', () => { state[s.dataset.f] = s.value; apply(); }));
    reset.addEventListener('click', () => { Object.keys(state).forEach(k => { if (k !== 'razeni') state[k] = ''; }); fillPrice(); apply(); });
    const tog = $('.f-toggle'), panel = $('#fpanel');
    if (tog) tog.addEventListener('click', () => { const o = !panel.classList.contains('open'); panel.classList.toggle('open', o); tog.setAttribute('aria-expanded', o); });
    fillPrice(); if (qs.get('cena')) { state.cena = qs.get('cena'); }
    apply(false);
  }

  /* ---------- detail: galerie + lightbox ---------- */
  const gal = $('.gal[data-lbsrc]'), lb = $('#lb');
  if (gal && lb) {
    const srcs = JSON.parse(gal.dataset.lbsrc);
    const img = $('.lb-f img', lb), cnt = $('.lb-c', lb);
    let i = 0, lastFocus = null;
    const show = k => {
      i = (k + srcs.length) % srcs.length;
      img.src = srcs[i]; cnt.textContent = `${i + 1} / ${srcs.length}`;
      [i + 1, i - 1].forEach(j => { const p = new Image(); p.src = srcs[(j + srcs.length) % srcs.length]; });
    };
    const open = k => { lastFocus = d.activeElement; lb.hidden = false; d.body.style.overflow = 'hidden'; show(k); $('.lb-x', lb).focus(); };
    const close = () => { lb.hidden = true; d.body.style.overflow = ''; img.removeAttribute('src'); if (lastFocus) lastFocus.focus(); };
    $$('[data-lb]', gal).forEach(b => b.addEventListener('click', () => open(+b.dataset.lb)));
    $('.lb-x', lb).addEventListener('click', close);
    $('.lb-p', lb).addEventListener('click', () => show(i - 1));
    $('.lb-n', lb).addEventListener('click', () => show(i + 1));
    lb.addEventListener('click', e => { if (e.target === lb || e.target.classList.contains('lb-f')) close(); });
    addEventListener('keydown', e => {
      if (lb.hidden) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowRight') show(i + 1);
      if (e.key === 'ArrowLeft') show(i - 1);
    });
    let sx = null;
    lb.addEventListener('touchstart', e => { sx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', e => {
      if (sx === null) return; const dx = e.changedTouches[0].clientX - sx;
      if (Math.abs(dx) > 40) show(i + (dx < 0 ? 1 : -1)); sx = null;
    });
  }

  /* ---------- detail: mapa na kliknutí ---------- */
  $$('[data-map]').forEach(m => $('button', m).addEventListener('click', () => {
    const f = d.createElement('iframe');
    f.src = m.dataset.map; f.loading = 'lazy'; f.title = 'Mapa lokality'; f.referrerPolicy = 'no-referrer-when-downgrade';
    m.appendChild(f);
  }));

  /* ---------- detail: hypoteční kalkulačka ---------- */
  $$('[data-calc]').forEach(c => {
    const price = +c.dataset.price;
    const g = k => $(`[data-i="${k}"]`, c), o = k => $(`[data-o="${k}"]`, c);
    const nf = new Intl.NumberFormat('cs-CZ', { maximumFractionDigits: 0 });
    const calc = () => {
      const own = +g('own').value, yrs = +g('yrs').value, rate = +g('rate').value;
      const P = price * (1 - own / 100), r = rate / 100 / 12, n = yrs * 12;
      const pay = r ? P * r / (1 - Math.pow(1 + r, -n)) : P / n;
      o('own').textContent = own + ' %';
      o('yrs').textContent = yrs + (yrs < 5 ? ' roky' : ' let');
      o('rate').textContent = rate.toLocaleString('cs-CZ', { minimumFractionDigits: 1 }) + ' %';
      o('pay').textContent = nf.format(pay) + ' Kč';
    };
    $$('input', c).forEach(i => i.addEventListener('input', calc));
    calc();
  });
})();
