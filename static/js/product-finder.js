/**
 * Product Hunter — live search UI + Import → Node via Django API.
 */
(function () {
  var root = document.querySelector("[data-product-finder]");
  if (!root) return;

  var csrf = root.getAttribute("data-csrf") || "";
  var importApi = root.getAttribute("data-import-api") || "";
  var importsUrl = root.getAttribute("data-imports-url") || "/dashboard/imports/";
  var canImport = root.getAttribute("data-can-import") === "1";
  var connectUrl ="/dashboard/connect/";

  function bindImageFallback(img) {
    if (!img || img.getAttribute("data-fallback-bound")) return;
    img.setAttribute("data-fallback-bound","1");
    img.addEventListener("error", function () {
      var card = img.closest("[data-product-card]") || img.closest("[data-m-media]") || root;
      var list = (card && card.getAttribute("data-images")) || "";
      var alts = list.split("|").map(function (s) { return s.trim(); }).filter(Boolean);
      var i = parseInt(img.getAttribute("data-img-i") || "0", 10) + 1;
      if (i < alts.length) {
        img.setAttribute("data-img-i", String(i));
        img.src = alts[i];
        return;
      }
      img.style.display ="none";
      var media = img.closest(".cat-card__media, .cat-modal__media");
      if (media) media.classList.remove("has-image");
    });
  }

  root.querySelectorAll("img[data-img-fallback]").forEach(bindImageFallback);
  function closeSelect(wrap) {
    if (!wrap) return;
    wrap.classList.remove("is-open");
    var menu = wrap.querySelector(".cat-select__menu");
    var trigger = wrap.querySelector(".cat-select__trigger");
    if (menu) menu.hidden = true;
    if (trigger) trigger.setAttribute("aria-expanded","false");
  }

  function closeAllSelects(except) {
    root.querySelectorAll("[data-cat-select].is-open").forEach(function (wrap) {
      if (wrap !== except) closeSelect(wrap);
    });
  }

  function selectOption(wrap, option) {
    var native = wrap.querySelector(".cat-select__native");
    var valueEl = wrap.querySelector(".cat-select__value");
    var value = option.getAttribute("data-value") || "";
    var label = option.textContent.trim();

    if (native) {
      native.value = value;
      native.dispatchEvent(new Event("change", { bubbles: true }));
    }
    if (valueEl) valueEl.textContent = label;

    wrap.querySelectorAll(".cat-select__menu [role='option']").forEach(function (li) {
      var on = li === option;
      li.classList.toggle("is-selected", on);
      if (on) li.setAttribute("aria-selected","true");
      else li.removeAttribute("aria-selected");
    });
    closeSelect(wrap);
  }

  root.querySelectorAll("[data-cat-select]").forEach(function (wrap) {
    var trigger = wrap.querySelector(".cat-select__trigger");
    var menu = wrap.querySelector(".cat-select__menu");
    if (!trigger || !menu) return;

    trigger.addEventListener("click", function (e) {
      e.preventDefault();
      var open = wrap.classList.contains("is-open");
      closeAllSelects();
      if (!open) {
        wrap.classList.add("is-open");
        menu.hidden = false;
        trigger.setAttribute("aria-expanded","true");
      }
    });

    menu.addEventListener("click", function (e) {
      var option = e.target.closest("[role='option']");
      if (!option) return;
      selectOption(wrap, option);
    });
  });

  document.addEventListener("click", function (e) {
    if (!e.target.closest("[data-cat-select]")) closeAllSelects();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeAllSelects();
  });

  function markImported(card) {
    if (!card) return;
    card.setAttribute("data-status","imported");
    var actions = card.querySelector(".cat-card__actions");
    if (!actions) return;
    var btn = actions.querySelector("[data-import-product]");
    if (!btn) return;
    var a = document.createElement("a");
    a.className = "cat-badge cat-badge--imported";
    a.href = importsUrl;
    a.textContent ="Added to My Imports";
    btn.replaceWith(a);
  }

  function importProduct(sourceId, card, btn) {
    if (!canImport) {
      window.location.href = connectUrl;
      return;
    }
    if (!importApi || !sourceId) return;
    if (btn) {
      btn.disabled = true;
      btn.textContent ="Importing…";
    }
    fetch(importApi, {
      method:"POST",
      credentials:"same-origin",
      headers: {
        Accept:"application/json","Content-Type":"application/json","X-CSRFToken": csrf,
      },
      body: JSON.stringify({ sourceId: sourceId }),
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { ok: r.ok, data: data };
        });
      })
      .then(function (res) {
        if (!res.ok || !res.data.ok) {
          var msg =
            (res.data && (res.data.message || res.data.error)) || "Import failed";
          window.alert(msg);
          if (btn) {
            btn.disabled = false;
            btn.innerHTML =
              'Import <span class="material-symbols-outlined btn-text__arrow" aria-hidden="true">arrow_outward</span>';
          }
          return;
        }
        markImported(card);
      })
      .catch(function () {
        window.alert("Import failed — try again.");
        if (btn) {
          btn.disabled = false;
          btn.innerHTML =
            'Import <span class="material-symbols-outlined btn-text__arrow" aria-hidden="true">arrow_outward</span>';
        }
      });
  }

  var grid = root.querySelector("[data-cat-grid]");
  var toggle = root.querySelector("[data-view-toggle]");
  var modal = root.querySelector("[data-cat-modal]");

  root.addEventListener("click", function (e) {
    var importBtn = e.target.closest("[data-import-product]");
    if (importBtn) {
      var card = importBtn.closest("[data-product-card]");
      var sourceId = card && card.getAttribute("data-source-id");
      importProduct(sourceId, card, importBtn);
      return;
    }
  });

  if (!grid || !toggle || !modal) return;

  var dialog = modal.querySelector("[data-cat-dialog]");
  var backdrop = modal.querySelector("[data-cat-backdrop]");
  var closeBtn = modal.querySelector("[data-cat-close]");
  var lastFocus = null;

  function setView(view) {
    grid.setAttribute("data-view", view);
    toggle.querySelectorAll("button[data-view]").forEach(function (btn) {
      var on = btn.getAttribute("data-view") === view;
      btn.setAttribute("aria-pressed", on ?"true" :"false");
    });
  }

  toggle.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-view]");
    if (!btn) return;
    setView(btn.getAttribute("data-view"));
  });

  function fillModal(card) {
    var data = {
      sourceId: card.getAttribute("data-source-id") || "",
      title: card.getAttribute("data-title") || "",
      niche: card.getAttribute("data-niche") || "",
      country: card.getAttribute("data-country") || "",
      cost: card.getAttribute("data-cost") || "",
      sell: card.getAttribute("data-sell") || "",
      margin: card.getAttribute("data-margin") || "",
      source: card.getAttribute("data-source") || "",
      status: card.getAttribute("data-status") || "default",
      hue: card.getAttribute("data-hue") || "160",
      image: card.getAttribute("data-image") || "",
      images: (card.getAttribute("data-images") || "").split("|").filter(Boolean),
    };

    modal.querySelector("[data-m-title]").textContent = data.title;
    modal.querySelector("[data-m-niche]").textContent = data.niche;
    modal.querySelector("[data-m-country]").textContent = data.country;
    modal.querySelector("[data-m-cost]").textContent = data.cost;
    modal.querySelector("[data-m-sell]").textContent = data.sell;
    modal.querySelector("[data-m-margin]").textContent = data.margin + "%";
    modal.querySelector("[data-m-source-link]").href = data.source || "#";
    modal.querySelector("[data-m-source-url]").textContent = data.source;
    var media = modal.querySelector("[data-m-media]");
    var mediaImg = modal.querySelector("[data-m-image]");
    media.style.setProperty("--cat-hue", data.hue);
    if (data.images.length) {
      media.setAttribute("data-images", data.images.join("|"));
    } else {
      media.removeAttribute("data-images");
    }
    if (data.image && mediaImg) {
      mediaImg.removeAttribute("data-fallback-bound");
      mediaImg.removeAttribute("data-img-i");
      mediaImg.style.display ="";
      mediaImg.setAttribute("data-img-fallback","");
      mediaImg.src = data.image;
      mediaImg.hidden = false;
      media.classList.add("has-image");
      bindImageFallback(mediaImg);
    } else {
      if (mediaImg) {
        mediaImg.removeAttribute("src");
        mediaImg.hidden = true;
      }
      media.classList.remove("has-image");
    }
    var actions = modal.querySelector("[data-m-actions]");
    actions.innerHTML ="";
    if (data.status === "imported") {
      var a = document.createElement("a");
      a.className = "cat-badge cat-badge--imported";
      a.href = importsUrl;
      a.textContent ="Added to My Imports";
      actions.appendChild(a);
    } else if (data.status === "in_store") {
      var b = document.createElement("span");
      b.className = "cat-badge cat-badge--live";
      b.textContent ="In store";
      actions.appendChild(b);
    } else {
      var btn = document.createElement("button");
      btn.type ="button";
      btn.className = "btn-primary";
      btn.setAttribute("data-import-product","");
      btn.setAttribute("data-source-id", data.sourceId);
      btn.innerHTML =
        'Import <span class="material-symbols-outlined btn-text__arrow" aria-hidden="true">arrow_outward</span>';
      btn.addEventListener("click", function () {
        importProduct(data.sourceId, card, btn);
        closeModal();
      });
      actions.appendChild(btn);
    }
  }

  function openModal(card) {
    lastFocus = document.activeElement;
    fillModal(card);
    modal.hidden = false;
    document.body.style.overflow ="hidden";
    if (closeBtn) closeBtn.focus();
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow ="";
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  root.addEventListener("click", function (e) {
    if (e.target.closest("[data-import-product], .cat-badge, a")) return;
    var trigger = e.target.closest("[data-open-details]");
    if (!trigger) return;
    var card = trigger.closest("[data-product-card]");
    if (card) openModal(card);
  });

  root.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var trigger = e.target.closest("[data-open-details]");
    if (!trigger || trigger.tagName === "BUTTON") return;
    e.preventDefault();
    var card = trigger.closest("[data-product-card]");
    if (card) openModal(card);
  });

  if (backdrop) backdrop.addEventListener("click", closeModal);
  if (closeBtn) closeBtn.addEventListener("click", closeModal);

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) closeModal();
  });

  if (dialog) {
    dialog.addEventListener("click", function (e) {
      e.stopPropagation();
    });
  }
})();
