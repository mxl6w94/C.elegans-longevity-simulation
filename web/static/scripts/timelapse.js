// Time-lapse of the survival curves, with a worm population that shrinks to
// match the share of worms still alive at each moment.
//
// Each worm type can have two curves:
//   measured: the wild-type curve stretched by the lifespan measured in the lab
//   model:    this project's prediction from its metabolic model (drawn dashed)
//
// Data comes from /api/curves (built by app.py from core/results/*.csv and
// core/data/lifespan_reference.csv). Time is relative: 1.0 = the wild-type mean lifespan.
// Requires Chart.js (static/vendor/chart.umd.min.js), loaded before this file.

(() => {
  "use strict";

  const root = document.getElementById("timelapse");
  if (!root || typeof Chart === "undefined") return;

  const POPULATION = 100;      // worms per population panel
  const BASE_DURATION = 10000; // ms to play the visible time range at 1x speed
  const GONE = 0.002;          // a curve below this counts as "everyone has died"

  const els = {
    canvas: root.querySelector("#tl-canvas"),
    caption: root.querySelector("#tl-caption"),
    play: root.querySelector("#tl-play"),
    scrub: root.querySelector("#tl-scrub"),
    time: root.querySelector("#tl-time"),
    speed: root.querySelector("#tl-speed"),
    all: root.querySelector("#tl-all"),
    pops: root.querySelector("#tl-pops"),
    status: root.querySelector("#tl-status"),
  };

  const CAPTIONS = {
    both:
      "Each line is the share of worms still alive as time passes. The solid line uses the lifespan " +
      "measured in the lab. The dashed line is what this project's model predicts for the same worm.",
    modelOnly:
      "Each line is the share of worms still alive as time passes. No lab measurement is available for " +
      "this worm, so only the model's prediction (dashed) is drawn.",
    reference: "The line is the share of normal worms still alive as time passes.",
  };

  const state = {
    data: null,
    selected: root.dataset.genotype,
    index: 0,
    last: 0,     // last time index shown for the current selection
    playing: false,
    lastFrame: 0,
    progress: 0, // 0..1 along the visible time range
    chart: null,
    deathOrder: [],
    panels: [],
  };

  // ------------------------------------------------------------ helpers ---

  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  // Each genotype's color is a CSS variable, so it follows the light/dark theme.
  const colorOf = (name) => css(state.data.genotypes[name].color_var) || css("--primary-color");

  const isReference = (name) => name === state.data.reference;
  const hasMeasured = (name) => Array.isArray(state.data.genotypes[name].measured);

  // The curve the worm panels follow: measured where it exists, otherwise the model.
  const bestCurve = (name) => (hasMeasured(name) ? state.data.genotypes[name].measured : state.data.genotypes[name].model);

  // Same pseudo-random order every time, so the same worms die first in every panel
  // and in every visit. That makes two populations easy to compare worm by worm.
  function seededOrder(n, seed = 52340) {
    const order = Array.from({ length: n }, (_, i) => i);
    let x = seed;
    for (let i = n - 1; i > 0; i--) {
      x = (x * 1103515245 + 12345) % 2147483648;
      const j = x % (i + 1);
      [order[i], order[j]] = [order[j], order[i]];
    }
    const rank = new Array(n);
    order.forEach((worm, position) => (rank[worm] = position));
    return rank; // rank[w] = how many worms die before worm w
  }

  function visibleGenotypes() {
    const ref = state.data.reference;
    const names = Object.keys(state.data.genotypes);
    if (els.all.checked) return names;
    return isReference(state.selected) ? [ref] : [state.selected, ref];
  }

  // Which line a dataset draws in the current view, or null if it is hidden.
  function seriesOf(ds) {
    const g = state.data.genotypes[ds.genotype];
    if (!visibleGenotypes().includes(ds.genotype)) return null;
    if (ds.kind === "measured") return g.measured;
    // The model line is drawn for the selected worm only, to keep the graph readable.
    // Wild type's model and measured curves are the same line, so it is skipped there.
    if (ds.genotype !== state.selected) return null;
    return isReference(ds.genotype) ? null : g.model;
  }

  // Last time index worth showing: where every visible line has run out.
  function lastIndex() {
    const n = state.data.t.length;
    let last = 1;
    state.chart.data.datasets.forEach((ds) => {
      const ys = seriesOf(ds);
      if (!ys) return;
      for (let k = n - 1; k > last; k--) {
        const v = ys[k];
        if (v !== null && v > GONE) {
          last = k;
          break;
        }
      }
    });
    return Math.min(n - 1, last + 2);
  }

  const fmtPct = (x, digits = 1) => `${(x * 100).toFixed(digits)}%`;

  // -------------------------------------------------------------- chart ---

  // Draws the 50% line, plus a vertical playhead and a dot on each visible line at the current time.
  const overlayPlugin = {
    id: "timelapseOverlay",
    afterDatasetsDraw(chart) {
      const { ctx, chartArea: area, scales } = chart;
      const t = state.data.t[state.index];
      ctx.save();

      // Reference line
      const y = scales.y.getPixelForValue(0.5);
      if (y >= area.top && y <= area.bottom) {
        ctx.strokeStyle = css("--muted-color");
        ctx.setLineDash([3, 4]);
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(area.left, y);
        ctx.lineTo(area.right, y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = css("--muted-color");
        ctx.font = "11px system-ui, sans-serif";
        ctx.textAlign = "right";
        ctx.fillText("half alive", area.right - 4, y - 5);
      }

      // Playhead
      const x = scales.x.getPixelForValue(t);
      ctx.strokeStyle = css("--text-color");
      ctx.globalAlpha = 0.35;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, area.top);
      ctx.lineTo(x, area.bottom);
      ctx.stroke();
      ctx.globalAlpha = 1;

      // Dot at the leading edge of each visible line
      chart.data.datasets.forEach((ds) => {
        if (ds.hidden || !ds.data.length) return;
        const last = ds.data[ds.data.length - 1];
        if (last.y === null) return;
        ctx.fillStyle = ds.borderColor;
        ctx.beginPath();
        ctx.arc(scales.x.getPixelForValue(last.x), scales.y.getPixelForValue(last.y), 4, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.restore();
    },
  };

  function labelOf(name, kind) {
    const display = state.data.genotypes[name].name;
    if (kind === "model") return `${display}: model prediction`;
    return isReference(name) ? display : `${display}: measured`;
  }

  function buildChart() {
    const names = Object.keys(state.data.genotypes);
    const datasets = [];
    names.forEach((name) => {
      ["measured", "model"].forEach((kind) => {
        datasets.push({
          label: labelOf(name, kind),
          genotype: name,
          kind,
          data: [],
          borderColor: colorOf(name),
          backgroundColor: colorOf(name),
          borderWidth: name === state.selected ? 3 : 2,
          borderDash: kind === "model" ? [7, 6] : [],
          // Lower order is drawn on top: the dashed model line sits above the solid lines it overlaps
          order: kind === "model" ? 0 : isReference(name) ? 2 : 1,
          pointRadius: 0,
          spanGaps: false,
          tension: 0,
        });
      });
    });

    state.chart = new Chart(els.canvas, {
      type: "line",
      data: { datasets },
      options: {
        animation: false,
        parsing: false,
        normalized: true,
        maintainAspectRatio: false,
        interaction: { mode: "nearest", axis: "x", intersect: false },
        scales: {
          x: { type: "linear", min: 0, title: { display: true, text: "Time (1.0 = average lifespan of a normal worm)" } },
          y: { min: 0, max: 1, title: { display: true, text: "Worms still alive" }, ticks: { callback: (v) => `${Math.round(v * 100)}%` } },
        },
        plugins: {
          // boxHeight 0 draws each legend key as a line, so dashed lines look dashed in the legend too
          legend: { labels: { boxWidth: 30, boxHeight: 0, filter: (item, d) => !d.datasets[item.datasetIndex].hidden } },
          tooltip: {
            callbacks: {
              title: (items) => `Time ${items[0].parsed.x.toFixed(2)}`,
              label: (item) => `${item.dataset.label}: ${fmtPct(item.parsed.y)} alive`,
            },
          },
        },
      },
      plugins: [overlayPlugin],
    });
    applyTheme();
    applyView();
  }

  function applyTheme() {
    const c = state.chart;
    if (!c) return;
    const text = css("--muted-color");
    const grid = css("--chart-grid");
    ["x", "y"].forEach((axis) => {
      c.options.scales[axis].ticks = { ...(c.options.scales[axis].ticks || {}), color: text };
      c.options.scales[axis].grid = { color: grid };
      c.options.scales[axis].title.color = text;
    });
    c.options.plugins.legend.labels.color = css("--text-color");
    c.data.datasets.forEach((ds) => {
      ds.borderColor = colorOf(ds.genotype);
      ds.backgroundColor = ds.borderColor;
    });
    c.update("none");
  }

  function applyView() {
    const c = state.chart;
    c.data.datasets.forEach((ds) => (ds.hidden = seriesOf(ds) === null));
    els.caption.textContent = isReference(state.selected)
      ? CAPTIONS.reference
      : hasMeasured(state.selected) ? CAPTIONS.both : CAPTIONS.modelOnly;

    // The time range follows what is on screen, so a short-lived worm isn't squeezed into a corner.
    state.last = lastIndex();
    const end = state.data.t[state.last];
    const step = end > 4 ? 0.5 : 0.1;
    c.options.scales.x.max = Math.ceil(end / step - 1e-9) * step; // round up so the last tick is a tidy number
    els.scrub.max = String(state.last);
    setIndex(Math.min(state.index, state.last));
  }

  // --------------------------------------------------------- population ---

  const WORM_PATH = "M3 12 C 7 4, 11 4, 14 10 S 21 16, 25 8";
  const SVG_NS = "http://www.w3.org/2000/svg";

  function buildPanels() {
    const ref = state.data.reference;
    const names = isReference(state.selected) ? [ref] : [state.selected, ref];
    els.pops.replaceChildren();
    state.panels = names.map((name) => {
      const g = state.data.genotypes[name];

      // Built with createElement and textContent, so a name can never be read as HTML.
      const panel = document.createElement("div");
      panel.className = "tl-pop";

      const heading = document.createElement("h4");
      const swatch = document.createElement("span");
      swatch.className = "tl-swatch";
      swatch.style.background = `var(${g.color_var})`;
      heading.append(swatch, document.createTextNode(g.name));

      const grid = document.createElement("div");
      grid.className = "tl-grid";
      grid.setAttribute("role", "img");
      grid.setAttribute("aria-label", `${POPULATION} worms of type ${g.name}`);

      const count = document.createElement("p");
      count.className = "tl-count";

      const worms = [];
      for (let i = 0; i < POPULATION; i++) {
        const svg = document.createElementNS(SVG_NS, "svg");
        svg.setAttribute("viewBox", "0 0 28 18");
        svg.setAttribute("class", "tl-worm");
        svg.style.color = `var(${g.color_var})`;
        const path = document.createElementNS(SVG_NS, "path");
        path.setAttribute("d", WORM_PATH);
        svg.appendChild(path);
        grid.appendChild(svg);
        worms.push(svg);
      }

      panel.append(heading, grid, count);
      els.pops.appendChild(panel);
      return { name, worms, count };
    });
  }

  function updatePanels() {
    const i = state.index;
    const refAlive = bestCurve(state.data.reference)[i];
    state.panels.forEach((p) => {
      const alive = bestCurve(p.name)[i];
      const n = Math.round(alive * POPULATION);
      p.worms.forEach((w, k) => w.classList.toggle("dead", state.deathOrder[k] < POPULATION - n));
      let text = `${fmtPct(alive)} alive`;
      if (!isReference(p.name)) {
        const gap = (alive - refAlive) * 100; // percentage points
        text += Math.abs(gap) < 0.05
          ? " · same as normal worm"
          : ` · ${gap > 0 ? "+" : ""}${gap.toFixed(1)} points vs normal worm`;
        text += hasMeasured(p.name) ? " (measured)" : " (model estimate, no lab number)";
      }
      p.count.textContent = text;
    });
  }

  // ---------------------------------------------------------- animation ---

  function drawFrame() {
    const i = state.index;
    const t = state.data.t;
    state.chart.data.datasets.forEach((ds) => {
      const ys = seriesOf(ds);
      ds.data = [];
      if (!ys) return;
      for (let k = 0; k <= i; k++) ds.data.push({ x: t[k], y: ys[k] });
    });
    state.chart.update("none");
    updatePanels();
    els.scrub.value = String(i);
    els.time.textContent = `Time ${t[i].toFixed(2)}`;
  }

  function setIndex(i) {
    state.index = Math.max(0, Math.min(state.last, i));
    state.progress = state.last ? state.index / state.last : 1;
    drawFrame();
  }

  function tick(now) {
    if (!state.playing) return;
    const speed = parseFloat(els.speed.value) || 1;
    const dt = Math.max(0, now - state.lastFrame); // the first frame's timestamp can precede play()
    state.lastFrame = now;
    state.progress = Math.min(1, state.progress + (dt * speed) / BASE_DURATION);
    const next = Math.max(0, Math.min(state.last, Math.round(state.progress * state.last)));
    if (next !== state.index) {
      state.index = next;
      drawFrame();
    }
    if (state.progress >= 1) return pause(true);
    requestAnimationFrame(tick);
  }

  function play() {
    if (state.progress >= 1) setIndex(0); // replay from the start
    state.playing = true;
    state.lastFrame = performance.now();
    els.play.textContent = "Pause";
    els.play.setAttribute("aria-label", "Pause time-lapse");
    requestAnimationFrame(tick);
  }

  function pause(finished = false) {
    state.playing = false;
    els.play.textContent = finished ? "Replay" : "Play";
    els.play.setAttribute("aria-label", finished ? "Replay time-lapse" : "Play time-lapse");
  }

  // -------------------------------------------------------------- start ---

  function wireControls() {
    els.play.addEventListener("click", () => (state.playing ? pause() : play()));
    els.scrub.addEventListener("input", () => {
      pause(Number(els.scrub.value) >= state.last);
      setIndex(Number(els.scrub.value));
    });
    els.all.addEventListener("change", applyView);

    // Follow light/dark changes from the system or a data-theme toggle
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", applyTheme);
    new MutationObserver(applyTheme).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  }

  async function start() {
    try {
      const res = await fetch(root.dataset.curvesUrl);
      if (!res.ok) throw new Error(`server returned ${res.status}`);
      state.data = await res.json();
    } catch (err) {
      els.status.textContent = `The graph couldn't be loaded (${err.message}). Try reloading the page.`;
      els.status.hidden = false;
      return;
    }
    if (!state.data.genotypes[state.selected]) state.selected = state.data.reference;

    state.deathOrder = seededOrder(POPULATION);
    buildPanels();
    buildChart();
    wireControls();

    // People who turn off animations see the finished graph and can scrub through it.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setIndex(state.last);
      pause(true);
    } else {
      setIndex(0);
      play();
    }
  }

  start();
})();
