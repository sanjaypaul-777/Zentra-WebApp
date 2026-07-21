/**
 * Hero headline typewriter — “AI Built Shopify Store” (type → pause → edit → repeat).
 */
(function () {
  var root = document.querySelector("[data-brandbox-hero-typed]");
  if (!root) return;

  var el = root.querySelector("[data-brandbox-hero-typed-text]");
  if (!el) return;

  var phrase = "AI Built Shopify Store";

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    el.textContent = phrase;
    return;
  }

  var charIndex = 0;
  var deleting = false;
  var holdMs = 0;

  var TYPE_MS = 55;
  var DELETE_MS = 32;
  var HOLD_AFTER_TYPE = 2200;
  var HOLD_AFTER_DELETE = 400;

  function tick() {
    if (holdMs > 0) {
      holdMs -= TYPE_MS;
      window.setTimeout(tick, TYPE_MS);
      return;
    }
    if (!deleting) {
      charIndex += 1;
      el.textContent = phrase.slice(0, charIndex);
      if (charIndex >= phrase.length) {
        deleting = true;
        holdMs = HOLD_AFTER_TYPE;
        window.setTimeout(tick, TYPE_MS);
        return;
      }
      window.setTimeout(tick, TYPE_MS);
      return;
    }

    charIndex -= 1;
    el.textContent = phrase.slice(0, Math.max(0, charIndex));
    if (charIndex <= 0) {
      deleting = false;
      holdMs = HOLD_AFTER_DELETE;
      window.setTimeout(tick, TYPE_MS);
      return;
    }
    window.setTimeout(tick, DELETE_MS);
  }

  el.textContent ="";
  tick();
})();
