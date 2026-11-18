#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstruct JVC Figure 5 *from real Pump event-camera DAT data*.

The four panels are the Healthy class at 30 Hz, with configurations:
(15 cm,-30 deg), (15 cm,0 deg), (18 cm,-30 deg), (18 cm,0 deg).

Provenance comes from the historical SHA-256 raw-DAT manifest and frozen
record-wise ROI registry. This script does not create/synthesize events,
interpolate the event histogram, denoise, inpaint, or move the registered ROIs.

Dependencies: Python 3.10+, numpy, matplotlib.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT.parent / 'data' / 'figure5.csv'
SENSOR_WIDTH, SENSOR_HEIGHT = 640, 480
BYTES_PER_EVENT = 8
READ_EVENTS = 1_000_000
PROJECTION_CHOICES = ('full', 'first-750ms')
INPUTS = (
    ('a', 15, -30, 'Healthy/30HZ_H_15_-30.dat'),
    ('b', 15,   0, 'Healthy/30HZ_H_15_0.dat'),
    ('c', 18, -30, 'Healthy/30HZ_H_18_-30.dat'),
    ('d', 18,   0, 'Healthy/30HZ_H_18_0.dat'),
)


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fin:
        while block := fin.read(chunk_size):
            h.update(block)
    return h.hexdigest()


def load_csv_index(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f'Missing source reference: {path}')
    with path.open('r', newline='', encoding='utf-8-sig') as fin:
        reader = csv.DictReader(fin)
        if not reader.fieldnames or 'relative_path' not in reader.fieldnames:
            raise ValueError(f'Expected relative_path column in {path}')
        rows: dict[str, dict[str, str]] = {}
        for item in reader:
            rel = item['relative_path'].replace('\\', '/')
            if rel in rows:
                raise ValueError(f'Duplicate relative_path in {path}: {rel}')
            rows[rel] = item
        return rows


def read_dat_header(stream, file_bytes: int, expected_event_count: int) -> tuple[int, int, list[str]]:
    """Decode original Prophesee DAT: %-header + 2-byte type/size + 8-byte CD events.

    Binary events are little-endian uint32(timestamp_us), uint32(payload).
    x = payload[13:0], y = payload[27:14], polarity = payload[28].
    """
    comments: list[str] = []
    for _ in range(64):
        start = stream.tell()
        prefix = stream.read(2)
        stream.seek(start)
        if prefix != b'% ':
            break
        line = stream.readline(4096)
        if not line.endswith(b'\n'):
            raise ValueError('Malformed or excessively long DAT header line')
        comments.append(line.decode('latin-1').strip())
    if not comments:
        raise ValueError('The file does not contain a Prophesee DAT ASCII header')
    meta = stream.read(2)
    if len(meta) != 2 or meta[0] not in (0, 12) or meta[1] != BYTES_PER_EVENT:
        raise ValueError(f'Unsupported DAT CD event type/size {meta!r}: fail closed')
    offset = stream.tell()
    if (file_bytes - offset) % BYTES_PER_EVENT != 0:
        raise ValueError('DAT payload length is not a multiple of 8 bytes')
    count = (file_bytes - offset) // BYTES_PER_EVENT
    if count != expected_event_count:
        raise ValueError(f'DAT event count mismatch: expected {expected_event_count}, actual {count}')
    return offset, count, comments


