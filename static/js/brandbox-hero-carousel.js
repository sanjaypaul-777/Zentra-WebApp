/**
 * brandbox-hero-carousel.js
 * Curved 3D track — cards slide close together, face mostly forward.
 *
 * Timing: AUTO_SEC_PER_CARD (seconds per step, clockwise)
 */
(function () {
  "use strict";

  var stage = document.querySelector("[data-brandbox-hero-carousel]");
  if (!stage) return;

  var items = Array.prototype.slice.call(
    stage.querySelectorAll(".brandbox-hero__theme")
  );
  var n = items.length;
  if (n < 2) return;

  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {}

  /* —— Timing: faster —— */
  var AUTO_SEC_PER_CARD = 1.8;
  var autoSpeed = 1 / AUTO_SEC_PER_CARD;
  var LERP = 12;

  var pos = Math.floor(n / 2);
  var displayPos = pos;
  var dragging = false;
  var dragMoved = false;
  var dragStartX = 0;
  var dragStartPos = 0;
  var lastTs = 0;
  var pauseUntil = 0;
  var snapTarget = null;

  function wrap(v) {
    v = v % n;
    if (v < 0) v += n;
    return v;
  }

  function shortestDelta(from, to) {
    var d = ((to - from) % n + n) % n;
    if (d > n / 2) d -= n;
    return d;
  }

  function relativeOffset(i, center) {
    var raw = i - center;
    if (raw > n / 2) raw -= n;
    if (raw < -n / 2) raw += n;
    return raw;
  }

  /**
   * Tight arc spacing. Cards stay mostly face-forward
   * (tiny tilt only — no spinning in place).
   */
  function metrics() {
    var w = window.innerWidth || 1200;
    if (w <= 640) {
      return {
        radius: 155,
        stepDeg: 18,
        tilt: 0.22,
        yLift: 4,
        scaleActive: 1.05,
        scaleFar: 0.86,
      };
    }
    if (w <= 900) {
      return {
        radius: 200,
        stepDeg: 16,
        tilt: 0.2,
        yLift: 5,
        scaleActive: 1.06,
        scaleFar: 0.88,
      };
    }
    return {
      radius: 250,
      stepDeg: 14,
      tilt: 0.18,
      yLift: 6,
      scaleActive: 1.08,
      scaleFar: 0.9,
    };
  }

  function paint() {
    var m = metrics();
    var step = (m.stepDeg * Math.PI) / 180;

    items.forEach(function (item, i) {
      var off = relativeOffset(i, displayPos);
      var angle = off * step;

      var x = Math.sin(angle) * m.radius;
      var z = Math.cos(angle) * m.radius - m.radius;
      var y = Math.abs(Math.sin(angle)) * m.yLift;
      /* Face mostly toward camera — only a light yaw */
      var ry = ((-angle * 180) / Math.PI) * m.tilt;

      var abs = Math.abs(off);
      var depth = Math.max(0, Math.cos(angle));
      var scale = m.scaleFar + (m.scaleActive - m.scaleFar) * depth;
      var blur = (1 - depth) * 1.6;
      var opacity = 0.55 + depth * 0.45;
      var zIndex = 10 + Math.round(depth * 20);

      item.style.zIndex = String(zIndex);
      item.style.opacity = String(opacity.toFixed(3));
      item.style.filter = blur > 0.15 ? "blur(" + blur.toFixed(2) + "px)" : "none";
      item.style.transform =
        "translate3d(-50%, -50%, 0) translate3d(" +
        x.toFixed(2) +
        "px, " +
        y.toFixed(2) +
        "px, " +
        z.toFixed(2) +
        "px) rotateY(" +
        ry.toFixed(2) +
        "deg) scale(" +
        scale.toFixed(3) +
        ")";

      var isActive = abs < 0.5;
      item.classList.toggle("is-active", isActive);
      item.setAttribute("aria-hidden", isActive ? "false" : "true");
    });
  }

  function tick(ts) {
    requestAnimationFrame(tick);
    if (!lastTs) lastTs = ts;
    var dt = Math.min(0.05, (ts - lastTs) / 1000);
    lastTs = ts;

    if (dragging) {
      displayPos = pos;
      paint();
      return;
    }

    if (snapTarget !== null) {
      var dSnap = shortestDelta(pos, snapTarget);
      if (Math.abs(dSnap) < 0.001) {
        pos = wrap(snapTarget);
        snapTarget = null;
      } else {
        pos = wrap(pos + dSnap * Math.min(1, dt * 9));
      }
    } else if (!reduceMotion && ts >= pauseUntil) {
      pos = wrap(pos + autoSpeed * dt);
    }

    var follow = shortestDelta(displayPos, pos);
    displayPos = wrap(displayPos + follow * Math.min(1, dt * LERP));
    paint();
  }

  function snapNow() {
    snapTarget = Math.round(wrap(pos));
  }

  function pauseAuto(ms) {
    pauseUntil = performance.now() + (ms || AUTO_SEC_PER_CARD * 1000);
  }

  function onPointerDown(e) {
    if (e.button != null && e.button !== 0) return;
    dragging = true;
    dragMoved = false;
    dragStartX = e.clientX;
    dragStartPos = pos;
    snapTarget = null;
    stage.classList.add("is-dragging");
    try {
      stage.setPointerCapture(e.pointerId);
    } catch (err) {}
  }

  function onPointerMove(e) {
    if (!dragging) return;
    var dx = e.clientX - dragStartX;
    if (Math.abs(dx) > 5) dragMoved = true;
    var m = metrics();
    var pxPerCard = Math.max(70, m.radius * stepRad(m) * 0.9);
    pos = wrap(dragStartPos - dx / pxPerCard);
  }

  function stepRad(m) {
    return (m.stepDeg * Math.PI) / 180;
  }

  function onPointerUp(e) {
    if (!dragging) return;
    dragging = false;
    stage.classList.remove("is-dragging");
    try {
      stage.releasePointerCapture(e.pointerId);
    } catch (err) {}
    snapNow();
    pauseAuto(AUTO_SEC_PER_CARD * 800);
  }

  stage.addEventListener("pointerdown", onPointerDown);
  stage.addEventListener("pointermove", onPointerMove);
  stage.addEventListener("pointerup", onPointerUp);
  stage.addEventListener("pointercancel", onPointerUp);
  stage.addEventListener(
    "click",
    function (e) {
      if (dragMoved) {
        e.preventDefault();
        e.stopPropagation();
        dragMoved = false;
      }
    },
    true
  );

  items.forEach(function (item, i) {
    item.addEventListener("click", function (e) {
      if (dragMoved) {
        e.preventDefault();
        return;
      }
      var cur = Math.round(wrap(displayPos));
      snapTarget = wrap(cur + shortestDelta(cur, i));
      pauseAuto(AUTO_SEC_PER_CARD * 800);
    });
    item.addEventListener("keydown", function (e) {
      var cur = Math.round(wrap(displayPos));
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        snapTarget = wrap(cur + shortestDelta(cur, i));
        pauseAuto(AUTO_SEC_PER_CARD * 800);
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        snapTarget = wrap(cur - 1);
        pauseAuto(AUTO_SEC_PER_CARD * 800);
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        snapTarget = wrap(cur + 1);
        pauseAuto(AUTO_SEC_PER_CARD * 800);
      }
    });
  });

  window.addEventListener("resize", paint, { passive: true });

  stage.classList.add("is-ready");
  displayPos = pos;
  paint();
  requestAnimationFrame(tick);
})();
