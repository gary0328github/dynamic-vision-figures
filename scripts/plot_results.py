"""Plot the submitted data, keeping the original evaluation and units."""
import csv
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

NAVY = '#31588c'
BLUE = '#b5cbe2'
AMBER = '#e68b39'
INK = '#193753'
EDGE = '#dce5ee'
LOSS = '#a05151'
FULL = 'DARM_FULL'
CAL = 'DARM_PP025'
COLORS = (NAVY, AMBER)
METHODS = ('Full DARM', 'Calibrated DARM (PtP = 0.25)')
DOMAINS = ('A1_R1000', 'A1_R2000', 'A2_R1000', 'A2_R2000', 'A3_R1000', 'A3_R2000')
CLASSES = dict(zip(('Ball', 'Inner', 'Outer', 'Healthy', 'Misalignment', 'Cavitation'),
                   ('#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b')))
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 8.2, 'axes.labelcolor': INK,
    'axes.edgecolor': '#657d90', 'axes.linewidth': 0.7,
    'xtick.color': INK, 'ytick.color': INK, 'text.color': INK,
    'legend.frameon': False, 'pdf.fonttype': 42,
    'axes.spines.top': False, 'axes.spines.right': False,
})


def new_panels(titles, ylabels, legend_bottom=0.25, height=3.04):
    fig, axes = plt.subplots(1, 2, figsize=(7.65, height))
    fig.subplots_adjust(left=0.092, bottom=legend_bottom, right=0.967,
                        top=0.86, wspace=0.31)
    for i, (ax, title, ylabel) in enumerate(zip(axes, titles, ylabels)):
        ax.set_title(f"({chr(97+i)}) {title}", loc='left', pad=11, weight='bold', fontsize=9.5)
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.tick_params(length=2.8, pad=3)
        ax.set_axisbelow(True)
        ax.grid(axis='y', color=EDGE, linewidth=.65)
    return fig, axes


def plot_legend(fig):
    fig.legend(handles=[Patch(color=color, label=method) for color, method in zip(COLORS, METHODS)],
               loc='lower center', bbox_to_anchor=(.5, .017), ncol=2, columnspacing=2.5)


def save(fig, axes, path, qa):
    fig.canvas.draw()
    left, right = [ax.get_position().bounds for ax in axes]
    assert np.allclose(left[1:], right[1:], atol=1e-7), (path, left, right)
    fig.savefig(path, dpi=600, facecolor='white')
    fig.savefig(qa / f'{path.stem}.pdf', facecolor='white')
    plt.close(fig)


def paired_bars(ax, categories, series):
    x = np.arange(len(categories))
    for shift, color, values in zip((-.19, .19), COLORS, series):
        bars = ax.bar(x + shift, values, .35, color=color, zorder=3)
        for rect, value in zip(bars, values):
            ax.annotate(f'{value:.2f}', (rect.get_x()+rect.get_width()/2, rect.get_height()),
                        xytext=(0, 3), textcoords='offset points', ha='center', va='bottom',
                        fontsize=6.8, clip_on=False)
    ax.set_xticks(x, categories)


def mean(rows, field):
    assert rows
    return 100 * np.mean([float(r[field]) for r in rows])


def figure6(rows, path, qa):
    fig, axes = new_panels(('30 Hz', '40 Hz'), ('Recording-level Macro-F1 (%)', ''), .26)
    labels = ('ItP', 'ItP + ItI', 'FULL')
    keys = ('DARM_IP_ONLY', 'DARM_IP_II', FULL)
    colors = (BLUE, '#e5b555', NAVY)
    expected = (48.10, 62.04, 60.88, 41.30, 43.06)
    actual = []
    for ax, speed, indices in zip(axes, ('30', '40'), ((0, 1, 2), (1, 2))):
        for i in indices:
            subset = [r for r in rows if r['speed'] == speed and r['method'] == keys[i]]
            assert len(subset) == 12
            value = mean(subset, 'DAT_macro_f1')
            actual.append(value)
            ax.bar(i, value, .61, color=colors[i], zorder=3)
            ax.text(i, value+1.5, f'{value:.2f}', ha='center', va='bottom', fontsize=7.5)
        ax.text(.5, .94, 'Adding PtP: ' + ('−1.16 pp' if speed == '30' else '+1.76 pp'),
                transform=ax.transAxes, ha='center', va='top', fontsize=7.5)
        ax.grid(False)
        ax.set_ylim(0, 78)
        ax.set_yticks(range(0, 71, 10))
        ax.set_xlim(-.57, 2.57)
        ax.set_xticks(indices, [labels[i] for i in indices])
    axes[1].tick_params(labelleft=False)
    assert np.allclose(actual, expected, atol=.006), actual
    fig.text(.5, .075, 'Pump development tasks  |  Objectives retained from update 1',
             ha='center', color=INK, fontsize=8.2)
    save(fig, axes, path, qa)


