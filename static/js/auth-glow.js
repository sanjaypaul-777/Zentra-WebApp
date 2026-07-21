/**
 * auth-glow.js — Soft pond-style circular ripples behind the auth logo.
 * Requires .auth-logo-wrap > .auth-glow
 */
(function () {
  "use strict";

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  var wrap = document.querySelector(".auth-logo-wrap");
  if (!wrap) return;

  var glow = wrap.querySelector(".auth-glow");
  var logo = wrap.querySelector(".auth-logo");

  var layer = document.createElement("div");
  layer.className = "auth-glow-ripples";
  layer.setAttribute("aria-hidden", "true");
  wrap.insertBefore(layer, logo || null);

  var DURATION = 6200;
  var INTERVAL = 2000;
  var MAX_SCALE = 2.05;
  var rippleIndex = 0;

  function spawnRipple() {
    var el = document.createElement("span");
    el.className =
      "auth-glow-ripple" +
      (rippleIndex % 2 === 0
        ? " auth-glow-ripple--magenta"
        : " auth-glow-ripple--green");
    rippleIndex += 1;
    layer.appendChild(el);

    if (typeof el.animate === "function") {
      var anim = el.animate(
        [
          {
            transform: "translate(-50%, -50%) scale(0.22)",
            opacity: 0,
          },
          {
            transform: "translate(-50%, -50%) scale(0.42)",
            opacity: 0.42,
            offset: 0.12,
          },
          {
            transform: "translate(-50%, -50%) scale(1.05)",
            opacity: 0.28,
            offset: 0.45,
          },
          {
            transform: "translate(-50%, -50%) scale(" + MAX_SCALE + ")",
            opacity: 0,
          },
        ],
        {
          duration: DURATION,
          easing: "cubic-bezier(0.33, 0.05, 0.2, 1)",
          fill: "forwards",
        }
      );
      anim.onfinish = function () {
        el.remove();
      };
    } else {
      el.classList.add("auth-glow-ripple--fallback");
      window.setTimeout(function () {
        el.remove();
      }, DURATION);
    }
  }

  spawnRipple();
  window.setTimeout(spawnRipple, INTERVAL / 2);
  window.setInterval(spawnRipple, INTERVAL);

  if (glow && typeof glow.animate === "function") {
    glow.animate(
      [
        {
          transform: "translate(-50%, -50%) scale(1)",
          opacity: 0.2,
          filter: "blur(90px)",
        },
        {
          transform: "translate(-50%, -50%) scale(1.08)",
          opacity: 0.28,
          filter: "blur(96px)",
          offset: 0.35,
        },
        {
          transform: "translate(-50%, -50%) scale(1.14)",
          opacity: 0.24,
          filter: "blur(100px)",
          offset: 0.65,
        },
        {
          transform: "translate(-50%, -50%) scale(1)",
          opacity: 0.2,
          filter: "blur(90px)",
        },
      ],
      {
        duration: 5200,
        iterations: Infinity,
        easing: "ease-in-out",
      }
    );
  }
})();
