"""Improve the lettering in Figures 4–6 with the original photo and plot content."""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
INK, RED = '#121212', '#9b171b'
DPI = 600
PHOTO_LABELS = (
    ((139, 81, 174, 95), 'Tank'),
    ((92, 185, 190, 201), 'Coupling (ROI)'),
    ((247, 188, 300, 202), 'Bearing'),
    ((426, 202, 466, 217), 'Pump'),
    ((66, 312, 105, 325), 'Motor'),
    ((377, 317, 466, 331), 'Event camera'),
    ((646, 94, 744, 107), 'Coupling (ROI)'),
    ((801, 84, 851, 98), 'Bearing'),
    ((955, 96, 992, 110), 'Rotor'),
    ((600, 183, 638, 195), 'Motor'),
    ((904, 281, 994, 295), 'Event camera'),
)


def photo_typography(previous, output, number):
    with Image.open(previous) as png:
        original = png.convert('RGB')
        dpi = png.info['dpi']
    image = original.copy()
    draw = ImageDraw.Draw(image)
    updated = Image.new('1', image.size)

    def pos(*values):
        return tuple(round(value * image.width / 1100) for value in values)

    def clear(bounds):
        rect = pos(*bounds)
        draw.rectangle(rect, fill='white')
        ImageDraw.Draw(updated).rectangle(rect, fill=1)
        return rect

    def font(size, bold):
        return ImageFont.truetype('arialbd.ttf' if bold else 'arial.ttf', pos(size)[0])

    headers = (('(a) Pump test rig', '(b) Rotor test rig') if number == 4
               else ('(a) 15 cm, −30°', '(b) 15 cm, 0°'))
    clear((0,0,1100,45))
    for x, label in zip((24,567), headers):
        draw.text(pos(x,24), label, fill=INK, font=font(25,True), anchor='lm')

    if number == 4:
        for box, label in PHOTO_LABELS:
            left, top, right, bottom = clear(box)
            text_size = pos(14.8)[0]
            while text_size > 1:
                face = ImageFont.truetype('arialbd.ttf', text_size)
                a,b,c,d = face.getbbox(label)
                if c-a <= right-left-3 and d-b <= bottom-top-3:
                    break
                text_size -= 1
            patch = Image.new('RGB',(right-left+1,bottom-top+1),'white')
            x = (patch.width-(c-a))//2-a
            y = (patch.height-(d-b))//2-b
            ImageDraw.Draw(patch).text((x,y),label,font=face,
                                       fill=RED if label == 'Coupling (ROI)' else INK)
            image.paste(patch,(left,top))
    else:
        clear((202,472,906,526))
        for n,x in enumerate((228,319,411,502,593,684,776,867)):
            draw.text(pos(x,484), str(n), fill=INK, font=font(18,True), anchor='mm')
        draw.text(pos(550,509), 'ln(1 + events per pixel per second) | shared display scale',
                  fill=INK, font=font(17.5,True), anchor='mm')

    # All changes must be confined to the existing text boxes and labels.
    untouched = ImageChops.invert(updated.convert('L'))
    assert ImageChops.multiply(ImageChops.difference(original,image),
                              untouched.convert('RGB')).getbbox() is None
    image.save(output, dpi=dpi, optimize=True)


def draw_figure6(data):
    with data.open(encoding='utf-8-sig',newline='') as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 60
    labels = ('ItP','ItP+ItI','FULL')
    keys = ('DARM_IP_ONLY','DARM_IP_II','DARM_FULL')
    colors = ('#bccee5','#f2c86d','#365f9f')
    rc = {'font.family': 'Arial', 'font.size': 9, 'axes.edgecolor': INK,
          'axes.labelcolor': INK, 'text.color': INK, 'axes.linewidth': .85,
          'xtick.color': INK, 'ytick.color': INK, 'pdf.fonttype': 42,
          'svg.fonttype': 'none'}
    with plt.rc_context(rc):
        fig, axes = plt.subplots(1,2, figsize=(7.1,2.81))
        fig.subplots_adjust(left=.097, right=.98, bottom=.225, top=.84, wspace=.29)
        means = {}
        for i,(ax,speed,indices) in enumerate(zip(axes,(30,40),((0,1,2),(1,2)))):
            panel = []
            for x,index in enumerate(indices):
                vals = [float(row['DAT_macro_f1']) for row in rows
                        if int(row['speed']) == speed and row['method'] == keys[index]]
                assert len(vals) == 12
                mean = 100*np.mean(vals)
                panel.append(mean)
                ax.bar(x, mean, .63, color=colors[index], edgecolor='#263147',
                       linewidth=.6, zorder=3)
                label_y = 51.5 if 47 <= mean < 50 else mean+1.2
                ax.text(x,label_y,f'{mean:.2f}',ha='center',va='bottom',fontsize=9)
            means[speed] = panel
            ax.set(title=None, ylim=(0,78), xlim=(-.48,len(indices)-.52),
                   xlabel='Objectives retained from update 1',
                   ylabel='Recording-level Macro-F1 (%)')
            ax.set_title(f'({chr(97+i)}) {speed} Hz', loc='left', fontsize=11,
                         fontweight='bold', pad=9)
            ax.set_xticks(range(len(indices)), [labels[index] for index in indices])
            ax.set_yticks(range(0,71,10))
            ax.tick_params(axis='both',labelsize=8.55,pad=3,length=3)
            ax.set_axisbelow(True)
            ax.grid(axis='y',color='#dce0e5',lw=.5)
            delta = panel[-1]-panel[-2]
            delta_text = f'{delta:+.2f}'.replace('-','−')
            ax.text(.5,72.0,f'Adding PtP: {delta_text} pp',ha='center',va='bottom',
                    transform=ax.get_yaxis_transform(),fontsize=9.0,fontweight='bold')
        assert np.allclose(means[30],[48.10,62.04,60.88],atol=.006)
        assert np.allclose(means[40],[41.30,43.06],atol=.006)
        fig.canvas.draw()
        assert np.allclose(axes[0].get_position().bounds[1:],axes[1].get_position().bounds[1:])
        return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('previous_figures', type=Path)
    parser.add_argument('figure6_csv', type=Path)
    args = parser.parse_args()
    qa = ROOT/'qa'
    output = ROOT/'02_Figures'
    for number in (4,5):
        name = f'figure{number}.png'
        photo_typography(args.previous_figures/name, output/name, number)
    fig = draw_figure6(args.figure6_csv)
    fig.savefig(output/'figure6.png',dpi=DPI)
    with plt.rc_context({'pdf.fonttype':42, 'svg.fonttype':'none'}):
        fig.savefig(qa/'vector'/'figure6.pdf')
        fig.savefig(qa/'vector'/'figure6.svg')
    plt.close(fig)


if __name__ == '__main__':
    main()
