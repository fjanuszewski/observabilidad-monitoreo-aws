/* ==========================================================================
   Observabilidad y Monitoreo en AWS — Motor de presentaciones (slides.js)
   Navegacion por teclado, swipe tactil, vista overview, barra de progreso
   y deep-link por hash (#3). Sin dependencias externas.
   ========================================================================== */
(function () {
  "use strict";

  var deck = document.querySelector(".deck");
  if (!deck) return;
  var slides = Array.prototype.slice.call(deck.querySelectorAll(".slide"));
  if (!slides.length) return;

  var current = 0;
  var overview = false;

  // --- barra de progreso, contador y ayuda (se crean si no existen) --------
  var progress = document.querySelector(".deck-progress");
  if (!progress) {
    progress = document.createElement("div");
    progress.className = "deck-progress";
    document.body.appendChild(progress);
  }
  var hint = document.querySelector(".deck-hint");
  if (!hint) {
    hint = document.createElement("div");
    hint.className = "deck-hint";
    hint.innerHTML = '<kbd>&larr;</kbd> <kbd>&rarr;</kbd> navegar &nbsp;·&nbsp; <kbd>O</kbd> vista general &nbsp;·&nbsp; <kbd>F</kbd> pantalla completa';
    document.body.appendChild(hint);
  }

  // Inserta contador en cada barra superior
  slides.forEach(function (s, i) {
    var top = s.querySelector(".slide-top");
    if (top && !top.querySelector(".st-count")) {
      var spacer = top.querySelector(".st-spacer");
      if (!spacer) {
        spacer = document.createElement("span");
        spacer.className = "st-spacer";
        top.appendChild(spacer);
      }
      var count = document.createElement("span");
      count.className = "st-count";
      count.textContent = (i + 1) + " / " + slides.length;
      top.appendChild(count);
    }
  });

  function clamp(n) { return Math.max(0, Math.min(slides.length - 1, n)); }

  function render() {
    slides.forEach(function (s, i) { s.classList.toggle("is-active", i === current); });
    progress.style.width = ((current) / (slides.length - 1) * 100) + "%";
    if (!overview) {
      if (history.replaceState) history.replaceState(null, "", "#" + (current + 1));
      else location.hash = "#" + (current + 1);
      var active = slides[current];
      if (active) active.scrollTop = 0;
    }
  }

  function go(n) { current = clamp(n); render(); }
  function next() { if (current < slides.length - 1) go(current + 1); }
  function prev() { if (current > 0) go(current - 1); }

  // --- vista overview ------------------------------------------------------
  function toggleOverview(force) {
    overview = (typeof force === "boolean") ? force : !overview;
    deck.classList.toggle("is-overview", overview);
    if (overview) {
      slides.forEach(function (s, i) {
        s.classList.add("is-active");
        s.onclick = function () { toggleOverview(false); go(i); };
      });
    } else {
      slides.forEach(function (s) { s.onclick = null; });
      render();
    }
  }

  // --- teclado -------------------------------------------------------------
  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var k = e.key;
    if (overview) {
      if (k === "Escape" || k === "o" || k === "O") { toggleOverview(false); e.preventDefault(); }
      return;
    }
    switch (k) {
      case "ArrowRight": case "PageDown": case " ": case "Spacebar":
        next(); e.preventDefault(); break;
      case "ArrowLeft": case "PageUp":
        prev(); e.preventDefault(); break;
      case "Home": go(0); e.preventDefault(); break;
      case "End": go(slides.length - 1); e.preventDefault(); break;
      case "o": case "O": toggleOverview(); e.preventDefault(); break;
      case "f": case "F":
        if (!document.fullscreenElement) { (document.documentElement.requestFullscreen || function () {}).call(document.documentElement); }
        else { (document.exitFullscreen || function () {}).call(document); }
        e.preventDefault(); break;
      default:
        if (k >= "1" && k <= "9" && slides.length < 10) { go(parseInt(k, 10) - 1); e.preventDefault(); }
    }
  });

  // --- swipe tactil --------------------------------------------------------
  var tx = 0, ty = 0;
  deck.addEventListener("touchstart", function (e) {
    tx = e.changedTouches[0].clientX; ty = e.changedTouches[0].clientY;
  }, { passive: true });
  deck.addEventListener("touchend", function (e) {
    if (overview) return;
    var dx = e.changedTouches[0].clientX - tx;
    var dy = e.changedTouches[0].clientY - ty;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy)) { dx < 0 ? next() : prev(); }
  }, { passive: true });

  // --- click en mitades (opcional, no invasivo) ----------------------------
  deck.addEventListener("click", function (e) {
    if (overview) return;
    if (e.target.closest("a, button, pre, code, .no-nav, .node")) return;
    // solo avanza con click sobre el tercio derecho
    var x = e.clientX / window.innerWidth;
    if (x > 0.82) next();
  });

  // --- arranque: respeta el hash ------------------------------------------
  var start = parseInt((location.hash || "").replace("#", ""), 10);
  if (!isNaN(start) && start >= 1 && start <= slides.length) current = start - 1;
  render();

  window.addEventListener("hashchange", function () {
    if (overview) return;
    var n = parseInt((location.hash || "").replace("#", ""), 10);
    if (!isNaN(n) && (n - 1) !== current) go(n - 1);
  });
})();
