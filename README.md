# Dynamic vision fault diagnosis figure materials

This repository provides source data and visualization scripts for Figures 5–9 of the associated Journal of Vibration and Control manuscript. The same source tables also support Supplementary Figures S4–S6. The PNG exports in `figures/` match the files embedded in the submission.

| Figure | Source table | Contents |
| --- | --- | --- |
| 5 and S4 | [figure5.csv](data/figure5.csv) | Four XJTU-DV Pump recording identifiers, original DAT checksums and registered ROI coordinates. |
| 6 | [figure6.csv](data/figure6.csv) | Recording-level Macro-F1 for the component comparisons at 30 Hz and 40 Hz. |
| 7 and S5 | [figure7.csv](data/figure7.csv) | Paired Pump task–seed scores and signed differences. The original panels 7(a,b) are Figure 7, and 7(c,d) are Supplementary Figure S5(a,b). |
| 8 | [figure8.csv](data/figure8.csv) | Recording-level Macro-F1 by held-out Rotor domain, method and training seed. |
| 9 and S6 | [figure9.csv](data/figure9.csv) | Independently fitted t-SNE coordinates. The Pump panels are Figure 9(a,b), and the Rotor panels are Supplementary Figure S6(a,b). Each row is a window in one panel. |

Original recordings are hosted in the [XJTU-DV Zenodo archive](https://doi.org/10.5281/zenodo.17447083). Score columns for Figures 6–8 are fractions. Plotting converts these to percent or percentage points. Figure 9 recording-level Macro-F1 is already expressed as a percentage and is repeated across the rows of each panel for convenience. The coordinates in one t-SNE panel have their own fitted scale and orientation.

## Render the figures

Run from the repository root on Windows with Arial installed. The checked-in exports were verified with Python 3.12.5, Matplotlib 3.10.0, NumPy 2.2.2 and Pillow 11.1.0.

~~~text
python -m pip install -r requirements.txt
python scripts/render_current.py
~~~

The script writes the current Figure 5–9 and Supplementary Figure S4–S6 PNGs to final_png/. For the 15 cm and 18 cm event-rate views, it assembles the archived projections using the shared scale. Figures 7 and S5 preserve the plot marks from the original four-panel render, and Figure 9 uses the original Pump embeddings. Figure 6 and Figure 8 are drawn directly from their numerical tables. Supplementary Figure S6 is drawn from the archived Rotor t-SNE coordinates. No embedding is fitted again when rendering.

The numerical plotting scripts plot_figures.py and figure9.py provide independent checks and write to outputs/. The preprocessing script figure5.py hashes the four original Healthy DAT recordings and recomputes their event-rate projections from XJTU-DV. Those recordings are needed only for that raw-data check.

The software license applies to the visualization scripts. The original XJTU-DV recordings remain available from the dataset record under its stated terms.
