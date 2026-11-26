/* Directory filtering. Plain DOM, no dependencies. */
(function () {
  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var input = document.querySelector("[data-filter-search]");
    var region = document.querySelector("[data-filter-region]");
    var rows = Array.prototype.slice.call(document.querySelectorAll("[data-row]"));
    var count = document.querySelector("[data-filter-count]");
    if (!rows.length) return;

    function apply() {
      var q = (input && input.value || "").toLowerCase().trim();
      var r = region && region.value || "";
      var shown = 0;
      rows.forEach(function (row) {
        var text = row.getAttribute("data-text") || "";
        var reg = row.getAttribute("data-region") || "";
        var ok = (!q || text.indexOf(q) !== -1) && (!r || reg === r);
        row.style.display = ok ? "" : "none";
        if (ok) shown++;
      });
      if (count) count.textContent = shown + (shown === 1 ? " record" : " records");
    }

    if (input) input.addEventListener("input", apply);
    if (region) region.addEventListener("change", apply);
    apply();
  });
})();
