/* ==========================================================================
   Observabilidad y Monitoreo en AWS — Guias de laboratorio (guide.js)
   Scrollspy del TOC, botones "copiar" y barra de progreso de lectura.
   ========================================================================== */
(function () {
  "use strict";

  // --- barra de progreso de lectura ---------------------------------------
  var bar = document.querySelector(".g-progress");
  if (!bar) { bar = document.createElement("div"); bar.className = "g-progress"; document.body.appendChild(bar); }
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
  }
  document.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // --- botones copiar ------------------------------------------------------
  document.querySelectorAll(".copy-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var wrap = btn.closest(".code");
      var pre = wrap && wrap.querySelector("pre");
      if (!pre) return;
      var text = pre.innerText;
      var done = function () {
        var old = btn.textContent; btn.textContent = "¡copiado!"; btn.classList.add("ok");
        setTimeout(function () { btn.textContent = old; btn.classList.remove("ok"); }, 1400);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(text); done(); });
      } else { fallback(text); done(); }
    });
  });
  function fallback(text) {
    var ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
  }

  // --- scrollspy del TOC ---------------------------------------------------
  var links = Array.prototype.slice.call(document.querySelectorAll(".g-side nav a"));
  var map = {};
  links.forEach(function (a) {
    var id = (a.getAttribute("href") || "").replace("#", "");
    var t = id && document.getElementById(id);
    if (t) map[id] = a;
  });
  var targets = Object.keys(map).map(function (id) { return document.getElementById(id); });

  if ("IntersectionObserver" in window && targets.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          links.forEach(function (l) { l.classList.remove("active"); });
          var a = map[e.target.id];
          if (a) a.classList.add("active");
        }
      });
    }, { rootMargin: "-80px 0px -70% 0px", threshold: 0 });
    targets.forEach(function (t) { io.observe(t); });
  }
})();
