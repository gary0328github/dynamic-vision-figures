"""Rebuild the current public JVC figure exports from the archived artwork and CSVs."""

import argparse
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from figure_canvas import paired
from strengthen_result_figures import draw_figure6, photo_typography
from restyle_figures import figure7, figure8, figure9

ROOT=Path(__file__).resolve().parents[1]
FIRST=ROOT/'archive'/'first_submission'
DATA=ROOT/'data'


def export(fig, stem):
    fig.savefig(stem.with_suffix('.png'), dpi=600)
    fig.savefig(stem.with_suffix('.svg'))
    plt.close(fig)


def render(output):
    output.mkdir(parents=True, exist_ok=True)
    event_panels=(FIRST,5,(838,650))
    scale=(195,589,643,641)
    with TemporaryDirectory() as temp:
        plate=Path(temp)/'figure5.png'
        paired(*event_panels,[(75,35,392,273),(469,35,787,273)],
               ['15 cm, −30°','15 cm, 0°'],plate,(520,390),scale,690)
        photo_typography(plate,output/'figure5.png',5)
    paired(*event_panels,[(75,318,392,556),(469,318,787,556)],
           ['18 cm, −30°','18 cm, 0°'],output/'figureS4.png',(520,390),scale,690)
    export(draw_figure6(DATA/'figure6.csv'),output/'figure6')
    figure7(FIRST/'figure7.png',output/'figure7.png',output/'figureS5.png')
    export(figure8(DATA/'figure8.csv'),output/'figure8')
    figure9(FIRST/'figure9.png',output/'figure9.png')
    # The Rotor plot uses the original archived coordinates, fitted per panel.
    with plt.rc_context():
        from plot_results import figure9 as rotor_tsne
        with (DATA/'figure9.csv').open(encoding='utf-8-sig',newline='') as source:
            rows=list(csv.DictReader(source))
        with TemporaryDirectory() as temp:
            rotor_tsne(rows,output/'figureS6.png',Path(temp),'Rotor')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'final_png')
    render(parser.parse_args().out)
