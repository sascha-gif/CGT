/* ==========================================================================
   CGT Pitch — Bewegung
   Scroll-Einblendungen, Parallax, hochzählende Kennzahlen, Slider, Fortschritt.
   Kein Framework, keine externen Abhängigkeiten.
   Wer "Bewegung reduzieren" im Betriebssystem eingestellt hat, bekommt alles
   sofort und statisch — das ist Absicht.
   ========================================================================== */
(function () {
  "use strict";

  document.documentElement.classList.remove("kein-js");

  var ruhig = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------------------------------------------------------- Auftritt
     Alles mit data-auftritt blendet ein, sobald es ins Bild kommt. */
  function auftritteStarten() {
    var teile = document.querySelectorAll("[data-auftritt]");
    if (ruhig || !("IntersectionObserver" in window)) {
      teile.forEach(function (el) { el.classList.add("ist-sichtbar"); });
      return;
    }
    var beobachter = new IntersectionObserver(function (eintraege) {
      eintraege.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add("ist-sichtbar");
        beobachter.unobserve(e.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

    teile.forEach(function (el) { beobachter.observe(el); });
  }

  /* ---------------------------------------------------------------- Parallax
     Hero- und Bandbilder laufen langsamer als die Seite.
     Läuft über requestAnimationFrame, nicht im Scroll-Ereignis. */
  function parallaxStarten() {
    var ebenen = Array.prototype.slice.call(
      document.querySelectorAll("[data-parallax]")
    );
    if (ruhig || !ebenen.length) return;
    if (window.matchMedia("(pointer: coarse)").matches && window.innerWidth < 600) {
      /* Auf kleinen Touch-Geräten kostet Parallax mehr als es bringt. */
      return;
    }

    var laeuft = false;

    function zeichnen() {
      laeuft = false;
      var hoehe = window.innerHeight;
      ebenen.forEach(function (ebene) {
        var kasten = ebene.parentElement.getBoundingClientRect();
        if (kasten.bottom < -200 || kasten.top > hoehe + 200) return;
        var tempo = parseFloat(ebene.getAttribute("data-parallax")) || 0.25;
        var mitte = kasten.top + kasten.height / 2 - hoehe / 2;
        ebene.style.transform = "translate3d(0," + (-mitte * tempo).toFixed(2) + "px,0)";
      });
    }

    function anstossen() {
      if (laeuft) return;
      laeuft = true;
      window.requestAnimationFrame(zeichnen);
    }

    window.addEventListener("scroll", anstossen, { passive: true });
    window.addEventListener("resize", anstossen);
    zeichnen();
  }

  /* -------------------------------------------------------------- Kennzahlen
     Zahlen zählen beim ersten Sichtkontakt hoch. Alles, was keine reine Zahl
     ist (z. B. "ab 2027"), bleibt wie es ist. */
  function kennzahlenStarten() {
    var werte = document.querySelectorAll("[data-zaehlen]");
    if (!werte.length) return;

    function zaehlen(el) {
      var roh = el.getAttribute("data-zaehlen");
      var zahl = parseFloat(roh.replace(/\./g, "").replace(",", "."));
      if (isNaN(zahl)) { el.textContent = el.getAttribute("data-fertig"); return; }

      var vor = el.getAttribute("data-vor") || "";
      var nach = el.getAttribute("data-nach") || "";
      var nachkomma = (roh.split(",")[1] || "").length;
      var dauer = 1100;
      var start = null;

      function schritt(jetzt) {
        if (start === null) start = jetzt;
        var p = Math.min((jetzt - start) / dauer, 1);
        var weich = 1 - Math.pow(1 - p, 3);
        var aktuell = zahl * weich;
        el.textContent = vor + aktuell.toLocaleString("de-DE", {
          minimumFractionDigits: nachkomma,
          maximumFractionDigits: nachkomma,
          useGrouping: el.getAttribute("data-gruppiert") === "1"
        }) + nach;
        if (p < 1) window.requestAnimationFrame(schritt);
      }
      window.requestAnimationFrame(schritt);
    }

    if (ruhig || !("IntersectionObserver" in window)) {
      werte.forEach(function (el) { el.textContent = el.getAttribute("data-fertig"); });
      return;
    }

    var beobachter = new IntersectionObserver(function (eintraege) {
      eintraege.forEach(function (e) {
        if (!e.isIntersecting) return;
        zaehlen(e.target);
        beobachter.unobserve(e.target);
      });
    }, { threshold: 0.5 });

    werte.forEach(function (el) { beobachter.observe(el); });
  }

  /* ------------------------------------------------------------------- Kopf
     Kopfzeile wird fest, sobald man den Hero verlässt. Dazu der
     Lesefortschritt als dünner Balken. */
  function kopfStarten() {
    var kopf = document.querySelector(".kopf");
    var balken = document.querySelector(".fortschritt");
    if (!kopf) return;

    var laeuft = false;

    function zeichnen() {
      laeuft = false;
      var y = window.scrollY || window.pageYOffset;
      kopf.classList.toggle("ist-geklebt", y > window.innerHeight * 0.55);
      if (balken) {
        var gesamt = document.documentElement.scrollHeight - window.innerHeight;
        var anteil = gesamt > 0 ? Math.min(y / gesamt, 1) : 0;
        balken.style.width = (anteil * 100).toFixed(1) + "%";
      }
    }

    function anstossen() {
      if (laeuft) return;
      laeuft = true;
      window.requestAnimationFrame(zeichnen);
    }

    window.addEventListener("scroll", anstossen, { passive: true });
    window.addEventListener("resize", anstossen);
    zeichnen();
  }

  /* ----------------------------------------------------------------- Slider
     Auf dem Handy wischt man. Am Desktop gibt es zwei Pfeile. */
  function sliderStarten() {
    document.querySelectorAll(".slider").forEach(function (slider) {
      var spur = slider.querySelector(".slider__spur");
      var zurueck = slider.querySelector("[data-slider='zurueck']");
      var vor = slider.querySelector("[data-slider='vor']");
      if (!spur || !zurueck || !vor) return;

      function schrittweite() {
        var erstes = spur.firstElementChild;
        if (!erstes) return spur.clientWidth;
        var luecke = parseFloat(getComputedStyle(spur).columnGap) || 16;
        return erstes.getBoundingClientRect().width + luecke;
      }

      function knoepfePruefen() {
        var maximal = spur.scrollWidth - spur.clientWidth - 2;
        var steuer = slider.querySelector(".slider__steuer");
        /* Passt alles ins Bild, braucht es keine Pfeile. */
        if (steuer) steuer.style.display = maximal > 2 ? "" : "none";
        zurueck.disabled = spur.scrollLeft <= 2;
        vor.disabled = spur.scrollLeft >= maximal;
      }

      zurueck.addEventListener("click", function () {
        spur.scrollBy({ left: -schrittweite(), behavior: ruhig ? "auto" : "smooth" });
      });
      vor.addEventListener("click", function () {
        spur.scrollBy({ left: schrittweite(), behavior: ruhig ? "auto" : "smooth" });
      });
      spur.addEventListener("scroll", knoepfePruefen, { passive: true });
      window.addEventListener("resize", knoepfePruefen);
      knoepfePruefen();
    });
  }

  /* --------------------------------------------------------------- Startschuss */
  function los() {
    auftritteStarten();
    parallaxStarten();
    kennzahlenStarten();
    kopfStarten();
    sliderStarten();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", los);
  } else {
    los();
  }
})();
