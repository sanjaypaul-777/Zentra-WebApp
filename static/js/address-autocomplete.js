/**
 * Address UX (onboarding Step 1 + Settings):
 * - Country: searchable worldwide dropdown (full list on open; filter while typing)
 * - State: searchable dropdown scoped to selected country
 * - Street: server autocomplete (Google Places → Photon → Nominatim)
 */
(function () {
  function debounce(fn, ms) {
    var t;
    return function () {
      var ctx = this;
      var args = arguments;
      clearTimeout(t);
      t = setTimeout(function () {
        fn.apply(ctx, args);
      }, ms);
    };
  }

  function qs(url, params) {
    var parts = [];
    Object.keys(params).forEach(function (k) {
      if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
        parts.push(encodeURIComponent(k) + "=" + encodeURIComponent(params[k]));
      }
    });
    return url + (url.indexOf("?") >= 0 ? "&" : "?") + parts.join("&");
  }

  function attachList(wrap) {
    var host = wrap.querySelector(".addr-combo__control") || wrap;
    host.classList.add("addr-suggest");
    var list = host.querySelector(".addr-suggest__list");
    if (!list) {
      list = document.createElement("ul");
      list.className = "addr-suggest__list";
      list.hidden = true;
      list.setAttribute("role", "listbox");
      host.appendChild(list);
    }
    return list;
  }

  function setExpanded(input, open) {
    input.setAttribute("aria-expanded", open ? "true" : "false");
    var combo = input.closest(".addr-combo");
    if (combo) combo.classList.toggle("is-open", !!open);
  }

  function ensureControlWrap(input) {
    var parent = input.parentElement;
    if (parent && parent.classList.contains("addr-combo__control")) {
      return parent;
    }
    var control = document.createElement("div");
    control.className = "addr-combo__control";
    parent.insertBefore(control, input);
    control.appendChild(input);
    return control;
  }

  /**
   * Searchable combobox.
   * opts.browseAllOnOpen — when opening, if current value equals selectedValue(),
   * fetch with empty query so the full list shows (not just the current match).
   */
  function bindSearchableCombo(opts) {
    var input = opts.input;
    var wrap =
      input.closest(".ob-field, .st-field, .addr-combo") || input.parentElement;
    var list = attachList(wrap);
    var items = [];
    var active = -1;
    var abortCtrl = null;
    var fetchFn = opts.fetch;
    var chevron = wrap.querySelector(".addr-combo__chevron");
    var typing = false;

    function hide() {
      list.hidden = true;
      list.innerHTML = "";
      items = [];
      active = -1;
      setExpanded(input, false);
    }

    function render(results) {
      list.innerHTML = "";
      items = results || [];
      active = -1;
      if (!items.length) {
        hide();
        return;
      }
      items.forEach(function (item) {
        var label =
          typeof item === "string" ? item : item.label || item.name || "";
        var li = document.createElement("li");
        li.className = "addr-suggest__item";
        li.setAttribute("role", "option");
        li.textContent = label;
        li.addEventListener("mousedown", function (e) {
          e.preventDefault();
          pick(item);
        });
        list.appendChild(li);
      });
      list.hidden = false;
      setExpanded(input, true);
    }

    function pick(item) {
      var label =
        typeof item === "string" ? item : item.label || item.name || "";
      input.value = label;
      typing = false;
      hide();
      if (opts.onPick) opts.onPick(item);
    }

    function setActive(next) {
      var nodes = list.querySelectorAll(".addr-suggest__item");
      nodes.forEach(function (n) {
        n.classList.remove("is-active");
      });
      if (next < 0 || next >= nodes.length) {
        active = -1;
        return;
      }
      active = next;
      nodes[active].classList.add("is-active");
      nodes[active].scrollIntoView({ block: "nearest" });
    }

    function queryForOpen() {
      var raw = (input.value || "").trim();
      if (!opts.browseAllOnOpen) return raw;
      if (typing) return raw;
      var selected =
        typeof opts.selectedValue === "function"
          ? (opts.selectedValue() || "").trim()
          : "";
      // Opening with the already-chosen value → show full list, not 1–2 matches
      if (selected && raw.toLowerCase() === selected.toLowerCase()) {
        return "";
      }
      return raw;
    }

    var run = debounce(function () {
      if (abortCtrl) abortCtrl.abort();
      abortCtrl = new AbortController();
      var q = queryForOpen();
      fetchFn(q, abortCtrl.signal)
        .then(function (results) {
          if (document.activeElement !== input) return;
          render(results);
        })
        .catch(function () {});
    }, 160);

    input.setAttribute("autocomplete", "off");
    input.addEventListener("focus", function () {
      typing = false;
      try {
        input.select();
      } catch (e) {}
      run();
    });
    input.addEventListener("input", function () {
      typing = true;
      run();
    });
    input.addEventListener("keydown", function (e) {
      if (list.hidden) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          run();
        }
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive(active + 1 >= items.length ? 0 : active + 1);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive(active <= 0 ? items.length - 1 : active - 1);
      } else if (e.key === "Enter" && active >= 0) {
        e.preventDefault();
        pick(items[active]);
      } else if (e.key === "Escape") {
        hide();
      }
    });
    input.addEventListener("blur", function () {
      setTimeout(hide, 150);
    });
    if (chevron) {
      chevron.addEventListener("mousedown", function (e) {
        e.preventDefault();
        if (list.hidden) {
          typing = false;
          input.focus();
          run();
        } else {
          hide();
        }
      });
    }

    return { refresh: run, hide: hide };
  }

  function bindRoot(root) {
    var street = root.querySelector("[data-address-street]");
    var city = root.querySelector("[data-address-city]");
    var state = root.querySelector("[data-address-state]");
    var zip = root.querySelector("[data-address-zip]");
    var countryHidden = root.querySelector("[data-address-country]");
    var countryDisplay = root.querySelector("[data-address-country-display]");
    var form = root.closest("form") || root;

    var countryCode =
      root.getAttribute("data-country-code") ||
      (countryHidden && countryHidden.getAttribute("data-country-code")) ||
      "";
    var countryName =
      root.getAttribute("data-country-name") ||
      (countryHidden && countryHidden.value) ||
      "";

    if (countryHidden && countryName) {
      countryHidden.value = countryName;
      countryHidden.setAttribute("data-country-code", countryCode);
    }
    if (countryDisplay && countryName) {
      countryDisplay.value = countryName;
    }

    var suggestUrl =
      root.getAttribute("data-suggest-url") || "/api/address-suggest/";
    var detailsUrl =
      root.getAttribute("data-details-url") || "/api/address-details/";
    var countriesUrl =
      root.getAttribute("data-countries-url") || "/api/geo/countries/";
    var statesUrl = root.getAttribute("data-states-url") || "/api/geo/states/";
    var timezoneUrl =
      root.getAttribute("data-timezone-url") || "/api/geo/timezone/";
    var phoneMetaUrl =
      root.getAttribute("data-phone-meta-url") || "/api/geo/phone-meta/";
    var allowClientDetect =
      root.getAttribute("data-geo-client-detect") === "1";
    var serverConfident = root.getAttribute("data-geo-confident") === "1";
    var userTouchedCountry = false;
    var phoneInput = root.querySelector("[data-address-phone]");
    var phoneDial = root.querySelector("[data-phone-dial]");
    var phoneLib = null;
    var phoneDialCode = "";

    function loadPhoneLib() {
      if (phoneLib) return Promise.resolve(phoneLib);
      if (window.libphonenumber) {
        phoneLib = window.libphonenumber;
        return Promise.resolve(phoneLib);
      }
      if (window.__bbPhoneLibLoading) return window.__bbPhoneLibLoading;
      window.__bbPhoneLibLoading = new Promise(function (resolve) {
        var s = document.createElement("script");
        s.src =
          "https://cdn.jsdelivr.net/npm/libphonenumber-js@1.11.18/bundle/libphonenumber-max.js";
        s.async = true;
        s.onload = function () {
          phoneLib = window.libphonenumber || null;
          resolve(phoneLib);
        };
        s.onerror = function () {
          resolve(null);
        };
        document.head.appendChild(s);
      });
      return window.__bbPhoneLibLoading;
    }

    function nationalDigits(raw) {
      var s = String(raw || "");
      // If user pasted +91... strip matching dial for national formatting
      if (phoneDialCode && s.replace(/\s/g, "").startsWith(phoneDialCode)) {
        s = s.replace(/\s/g, "").slice(phoneDialCode.length);
      }
      return s.replace(/[^\d+]/g, "");
    }

    function formatPhoneNational(raw) {
      var digits = nationalDigits(raw);
      if (!phoneLib || !countryCode || !digits) return digits;
      try {
        var formatter = new phoneLib.AsYouType(countryCode);
        return formatter.input(digits);
      } catch (e) {
        return digits;
      }
    }

    function refreshPhoneMeta() {
      if (!phoneInput && !phoneDial) return;
      fetch(
        qs(phoneMetaUrl, {
          country_code: countryCode,
          country: countryName,
        }),
        { credentials: "same-origin" }
      )
        .then(function (r) {
          return r.ok ? r.json() : null;
        })
        .then(function (data) {
          if (!data || !data.ok || !data.phone) return;
          var meta = data.phone;
          phoneDialCode = meta.dial_code || "";
          if (phoneDial) phoneDial.textContent = phoneDialCode || "+";
          if (phoneInput) {
            phoneInput.placeholder = meta.example
              ? meta.example
              : "Phone number";
            // Re-format existing value for the new country
            if (phoneInput.value) {
              phoneInput.value = formatPhoneNational(phoneInput.value);
            }
          }
        })
        .catch(function () {});
    }

    function bindPhoneInput() {
      if (!phoneInput) return;
      loadPhoneLib().then(function () {
        refreshPhoneMeta();
      });
      phoneInput.addEventListener("input", function () {
        if (!phoneLib) return;
        var start = phoneInput.selectionStart;
        var before = phoneInput.value;
        var formatted = formatPhoneNational(before);
        if (formatted !== before) {
          phoneInput.value = formatted;
          try {
            var pos = Math.min(formatted.length, start || formatted.length);
            phoneInput.setSelectionRange(pos, pos);
          } catch (e) {}
        }
      });
      phoneInput.addEventListener("blur", function () {
        if (!phoneLib || !phoneInput.value) return;
        try {
          var parsed = phoneLib.parsePhoneNumberFromString(
            phoneInput.value,
            countryCode || undefined
          );
          if (parsed && parsed.isValid()) {
            // Keep national formatting in the field; server stores E.164
            phoneInput.value = parsed.formatNational();
          }
        } catch (e) {}
      });
    }

    function setCountry(name, code) {
      countryName = name || "";
      countryCode = (code || "").toUpperCase();
      // Never leave the visible field as a bare ISO2 code (IN / US)
      if (countryName.length === 2 && countryName.toUpperCase() === countryCode) {
        countryName = "";
      }
      if (countryHidden) {
        countryHidden.value = countryName || countryCode;
        countryHidden.setAttribute("data-country-code", countryCode);
      }
      if (countryDisplay) countryDisplay.value = countryName || countryCode;
      root.setAttribute("data-country-code", countryCode);
      root.setAttribute("data-country-name", countryName || countryCode);
      refreshPhoneMeta();
    }

    /** Resolve ISO2 → full display name (India, United States, …). */
    function resolveFullCountryName(code, name) {
      code = (code || "").toUpperCase();
      name = (name || "").trim();
      if (name.length > 2 && name.toUpperCase() !== code) {
        return Promise.resolve(name);
      }
      return fetch(qs(countriesUrl, { q: code }), {
        credentials: "same-origin",
      })
        .then(function (r) {
          return r.ok ? r.json() : { items: [] };
        })
        .then(function (data) {
          var items = data.items || [];
          for (var i = 0; i < items.length; i++) {
            if ((items[i].code || "").toUpperCase() === code) {
              return items[i].name || name || code;
            }
          }
          return name || code;
        })
        .catch(function () {
          return name || code;
        });
    }

    function clearState() {
      if (state) state.value = "";
    }

    /**
     * Browser sees the merchant's real public IP (server often sees 127.0.0.1
     * on localhost or a wrong edge IP). Refine pre-selected country when
     * server wasn't confident, unless the user already changed Country.
     */
    function refineCountryFromClient() {
      if (!allowClientDetect) return;
      if (userTouchedCountry) return;

      function apply(code, name) {
        if (userTouchedCountry) return;
        code = (code || "").toUpperCase();
        name = (name || "").trim();
        if (!code || code.length !== 2) return;

        var displayLooksLikeCode =
          !countryName ||
          countryName.length <= 2 ||
          countryName.toUpperCase() === countryCode;
        if (code === countryCode && !displayLooksLikeCode) return;

        resolveFullCountryName(code, name).then(function (fullName) {
          if (userTouchedCountry) return;
          var prev = countryCode;
          setCountry(fullName, code);
          if (prev && prev !== code) clearState();
        });
      }

      function fromIpapi() {
        return fetch("https://ipapi.co/json/", { credentials: "omit" })
          .then(function (r) {
            return r.ok ? r.json() : null;
          })
          .then(function (data) {
            if (!data || data.error || !data.country_code) return null;
            return {
              code: data.country_code,
              name: data.country_name || "",
            };
          })
          .catch(function () {
            return null;
          });
      }

      function fromIpinfo() {
        return fetch("https://ipinfo.io/json", { credentials: "omit" })
          .then(function (r) {
            return r.ok ? r.json() : null;
          })
          .then(function (data) {
            if (!data || !data.country) return null;
            // ipinfo only returns ISO2 — name resolved via resolveFullCountryName
            return { code: data.country, name: "" };
          })
          .catch(function () {
            return null;
          });
      }

      function fromTimezone() {
        var tz = "";
        try {
          tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
        } catch (e) {
          return Promise.resolve(null);
        }
        if (!tz) return Promise.resolve(null);
        return fetch(qs(timezoneUrl, { tz: tz }), {
          credentials: "same-origin",
        })
          .then(function (r) {
            return r.ok ? r.json() : null;
          })
          .then(function (data) {
            if (!data || !data.ok || !data.country) return null;
            return {
              code: data.country.code,
              name: data.country.name || "",
            };
          })
          .catch(function () {
            return null;
          });
      }

      // Always try client IP when server wasn't confident; also when confident
      // but allowClientDetect (no saved profile) — IP APIs from the browser
      // beat a stale session / wrong proxy hop.
      var chain = serverConfident
        ? fromIpapi().then(function (hit) {
            return hit || fromIpinfo();
          })
        : fromIpapi()
            .then(function (hit) {
              return hit || fromIpinfo();
            })
            .then(function (hit) {
              return hit || fromTimezone();
            });

      chain.then(function (hit) {
        if (hit) apply(hit.code, hit.name);
      });
    }

    // If the field somehow loaded as "IN" / "US", expand to full name
    if (
      countryCode &&
      (!countryName ||
        countryName.length <= 2 ||
        countryName.toUpperCase() === countryCode)
    ) {
      resolveFullCountryName(countryCode, countryName).then(function (full) {
        if (!userTouchedCountry) setCountry(full, countryCode);
      });
    }

    if (countryDisplay) {
      countryDisplay.addEventListener("input", function () {
        userTouchedCountry = true;
      });
      bindSearchableCombo({
        input: countryDisplay,
        browseAllOnOpen: true,
        selectedValue: function () {
          return countryName;
        },
        fetch: function (q, signal) {
          return fetch(qs(countriesUrl, { q: q }), {
            credentials: "same-origin",
            signal: signal,
          })
            .then(function (r) {
              return r.ok ? r.json() : { items: [] };
            })
            .then(function (data) {
              return (data.items || []).map(function (row) {
                return {
                  name: row.name,
                  code: row.code,
                  label: row.name,
                };
              });
            });
        },
        onPick: function (item) {
          userTouchedCountry = true;
          var prev = countryCode;
          setCountry(item.name || item.label, item.code);
          if ((item.code || "").toUpperCase() !== prev) {
            clearState();
          }
        },
      });
    }

    if (state) {
      bindSearchableCombo({
        input: state,
        browseAllOnOpen: true,
        selectedValue: function () {
          return (state && state.value) || "";
        },
        fetch: function (q, signal) {
          return fetch(
            qs(statesUrl, {
              country: countryName,
              country_code: countryCode,
              q: q,
            }),
            { credentials: "same-origin", signal: signal }
          )
            .then(function (r) {
              return r.ok ? r.json() : { results: [] };
            })
            .then(function (data) {
              return data.results || [];
            });
        },
      });
    }

    function fillFromSuggestion(item) {
      if (item.street && street) street.value = item.street;
      else if (item.label && street && !item.street) {
        street.value = String(item.label).split(",")[0] || street.value;
      }
      if (item.city && city) city.value = item.city;
      if (item.state && state) state.value = item.state;
      if (item.zip && zip) zip.value = item.zip;
      if (item.country || item.country_code) {
        setCountry(
          item.country || countryName,
          item.country_code || countryCode
        );
      }
    }

    function bindStreetSuggest() {
      if (!street) return;
      ensureControlWrap(street);
      var wrap =
        street.closest(".ob-field, .st-field") || street.parentElement;
      var list = attachList(wrap);
      var items = [];
      var active = -1;
      var abortCtrl = null;

      function hide() {
        list.hidden = true;
        list.innerHTML = "";
        items = [];
        active = -1;
      }

      function render(results) {
        list.innerHTML = "";
        items = results || [];
        active = -1;
        if (!items.length) {
          hide();
          return;
        }
        items.forEach(function (item) {
          var li = document.createElement("li");
          li.className = "addr-suggest__item";
          li.textContent = item.label;
          li.addEventListener("mousedown", function (e) {
            e.preventDefault();
            selectItem(item);
          });
          list.appendChild(li);
        });
        list.hidden = false;
      }

      function selectItem(item) {
        if (item.place_id) {
          fetch(qs(detailsUrl, { place_id: item.place_id }), {
            credentials: "same-origin",
          })
            .then(function (r) {
              return r.ok ? r.json() : { ok: false };
            })
            .then(function (data) {
              if (data.ok && data.result) {
                fillFromSuggestion(data.result);
              } else if (item.label && street) {
                street.value = item.label.split(",")[0] || street.value;
              }
              hide();
            })
            .catch(function () {
              if (item.label && street) {
                street.value = item.label.split(",")[0] || street.value;
              }
              hide();
            });
          return;
        }
        fillFromSuggestion(item);
        hide();
      }

      var runStreet = debounce(function () {
        var q = (street.value || "").trim();
        if (q.length < 2) {
          hide();
          return;
        }
        if (abortCtrl) abortCtrl.abort();
        abortCtrl = new AbortController();
        fetch(qs(suggestUrl, { q: q, country: countryCode }), {
          credentials: "same-origin",
          signal: abortCtrl.signal,
        })
          .then(function (r) {
            return r.ok ? r.json() : { results: [] };
          })
          .then(function (data) {
            if (document.activeElement !== street) return;
            render(data.results || []);
          })
          .catch(function () {});
      }, 250);

      street.setAttribute("autocomplete", "off");
      street.addEventListener("input", runStreet);
      street.addEventListener("keydown", function (e) {
        if (list.hidden) return;
        var nodes = list.querySelectorAll(".addr-suggest__item");
        if (e.key === "ArrowDown") {
          e.preventDefault();
          active = active + 1 >= items.length ? 0 : active + 1;
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          active = active <= 0 ? items.length - 1 : active - 1;
        } else if (e.key === "Enter" && active >= 0) {
          e.preventDefault();
          selectItem(items[active]);
          return;
        } else if (e.key === "Escape") {
          hide();
          return;
        } else {
          return;
        }
        nodes.forEach(function (n, i) {
          n.classList.toggle("is-active", i === active);
        });
      });
      street.addEventListener("blur", function () {
        setTimeout(hide, 150);
      });
    }

    bindStreetSuggest();
    bindPhoneInput();
    refineCountryFromClient();

    // Keep hidden country in sync if user typed a known name without picking
    if (form && form.addEventListener) {
      form.addEventListener("submit", function () {
        if (!countryDisplay || !countryHidden) return;
        var typed = (countryDisplay.value || "").trim();
        if (typed && typed !== countryHidden.value) {
          countryHidden.value = typed;
        }
      });
    }
  }

  document.querySelectorAll("[data-address-autocomplete]").forEach(bindRoot);
})();
