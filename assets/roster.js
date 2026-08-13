/* Dramatis Personae filters.
 *
 * Every card carries what it is — data-name, data-clan, data-family,
 * data-state, and data-sessions as a space-separated list of "s7" tokens. The
 * bar reads the controls, hides what does not match, folds away any group left
 * empty, and says how many are showing. No build step, no dependencies; the
 * page is fully usable with this file missing.
 */
(function () {
  "use strict";

  var bar = document.querySelector("[data-roster-filters]");
  if (!bar) return;

  var cards = Array.prototype.slice.call(document.querySelectorAll(".rost"));
  var groups = Array.prototype.slice.call(document.querySelectorAll("[data-group]"));
  var count = document.querySelector("[data-roster-count]");
  var empty = document.querySelector(".roster-empty");
  var controls = Array.prototype.slice.call(bar.querySelectorAll("[data-filter]"));
  var total = cards.length;

  function values() {
    var v = {};
    controls.forEach(function (c) { v[c.getAttribute("data-filter")] = c.value.trim(); });
    return v;
  }

  function matches(card, v) {
    if (v.q) {
      // Match on the normalised name the builder wrote, so "doji s" finds
      // Doji Setsuna and accents do not have to be typed.
      var q = v.q.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
      if (q && (card.getAttribute("data-name") || "").indexOf(q) === -1) return false;
    }
    if (v.clan && card.getAttribute("data-clan") !== v.clan) return false;
    if (v.family && card.getAttribute("data-family") !== v.family) return false;
    if (v.state && card.getAttribute("data-state") !== v.state) return false;
    if (v.sessions) {
      var list = (card.getAttribute("data-sessions") || "").split(" ");
      if (list.indexOf(v.sessions) === -1) return false;
    }
    return true;
  }

  function apply() {
    var v = values(), shown = 0;
    cards.forEach(function (card) {
      var ok = matches(card, v);
      card.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(function (g) {
      var any = g.querySelector(".rost:not([hidden])");
      g.hidden = !any;
    });
    var filtered = shown !== total;
    if (empty) empty.hidden = shown !== 0;
    if (count) {
      count.textContent = filtered
        ? shown + " of " + total
        : total + " in the record";
    }
    bar.classList.toggle("is-filtered", filtered);
  }

  controls.forEach(function (c) {
    c.addEventListener("input", apply);
    c.addEventListener("change", apply);
  });

  var clear = bar.querySelector("[data-roster-clear]");
  if (clear) {
    clear.addEventListener("click", function () {
      controls.forEach(function (c) { c.value = ""; });
      apply();
    });
  }

  apply();
}());
