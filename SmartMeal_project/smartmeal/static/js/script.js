/* SmartMeal front-end helpers.
 * 1. Context detection: proposes device type and connection quality from the browser
 *    (screen width, Network Information API). The user can always override them.
 * 2. Context bar: re-submits the context as soon as a value changes.
 * 3. Session heartbeat: keeps last_seen_at fresh so session duration is measured.
 */
(function () {
  "use strict";

  function detectDevice() {
    var w = Math.min(window.screen.width || window.innerWidth, window.innerWidth);
    var touch = "ontouchstart" in window || navigator.maxTouchPoints > 0;
    if (w < 768) return "mobile";
    if (w < 1100 && touch) return "tablet";
    return "desktop";
  }

  function detectConnection() {
    var c = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (!c) return null;
    if (c.saveData) return "slow";
    var t = c.effectiveType;
    if (t === "slow-2g" || t === "2g") return "slow";
    if (t === "3g") return "normal";
    if (t === "4g") return (c.downlink && c.downlink < 1.5) ? "normal" : "fast";
    return null;
  }

  var start = document.getElementById("startForm");
  if (start) {
    var fresh = start.getAttribute("data-fresh") === "1";
    var detected = { device: detectDevice(), connection: detectConnection() };
    start.querySelectorAll("[data-autodetect]").forEach(function (sel) {
      var kind = sel.getAttribute("data-autodetect");
      var value = detected[kind];
      var hint = start.querySelector('[data-hint="' + kind + '"]');
      var label = function (v) {          // option text is already translated by the server
        var o = sel.querySelector('option[value="' + v + '"]');
        return o ? o.textContent : v;
      };
      if (!value) {
        if (hint) hint.textContent = start.getAttribute("data-undetected");
        return;
      }
      var previous = sel.value;
      if (fresh) sel.value = value;
      if (hint) hint.textContent = start.getAttribute("data-detected") + " " + label(value) +
        (fresh ? "" : " (" + start.getAttribute("data-last") + " " + label(previous) + ")");
    });

    var range = document.getElementById("available_time");
    var out = document.getElementById("timeOut");
    if (range && out) range.addEventListener("input", function () { out.textContent = range.value; });
  }

  document.querySelectorAll("form[data-autosubmit] select").forEach(function (sel) {
    sel.addEventListener("change", function () { sel.form.submit(); });
  });
  document.querySelectorAll("[data-autosubmit-select]").forEach(function (sel) {
    sel.addEventListener("change", function () { sel.form.submit(); });
  });

  var hb = document.body.getAttribute("data-heartbeat");
  if (hb && navigator.sendBeacon) {
    var beat = function () { navigator.sendBeacon(hb); };
    setInterval(beat, 60000);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden") beat();
    });
  }
})();