def figure7(rows, path, supplement, qa):
    assert len(rows) == 36
    keys = ('DARM_FULL', 'DARM_PP025')
    speeds = ('20', '30', '40')
    values = {k: np.array([100*float(r[k]) for r in rows]) for k in keys}
    by_speed = [[mean([r for r in rows if r['speed'] == speed], k) for speed in speeds] for k in keys]
    bottom = [np.mean(np.sort(values[k])[:9]) for k in keys]
    assert np.allclose([min(s) for s in by_speed] + bottom, [43.06, 45.37, 21.30, 30.99], atol=.006)
    fig, axes = new_panels(('Performance across Pump speeds', 'Ranked task–seed scores'),
                           ('Recording-level Macro-F1 (%)', ''), .25)
    paired_bars(axes[0], [f'{s} Hz' for s in speeds], by_speed)
    axes[1].axvspan(.5, 9.5, color='#f6e8c9', zorder=0)
    for key, color in zip(keys, COLORS):
        axes[1].plot(np.arange(1, 37), np.sort(values[key]), color=color, lw=1.25,
                     marker='o', ms=2.35, zorder=3)
    axes[1].set_xlim(.5, 36.5)
    axes[1].set_xticks([1, 9, 18, 27, 36])
    axes[1].set_xlabel('Task–seed rank (separate ranking for each method)')
    axes[1].text(1.4, 93, 'Lowest quarter', fontsize=7, va='top')
    for ax in axes:
        ax.set_ylim(0, 100)
        ax.set_yticks(range(0, 101, 20))
    plot_legend(fig)
    save(fig, axes, path, qa)

    fig, axes = new_panels(('Overall and lower-tail performance', 'Paired changes by task and seed'),
                           ('Recording-level Macro-F1 (%)', 'Change in Macro-F1 (pp)'), .27)
    paired_bars(axes[0], ('Overall\nmean', 'Lowest\nspeed mean', 'Lowest\nquarter'),
                [[np.mean(values[k]), min(by_speed[i]), bottom[i]] for i, k in enumerate(keys)])
    axes[0].grid(False)
    axes[1].grid(False)
    axes[0].set_ylim(0, 65)
    axes[1].axhline(0, color='#92a3ae', lw=.8, zorder=2)
    delta = 100*np.array([float(r['delta']) for r in rows])
    assert np.allclose(delta, values[keys[1]] - values[keys[0]])
    counts = Counter(r['outcome'] for r in rows)
    assert counts == {'win': 11, 'loss': 8, 'tie': 17}, counts
    axes[1].bar(range(36), delta, color=[AMBER if d > 1e-8 else LOSS for d in delta], width=.72)
    ties = np.flatnonzero(np.isclose(delta, 0))
    axes[1].plot(ties, np.zeros(len(ties)), 's', color='#778692', ms=2.6, zorder=4)
    axes[1].set_xticks((5.5, 17.5, 29.5), ('20 Hz', '30 Hz', '40 Hz'))
    axes[1].set_xlim(-1.2, 36.2)
    axes[1].text(.98, .97, '11 improved · 8 declined · 17 tied', transform=axes[1].transAxes,
                 ha='right', va='top', fontsize=7)
    plot_legend(fig)
    save(fig, axes, supplement, qa)


