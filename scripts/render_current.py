"""Render the manuscript's Figures 6–8 from their final labelled SVG files."""
import argparse
from pathlib import Path
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SIZES = {6: (4231, 1642), 7: (4334, 3370), 8: (4219, 2110)}


DPI = {6: 599.9734, 7: 143.9926, 8: 599.9734}


def render(number, output):
    width, height = SIZES[number]
    with pymupdf.open(ROOT / 'figures' / f'figure{number}.svg') as svg:
        page = svg[0]
        matrix = pymupdf.Matrix(width / page.rect.width, height / page.rect.height)
        pixmap = page.get_pixmap(matrix=matrix)
        raster = Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples)
    assert raster.width in (width, width + 1) and raster.height in (height, height + 1)
    raster.crop((0, 0, width, height)).save(output / f'figure{number}.png', dpi=(DPI[number], DPI[number]))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,default=ROOT / 'final_png')
    p.add_argument('--figure',type=int,choices=tuple(SIZES))
    a = p.parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)
    for number in ([a.figure] if a.figure else SIZES):
        render(number, a.output_dir)


