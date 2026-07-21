/**
 * status-404.js — Compass needle spins fast, then settles pointing at
 * the “Back to Dashboard” button (reinforces the wrong-turn copy).
 */
(function () {
  "use strict";

  var needle = document.getElementById("status-404-needle");
  var target = document.getElementById("status-404-target");
  var compass = document.querySelector(".status-404-compass");
  if (!needle || !target || !compass) return;

  function angleToTarget() {
    var c = compass.getBoundingClientRect();
    var t = target.getBoundingClientRect();
    var cx = c.left + c.width / 2;
    var cy = c.top + c.height / 2;
    var tx = t.left + t.width / 2;
    var ty = t.top + t.height / 2;
    // 0° = north tip up; positive = clockwise.
    return (Math.atan2(tx - cx, cy - ty) * 180) / Math.PI;
  }

  function setAngle(deg) {
    needle.setAttribute("transform", "rotate(" + deg + " 60 60)");
  }

  function easeOutQuint(u) {
    return 1 - Math.pow(1 - u, 5);
  }

  var resting = angleToTarget();

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    setAngle(resting);
    needle.classList.add("is-settled");
    return;
  }

  var start = 0;
  var duration = 2600;
  var t0 = null;

  function frame(now) {
    if (t0 === null) t0 = now;
    var u = Math.min(1, (now - t0) / duration);
    resting = angleToTarget();

    var progressed = easeOutQuint(u);
    var angle = start + (resting - start) * progressed;

    if (u > 0.5 && u < 1) {
      var fade = Math.pow(1 - u, 2);
      angle += Math.sin((u - 0.5) * 32) * 7 * fade;
    }

    setAngle(angle);

    if (u < 1) {
      requestAnimationFrame(frame);
    } else {
      setAngle(resting);
      needle.classList.add("is-settled");
    }
  }

  requestAnimationFrame(function () {
    resting = angleToTarget();
    start = resting - 360 * (5 + Math.random() * 2);
    setAngle(start);
    requestAnimationFrame(frame);
  });

  window.addEventListener(
    "resize",
    function () {
      if (!needle.classList.contains("is-settled")) return;
      setAngle(angleToTarget());
    },
    { passive: true }
  );
})();