def histogram_from_dat(path: Path, expected: dict[str, str], projection: str) -> tuple[np.ndarray, dict[str, Any]]:
    """Read entire DAT in constant memory, hash all bytes, retain positions unchanged."""
    if projection not in PROJECTION_CHOICES:
        raise ValueError(projection)
    actual_size = path.stat().st_size
    manifest_size = int(expected['bytes'])
    if actual_size != manifest_size:
        raise ValueError(f'Wrong source file size for {path}: {actual_size} != {manifest_size}')
    expected_count = int(expected['event_count'])
    hist = np.zeros(SENSOR_HEIGHT * SENSOR_WIDTH, dtype=np.uint64)
    digest = hashlib.sha256()
    read_events, displayed_events = 0, 0
    min_t, max_t = None, None
    t0 = int(expected['timestamp_min_us'])
    t1 = t0 + 750_000
    with path.open('rb') as fin:
        offset, actual_count, comments = read_dat_header(fin, actual_size, expected_count)
        fin.seek(0)
        digest.update(fin.read(offset))
        fin.seek(offset)
        remaining = actual_count
        while remaining:
            raw = fin.read(min(READ_EVENTS, remaining) * BYTES_PER_EVENT)
            if not raw or len(raw) % BYTES_PER_EVENT:
                raise ValueError(f'Truncated DAT payload in {path}')
            digest.update(raw)
            arr = np.frombuffer(raw, dtype='<u4').reshape(-1, 2)
            ts = arr[:, 0]
            payload = arr[:, 1]
            x = payload & 0x3FFF
            y = (payload >> 14) & 0x3FFF
            if np.any(x >= SENSOR_WIDTH) or np.any(y >= SENSOR_HEIGHT):
                raise ValueError(f'Out-of-range event coordinates in {path}')
            min_here, max_here = int(ts.min()), int(ts.max())
            min_t = min_here if min_t is None else min(min_t, min_here)
            max_t = max_here if max_t is None else max(max_t, max_here)
            if projection == 'first-750ms':
                mask = (ts >= t0) & (ts < t1)
                pos = y[mask].astype(np.int64) * SENSOR_WIDTH + x[mask]
            else:
                pos = y.astype(np.int64) * SENSOR_WIDTH + x
            hist += np.bincount(pos, minlength=SENSOR_WIDTH * SENSOR_HEIGHT).astype(np.uint64)
            displayed_events += len(pos)
            read_events += len(arr)
            remaining -= len(arr)
        if fin.read(1):
            raise ValueError(f'Unexpected trailing bytes in {path}')
    actual_sha256 = digest.hexdigest()
    if actual_sha256.lower() != expected['sha256'].lower():
        raise ValueError(f'SHA-256 mismatch for {path}\n'
                         f' expected={expected["sha256"]}\n actual={actual_sha256}')
    if read_events != expected_count:
        raise ValueError('Unexpected decoded-event count')
    if min_t != t0 or max_t != int(expected['timestamp_max_us']):
        raise ValueError('Timestamp range differs from historical original-data manifest')
    if int(hist.sum()) != displayed_events:
        raise AssertionError('Projection event conservation failed')
    if displayed_events == 0:
        raise ValueError(f'No events within selected projection interval: {path}')
    duration_s = (int(expected['timestamp_max_us']) - t0) / 1e6
    if projection == 'first-750ms':
        duration_s = .75
    if duration_s <= 0:
        raise ValueError(f'Invalid recording duration for {path}')
    result = hist.reshape(SENSOR_HEIGHT, SENSOR_WIDTH)
    details = {
        'relative_dat': expected['relative_path'],
        'raw_sha256_verified': actual_sha256, 'file_size_bytes': actual_size,
        'all_events_read': read_events, 'displayed_events': displayed_events,
        'sensor_width': SENSOR_WIDTH, 'sensor_height': SENSOR_HEIGHT,
        'timestamp_min_us': min_t, 'timestamp_max_us': max_t,
        'projection_mode': projection, 'normalization_duration_seconds': duration_s,
        'source_parser': 'Prophesee DAT CD events: <u4 t, <u4 packed x14 y14 p1',
    }
    return result, details


def validate_sources(pump_root: Path, manifest, roi_registry):
    plans = []
    for label, distance_cm, angle_deg, rel in INPUTS:
        if rel not in manifest or rel not in roi_registry:
            raise ValueError(f'Frozen manifest/ROI registry missing {rel}')
        m, r = manifest[rel], roi_registry[rel]
        if (int(m['speed_hz']), int(m['distance_code']), int(m['angle_deg']), m['class']) != (30, distance_cm, angle_deg, 'Healthy'):
            raise ValueError(f'Frozen manifest metadata disagree with panel {label}: {rel}')
        if r.get('registration_status') != 'approved_recordwise_human_annotation':
            raise ValueError(f'ROI lacks historical approval: {rel}')
        x0, y0, w, h = (int(r[k]) for k in ('x0','y0','roi_width','roi_height'))
        if (w,h) != (68,152) or not (0<=x0 and 0<=y0 and x0+w<=SENSOR_WIDTH and y0+h<=SENSOR_HEIGHT):
            raise ValueError(f'ROI coordinates or dimensions invalid: {rel} -> {(x0,y0,w,h)}')
        p = pump_root / rel
        if not p.is_file():
            raise FileNotFoundError(f'Original DAT not found: {p}')
        plans.append((label, distance_cm, angle_deg, rel, p, m, r, (x0,y0,w,h)))
    return plans


