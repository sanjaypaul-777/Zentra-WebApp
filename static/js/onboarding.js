/**
 * Onboarding — pill + circle-list single/multi select wired to hidden inputs.
 */
(function () {
  var root = document.querySelector("[data-onboarding]");
  if (!root) return;

  function optionButtons(group) {
    return group.querySelectorAll(".ob-pill, .ob-choice");
  }

  root.querySelectorAll("[data-ob-single]").forEach(function (group) {
    var hidden = group.parentElement.querySelector("[data-ob-hidden]");
    var otherWrap = group.parentElement.querySelector("[data-ob-other]");
    optionButtons(group).forEach(function (btn) {
      btn.addEventListener("click", function () {
        optionButtons(group).forEach(function (b) {
          b.classList.remove("is-selected");
          b.setAttribute("aria-pressed", "false");
          if (b.getAttribute("role") === "radio") {
            b.setAttribute("aria-checked", "false");
          }
        });
        btn.classList.add("is-selected");
        btn.setAttribute("aria-pressed", "true");
        if (btn.getAttribute("role") === "radio") {
          btn.setAttribute("aria-checked", "true");
        }
        if (hidden) hidden.value = btn.getAttribute("data-value") || "";
        if (otherWrap) {
          if (btn.getAttribute("data-value") === "other") {
            otherWrap.classList.remove("is-hidden");
          } else {
            otherWrap.classList.add("is-hidden");
          }
        }
      });
    });
  });

  root.querySelectorAll("[data-ob-multi]").forEach(function (group) {
    var parent = group.parentElement;
    var inputsHost = parent.querySelector("[data-ob-multi-inputs]");
    var otherWrap = parent.querySelector("[data-ob-other]");
    var name = group.getAttribute("data-ob-name") || "biggest_challenges";

    function sync() {
      if (!inputsHost) return;
      inputsHost.innerHTML = "";
      var hasOther = false;
      group
        .querySelectorAll(".ob-pill.is-selected, .ob-choice.is-selected")
        .forEach(function (btn) {
          var value = btn.getAttribute("data-value") || "";
          if (value === "other") hasOther = true;
          var input = document.createElement("input");
          input.type = "hidden";
          input.name = name;
          input.value = value;
          inputsHost.appendChild(input);
        });
      if (otherWrap) {
        if (hasOther) {
          otherWrap.classList.remove("is-hidden");
        } else {
          otherWrap.classList.add("is-hidden");
          var otherInput = otherWrap.querySelector("input, textarea");
          if (otherInput && !hasOther) {
            // keep typed text if they re-toggle Other; only clear on submit via form clean
          }
        }
      }
    }

    optionButtons(group).forEach(function (btn) {
      btn.addEventListener("click", function () {
        btn.classList.toggle("is-selected");
        var on = btn.classList.contains("is-selected");
        btn.setAttribute("aria-pressed", on ? "true" : "false");
        sync();
        if (
          on &&
          btn.getAttribute("data-value") === "other" &&
          otherWrap
        ) {
          var otherInput = otherWrap.querySelector("input, textarea");
          if (otherInput) {
            try {
              otherInput.focus();
            } catch (e) {}
          }
        }
      });
    });
    sync();
  });
})();
