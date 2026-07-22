/**
 * brandbox-home-scroll.js — Scroll-driven 3D reveals + hero depth.
 */
(function () {
  "use strict";

  document.documentElement.classList.add("brandbox-motion");

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var canHover = window.matchMedia("(hover: hover)").matches;

  function revealSections() {
    var sections = document.querySelectorAll("section.brandbox-reveal");
    var children = document.querySelectorAll("[data-brandbox-reveal-child]");
    if (!sections.length && !children.length) return;

    children.forEach(function (child, i) {
      var siblings = child.parentElement
        ? child.parentElement.querySelectorAll(":scope > [data-brandbox-reveal-child]")
        : [];
      var index = siblings.length
        ? Array.prototype.indexOf.call(siblings, child)
        : i;
      child.style.setProperty("--reveal-delay", (0.05 + Math.max(0, index) * 0.1).toFixed(2) + "s");
    });

    function showAll() {
      sections.forEach(function (el) {
        el.classList.add("is-visible");
      });
      children.forEach(function (el) {
        el.classList.add("is-visible");
      });
    }

    if (reduceMotion || !("IntersectionObserver" in window)) {
      showAll();
      return;
    }

    var sectionIo = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          sectionIo.unobserve(entry.target);
        });
      },
      { threshold: 0.18, rootMargin: "0px 0px -10% 0px" }
    );

    var childIo = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          childIo.unobserve(entry.target);
        });
      },
      { threshold: 0.22, rootMargin: "0px 0px -14% 0px" }
    );

    sections.forEach(function (section) {
      sectionIo.observe(section);
    });
    children.forEach(function (child) {
      childIo.observe(child);
    });
  }

  function heroDepth() {
    var hero = document.querySelector(".brandbox-hero");
    var stage = document.querySelector("[data-brandbox-hero-stage]");
    if (!hero || !stage) return;

    var frames = stage.querySelectorAll(".brandbox-hero__theme-frame");
    if (!frames.length) return;

    if (reduceMotion) {
      stage.classList.add("is-ready");
      return;
    }

    var pointer = { x: 0.5, y: 0.5 };
    var target = { x: 0.5, y: 0.5 };
    var scrollY = 0;
    var raf = 0;

    var base = [
      { rx: -6, ry: 10, tz: -40, ty: -12 },
      { rx: -3, ry: 4, tz: -16, ty: -6 },
      { rx: 0, ry: 0, tz: 28, ty: 0 },
      { rx: 3, ry: -4, tz: -16, ty: -6 },
      { rx: 6, ry: -10, tz: -40, ty: -12 },
    ];

    function layout() {
      var rect = hero.getBoundingClientRect();
      var vh = window.innerHeight || 1;
      var progress = 1 - Math.min(1, Math.max(0, (rect.bottom - vh * 0.15) / (rect.height + vh * 0.2)));
      scrollY = progress;
    }

    function paint() {
      raf = 0;
      pointer.x += (target.x - pointer.x) * 0.08;
      pointer.y += (target.y - pointer.y) * 0.08;

      var px = (pointer.x - 0.5) * 2;
      var py = (pointer.y - 0.5) * 2;
      var depthFade = 1 - scrollY * 0.35;

      stage.style.transform =
        "perspective(1200px) rotateX(" +
        (py * -4 + scrollY * 8).toFixed(2) +
        "deg) rotateY(" +
        (px * 6).toFixed(2) +
        "deg) translateZ(0)";

      frames.forEach(function (frame, i) {
        var b = base[i] || base[2];
        var extraY = scrollY * (18 + Math.abs(i - 2) * 10);
        var extraZ = -scrollY * (20 + Math.abs(i - 2) * 14);
        var tiltX = b.rx + py * -3;
        var tiltY = b.ry + px * 5;
        var scale = i === 2 ? 1.04 : 1;

        frame.style.transform =
          "translate3d(0, " +
          (b.ty + extraY).toFixed(2) +
          "px, " +
          (b.tz + extraZ).toFixed(2) +
          "px) rotateX(" +
          tiltX.toFixed(2) +
          "deg) rotateY(" +
          tiltY.toFixed(2) +
          "deg) scale(" +
          scale +
          ")";
        frame.style.opacity = String(Math.max(0.55, depthFade));
      });
    }

    function requestPaint() {
      if (!raf) raf = requestAnimationFrame(paint);
    }

    function onPointer(e) {
      var rect = stage.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      target.x = (e.clientX - rect.left) / rect.width;
      target.y = (e.clientY - rect.top) / rect.height;
      requestPaint();
    }

    function onLeave() {
      target.x = 0.5;
      target.y = 0.5;
      requestPaint();
    }

    function onScroll() {
      layout();
      requestPaint();
    }

    if (canHover) {
      stage.addEventListener("pointermove", onPointer, { passive: true });
      stage.addEventListener("pointerleave", onLeave);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });

    stage.classList.add("is-ready");
    layout();
    paint();
  }

  function animateTopStage() {
    var top = document.querySelector("[data-brandbox-top]");
    if (!top) return;

    var grid = top.querySelector("[data-brandbox-top-grid]");
    var orbA = top.querySelector('[data-brandbox-top-orb="a"]');
    var orbB = top.querySelector('[data-brandbox-top-orb="b"]');
    var nodes = top.querySelector("[data-brandbox-top-nodes]");
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
          "rotate(-16deg) translate3d(" +
          ax.toFixed(2) +
          "px, " +
          ay.toFixed(2) +
          "px, 0)";
      }

      if (orbB) {
        var bx = Math.cos(t * 0.32) * 22 + (pointer.x - 0.5) * 30;
        var by = Math.sin(t * 0.4) * 26 + (pointer.y - 0.35) * 18;
        orbB.style.transform =
          "rotate(14deg) translate3d(" +
          bx.toFixed(2) +
          "px, " +
          by.toFixed(2) +
          "px, 0)";
      }

      if (nodes) {
        var nx = Math.sin(t * 0.22) * 10 + (pointer.x - 0.5) * 16;
        var ny = Math.cos(t * 0.26) * 8 + (pointer.y - 0.35) * 12;
        var no = 0.45 + Math.sin(t * 0.55) * 0.12;
        nodes.style.transform =
          "translate3d(" + nx.toFixed(2) + "px, " + ny.toFixed(2) + "px, 0)";
        nodes.style.opacity = String(no);
      }

      requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);
  }

  function bindCardTilt() {
    if (reduceMotion || !canHover) return;

    var cards = document.querySelectorAll("[data-brandbox-tilt]");
    cards.forEach(function (card) {
      var max = 8;

      function onMove(e) {
        var rect = card.getBoundingClientRect();
        var x = (e.clientX - rect.left) / rect.width;
        var y = (e.clientY - rect.top) / rect.height;
        var rotY = (x - 0.5) * max * 2;
        var rotX = (0.5 - y) * max * 2;
        card.classList.add("is-tilting");
        card.style.transform =
          "perspective(900px) rotateX(" +
          rotX.toFixed(2) +
          "deg) rotateY(" +
          rotY.toFixed(2) +
          "deg) translateZ(12px)";
      }

      function onLeave() {
        card.classList.remove("is-tilting");
        card.style.transform = "";
      }

      card.addEventListener("pointermove", onMove);
      card.addEventListener("pointerleave", onLeave);
    });
  }

  function init() {
    animateTopStage();
    revealSections();
    heroDepth();
    bindCardTilt();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
