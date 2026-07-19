/**
 * Newsletter thank-you modal — open on ?newsletter=thanks, close cleans URL.
 */
(function () {
  var modal = document.getElementById("brandbox-newsletter-thanks");
  if (!modal) return;

  function closeModal() {
    modal.remove();
    if (window.history && window.history.replaceState) {
      var url = new URL(window.location.href);
      url.searchParams.delete("newsletter");
      window.history.replaceState({}, "", url.pathname + url.search + url.hash);
    }
  }

  modal.querySelectorAll("[data-brandbox-newsletter-close]").forEach(function (el) {
    el.addEventListener("click", closeModal);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeModal();
  });
})();
