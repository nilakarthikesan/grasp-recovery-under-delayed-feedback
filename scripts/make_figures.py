"""Figures for the paper from results/<run>/report.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from delayed_recovery import config as C

plt.rcParams.update({"font.size": 7, "axes.labelsize": 7, "legend.fontsize": 6, "xtick.labelsize": 6, "ytick.labelsize": 6, "pdf.fonttype": 42})
DT_MS = int(C.CONTROL_DT * 1000)
LABELS = {
    "nominal": "nominal (no intervention)",
    "reactive_slip+squeeze": "reactive slip det. + squeeze",
    "failure_predictor+squeeze": "future-loss pred. + squeeze",
    "value_delay_agnostic": "value selector (delay-agnostic)",
    "value_delay_aware": "value selector (delay-aware)",
    "random_budget": "random @ matched budget",
    "oracle_menu": "privileged menu oracle",
}
STYLE = {
    "nominal": dict(color="0.4", ls=":"),
    "reactive_slip+squeeze": dict(color="tab:orange", marker="v"),
    "failure_predictor+squeeze": dict(color="tab:green", marker="s"),
    "value_delay_agnostic": dict(color="tab:purple", marker="D"),
    "value_delay_aware": dict(color="tab:red", marker="o"),
    "random_budget": dict(color="0.6", ls="--"),
    "oracle_menu": dict(color="k", ls="-."),
}


def fig_frontier(rep, out):
    fr = rep["recovery_frontier_test"]
    lead = np.array(fr["lead_steps"]) * DT_MS
    frac = np.array(fr["fraction_placed"])
    delays = fr["delays"]
    remedies = fr["remedies"]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 1.7), sharey=True)
    for ax, r in zip(axes, [i for i, n in enumerate(remedies) if n != "continue"]):
        for k, d in enumerate(delays):
            ax.plot(lead, frac[:, r, k], marker=".", ms=3, lw=1, label=f"delay {d * DT_MS} ms")
        ax.set_title(remedies[r].replace("_", "/"), fontsize=7)
        ax.set_xlabel("decision lead before nominal loss [ms]")
        ax.invert_xaxis()
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("fraction of states recovered")
    axes[0].legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(out / "fig_frontier.pdf")
    plt.close(fig)


def fig_grid(rep, out):
    ages = rep["config"]["ages_steps"]
    delays = rep["config"]["delays_steps"]
    res = rep["results"]
    fig, axes = plt.subplots(1, len(ages), figsize=(7.0, 1.95), sharey=True)
    for ax, a in zip(axes, ages):
        for name in ("nominal", "random_budget", "reactive_slip+squeeze", "failure_predictor+squeeze", "value_delay_agnostic", "value_delay_aware", "oracle_menu"):
            ys = [res[name]["cells"][f"age{a}_delay{d}"]["completion"] for d in delays]
            ax.plot([d * DT_MS for d in delays], ys, lw=1, ms=3, label=LABELS[name], **STYLE[name])
        ax.set_title(f"observation age {a * DT_MS} ms", fontsize=7)
        ax.set_xlabel("added response delay [ms]")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("completion (stable placement)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(out / "fig_grid.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_budget(rep, out):
    curves = rep["budget_curves_test"]
    nominal = rep["results"]["nominal"]["pooled"]["completion"]
    oracle = rep["results"]["oracle_menu"]["pooled"]
    fig, ax = plt.subplots(figsize=(3.4, 1.75))
    for name, curve in curves.items():
        xs = [c["intervention_rate"] for c in curve]
        ys = [c["completion"] for c in curve]
        order = np.argsort(xs)
        ax.plot(np.array(xs)[order], np.array(ys)[order], lw=1, ms=2.5, label=LABELS[name], **STYLE[name])
    ax.axhline(nominal, **STYLE["nominal"], lw=1, label=LABELS["nominal"])
    ax.plot([oracle["intervention_rate"]], [oracle["completion"]], marker="*", color="k", ms=7, ls="none", label=LABELS["oracle_menu"])
    ax.axvline(rep["config"]["budget"], color="0.7", lw=0.8)
    ax.set_xlabel("intervention rate (fraction of episodes)")
    ax.set_ylabel("completion")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out / "fig_budget.pdf")
    plt.close(fig)


def fig_nulls(rep, out):
    nulls = rep["feedback_null_value_delay_aware"]
    names = ["intact", "frozen", "mismatched", "masked", "nominal"]
    vals = [rep["results"]["value_delay_aware"]["pooled"]["completion"]] + [nulls[m]["pooled"]["completion"] for m in ("frozen", "mismatched", "masked")] + [rep["results"]["nominal"]["pooled"]["completion"]]
    rates = [rep["results"]["value_delay_aware"]["pooled"]["intervention_rate"]] + [nulls[m]["pooled"]["intervention_rate"] for m in ("frozen", "mismatched", "masked")] + [0.0]
    fig, ax = plt.subplots(figsize=(3.4, 1.8))
    ax.bar(names, vals, color=["tab:red", "0.55", "0.65", "0.75", "0.4"])
    for i, (v, r) in enumerate(zip(vals, rates)):
        ax.text(i, v + 0.005, f"{v:.2f}\n({r:.0%} int.)", ha="center", va="bottom", fontsize=5.5)
    ax.set_ylabel("completion (pooled)")
    ax.set_ylim(min(vals) - 0.08, max(vals) + 0.08)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "fig_nulls.pdf")
    plt.close(fig)


def fig_remedy_mix(rep, out):
    delays = rep["config"]["delays_steps"]
    ages = rep["config"]["ages_steps"]
    fig, axes = plt.subplots(1, 2, figsize=(3.4, 1.8), sharey=True)
    for ax, name in zip(axes, ("value_delay_agnostic", "value_delay_aware")):
        mix = rep["results"][name]["remedy_mix"]
        bottom = np.zeros(len(delays))
        for remedy, color in (("slow", "tab:blue"), ("squeeze", "tab:red"), ("place_regrasp", "tab:green")):
            counts = np.array([sum(mix[f"age{a}_delay{d}"][remedy] for a in ages) for d in delays], dtype=float)
            ax.bar([str(d * DT_MS) for d in delays], counts, bottom=bottom, color=color, label=remedy.replace("_", "/"))
            bottom += counts
        ax.set_title(LABELS[name].replace("value selector ", ""), fontsize=7)
        ax.set_xlabel("response delay [ms]")
    axes[0].set_ylabel("interventions (test, all ages)")
    axes[1].legend(fontsize=5.5)
    fig.tight_layout()
    fig.savefig(out / "fig_remedy_mix.pdf")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, default=Path("results/pilot_v1/report.json"))
    ap.add_argument("--out", type=Path, default=Path("paper/figures"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rep = json.load(open(args.report))
    fig_frontier(rep, args.out)
    fig_grid(rep, args.out)
    fig_budget(rep, args.out)
    fig_nulls(rep, args.out)
    fig_remedy_mix(rep, args.out)
    print("figures written to", args.out)


if __name__ == "__main__":
    main()
