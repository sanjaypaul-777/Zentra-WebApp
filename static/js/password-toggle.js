/**
 * Password visibility toggle — wraps input[type=password] with an eye button.
 */
(function () {
  function enhance(input) {
    if (!input || input.dataset.pwToggle === "1") return;
    if (input.type !== "password" && input.type !== "text") return;
    if (input.closest(".pw-field")) return;

    input.dataset.pwToggle = "1";
    var wrap = document.createElement("div");
    wrap.className = "pw-field";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pw-field__toggle";
    btn.setAttribute("aria-label", "Show password");
    btn.setAttribute("aria-pressed", "false");
    btn.innerHTML =
      '<span class="material-symbols-outlined pw-field__icon" aria-hidden="true">visibility</span>';
    wrap.appendChild(btn);

    var icon = btn.querySelector(".pw-field__icon");
    btn.addEventListener("click", function () {
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      icon.textContent = show ? "visibility_off" : "visibility";
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
      btn.setAttribute("aria-pressed", show ? "true" : "false");
      try {
        input.focus();
        var len = input.value.length;
        input.setSelectionRange(len, len);
      } catch (e) {}
    });
  }

  function scan(root) {
    (root || document)
      .querySelectorAll('input[type="password"]')
      .forEach(enhance);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      scan();
    });
  } else {
    scan();
  }

  // In case password fields are injected later (e.g. checkout guest flow)
  window.BrandBoxPasswordToggle = { scan: scan };
})();
