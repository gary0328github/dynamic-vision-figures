"""Redraw the returned t-SNE coordinates with legible publication labels."""

import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
CLASSES = ["Ball", "Inner", "Outer", "Healthy", "Misalignment", "Cavitation"]
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.linewidth": 0.7,
                     "pdf.fonttype": 42, "svg.fonttype": "none"})
figure, axes = plt.subplots(2, 2, figsize=(7.0, 5.5))
with (ROOT / "data" / "figure9.csv").open(encoding="utf-8", newline="") as source:
    rows = list(csv.DictReader(source))
for index, panel in enumerate("abcd"):
    data = [row for row in rows if row["panel"] == panel]
    dataset = data[0]["dataset"]
    variant = "full" if data[0]["method"] == "DARM_FULL" else "calibrated"
    score = float(data[0]["recording_macro_f1_percent"])
    xy = np.array([(float(row["tsne1"]), float(row["tsne2"])) for row in data])
    labels = np.array([CLASSES.index(row["class"]) for row in data])
    target = np.array([row["split"] == "held_out" for row in data])
    assert len(xy) == (313 if dataset == "Pump" else 435)
    assert target.sum() == (81 if dataset == "Pump" else 71)
    ax = axes.flat[index]
    for label in range(6 if dataset == "Pump" else 4):
        color = plt.get_cmap("tab10")(label)
        source_mask = (labels == label) & ~target
        target_mask = (labels == label) & target
        ax.scatter(xy[source_mask, 0], xy[source_mask, 1], color=color, s=11,
                   alpha=0.65, marker="o", linewidths=0, rasterized=True)
        ax.scatter(xy[target_mask, 0], xy[target_mask, 1], facecolors=color, s=23,
                   alpha=0.98, marker="^", edgecolors="black", linewidths=0.4,
                   rasterized=True)
    method = "Full DARM" if variant == "full" else "Calibrated DARM"
    ax.set_title(f"({'abcd'[index]}) {dataset} / {method}", fontsize=9.2,
                 fontweight="bold", loc="left", pad=22)
    ax.text(0, 1.025, f"Recording-level Macro-F1 {score:.2f}%",
            transform=ax.transAxes, fontsize=8.5, va="bottom")
    ax.set_xlabel("t-SNE 1", fontsize=8)
    ax.set_ylabel("t-SNE 2", fontsize=8)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.margins(0.06)
figure.subplots_adjust(left=0.065, right=0.99, bottom=0.20, top=0.89,
                       wspace=0.19, hspace=0.55)
class_handles = [Line2D([], [], marker="o", color=plt.get_cmap("tab10")(i),
                        linestyle="None", label=name, markersize=5)
                 for i, name in enumerate(CLASSES)]
figure.legend(handles=class_handles, loc="lower center", bbox_to_anchor=(0.53, 0.060),
              ncol=3, frameon=False, fontsize=8.5, columnspacing=1.7,
              handletextpad=0.35, labelspacing=0.5)
domain_handles = [
    Line2D([], [], marker="o", color="gray", linestyle="None", label="Source window", markersize=5),
    Line2D([], [], marker="^", color="black", markerfacecolor="lightgray", linestyle="None",
           label="Held-out window", markersize=6),
]
figure.legend(handles=domain_handles, loc="lower center", bbox_to_anchor=(0.53, 0.012),
              ncol=2, frameon=False, fontsize=8.5, columnspacing=2.0, handletextpad=0.5)
for extension in ["png", "pdf", "svg"]:
    figure.savefig(OUT / f"figure9.{extension}", dpi=600, bbox_inches="tight", pad_inches=0.04)
plt.close(figure)
