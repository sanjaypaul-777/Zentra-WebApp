/**
 * affiliate-landing.js — Scroll reveals, card tilt, top-stage texture animation.
 */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function reveal() {
    var nodes = document.querySelectorAll(".aff-reveal");
    if (!nodes.length) return;

    if (reduceMotion || !("IntersectionObserver" in window)) {
      nodes.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -6% 0px" }
    );

    nodes.forEach(function (el) {
      io.observe(el);
    });
  }

  function bindTilt(root) {
    if (reduceMotion || !window.matchMedia("(hover: hover)").matches) return;

    var max = 7;

    function onMove(e) {
      var face = root.querySelector(".aff-tilt-card__face, .aff-earn__panel-face");
      if (!face) return;
      var rect = root.getBoundingClientRect();
      var x = (e.clientX - rect.left) / rect.width;
      var y = (e.clientY - rect.top) / rect.height;
      var rotY = (x - 0.5) * max * 2;
      var rotX = (0.5 - y) * max * 2;
      root.classList.add("is-tilting");
      face.style.transform =
        "translateZ(18px) rotateX(" +
        rotX.toFixed(2) +
        "deg) rotateY(" +
        rotY.toFixed(2) +
        "deg)";
    }

    function onLeave() {
      var face = root.querySelector(".aff-tilt-card__face, .aff-earn__panel-face");
      root.classList.remove("is-tilting");
      if (face) face.style.transform = "";
    }

    root.addEventListener("pointermove", onMove);
    root.addEventListener("pointerleave", onLeave);
  }

  function animateTopStage() {
    var top = document.querySelector("[data-aff-top]");
    if (!top) return;

    var grid = top.querySelector("[data-aff-grid]");
    var orbA = top.querySelector('[data-aff-orb="a"]');
    var orbB = top.querySelector('[data-aff-orb="b"]');
    if (!grid) return;

    if (reduceMotion) return;

    var pointer = { x: 0.5, y: 0.35 };
    var target = { x: 0.5, y: 0.35 };
    var start = performance.now();

    function onPointer(e) {
      var rect = top.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      target.x = (e.clientX - rect.left) / rect.width;
      target.y = (e.clientY - rect.top) / rect.height;
    }

    top.addEventListener("pointermove", onPointer, { passive: true });

    function frame(now) {
      var t = (now - start) / 1000;
      pointer.x += (target.x - pointer.x) * 0.06;
      pointer.y += (target.y - pointer.y) * 0.06;

      var driftX = Math.sin(t * 0.35) * 18 + (pointer.x - 0.5) * 28;
      var driftY = Math.cos(t * 0.28) * 12 + (pointer.y - 0.35) * 22;
      var scale = 1.4 + Math.sin(t * 0.2) * 0.02;

      grid.style.transform =
        "perspective(900px) rotateX(56deg) translate3d(" +
        driftX.toFixed(2) +
        "px, " +
        driftY.toFixed(2) +
        "px, 0) scale(" +
        scale.toFixed(3) +
        ")";

      if (orbA) {
        var ax = Math.sin(t * 0.45) * 24 + (pointer.x - 0.5) * -36;
        var ay = Math.cos(t * 0.38) * 20 + (pointer.y - 0.35) * -20;
        orbA.style.transform =
          "rotate(-18deg) translate3d(" +
          ax.toFixed(2) +
          "px, " +
          ay.toFixed(2) +
          "px, 0)";
      }

      if (orbB) {
        var bx = Math.cos(t * 0.32) * 22 + (pointer.x - 0.5) * 30;
        var by = Math.sin(t * 0.4) * 26 + (pointer.y - 0.35) * 18;
        orbB.style.transform =
          "rotate(12deg) translate3d(" +
          bx.toFixed(2) +
          "px, " +
          by.toFixed(2) +
          "px, 0)";
      }

      requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);
  }

  function animateWhoPanels() {
    var root = document.querySelector("[data-aff-who]");
    if (!root || reduceMotion) return;

    var panels = root.querySelectorAll("[data-aff-who-panel]");
    if (!panels.length) return;

    var ticking = false;

    function update() {
      ticking = false;
      var vh = window.innerHeight || 1;
      panels.forEach(function (panel, index) {
        var layer = panel.querySelector("[data-aff-who-parallax]");
        if (!layer || !panel.classList.contains("is-visible")) return;
        var rect = panel.getBoundingClientRect();
        var mid = rect.top + rect.height * 0.5;
        var progress = (mid - vh * 0.5) / vh;
        var shift = Math.max(-16, Math.min(16, progress * -26));
        var offset = (index % 2 === 0 ? 1 : -1) * 3;
        layer.style.transform =
          "translate3d(0, " + (shift + offset).toFixed(2) + "px, 0)";
      });
    }

    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    update();
  }

  document.addEventListener("DOMContentLoaded", function () {
    reveal();
    document.querySelectorAll(".aff-tilt-card, [data-aff-tilt]").forEach(bindTilt);
    animateTopStage();
    animateWhoPanels();
  });
})();
