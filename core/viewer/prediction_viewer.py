"""fluxworm prediction viewer.

A standalone desktop window that graphs the pipeline's predictions
(illustrative survival curves and constrained-FBA growth flux per genotype)
and explains what they mean. Reads the CSVs the pipeline writes to
results\\; if no results folder is found next to the program, it falls back
to the copy bundled into the executable at build time.

Run directly with `python viewer\\prediction_viewer.py`, or build the
.exe with `viewer\\build_exe.bat`.
"""

from __future__ import annotations

import csv
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import matplotlib

matplotlib.use("TkAgg")

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

REFERENCE = "wild type"
COLORS = {
    "wild type": "#555555",
    "rsks-1": "#4C72B0",
    "daf-2": "#DD8452",
    "daf-2 rsks-1": "#C44E52",
    "daf-16; daf-2 rsks-1": "#55A868",
}


# ---------------------------------------------------------------- data ----

def find_results_dir() -> Path:
    """Prefer a live results\\ folder near the program; else the bundled copy."""
    here = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
    for candidate in (here / "results", here.parent / "results", here.parent.parent / "results"):
        if (candidate / "survival_curves_illustrative.csv").exists():
            return candidate
    bundled = Path(getattr(sys, "_MEIPASS", here)) / "results"
    if (bundled / "survival_curves_illustrative.csv").exists():
        return bundled
    raise FileNotFoundError(
        "Could not find results\\survival_curves_illustrative.csv. "
        "Run the pipeline first (python launcher.py)."
    )


def load_survival(path: Path) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    t_col = header.index("t")
    genotypes = [h for i, h in enumerate(header) if h and i != t_col]
    t = np.array([float(r[t_col]) for r in body])
    curves = {g: np.array([float(r[header.index(g)]) for r in body]) for g in genotypes}
    return t, curves


