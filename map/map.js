/* ============================================================
   map.js — Rokugan overview → clan region maps
   Coordinates are percentages of the map frame (x 0–100, y 0–100).
   ============================================================ */
(function () {
  "use strict";

  // clan colours (mirror rokugan.css --clan-*)
  var C = {
    crab:"#3c6b46", crane:"#4f88b4", dragon:"#2f8f6b", lion:"#c2922f",
    phoenix:"#d0602a", scorpion:"#8e2f3a", unicorn:"#6f4e9c", shadow:"#5b5560"
  };

  // Region definitions. `shapes` are polygons on the overview map.
  // `map` is the detailed region image (null = not yet charted).
  var REGIONS = [
    { key:"dragon", name:"Dragon Lands", color:C.dragon, map:"../assets/regions/dragon.webp",
      shapes:[[[16,7],[30,3],[52,3],[60,9],[60,18],[46,22],[34,21],[24,19],[16,13]]],
      label:[38,12],
      pins:[] },
    { key:"unicorn", name:"Unicorn Lands", color:C.unicorn, map:"../assets/regions/unicorn.webp",
      shapes:[[[2,9],[16,9],[24,20],[22,34],[18,46],[10,50],[3,40],[1,22]]], label:[12,22] },
    { key:"phoenix", name:"Phoenix Lands", color:C.phoenix, map:"../assets/regions/phoenix.webp",
      shapes:[[[62,3],[90,2],[92,22],[84,33],[72,32],[62,18],[60,9]]], label:[80,15] },
    { key:"lion", name:"Lion Lands", color:C.lion, map:"../assets/regions/lion.webp",
      shapes:[[[36,22],[58,20],[66,32],[60,44],[46,45],[35,36],[34,27]]], label:[50,32] },
    { key:"crane", name:"Crane Lands", color:C.crane, map:"../assets/regions/crane.webp",
      shapes:[
        [[58,33],[80,33],[82,52],[66,55],[58,46],[56,40]],
        [[44,63],[64,58],[67,74],[52,85],[42,74],[42,66]]
      ], label:[71,45], label2:[54,73] },
    { key:"crab", name:"Crab Lands", color:C.crab, map:"../assets/regions/crab.webp",
      shapes:[[[8,58],[30,56],[39,66],[35,80],[20,85],[7,73]]], label:[22,69] },
    { key:"scorpion", name:"Scorpion Lands", color:C.scorpion, map:null,
      shapes:[[[28,44],[46,45],[50,55],[44,63],[32,61],[25,52]]], label:[38,53] },
    { key:"shadow", name:"The Shadowlands", color:C.shadow, map:null,
      shapes:[[[5,76],[20,84],[22,93],[11,97],[3,90],[2,80]]], label:[11,86] }
  ];

  var byKey = {};
  REGIONS.forEach(function (r) { byKey[r.key] = r; });

  // --- DOM ---
  var vp = document.getElementById("viewport");
  var frame = document.getElementById("frame");
  var baseImg = document.getElementById("baseimg");
  var regionImg = document.getElementById("regionimg");
  var svg = document.getElementById("hotspots");
  var labels = document.getElementById("labels");
  var pins = document.getElementById("pins");
  var titleEl = document.getElementById("rtitle");
  var hintEl = document.getElementById("hint");
  var backBtn = document.getElementById("backBtn");
  var clanrow = document.getElementById("clanrow");
  var zin = document.getElementById("zin"), zout = document.getElementById("zout"), zreset = document.getElementById("zreset");

  var SVGNS = "http://www.w3.org/2000/svg";
  var view = "overview";       // or a region key
  var scale = 1, tx = 0, ty = 0;

  // ---- build overview hotspots + labels ----
  function centroid(pts) {
    var x = 0, y = 0; pts.forEach(function (p) { x += p[0]; y += p[1]; });
    return [x / pts.length, y / pts.length];
  }

  REGIONS.forEach(function (r) {
    r.shapes.forEach(function (pts, i) {
      var poly = document.createElementNS(SVGNS, "polygon");
      poly.setAttribute("points", pts.map(function (p) { return p.join(","); }).join(" "));
      poly.style.setProperty("--c", r.color);
      poly.setAttribute("data-key", r.key);
      poly.dataset.centroid = centroid(pts).join(",");
      poly.addEventListener("click", function () { enterRegion(r.key, this.dataset.centroid); });
      svg.appendChild(poly);
    });
    // labels (one, plus optional label2 for split territories)
    [r.label, r.label2].forEach(function (pos) {
      if (!pos) return;
      var el = document.createElement("div");
      el.className = "lab" + (r.map ? "" : " uncharted");
      el.style.left = pos[0] + "%"; el.style.top = pos[1] + "%";
      el.innerHTML = r.name.replace(/ Lands$/, "") +
        (r.map ? "" : "<span class='sub'>not yet charted</span>");
      labels.appendChild(el);
    });
  });

  // ---- clan chooser row ----
  REGIONS.forEach(function (r) {
    var b = document.createElement("button");
    b.className = "clanbtn" + (r.map ? "" : " uncharted");
    b.style.setProperty("--c", r.color);
    var hasMon = r.key !== "shadow";
    b.innerHTML = (hasMon ? "<img class='cmon' src='../assets/mon/" + r.key + ".svg' alt=''>" : "") +
      "<span>" + r.name.replace(/ Lands$/, "") + "</span>";
    b.setAttribute("data-key", r.key);
    if (r.map) b.addEventListener("click", function () { enterRegion(r.key, centroid(r.shapes[0]).join(",")); });
    clanrow.appendChild(b);
  });

  // ---- transitions ----
  function enterRegion(key, centroidStr) {
    var r = byKey[key];
    if (!r || !r.map) return;
    // zoom the overview toward the clicked centroid, then swap
    var c = (centroidStr || "50,50").split(",");
    frame.style.transformOrigin = c[0] + "% " + c[1] + "%";
    frame.classList.add("animate");
    // force reflow so the transition applies
    void frame.offsetWidth;
    scale = 2.6; applyTransform();
    frame.classList.add("fading");

    setTimeout(function () {
      regionImg.src = r.map;
      regionImg.alt = r.name;
      view = key;
      // reset transform for region view
      frame.classList.remove("animate");
      scale = 1; tx = 0; ty = 0;
      frame.style.transformOrigin = "center center";
      applyTransform();
      baseImg.style.display = "none";
      regionImg.style.display = "block";
      svg.classList.add("hidden");
      labels.classList.add("hidden");
      frame.classList.remove("fading");
      frame.classList.add("region-enter");
      // pins for this region
      buildPins(r);
      setTimeout(function () { frame.classList.remove("region-enter"); }, 600);
      updateChrome();
    }, 480);
  }

  function goOverview() {
    view = "overview";
    regionImg.style.display = "none";
    baseImg.style.display = "block";
    svg.classList.remove("hidden");
    labels.classList.remove("hidden");
    pins.classList.add("hidden"); pins.innerHTML = "";
    frame.classList.remove("animate");
    scale = 1; tx = 0; ty = 0; frame.style.transformOrigin = "center center";
    applyTransform();
    updateChrome();
  }

  function buildPins(r) {
    pins.innerHTML = "";
    if (!r.pins || !r.pins.length) { pins.classList.add("hidden"); return; }
    r.pins.forEach(function (p) {
      var a = document.createElement("a");
      a.className = "pin"; a.href = p.href;
      a.style.left = p.x + "%"; a.style.top = p.y + "%";
      a.innerHTML = "<span class='dot'></span><span class='plabel'>" + p.name + "</span>";
      pins.appendChild(a);
    });
    pins.classList.remove("hidden");
  }

  function updateChrome() {
    if (view === "overview") {
      titleEl.innerHTML = "The Emerald Empire of Rokugan";
      hintEl.textContent = "Choose a clan's lands to descend";
      backBtn.setAttribute("disabled", "");
      clanrow.querySelectorAll(".clanbtn").forEach(function (b) { b.classList.remove("active"); });
    } else {
      var r = byKey[view];
      titleEl.innerHTML = "<span class='clandot' style='background:" + r.color + "'></span>" + r.name;
      hintEl.textContent = "Drag to pan · scroll or ± to zoom";
      backBtn.removeAttribute("disabled");
      clanrow.querySelectorAll(".clanbtn").forEach(function (b) {
        b.classList.toggle("active", b.getAttribute("data-key") === view);
      });
    }
    vp.classList.toggle("grab", view !== "overview");
  }

  // ---- pan / zoom (region view only) ----
  function bounds() {
    var vpr = vp.getBoundingClientRect();
    var fh = vpr.height, fw = fh * (2513 / 3263);
    var cw = fw * scale, ch = fh * scale;
    return { mx: Math.max(0, (cw - vpr.width) / 2), my: Math.max(0, (ch - vpr.height) / 2) };
  }
  function applyTransform() {
    if (view !== "overview") {
      var b = bounds();
      tx = Math.max(-b.mx, Math.min(b.mx, tx));
      ty = Math.max(-b.my, Math.min(b.my, ty));
    }
    frame.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + scale + ")";
  }
  function zoomBy(f) {
    if (view === "overview") return;
    scale = Math.max(1, Math.min(4.5, scale * f));
    if (scale === 1) { tx = 0; ty = 0; }
    frame.classList.add("animate");
    applyTransform();
    setTimeout(function () { frame.classList.remove("animate"); }, 260);
  }
  zin.addEventListener("click", function () { zoomBy(1.4); });
  zout.addEventListener("click", function () { zoomBy(1 / 1.4); });
  zreset.addEventListener("click", function () { scale = 1; tx = 0; ty = 0; applyTransform(); });

  vp.addEventListener("wheel", function (e) {
    if (view === "overview") return;
    e.preventDefault();
    var f = e.deltaY < 0 ? 1.12 : 1 / 1.12;
    scale = Math.max(1, Math.min(4.5, scale * f));
    if (scale === 1) { tx = 0; ty = 0; }
    applyTransform();
  }, { passive: false });

  // drag to pan
  var dragging = false, sx = 0, sy = 0, stx = 0, sty = 0;
  vp.addEventListener("pointerdown", function (e) {
    if (view === "overview" || scale === 1) return;
    dragging = true; sx = e.clientX; sy = e.clientY; stx = tx; sty = ty;
    vp.classList.add("grabbing"); vp.setPointerCapture(e.pointerId);
  });
  vp.addEventListener("pointermove", function (e) {
    if (!dragging) return;
    tx = stx + (e.clientX - sx); ty = sty + (e.clientY - sy);
    applyTransform();
  });
  function endDrag() { dragging = false; vp.classList.remove("grabbing"); }
  vp.addEventListener("pointerup", endDrag);
  vp.addEventListener("pointercancel", endDrag);

  backBtn.addEventListener("click", goOverview);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && view !== "overview") goOverview(); });
  window.addEventListener("resize", applyTransform);

  // deep-link: #dragon etc.
  var hash = (location.hash || "").replace("#", "");
  if (hash && byKey[hash] && byKey[hash].map) {
    enterRegion(hash, centroid(byKey[hash].shapes[0]).join(","));
  } else {
    updateChrome();
  }
})();
