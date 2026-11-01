// Time-lapse of the predicted survival curves, with a worm population that
// shrinks to match the share of worms still alive at each moment.
//
// Data comes from /api/curves (built from core/results/*.csv by app.py).
// Requires Chart.js (static/vendor/chart.umd.min.js), loaded before this file.

(() => {
  "use strict";

  const root = document.getElementById("timelapse");
  if (!root || typeof Chart === "undefined") return;

  const POPULATION = 100;      // worms per population panel
  const BASE_DURATION = 10000; // ms to play the full time range at 1x speed

  const els = {
    canvas: root.querySelector("#tl-canvas"),
    caption: root.querySelector("#tl-caption"),
    play: root.querySelector("#tl-play"),
    scrub: root.querySelector("#tl-scrub"),
    time: root.querySelector("#tl-time"),
    speed: root.querySelector("#tl-speed"),
    all: root.querySelector("#tl-all"),
    views: root.querySelectorAll("[data-view]"),
    pops: root.querySelector("#tl-pops"),
    status: root.querySelector("#tl-status"),
  };

  const CAPTIONS = {
    survival:
      "Each line is the share of worms still alive as time passes. The lines almost overlap because the " +
      "model's differences are tiny. Switch to “Difference from normal worm” to see them.",
    diff:
      "How many more (or fewer) worms are alive than in a normal worm at each moment, in percent. " +
      "Above zero means this worm type is predicted to live longer. The line stops once 99% of normal " +
      "worms have died, because after that the percentages are based on only a handful of worms.",
  };

  const state = {
    data: null,
    selected: root.dataset.genotype,
    view: "survival",
    index: 0,
    playing: false,
    lastFrame: 0,
    progress: 0, // 0..1 along the time axis
    chart: null,
    deathOrder: [],
    panels: [],
  };

  // ------------------------------------------------------------ helpers ---

  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  // Each genotype's color is a CSS variable, so it follows the light/dark theme.
  const colorOf = (name) => css(state.data.genotypes[name].color_var) || css("--primary-color");

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
    return state.selected === ref ? [ref] : [state.selected, ref];
  }

  function fmtPct(x, digits = 2) {
    return `${(x * 100).toFixed(digits)}%`;
  }

  // -------------------------------------------------------------- chart ---

  // Draws the 50% line (survival view) or the zero line (difference view),
  // plus a vertical playhead and a dot on each visible line at the current time.
  const overlayPlugin = {
    id: "timelapseOverlay",
    afterDatasetsDraw(chart) {
      const { ctx, chartArea: area, scales } = chart;
      const t = state.data.t[state.index];
      ctx.save();

      // Reference line
      const refY = state.view === "survival" ? 0.5 : 0;
      const y = scales.y.getPixelForValue(refY);
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
        ctx.fillText(state.view === "survival" ? "half alive (median)" : "same as normal worm", area.right - 4, y - 5);
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

  function seriesFor(name) {
    const g = state.data.genotypes[name];
    return state.view === "survival" ? g.survival : g.diff_pct;
  }

  function diffRange() {
    let lo = 0, hi = 0;
    visibleGenotypes().forEach((name) => {
      state.data.genotypes[name].diff_pct.forEach((v) => {
        if (v === null) return;
        lo = Math.min(lo, v);
        hi = Math.max(hi, v);
      });
    });
    const pad = Math.max((hi - lo) * 0.12, 0.001);
    return { min: lo - pad, max: hi + pad };  // used as suggested bounds so Chart.js rounds the ticks
  }

  function buildChart() {
    const names = Object.keys(state.data.genotypes);
    const t = state.data.t;
    state.chart = new Chart(els.canvas, {
      type: "line",
      data: {
        datasets: names.map((name) => ({
          label: state.data.genotypes[name].name,
          genotype: name,
          data: [],
          borderColor: colorOf(name),
          backgroundColor: colorOf(name),
          borderWidth: name === state.selected ? 3 : 2,
          borderDash: name === state.data.reference ? [6, 4] : [],
          pointRadius: 0,
          spanGaps: false,
          tension: 0,
        })),
      },
      options: {
        animation: false,
        parsing: false,
        normalized: true,
        maintainAspectRatio: false,
        interaction: { mode: "nearest", axis: "x", intersect: false },
        scales: {
          x: { type: "linear", min: t[0], max: t[t.length - 1], title: { display: true, text: "Model time (not days)" } },
          y: { title: { display: true } },
        },
        plugins: {
          legend: { labels: { usePointStyle: true, pointStyle: "line", filter: (item, d) => !d.datasets[item.datasetIndex].hidden } },
          tooltip: {
            callbacks: {
              title: (items) => `Model time ${items[0].parsed.x.toFixed(1)}`,
              label: (item) =>
                state.view === "survival"
                  ? `${item.dataset.label}: ${fmtPct(item.parsed.y)} alive`
                  : `${item.dataset.label}: ${item.parsed.y >= 0 ? "+" : ""}${item.parsed.y.toFixed(4)}%`,
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
    const visible = new Set(visibleGenotypes());
    c.data.datasets.forEach((ds) => (ds.hidden = !visible.has(ds.genotype)));
    if (state.view === "survival") {
      c.options.scales.y.suggestedMin = undefined;
      c.options.scales.y.suggestedMax = undefined;
      c.options.scales.y.min = 0;
      c.options.scales.y.max = 1;
      c.options.scales.y.ticks = { ...c.options.scales.y.ticks, callback: (v) => `${Math.round(v * 100)}%` };
      c.options.scales.y.title.text = "Worms still alive";
    } else {
      const r = diffRange();
      c.options.scales.y.min = undefined;
      c.options.scales.y.max = undefined;
      c.options.scales.y.suggestedMin = r.min;
      c.options.scales.y.suggestedMax = r.max;
      c.options.scales.y.ticks = { ...c.options.scales.y.ticks, callback: (v) => `${v > 0 ? "+" : ""}${Number(v).toFixed(2)}%` };
      c.options.scales.y.title.text = "Alive compared with normal worm";
    }
    els.caption.textContent = CAPTIONS[state.view];
    els.views.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === state.view)));
    drawFrame();
  }

  // --------------------------------------------------------- population ---

  const WORM_PATH = "M3 12 C 7 4, 11 4, 14 10 S 21 16, 25 8";

  function buildPanels() {
    const ref = state.data.reference;
    const names = state.selected === ref ? [ref] : [state.selected, ref];
    els.pops.innerHTML = "";
    state.panels = names.map((name) => {
      const g = state.data.genotypes[name];
      const panel = document.createElement("div");
      panel.className = "tl-pop";
      panel.innerHTML = `
        <h4><span class="tl-swatch" style="background:var(${g.color_var})"></span>${g.name}</h4>
        <div class="tl-grid" role="img" aria-label="${POPULATION} worms of type ${g.name}"></div>
        <p class="tl-count"></p>`;
      const grid = panel.querySelector(".tl-grid");
      const worms = [];
      for (let i = 0; i < POPULATION; i++) {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("viewBox", "0 0 28 18");
        svg.setAttribute("class", "tl-worm");
        svg.style.color = `var(${g.color_var})`;
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", WORM_PATH);
        svg.appendChild(path);
        grid.appendChild(svg);
        worms.push(svg);
      }
      els.pops.appendChild(panel);
      return { name, worms, count: panel.querySelector(".tl-count") };
    });
  }

  function updatePanels() {
    const i = state.index;
    const refAlive = state.data.genotypes[state.data.reference].survival[i];
    state.panels.forEach((p) => {
      const alive = state.data.genotypes[p.name].survival[i];
      const n = Math.round(alive * POPULATION);
      p.worms.forEach((w, k) => w.classList.toggle("dead", state.deathOrder[k] < POPULATION - n));
      let text = `${fmtPct(alive)} alive`;
      if (p.name !== state.data.reference) {
        const gap = (alive - refAlive) * 100; // percentage points
        text += Math.abs(gap) < 0.005
          ? " · same as normal worm"
          : ` · ${gap > 0 ? "+" : ""}${gap.toFixed(2)} points vs normal worm`;
      }
      p.count.textContent = text;
    });
  }

  // ---------------------------------------------------------- animation ---

  function drawFrame() {
    const i = state.index;
    const t = state.data.t;
    state.chart.data.datasets.forEach((ds) => {
      const ys = seriesFor(ds.genotype);
      ds.data = [];
      for (let k = 0; k <= i; k++) ds.data.push({ x: t[k], y: ys[k] });
    });
    state.chart.update("none");
    updatePanels();
    els.scrub.value = String(i);
    els.time.textContent = `Model time ${t[i].toFixed(1)}`;
  }

  function setIndex(i) {
    const last = state.data.t.length - 1;
    state.index = Math.max(0, Math.min(last, i));
    state.progress = state.index / last;
    drawFrame();
  }

  function tick(now) {
    if (!state.playing) return;
    const speed = parseFloat(els.speed.value) || 1;
    const dt = now - state.lastFrame;
    state.lastFrame = now;
    state.progress = Math.min(1, state.progress + (dt * speed) / BASE_DURATION);
    const last = state.data.t.length - 1;
    const next = Math.round(state.progress * last);
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
      pause(Number(els.scrub.value) >= state.data.t.length - 1);
      setIndex(Number(els.scrub.value));
    });
    els.views.forEach((b) =>
      b.addEventListener("click", () => {
        state.view = b.dataset.view;
        applyView();
      })
    );
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
    els.scrub.max = String(state.data.t.length - 1);
    buildPanels();
    buildChart();
    wireControls();

    // People who turn off animations see the finished graph and can scrub through it.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setIndex(state.data.t.length - 1);
      pause(true);
    } else {
      setIndex(0);
      play();
    }
  }

  start();
})();