def load_growth(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def median_lifespan(t: np.ndarray, s: np.ndarray) -> float:
    """Model time at which survival crosses 0.5 (linear interpolation)."""
    idx = np.argmax(s <= 0.5)
    if s[idx] > 0.5:
        return float("nan")
    t0, t1, s0, s1 = t[idx - 1], t[idx], s[idx - 1], s[idx]
    return float(t0 + (0.5 - s0) * (t1 - t0) / (s1 - s0))


def mean_lifespan(t: np.ndarray, s: np.ndarray) -> float:
    """Area under the survival curve = expected lifespan in model time."""
    return float(np.trapezoid(s, t) if hasattr(np, "trapezoid") else np.trapz(s, t))


def pct(ratio: float) -> str:
    """Format a ratio vs WT as a signed % change, without printing '-0.0000%'."""
    return f"{round((ratio - 1) * 100, 4) + 0.0:+.4f}%"


# ------------------------------------------------------------- explain ----

EXPLANATION = """\
WHAT YOU ARE LOOKING AT

These graphs show the predictions of the fluxworm pipeline for five C. elegans
genotypes from the GSE52340 microarray study (Chen et al. 2013, Cell Reports):

  - wild type                      the normal worm (the reference)
  - rsks-1                         loses S6 kinase (TOR signaling)
  - daf-2                          weakened insulin/IGF-1 receptor
  - daf-2 rsks-1                   both mutations together
  - daf-16; daf-2 rsks-1           double mutant plus loss of daf-16, the
                                   transcription factor the longevity effect
                                   depends on

In the lab, Chen et al. found: wild type lives shortest, the single mutants
live longer, the daf-2 rsks-1 double mutant lives much longer, and removing
daf-16 cancels most of that gain.


HOW THE MODEL MAKES A PREDICTION

1. Gene expression. For each mutant, the microarray shows which metabolic
   genes are turned up or down compared with wild type.

2. Metabolism (FBA). Those changes are used to tighten or loosen the limits
   on reactions in iCEL1314, a computer model of the worm's 2,230 metabolic
   reactions. Flux balance analysis then finds the best achievable growth
   rate (the "biomass flux") under those limits.

3. Aging proxy. Two numbers from the metabolism result are combined into a
   score Z:
       Z = 0.5 x (growth vs WT) + 0.5 x (2 - lipid-pathway flux vs WT)
   A higher Z means slower assumed aging. Z sets the aging rate of a Gompertz
   survival curve, S(t) = exp(-(B/C)(e^(Ct) - 1)), with C = C_WT / Z.
   Reduced lipid-pathway flux is counted as favorable because the
   long-lived mutants are known to burn less fat.


THE TABS

Survival curves     Fraction of worms predicted to still be alive over time.
                    The curves overlap almost completely: the predicted
                    differences are tiny.

Difference vs WT    The same curves, shown as the % change in survival
                    relative to wild type at each moment. This is where the
                    differences become visible. Above zero = more worms
                    alive than wild type at that time.

Growth flux         The FBA growth rate per genotype, as % change from wild
                    type. daf-2 and daf-2 rsks-1 show a small (~0.12%) drop.

The table at the bottom gives the median lifespan (when half the worms are
dead) and the mean lifespan (area under the curve) for each genotype.


WHAT THE RESULTS SAY

  - daf-2 and daf-2 rsks-1 are predicted to live longer than wild type, with
    the double mutant slightly ahead. That matches the order seen in the lab.
  - rsks-1 alone and the daf-16 triple mutant come out the same as wild type.
    The triple mutant reverting to wild type matches the lab. rsks-1 alone
    showing no gain does not: the lab saw a lifespan increase. This is a real
    limit of how sensitive the pipeline is.
  - The size of the predicted effect is far smaller than the real one. In
    the lab the double mutant lives several times longer; here it is
    fractions of a percent.


IMPORTANT LIMITATIONS: READ BEFORE USING THESE NUMBERS

  * This is an ILLUSTRATIVE AGING PROXY, NOT A VALIDATED LIFESPAN PREDICTION.
    FBA describes metabolism at a single steady state. It has no built-in
    concept of aging over time.
  * The time axis is arbitrary model units, not days.
  * The scoring formula, its weights, and the sign of the lipid term were
    chosen so the output reproduces the known order of the genotypes. The
    lipid-term sign was flipped after the first real run ranked the mutants
    backwards. The model therefore cannot independently confirm that order,
    and it has no predictive value for genotypes whose lifespan is unknown.
  * "Lipid-pathway" reactions are picked by keyword ("lipid", "fatty acid")
    in reaction names, because iCEL1314 has no pathway annotations. It is a
    heuristic, not a curated grouping.

For the full walkthrough, open PRIMER.html in the project folder.
"""


# ------------------------------------------------------------------ app ----

class ViewerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("fluxworm: C. elegans longevity model predictions")
        self.geometry("1100x800")
        self.minsize(800, 600)

        try:
            self.results_dir = find_results_dir()
            self.t, self.curves = load_survival(self.results_dir / "survival_curves_illustrative.csv")
            self.growth = load_growth(self.results_dir / "growth_comparison.csv")
        except Exception as exc:  # show the problem in the window, not a silent crash
            ttk.Label(self, text=f"Could not load results:\n\n{exc}", padding=30, wraplength=700).pack()
            return

        banner = ttk.Label(
            self,
            text="Illustrative Aging Proxy (Not Validated). See the Explanation tab before interpreting these graphs.",
            foreground="#B00020",
            padding=(10, 6),
        )
        banner.pack(fill="x")

        # Bottom rows are packed before the notebook so that, in a small
        # window, the graphs shrink instead of these rows being cut off.
        ttk.Label(self, text=f"Data source: {self.results_dir}", foreground="#666666", padding=(10, 2)).pack(side="bottom", anchor="w")
        self._add_summary_table()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=4)
        self._add_plot_tab(notebook, "Survival curves", self._plot_survival)
        self._add_plot_tab(notebook, "Difference vs WT", self._plot_difference)
        self._add_plot_tab(notebook, "Growth flux", self._plot_growth)
        self._add_explanation_tab(notebook)

    # --- tabs ---

    def _add_plot_tab(self, notebook: ttk.Notebook, title: str, draw) -> None:
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)
        fig = Figure(figsize=(9, 5), dpi=100)
        draw(fig)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        NavigationToolbar2Tk(canvas, frame).update()
        ttk.Label(
            frame,
            text="Toolbar: Pan (cross arrows) or Zoom (magnifier) is a mode; click it, then drag on the graph. "
                 "Back/Forward/Home stay inactive until you have zoomed or panned. Save exports a PNG.",
            foreground="#666666",
            padding=(6, 0),
        ).pack(side="bottom", anchor="w")
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

    def _add_explanation_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Explanation")
        text = tk.Text(frame, wrap="word", font=("Consolas", 10), padx=14, pady=10, relief="flat")
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        text.insert("1.0", EXPLANATION)
        text.configure(state="disabled")

    def _add_summary_table(self) -> None:
        frame = ttk.LabelFrame(self, text="Predicted lifespan summary (model time units)", padding=6)
        frame.pack(side="bottom", fill="x", padx=8, pady=4)
        cols = ("genotype", "median", "median_pct", "mean", "mean_pct", "growth_pct")
        heads = ("Genotype", "Median lifespan", "vs WT", "Mean lifespan", "vs WT", "Growth vs WT")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=len(self.curves))
        for c, h in zip(cols, heads):
            tree.heading(c, text=h, command=lambda c=c: self._sort_table(tree, c))
            tree.column(c, anchor="center", width=150)
        tree.column("genotype", anchor="w", width=200)

        wt_med = median_lifespan(self.t, self.curves[REFERENCE])
        wt_mean = mean_lifespan(self.t, self.curves[REFERENCE])
        growth_fc = {r["genotype"]: float(r["fold_change_vs_wt"]) for r in self.growth}
        for g, s in self.curves.items():
            med, mean = median_lifespan(self.t, s), mean_lifespan(self.t, s)
            tree.insert("", "end", values=(
                g,
                f"{med:.4f}",
                pct(med / wt_med),
                f"{mean:.4f}",
                pct(mean / wt_mean),
                pct(growth_fc.get(g, float("nan"))),
            ))
        tree.pack(fill="x")
        ttk.Label(frame, text="Click a column header to sort.", foreground="#666666").pack(anchor="w")

    def _sort_table(self, tree: ttk.Treeview, col: str) -> None:
        """Sort rows by a column; clicking the same header again reverses the order."""
        reverse = getattr(self, "_sort_state", None) == (col, False)
        self._sort_state = (col, reverse)

        def key(item: str):
            value = tree.set(item, col)
            try:
                return (0, float(value.rstrip("%")))
            except ValueError:
                return (1, value.lower())

        for index, item in enumerate(sorted(tree.get_children(""), key=key, reverse=reverse)):
            tree.move(item, "", index)

    # --- plots ---

    def _plot_survival(self, fig: Figure) -> None:
        ax = fig.add_subplot(111)
        for g, s in self.curves.items():
            ax.plot(self.t, s, label=g, color=COLORS.get(g), lw=2)
        ax.axhline(0.5, color="#999999", ls=":", lw=1)
        ax.text(self.t[-1], 0.51, "50% alive (median)", ha="right", va="bottom", fontsize=8, color="#777777")
        ax.set_xlabel("Model time (arbitrary units, not calibrated to days)")
        ax.set_ylabel("Fraction surviving")
        ax.set_title("Predicted survival curves\n(lines overlap: lifespan differences are < 0.1%, see 'Difference vs WT')")
        ax.legend()
        ax.grid(alpha=0.3)

    def _plot_difference(self, fig: Figure) -> None:
        ax = fig.add_subplot(111)
        wt = self.curves[REFERENCE]
        mask = wt > 1e-12
        for g, s in self.curves.items():
            rel = (s[mask] / wt[mask] - 1.0) * 100.0
            ax.plot(self.t[mask], rel, label=g, color=COLORS.get(g), lw=2,
                    ls="--" if g == REFERENCE else "-")
        ax.axhline(0, color="#333333", lw=0.8)
        ax.set_xlabel("Model time (arbitrary units)")
        ax.set_ylabel("Survival vs wild type (% change)")
        ax.set_title("How much more (or less) survival each genotype has than wild type\n"
                     "(above 0 = longer-lived; rsks-1 and the triple mutant sit on the 0 line)")
        ax.legend()
        ax.grid(alpha=0.3)

    def _plot_growth(self, fig: Figure) -> None:
        ax = fig.add_subplot(111)
        names = [r["genotype"] for r in self.growth]
        pct = [(float(r["fold_change_vs_wt"]) - 1) * 100 for r in self.growth]
        bars = ax.bar(names, pct, color=[COLORS.get(n, "#4C72B0") for n in names])
        for b, v in zip(bars, pct):
            ax.annotate(f"{v:+.3f}%", (b.get_x() + b.get_width() / 2, v),
                        xytext=(0, -12 if v < 0 else 4), textcoords="offset points",
                        ha="center", fontsize=9)
        ax.axhline(0, color="#333333", lw=0.8)
        ax.set_ylabel("Biomass flux vs wild type (% change)")
        ax.set_title("Constrained-FBA growth flux by genotype\n(wild type = 0.0717 model units)")
        ax.tick_params(axis="x", rotation=15)
        ax.grid(axis="y", alpha=0.3)


def main() -> None:
    ViewerApp().mainloop()


if __name__ == "__main__":
    main()
