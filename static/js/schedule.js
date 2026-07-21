/**
 * Schedule — live clock + calendar-style call booking.
 * Slots come from data-slots JSON; later swap source for external calendar.
 */
(function () {
  var liveRoot = document.querySelector("[data-sch-live]");
  if (liveRoot) {
    var clockEl = liveRoot.querySelector("[data-sch-clock]");
    var greetEl = liveRoot.querySelector("[data-sch-greeting]");
    var firstName = (liveRoot.getAttribute("data-first-name") || "there").trim();

    function dayPart(hour) {
      if (hour < 12) return "morning";
      if (hour < 17) return "afternoon";
      return "evening";
    }

    function tick() {
      var now = new Date();
      var time = now.toLocaleTimeString(undefined, {
        hour: "numeric",
        minute: "2-digit",
      });
      var date = now.toLocaleDateString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
      });
      if (clockEl) clockEl.textContent = time + " — " + date;
      if (greetEl) {
        greetEl.textContent = "Good " + dayPart(now.getHours()) + ", " + firstName;
      }
    }

    tick();
    setInterval(tick, 1000);
  }

  var root = document.querySelector("[data-sch-calendar]");
  if (!root) return;

  var slots = [];
  var slotsNode = document.getElementById("sch-slots-data");
  if (slotsNode) {
    try {
      slots = JSON.parse(slotsNode.textContent || "[]") || [];
    } catch (e) {
      slots = [];
    }
  }

  function ymd(d) {
    var m = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + "-" + m + "-" + day;
  }

  var byDate = {};
  slots.forEach(function (slot) {
    var when = new Date(slot.iso);
    if (isNaN(when.getTime())) return;
    var date = ymd(when);
    var timeLabel = when.toLocaleTimeString(undefined, {
      hour: "numeric",
      minute: "2-digit",
    });
    var normalized = {
      id: slot.id,
      date: date,
      time_label: timeLabel,
      duration: slot.duration,
      topic: slot.topic,
      iso: slot.iso,
    };
    if (!byDate[date]) byDate[date] = [];
    byDate[date].push(normalized);
  });

  Object.keys(byDate).forEach(function (key) {
    byDate[key].sort(function (a, b) {
      return new Date(a.iso) - new Date(b.iso);
    });
  });

  var monthEl = root.querySelector("[data-cal-month]");
  var gridEl = root.querySelector("[data-cal-grid]");
  var prevBtn = root.querySelector("[data-cal-prev]");
  var nextBtn = root.querySelector("[data-cal-next]");
  var dayLabel = root.querySelector("[data-cal-day-label]");
  var hintEl = root.querySelector("[data-cal-hint]");
  var timesEl = root.querySelector("[data-cal-times]");
  var formEl = root.querySelector("[data-cal-form]");
  var slotIdInput = root.querySelector("[data-cal-slot-id]");
  var summaryEl = root.querySelector("[data-cal-summary]");

  var today = new Date();
  today.setHours(0, 0, 0, 0);
  var view = new Date(today.getFullYear(), today.getMonth(), 1);
  var selectedDate = null;
  var selectedSlotId = null;

  function formatDayLabel(dateStr) {
    var parts = dateStr.split("-");
    var d = new Date(+parts[0], +parts[1] - 1, +parts[2]);
    return d.toLocaleDateString(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
    });
  }

  function renderMonth() {
    if (!monthEl || !gridEl) return;
    monthEl.textContent = view.toLocaleDateString(undefined, {
      month: "long",
      year: "numeric",
    });

    gridEl.innerHTML = "";
    var year = view.getFullYear();
    var month = view.getMonth();
    var firstDow = new Date(year, month, 1).getDay();
    var daysInMonth = new Date(year, month + 1, 0).getDate();

    for (var i = 0; i < firstDow; i++) {
      var empty = document.createElement("span");
      empty.className = "sch-cal__day sch-cal__day--empty";
      empty.setAttribute("aria-hidden", "true");
      gridEl.appendChild(empty);
    }

    for (var day = 1; day <= daysInMonth; day++) {
      var dateObj = new Date(year, month, day);
      var key = ymd(dateObj);
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "sch-cal__day";
      btn.textContent = String(day);
      btn.setAttribute("data-date", key);

      var isPast = dateObj < today;
      var hasSlots = !!(byDate[key] && byDate[key].length);

      if (isPast) {
        btn.classList.add("is-past");
        btn.disabled = true;
      } else if (hasSlots) {
        btn.classList.add("has-slots");
      } else {
        btn.classList.add("is-unavailable");
        btn.disabled = true;
      }

      if (key === ymd(today)) btn.classList.add("is-today");
      if (selectedDate === key) btn.classList.add("is-selected");

      if (!btn.disabled) {
        btn.addEventListener("click", onSelectDate);
      }
      gridEl.appendChild(btn);
    }
  }

  function onSelectDate(ev) {
    var key = ev.currentTarget.getAttribute("data-date");
    selectedDate = key;
    selectedSlotId = null;
    renderMonth();
    renderTimes();
  }

  function renderTimes() {
    if (!timesEl || !dayLabel || !hintEl || !formEl) return;

    if (!selectedDate || !byDate[selectedDate]) {
      dayLabel.textContent = "Select a date";
      hintEl.hidden = false;
      hintEl.textContent = "Available times will appear here.";
      timesEl.hidden = true;
      timesEl.innerHTML = "";
      formEl.hidden = true;
      return;
    }

    dayLabel.textContent = formatDayLabel(selectedDate);
    hintEl.hidden = true;
    timesEl.hidden = false;
    timesEl.innerHTML = "";

    byDate[selectedDate].forEach(function (slot) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "sch-cal__time";
      btn.textContent = slot.time_label;
      btn.setAttribute("data-slot-id", String(slot.id));
      if (String(slot.id) === String(selectedSlotId)) {
        btn.classList.add("is-selected");
      }
      btn.addEventListener("click", function () {
        selectedSlotId = slot.id;
        renderTimes();
        showConfirm(slot);
      });
      timesEl.appendChild(btn);
    });

    if (!selectedSlotId) {
      formEl.hidden = true;
    }
  }

  function showConfirm(slot) {
    if (!formEl || !slotIdInput || !summaryEl) return;
    slotIdInput.value = String(slot.id);
    summaryEl.textContent =
      formatDayLabel(slot.date) +
      " · " +
      slot.time_label +
      " · " +
      slot.duration +
      " min · " +
      slot.topic;
    formEl.hidden = false;
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", function () {
      view = new Date(view.getFullYear(), view.getMonth() - 1, 1);
      renderMonth();
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      view = new Date(view.getFullYear(), view.getMonth() + 1, 1);
      renderMonth();
    });
  }

  // Prefer first day with availability in the current month.
  var keys = Object.keys(byDate).sort();
  for (var i = 0; i < keys.length; i++) {
    var parts = keys[i].split("-");
    var d = new Date(+parts[0], +parts[1] - 1, +parts[2]);
    if (d >= today) {
      selectedDate = keys[i];
      view = new Date(d.getFullYear(), d.getMonth(), 1);
      break;
    }
  }

  renderMonth();
  renderTimes();
})();
