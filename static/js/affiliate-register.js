/**
 * affiliate-register.js — Toggle “Other” detail fields on the register form.
 */
(function () {
  "use strict";

  function bindOther(triggerKey) {
    var trigger = document.querySelector(
      '[data-aff-other-trigger="' + triggerKey + '"]'
    );
    var wrap = document.querySelector(
      '[data-aff-other-panel="' + triggerKey + '"]'
    );
    if (!trigger || !wrap) return;

    var field = wrap.querySelector("textarea, input");

    function sync() {
      var isOther = trigger.value === "other";
      wrap.hidden = !isOther;
      wrap.classList.toggle("is-open", isOther);
      if (field) {
        field.required = isOther;
        if (!isOther) field.value = "";
      }
    }

    trigger.addEventListener("change", sync);
    sync();
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindOther("activity");
    bindOther("promotion");
  });
})();