def figure8(rows, path, qa):
    assert len(rows) == 36
    methods = ('DARM_FULL', 'DARM_PP025')
    domain_means = [[mean([r for r in rows if r['method'] == m and r['target_domain'] == d],
                          'target_DAT') for d in DOMAINS] for m in methods]
    seeds = sorted({r['seed'] for r in rows}, key=int)
    seed_means = [[mean([r for r in rows if r['method'] == m and r['seed'] == seed],
                        'target_DAT') for seed in seeds] for m in methods]
    assert np.allclose(np.mean(domain_means, axis=1), [25.93, 28.80], atol=.006)
    assert sum(b > a for a, b in zip(*domain_means)) == 5
    fig, axes = new_panels(('Held-out Rotor domains', 'Means across Rotor domains'), ('', ''), .255)
    for i, (base, calibrated) in enumerate(zip(*domain_means)):
        axes[0].plot([base, calibrated], [i, i], color='#a4b3c3', lw=1.3, zorder=2)
    for values, color, marker in zip(domain_means, COLORS, ('o', 'D')):
        axes[0].scatter(values, range(6), color=color, marker=marker, s=18, zorder=3)
    axes[0].set_yticks(range(6), DOMAINS)
    axes[0].set_ylim(5.45, -0.69)
    axes[0].set_xlim(0, 64)
    axes[0].set_xticks(range(0, 51, 10))
    axes[0].text(61, -0.46, 'Δ (pp)', ha='right', va='center', fontsize=6.8)
    for i, (base, calibrated) in enumerate(zip(*domain_means)):
        axes[0].text(61, i, f'{calibrated-base:+.2f}', ha='right', va='center', fontsize=7.1)
    axes[0].set_xlabel('Recording-level Macro-F1 (%)')
    axes[0].grid(axis='x', color=EDGE, linewidth=.65)
    axes[0].grid(axis='y', visible=False)
    paired_bars(axes[1], seeds, seed_means)
    for i, (base, calibrated) in enumerate(zip(*seed_means)):
        axes[1].text(i, max(base, calibrated)+5.5, f'Δ {calibrated-base:+.2f} pp',
                     ha='center', va='bottom', fontsize=7)
    axes[1].grid(False)
    axes[1].set_ylim(0, 50)
    axes[1].set_xlabel('Training seed')
    axes[1].set_ylabel('Recording-level Macro-F1 (%)')
    plot_legend(fig)
    save(fig, axes, path, qa)


def figure9(rows, path, qa, dataset):
    panels = [(label, [r for r in rows if r['panel'] == label])
              for label in ('ab' if dataset == 'Pump' else 'cd')]
    fig, axes = new_panels((f'{dataset} / Full DARM', f'{dataset} / Calibrated DARM'),
                           ('t-SNE 2', ''), .285, 3.4)
    present = [label for label in CLASSES if any(r['class'] == label for _, group in panels for r in group)]
    for ax, (_, group) in zip(axes, panels):
        assert len(group) == {'Pump': 313, 'Rotor': 435}[dataset], Counter(r['panel'] for r in rows)
        assert sum(r['split'] != 'source' for r in group) == {'Pump': 81, 'Rotor': 71}[dataset]
        scores = {float(r['recording_macro_f1_percent']) for r in group}
        assert len(scores) == 1
        for target in (False, True):
            for label in present:
                selected = [r for r in group if r['class'] == label and (r['split'] != 'source') == target]
                ax.scatter([float(r['tsne1']) for r in selected], [float(r['tsne2']) for r in selected],
                           s=13 if target else 7, marker='^' if target else 'o',
                           color=CLASSES[label], linewidth=.3 if target else 0,
                           edgecolors='#202833' if target else 'none',
                           alpha=.96 if target else .69, zorder=3 if target else 2)
        ax.text(.015, 1.015, f'Recording-level Macro-F1: {scores.pop():.2f}%',
                transform=ax.transAxes, ha='left', va='bottom', fontsize=7.0)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel('t-SNE 1')
        ax.set_ylabel('t-SNE 2')
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(True)

    fig.legend(handles=[Line2D([], [], marker='o', ls='', color=CLASSES[label], ms=4, label=label)
                        for label in present], loc='lower center', bbox_to_anchor=(.5, .097), ncol=len(present),
               columnspacing=1.45, handletextpad=.22)
    fig.legend(handles=[Line2D([], [], marker=marker, ls='', color='#55697a', ms=4, label=label)
                        for marker, label in (('o', 'Source window'), ('^', 'Held-out window'))],
               loc='lower center', bbox_to_anchor=(.5, .018), ncol=2, columnspacing=2.2)
    save(fig, axes, path, qa)


def plot_all(data, figures, supplement, qa):
    def read(number):
        with (data / f'figure{number}.csv').open(encoding='utf-8-sig', newline='') as source:
            return list(csv.DictReader(source))
    figure6(read(6), figures/'figure6.png', qa)
    figure7(read(7), figures/'figure7.png', supplement/'figureS5.png', qa)
    figure8(read(8), figures/'figure8.png', qa)
    rows = read(9)
    figure9(rows, figures/'figure9.png', qa, 'Pump')
    figure9(rows, supplement/'figureS6.png', qa, 'Rotor')
