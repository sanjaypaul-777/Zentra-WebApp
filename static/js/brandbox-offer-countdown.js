/**
 * Offer countdown — HH:MM:SS in the outlined time pill.
 * Set end via data-end="ISO-8601" on [data-brandbox-offer-countdown].
 */
(function () {
  var root = document.querySelector("[data-brandbox-offer-countdown]");
  if (!root) return;

  var timeEl = root.querySelector("[data-brandbox-offer-countdown-time]");
  if (!timeEl) return;

  var endRaw = root.getAttribute("data-end");
  var endAt = endRaw ? Date.parse(endRaw) : NaN;
  if (!Number.isFinite(endAt)) {
    var d = new Date();
    d.setHours(23, 59, 59, 999);
    endAt = d.getTime();
  }

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function render() {
    var remaining = endAt - Date.now();
    if (remaining <= 0) {
      root.classList.add("is-ended");
      timeEl.textContent = "Offer ended";
      return false;
    }

    var totalSec = Math.floor(remaining / 1000);
    var hours = Math.floor(totalSec / 3600);
    var mins = Math.floor((totalSec % 3600) / 60);
    var secs = totalSec % 60;

    timeEl.textContent = pad(hours) + ":" + pad(mins) + ":" + pad(secs);
    return true;
  }

  if (!render()) return;

  var timerId = window.setInterval(function () {
    if (!render()) window.clearInterval(timerId);
  }, 1000);
})();