def make_figure(data, output: Path, projection: str, measure: str,
                dpi: int, cmax_pct: float, style: str):
    """Journal layout or documented reference-style grid. Both use identical real histograms.

    The only differences between styles are background grid lines, border styling
    and typographic presentation. No pixel positions or event counts are altered.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib.patches import Rectangle
    from matplotlib.cm import ScalarMappable

    if style not in ('journal', 'reference'):
        raise ValueError('Unknown style: ' + style)
    if not (50 <= cmax_pct < 100):
        raise ValueError('--display-percentile must be >=50 and <100')
    if measure not in ('rate', 'count'):
        raise ValueError(measure)
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 10,
        'pdf.fonttype': 42, 'ps.fonttype': 42,
        'svg.fonttype': 'none',
        'figure.facecolor': 'white', 'savefig.facecolor': 'white',
    })

    # Visualization only; underlying event coordinates and counts are unchanged.
    display_values = []
    for item in data:
        counts = item['counts'].astype(np.float64)
        denom = item['record']['normalization_duration_seconds'] if measure == 'rate' else 1.0
        display_values.append(np.log1p(counts / denom))
    positive_vals = np.concatenate([v[v > 0].ravel() for v in display_values])
    cap = float(np.percentile(positive_vals, cmax_pct))
    if not np.isfinite(cap) or cap <= 0:
        raise ValueError('No positive finite event values to display')
    norm = Normalize(vmin=0, vmax=cap, clip=True)

    # Uniform color map and numerical limits across all 4 panels (auditable).
    cmap = LinearSegmentedColormap.from_list('scientific-navy-gold',
        ['#041a3c', '#12355a', '#496983', '#bcae78', '#f7d86a', '#fff184'], N=256)

    # Extra headroom to prevent the overlap present in R1; no gray label bands.
    fig = plt.figure(figsize=(11.6, 9.0), facecolor='white')
    gs = fig.add_gridspec(2, 2, left=0.058, right=0.970,
                          bottom=0.145, top=0.945, wspace=0.075, hspace=0.20)
    for idx, (item, image) in enumerate(zip(data, display_values)):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        ax.imshow(image, cmap=cmap, norm=norm,
                  interpolation='nearest', origin='upper',
                  extent=(-.5, SENSOR_WIDTH-.5, SENSOR_HEIGHT-.5, -.5),
                  aspect='equal', rasterized=True)
        # The published figure has a visible grid. The reference preset
        # adds it as an AXIS OVERLAY, not as new event pixels.
        if style == 'reference':
            for x in range(80, SENSOR_WIDTH, 80):
                ax.axvline(x-.5, color='white', alpha=0.18,
                           lw=0.38, zorder=2)
            for y in range(80, SENSOR_HEIGHT, 80):
                ax.axhline(y-.5, color='white', alpha=0.18,
                           lw=0.38, zorder=2)
        x0, y0, w, h = item['roi']
        ax.add_patch(Rectangle((x0-.5, y0-.5), w, h,
                               fill=False, edgecolor='#ff951f',
                               linewidth=2.0, zorder=4))
        angle = f"−{abs(item['angle_deg'])}°" if item['angle_deg'] < 0 else f"{item['angle_deg']}°"
        ax.set_title(f"({item['label']})  {item['distance_cm']} cm, {angle}",
                     loc='left', fontweight='bold', fontsize=12, pad=9)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(0.55)
            spine.set_edgecolor('#444444')
        ax.set_xlim(-.5, SENSOR_WIDTH-.5)
        ax.set_ylim(SENSOR_HEIGHT-.5, -.5)

    cbax = fig.add_axes([.245, .066, .51, .017])
    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cb = fig.colorbar(sm, cax=cbax, orientation='horizontal')
    cb.ax.tick_params(labelsize=9, length=2, pad=3)
    cb.outline.set_linewidth(.5)
    unit = 'events per pixel per second' if measure == 'rate' else 'events per pixel'
    cb.set_label(f'ln(1 + {unit})  |  shared display scale', fontsize=10, labelpad=7)
    outstem = 'figure5'
    for extension in ('png','pdf','svg'):
        fig.savefig(output / f'{outstem}.{extension}', dpi=dpi,
                    facecolor='white', bbox_inches=None)
    plt.close(fig)
    return {
        'style': style,
        'display_transform': f'ln(1 + {measure})',
        'normalization': 'recording duration in seconds' if measure == 'rate' else 'none',
        'colormap': 'fixed scientific navy-gold continuous palette in source code',
        'color_scale': 'shared across all four panels',
        'vmin': 0., 'vmax': cap,
        'vmax_rule': f'{cmax_pct}th percentile of pooled positive display values',
        'clipping': 'values above shared vmax clipped for display only; raw count histogram unchanged',
        'image_interpolation': 'nearest; no smoothing',
        'dpi': dpi,
        'panel_layout': '2 × 2; original 640 × 480 sensor coordinates',
        'axis_grid': 'subtle white coordinate grid every 80 pixels' if style == 'reference' else 'none',
        'roi_color': 'orange',
        'roi_coordinates': 'frozen record-wise ROI registry; no re-annotation',
        'green_annotation': 'omitted: no separately verified numerical coordinates',
        'headings': 'standalone black panel labels, no colored or gray bands, no overlapping global heading',
    }



def main():
    parser = argparse.ArgumentParser(description='Draw Figure 5 from the four original Pump recordings.')
    parser.add_argument('--pump-root', type=Path, required=True, help='Directory containing Healthy/*.dat')
    parser.add_argument('--output-dir', type=Path, default=ROOT.parent / 'outputs')
    args = parser.parse_args()
    details = load_csv_index(REFERENCE)
    plan = validate_sources(args.pump_root, details, details)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    panels = []
    for label, distance, angle, name, path, metadata, _, roi in plan:
        counts, record = histogram_from_dat(path, metadata, 'full')
        panels.append({'label': label, 'distance_cm': distance, 'angle_deg': angle,
                       'roi': roi, 'counts': counts, 'record': record})
        print(f"{label}: {name} (SHA-256 verified)")
    make_figure(panels, args.output_dir, 'full', 'rate', 600, 99.5, 'journal')


if __name__ == '__main__':
    main()
