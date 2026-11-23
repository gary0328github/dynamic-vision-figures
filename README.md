# Dynamic vision fault diagnosis figure materials

This repository provides source data and visualization scripts for Figures 5–9 of the associated Journal of Vibration and Control manuscript. The same source tables also support Supplementary Figures S5 and S6.

| Figure | Source table | Contents |
| --- | --- | --- |
| 5 | [figure5.csv](data/figure5.csv) | Four XJTU-DV Pump recording identifiers, original DAT checksums and registered ROI coordinates. |
| 6 | [figure6.csv](data/figure6.csv) | Recording-level Macro-F1 for the component comparisons at 30 Hz and 40 Hz. |
| 7 and S5 | [figure7.csv](data/figure7.csv) | Paired Pump task–seed scores and signed differences. The original panels 7(a,b) are Figure 7, and 7(c,d) are Supplementary Figure S5(a,b). |
| 8 | [figure8.csv](data/figure8.csv) | Recording-level Macro-F1 by held-out Rotor domain, method and training seed. |
| 9 and S6 | [figure9.csv](data/figure9.csv) | Independently fitted t-SNE coordinates. The Pump panels are Figure 9(a,b), and the Rotor panels are Supplementary Figure S6(a,b). Each row is a window in one panel. |

Original recordings are hosted in the [XJTU-DV Zenodo archive](https://doi.org/10.5281/zenodo.17447083). Score columns for Figures 6–8 are fractions. Plotting converts these to percent or percentage points. Figure 9 recording-level Macro-F1 is already expressed as a percentage and is repeated across the rows of each panel for convenience. The coordinates in one t-SNE panel have their own fitted scale and orientation.

## Render the figures

Run from the repository root. The figures use Arial for the t-SNE plot and the event-rate projections. Font and library versions can affect rendering; the checked-in PNG and SVG files in `figures/` preserve the previous layouts.

```text
python -m pip install -r requirements.txt
python scripts/figure5.py --pump-root /path/to/Pump/Data
python scripts/plot_figures.py
python scripts/figure9.py
python scripts/render_current.py
```

`figure5.py` reads the four original DAT files from `Healthy/`, checks the stored hashes, and draws the full-record event rates using one logarithmic display scale. `plot_figures.py` recomputes Figures 6–8 and Supplementary Figure S5 from their tabular scores. `figure9.py` renders Figure 9 and Supplementary Figure S6 from the archived coordinates. `render_current.py` exports the archived SVG layouts of Figures 6–8. CSV-based plots are written to `outputs/`, and SVG-based exports to `final_png/` by default.

The software license applies to the visualization scripts. The original XJTU-DV recordings remain available from the dataset record under its stated terms.
