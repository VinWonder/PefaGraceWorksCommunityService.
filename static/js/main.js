/* PEFA GraceWorks — site behaviour. No build step needed. */
(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Theme (light / dark) ---------- */
  const root = document.documentElement;
  function applyTheme(theme) {
    root.setAttribute("data-bs-theme", theme);
    document.querySelectorAll("[data-theme-icon]").forEach((i) => {
      i.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
    });
  }
  let stored = null;
  try { stored = localStorage.getItem("pgcs-theme"); } catch (e) { /* storage blocked */ }
  applyTheme(stored || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem("pgcs-theme", next); } catch (e) { /* ignore */ }
    })
  );

  const saveData = !!(navigator.connection && navigator.connection.saveData);
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  /* ---------- Hero slider (Swiper): fade + slow zoom, reel plays only on its slide ---------- */
  const heroEl = document.querySelector(".hero-swiper");
  if (window.Swiper && heroEl) {
    const HERO_DELAY = 7000;
    heroEl.style.setProperty("--hero-delay", HERO_DELAY + "ms");
    const syncReels = (swiper) => {
      swiper.slides.forEach((slide, i) => {
        const v = slide.querySelector("video");
        if (!v) return;
        if (i === swiper.activeIndex && !reduceMotion) v.play().catch(() => {}); else v.pause();
      });
    };
    new Swiper(heroEl, {
      loop: heroEl.querySelectorAll(".swiper-slide").length > 1,
      effect: "fade",
      fadeEffect: { crossFade: true },
      speed: reduceMotion ? 0 : 1100,
      autoplay: reduceMotion ? false : { delay: HERO_DELAY, disableOnInteraction: false, pauseOnMouseEnter: true },
      pagination: { el: ".hero .swiper-pagination", clickable: true },
      navigation: { nextEl: ".hero-next", prevEl: ".hero-prev" },
      a11y: { enabled: true },
      keyboard: { enabled: true },
      on: { init: syncReels, slideChangeTransitionStart: syncReels },
    });
  }

  /* ---------- Carousels ---------- */
  const carousel = (selector, options) => {
    document.querySelectorAll(selector).forEach((el) => new Swiper(el, Object.assign({
      slidesPerView: "auto", spaceBetween: 20, grabCursor: true, keyboard: { enabled: true }, a11y: { enabled: true },
    }, options)));
  };
  if (window.Swiper) {
    carousel(".focus-swiper", { navigation: { nextEl: ".focus-next", prevEl: ".focus-prev" } });
    carousel(".reels-swiper", { spaceBetween: 18, navigation: { nextEl: ".reels-next", prevEl: ".reels-prev" } });
    carousel(".album-swiper", {
      navigation: { nextEl: ".album-next", prevEl: ".album-prev" },
      autoplay: reduceMotion ? false : { delay: 5000, disableOnInteraction: true, pauseOnMouseEnter: true },
    });
    carousel(".strip-swiper", { spaceBetween: 14, freeMode: true });
    carousel(".moments-swiper", {
      effect: reduceMotion ? "slide" : "coverflow",
      centeredSlides: true,
      loop: document.querySelectorAll(".moments-swiper .swiper-slide").length > 4,
      spaceBetween: 0,
      speed: 800,
      coverflowEffect: { rotate: 0, stretch: 60, depth: 220, modifier: 1, slideShadows: false },
      autoplay: reduceMotion ? false : { delay: 3500, disableOnInteraction: false, pauseOnMouseEnter: true },
      pagination: { el: ".moments-swiper .swiper-pagination", clickable: true, dynamicBullets: true },
    });
    // Older templates still use the plain image carousel.
    carousel(".gallery-swiper", { spaceBetween: 16, freeMode: true, navigation: { nextEl: ".gallery-next", prevEl: ".gallery-prev" } });
  }

  /* ---------- Lightbox (photos and videos) ---------- */
  let lightbox = null;
  if (window.GLightbox) {
    lightbox = GLightbox({ selector: ".glightbox", touchNavigation: true, loop: true, autoplayVideos: true });
    // Pause silent previews while a video plays with sound.
    lightbox.on("open", () => document.querySelectorAll("video").forEach((v) => v.pause()));
  }

  /* ---------- Reels: silent preview on hover (desktop only, never on mobile data) ---------- */
  if (finePointer && !reduceMotion && !saveData) {
    document.querySelectorAll(".reel").forEach((reel) => {
      const v = reel.querySelector("video");
      if (!v) return;
      reel.addEventListener("mouseenter", () => { v.play().then(() => reel.classList.add("is-previewing")).catch(() => {}); });
      reel.addEventListener("mouseleave", () => { v.pause(); reel.classList.remove("is-previewing"); });
    });
  }

  /* ---------- Gallery filter ---------- */
  const grid = document.querySelector("[data-filter-grid]");
  if (grid) {
    const chips = document.querySelectorAll(".filter-chip[data-filter]");
    chips.forEach((chip) => chip.addEventListener("click", () => {
      const f = chip.dataset.filter;
      chips.forEach((c) => { c.classList.toggle("active", c === chip); c.setAttribute("aria-pressed", c === chip); });
      grid.querySelectorAll(".mosaic-item").forEach((item) => {
        const show = f === "all" || item.dataset.album === f;
        item.classList.toggle("is-hidden", !show);
        item.classList.remove("pop");
        if (show && !reduceMotion) { void item.offsetWidth; item.classList.add("pop"); }
        item.dataset.gallery = show ? "gallery" : "hidden";  // the lightbox only pages through what's shown
      });
      if (lightbox) lightbox.reload();
    }));
  }

  /* ---------- Scroll reveal ---------- */
  const revealEls = document.querySelectorAll("[data-reveal]");
  if (revealEls.length) {
    if (reduceMotion || !("IntersectionObserver" in window)) {
      revealEls.forEach((el) => el.classList.add("is-visible"));
    } else {
      const ro = new IntersectionObserver((entries, obs) => {
        entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-visible"); obs.unobserve(e.target); } });
      }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
      revealEls.forEach((el) => ro.observe(el));
    }
  }

  /* ---------- Progress bars fill when seen ---------- */
  const bars = document.querySelectorAll("[data-progress]");
  if (bars.length && !reduceMotion && "IntersectionObserver" in window) {
    bars.forEach((b) => { b.style.width = "0%"; });
    const po = new IntersectionObserver((entries, obs) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.style.width = e.target.dataset.progress + "%"; obs.unobserve(e.target); } });
    }, { threshold: 0.5 });
    bars.forEach((b) => po.observe(b));
  }

  /* ---------- Gentle 3D tilt on feature photos ---------- */
  if (finePointer && !reduceMotion) {
    document.querySelectorAll(".tilt").forEach((el) => {
      el.addEventListener("pointermove", (e) => {
        const r = el.getBoundingClientRect();
        el.style.setProperty("--ry", ((e.clientX - r.left) / r.width - 0.5) * 8 + "deg");
        el.style.setProperty("--rx", ((e.clientY - r.top) / r.height - 0.5) * -8 + "deg");
      });
      el.addEventListener("pointerleave", () => { el.style.setProperty("--rx", "0deg"); el.style.setProperty("--ry", "0deg"); });
    });
  }

  /* ---------- Scroll effects: progress bar, glass navbar, back-to-top, parallax ---------- */
  const nav = document.querySelector(".site-nav");
  const toTop = document.querySelector(".back-to-top");
  const parallax = reduceMotion ? [] : document.querySelectorAll(".impact-bg, .quote-bg");
  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    root.style.setProperty("--scroll", max > 0 ? (y / max).toFixed(4) : 0);
    if (nav) nav.classList.toggle("is-scrolled", y > 40);
    if (toTop) toTop.classList.toggle("show", y > 900);
    parallax.forEach((el) => {
      const r = el.parentElement.getBoundingClientRect();
      if (r.bottom > 0 && r.top < window.innerHeight) {
        el.style.setProperty("--parallax", ((r.top + r.height / 2 - window.innerHeight / 2) * -0.15).toFixed(1) + "px");
      }
    });
    ticking = false;
  };
  // Sticky bars (gallery filters) sit right under the navbar, whatever height it wraps to.
  const syncNavHeight = () => { if (nav) root.style.setProperty("--nav-h", nav.offsetHeight + "px"); };
  syncNavHeight();
  window.addEventListener("resize", syncNavHeight);
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" }));

  /* ---------- Impact counters: one orchestrated moment ---------- */
  const counters = document.querySelectorAll("[data-count]");
  if (counters.length) {
    const fmt = new Intl.NumberFormat("en-KE");
    const run = (el) => {
      const target = parseInt(el.dataset.count, 10) || 0;
      if (reduceMotion || target === 0) { el.textContent = fmt.format(target); return; }
      const start = performance.now(), dur = 1600;
      const step = (now) => {
        const p = Math.min(1, (now - start) / dur);
        el.textContent = fmt.format(Math.round(target * (1 - Math.pow(1 - p, 3))));
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((e) => { if (e.isIntersecting) { run(e.target); obs.unobserve(e.target); } });
    }, { threshold: 0.4 });
    counters.forEach((c) => io.observe(c));
  }

  /* ---------- Donation form ---------- */
  const donateForm = document.getElementById("donate-form");
  if (donateForm) {
    const amount = donateForm.querySelector("[name=amount]");
    const cardCurrency = donateForm.dataset.cardCurrency || "USD";
    const label = donateForm.querySelector("[data-submit-label]");
    const live = donateForm.querySelector("[data-impact-live]");
    const currencyLabel = donateForm.querySelector("[data-currency-label]");
    const grids = donateForm.querySelectorAll(".impact-grid");
    const fmt = new Intl.NumberFormat("en-KE");
    const method = () => donateForm.querySelector("[name=method]:checked")?.value || "mpesa";
    const currency = () => (["card", "paypal"].includes(method()) ? cardCurrency : "KES");
    const monthly = () => donateForm.querySelector("[name=frequency]:checked")?.value === "monthly";
    let lastCurrency = null;

    const refresh = () => {
      const m = method(), cur = currency(), val = parseFloat(amount.value) || 0;
      donateForm.querySelectorAll("[data-show-for]").forEach((el) => { el.hidden = !el.dataset.showFor.split(" ").includes(m); });
      grids.forEach((g) => { g.hidden = g.dataset.currency !== cur; });
      if (currencyLabel) currencyLabel.textContent = cur;
      // Switching between shillings and dollars: an old amount would be wildly wrong, so pick the middle tile.
      if (lastCurrency && lastCurrency !== cur) {
        const mid = donateForm.querySelectorAll(`.impact-grid[data-currency="${cur}"] .impact-tile`)[2];
        amount.value = mid ? mid.dataset.amount : "";
        lastCurrency = cur;
        return refresh();
      }
      lastCurrency = cur;
      let match = null;
      donateForm.querySelectorAll(`.impact-grid[data-currency="${cur}"] .impact-tile`).forEach((t) => {
        const on = t.dataset.amount === String(val) && val > 0;
        t.classList.toggle("active", on);
        if (on) match = t.querySelector("small").textContent;
      });
      const shown = val ? `${cur} ${fmt.format(val)}` : "";
      if (live) live.innerHTML = val ? `<i class="bi bi-stars"></i> ${shown}${monthly() ? " every month" : ""}${match ? `: ${match.toLowerCase()}` : " to serve families in Kisumu East"}.` : "";
      if (label) {
        label.textContent = {
          mpesa: `Give ${shown || "now"} by M-Pesa`,
          card: `Continue to pay ${shown} by card`,
          paypal: `Continue to PayPal${shown ? ` · ${shown}` : ""}`,
          bank: "Get bank details",
          in_kind: "Pledge my gift",
        }[m];
      }
    };
    donateForm.querySelectorAll(".impact-tile").forEach((t) => t.addEventListener("click", () => { amount.value = t.dataset.amount; refresh(); }));
    donateForm.querySelectorAll("[name=method], [name=frequency]").forEach((i) => i.addEventListener("change", refresh));
    amount.addEventListener("input", refresh);
    if (!amount.value) amount.value = currency() === "KES" ? "2500" : "50";
    lastCurrency = currency();
    refresh();

    donateForm.addEventListener("submit", () => {
      const btn = donateForm.querySelector("button[type=submit]");
      btn.disabled = true;
      btn.insertAdjacentHTML("afterbegin", '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>');
    });
  }

  /* ---------- Copy buttons (Paybill, account) ---------- */
  document.querySelectorAll("[data-copy]").forEach((btn) => btn.addEventListener("click", () => {
    navigator.clipboard?.writeText(btn.dataset.copy).then(() => {
      btn.innerHTML = '<i class="bi bi-check2"></i>';
      setTimeout(() => { btn.innerHTML = '<i class="bi bi-copy"></i>'; }, 1600);
    });
  }));

  /* ---------- Countdown to the next event ---------- */
  document.querySelectorAll("[data-countdown]").forEach((el) => {
    const target = new Date(el.dataset.countdown).getTime();
    const parts = el.querySelectorAll("[data-unit]");
    const tick = () => {
      let s = Math.max(0, Math.floor((target - Date.now()) / 1000));
      const v = { d: Math.floor(s / 86400), h: Math.floor((s % 86400) / 3600), m: Math.floor((s % 3600) / 60), s: s % 60 };
      parts.forEach((p) => { p.textContent = String(v[p.dataset.unit]).padStart(2, "0"); });
      if (s > 0) setTimeout(tick, 1000);
    };
    tick();
  });

  /* ---------- M-Pesa status polling ---------- */
  const statusBox = document.getElementById("mpesa-status");
  if (statusBox) {
    const url = statusBox.dataset.checkUrl;
    const show = (state) => statusBox.querySelectorAll("[data-state]").forEach((el) => { el.hidden = el.dataset.state !== state; });
    let tries = 0;
    const poll = async () => {
      tries += 1;
      try {
        const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
        const data = await res.json();
        if (data.status === "completed") {
          const r = statusBox.querySelector("[data-receipt]");
          if (r) r.textContent = data.receipt || "—";
          show("completed"); return;
        }
        if (data.status === "failed" || data.status === "cancelled") {
          const m = statusBox.querySelector("[data-message]");
          if (m) m.textContent = data.message || "The payment did not go through.";
          show("failed"); return;
        }
      } catch (e) { /* network blip: keep trying */ }
      if (tries < 45) setTimeout(poll, 4000); else show("failed");
    };
    setTimeout(poll, 4000);
  }

  /* ---------- Newsletter (AJAX with graceful fallback) ---------- */
  document.querySelectorAll("form[data-newsletter]").forEach((form) => {
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const out = form.querySelector("[data-newsletter-msg]");
      try {
        const res = await fetch(form.action, {
          method: "POST", body: new FormData(form), headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        const data = await res.json();
        out.textContent = data.message;
        out.className = "small mt-2 " + (data.ok ? "text-success-emphasis" : "text-warning");
        if (data.ok) form.reset();
      } catch (e) { form.submit(); }
    });
  });

  /* ---------- Bootstrap validation styling ---------- */
  document.querySelectorAll("form.needs-validation").forEach((form) => {
    form.addEventListener("submit", (ev) => {
      if (!form.checkValidity()) { ev.preventDefault(); ev.stopPropagation(); }
      form.classList.add("was-validated");
    });
  });

  /* ---------- Year ---------- */
  document.querySelectorAll("[data-year]").forEach((el) => { el.textContent = new Date().getFullYear(); });
})();
