"""Compose Figure 7 and S5 from the published-ready four-panel source.

Retype labels in black Arial and keep the original bar, scatter, and legend artwork.
Figure 8 is re-exported from its original CSV using the Figure 6 typography.
"""
import argparse
import csv
from functools import lru_cache
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
INK = '#121212'
BLUE, AMBER = '#2e6098', '#de8738'
DPI = 600


@lru_cache
def arial(size, bold):
    font = 'arialbd.ttf' if bold else 'arial.ttf'
    return ImageFont.truetype(font, size)


class Lettering:
    """Place matching lettering using the 1050-pixel source preview coordinates."""
    def __init__(self, source):
        with Image.open(source) as original:
            self.dpi = original.info['dpi']
            self.source = original.convert('RGB')
        self.image = self.source.copy()
        self.draw = ImageDraw.Draw(self.image)

    def xy(self, *values):
        return tuple(round(val*self.image.width/1050) for val in values)

    def wipe(self, rect, color='white'):
        self.draw.rectangle(self.xy(*rect), fill=color)

    def text(self, x, y, label, size=17, bold=False, align='mm'):
        self.draw.text(self.xy(x,y), label, fill=INK, anchor=align,
                       font=arial(self.xy(size)[0],bold))

    def vertical(self, x, y, label, size=17.5):
        face = arial(self.xy(size)[0],False)
        a,b,c,d = face.getbbox(label)
        patch = Image.new('RGBA',(c-a+4,d-b+4))
        ImageDraw.Draw(patch).text((2-a,2-b),label,font=face,fill=INK)
        patch = patch.rotate(90, expand=True)
        xv,yv = self.xy(x,y)
        self.image.paste(patch,(xv-patch.width//2,yv-patch.height//2),patch)

    def verify_plot_pixels(self, rect, allowed=()):
        """Check every pixel in a plot window outside its text-only touch-ups."""
        from PIL import ImageChops
        diff = ImageChops.difference(self.source,self.image)
        draw = ImageDraw.Draw(diff)
        for box in allowed:
            draw.rectangle(self.xy(*box),fill=(0,0,0))
        assert diff.crop(self.xy(*rect)).getbbox() is None, rect

    def compose(self, top, bottom, legend_top, target, space=5):
        crop = self.image.crop((0,self.xy(top)[0],self.image.width,self.xy(bottom)[0]))
        legend = self.image.crop((0,self.xy(legend_top)[0],self.image.width,self.image.height))
        y = crop.height + self.xy(space)[0]
        canvas = Image.new('RGB',(self.image.width,y+legend.height),'white')
        canvas.paste(crop,(0,0))
        canvas.paste(legend,(0,y))
        canvas.save(target,dpi=self.dpi,optimize=True)


# x, y, text for the numbers and percentage-point changes from the original charts.
PUMP7_LABELS = (
    (127,138,'46.76'), (172,143,'45.37'),
    (266,94,'60.88'), (310,94,'60.65'),
    (405,149,'43.06'), (450,129,'49.63'),
    (149,117,'Δ −1.39 pp'), (288,74,'Δ −0.23 pp'), (427,109,'Δ +6.57 pp'),
    (671,127,'50.23'), (716,122,'51.88'),
    (811,149,'43.06'), (855,142,'45.37'),
    (950,217,'21.30'), (994,187,'30.99'),
    (693,102,'Δ +1.65 pp'), (832,123,'Δ +2.31 pp'), (971,166,'Δ +9.69 pp'),
)
# Wipe only the existing glyph areas above the bars. The locations of the
# labels, ticks, axes, marks, and highlighted lowest-nine bin come from
# the source rendering and do not depend on replotting the CSV.
PUMP7_PATCHES = (
    (107,130,148,145), (151,135,192,150),
    (246,87,287,101), (290,87,332,102),
    (387,142,425,156), (431,121,469,136),
    (110,108,188,126), (249,66,329,81), (389,101,468,118),
    (652,120,691,134), (697,114,736,130),
    (792,142,830,154), (836,135,874,149),
    (931,209,970,225), (975,179,1014,194),
    (654,94,734,109), (794,114,871,131), (931,157,1013,174),
)


def figure7(source, main, supplement):
    style = Lettering(source)
    for offset, xlabel, xticks in (
        (0,'Rotational speed',('20 Hz','30 Hz','40 Hz')),
        (544,'Summary metric',('Overall mean','Worst speed','Bottom-25%')),
    ):
        style.wipe((20+offset,43,52+offset,297))
        style.wipe((53+offset,38,79+offset,307))
        style.vertical(38+offset,172,'Recording-level Macro-F1 (%)')
        for tick in range(0,81,10):
            style.text(73+offset,297-tick*250/80,str(tick),17,align='rm')
        style.wipe((80+offset,305,min(1049,505+offset),355))
        for x,label in zip((149,288,428),xticks):
            style.text(x+offset,318,label,17,label=='Bottom-25%')
        style.text(288+offset,342,xlabel,18.4)
        style.wipe((80+offset,6,min(1049,515+offset),34))
    style.text(87,20,'(a) Performance across Pump speeds',21.5,True,'lm')
    style.text(631,20,'(b) Overall and lower-tail performance',21.5,True,'lm')

    for rect in PUMP7_PATCHES:
        style.wipe(rect)
    allowed = list(PUMP7_PATCHES)
    for x,y,label in PUMP7_LABELS:
        is_delta = label.startswith('Δ')
        featured = label in ('21.30','30.99','Δ +9.69 pp')
        size = 16 if is_delta else 16.25
        style.text(x,y,label,size,featured)
        # Extend verification masks just enough to cover the new glyphs.
        font = arial(style.xy(size)[0],featured)
        full_width = font.getlength(label)*1050/style.image.width
        allowed.append((x-full_width/2-1,y-9,x+full_width/2+1,y+9))
    style.verify_plot_pixels((87,47,490,296),allowed)
    style.verify_plot_pixels((631,47,1034,296),allowed)
    restyle_pump_legend(style)
    style.compose(0,361,774,main)

    # The original panels 7(c) and 7(d) become S5(a) and S5(b).
    style.wipe((80,412,517,444))
    style.wipe((625,412,1050,444))
    style.text(87,430,'(a) Separately ranked task–seed scores',20,True,'lm')
    style.text(631,430,'(b) Paired task–seed changes',20,True,'lm')
    for rect in ((21,455,52,701),(52,446,79,714),(561,455,593,701),(591,460,623,711)):
        style.wipe(rect)
    style.vertical(35,579,'Recording-level Macro-F1 (%)')
    style.vertical(578,579,'Δ recording-level Macro-F1 (pp)')
    for tick in range(0,101,20):
        style.text(74,704-tick*2.475,str(tick),16,align='rm')
    for tick in (-60,-30,0,30,60):
        style.text(618,589-tick*1.865,str(tick).replace('-','−'),16,align='rm')
    for rect in ((82,713,510,763),(630,713,1049,763)):
        style.wipe(rect)
    for x,tag in ((92,'1'),(182,'9'),(282,'18'),(383,'27'),(484,'36'),
                  (700,'20 Hz'),(832,'30 Hz'),(965,'40 Hz')):
        style.text(x,723,tag,16)
    style.text(288,746,'Rank within each method',17.5)
    style.text(833,746,'Paired task–seed results, grouped by speed',17.5)
    style.verify_plot_pixels((87,454,490,703))
    style.verify_plot_pixels((631,454,1034,703))
    style.compose(410,766,774,supplement)


def restyle_pump_legend(style):
    style.wipe((416,776,514,802))
    style.wipe((565,776,818,802))
    style.text(423,788,'Full DARM',17,False,'lm')
    style.text(570,788,'Calibrated DARM (PtP = 0.25)',17,False,'lm')


def figure9(source, target):
    style = Lettering(source)
    for offset, method, score in ((0,'Full DARM','5.56%'),(550,'Calibrated DARM','17.78%')):
        style.wipe((27+offset,0,min(1049,510+offset),66))
        style.text(31+offset,16,f"({'a' if offset == 0 else 'b'}) Pump / {method}",22,True,'lm')
        style.text(31+offset,53,f'Recording-level Macro-F1 {score}',18,True,'lm')
        style.wipe((0+offset,144,29+offset,224))
        style.vertical(15+offset,185,'t-SNE 2',18)
        style.wipe((222+offset,305,312+offset,329))
        style.text(262+offset,317,'t-SNE 1',18)
        style.verify_plot_pixels((31+offset,68,min(1044,494+offset),301))
    for x,y,label,limit in (
        (381,729,'Ball',465),(381,756,'Inner',465),
        (498,729,'Outer',601),(498,756,'Healthy',601),
        (635,729,'Misalignment',800),(635,756,'Cavitation',795),
        (390,797,'Source window',553),(600,797,'Held-out window',798),
    ):
        style.wipe((x-3,y-11,limit,y+12))
        style.text(x,y,label,18,False,'lm')
    style.compose(0,332,713,target)


def figure8(csv_file):
    with csv_file.open(encoding='utf-8-sig',newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 36
    methods = ('DARM_FULL','DARM_PP025')
    domains = ('A1_R1000','A1_R2000','A2_R1000','A2_R2000','A3_R1000','A3_R2000')
    seeds = ('42','2026','3407')

    def average(field, group):
        result = [[100*np.mean([float(r['target_DAT']) for r in rows
                               if r[field] == item and r['method'] == method])
                   for item in group] for method in methods]
        return np.asarray(result)

    domain = average('target_domain',domains)
    seed = average('seed',seeds)
    assert np.allclose(np.mean(domain,axis=1),[25.93,28.80],atol=.006)
    assert np.allclose(seed[1]-seed[0],[8.33,-3.19,3.47],atol=.006)
    assert np.allclose(domain[1]-domain[0],[5.56,8.89,5.56,9.72,9.72,-22.22],atol=.006)
    plt.rcParams.update({'font.family':'Arial','font.size':9.0,'axes.labelcolor':INK,
                        'text.color':INK,'axes.edgecolor':INK,'xtick.color':INK,'ytick.color':INK,
                        'axes.linewidth':.85,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig = plt.figure(figsize=(7.45,3.71))
    ax1 = fig.add_axes((.142,.205,.458,.69))
    ax2 = fig.add_axes((.699,.205,.288,.69))
    for ax in (ax1,ax2):
        ax.spines[['top','right']].set_visible(False)
        ax.tick_params(labelsize=8.55,length=3,pad=3.5)
    ax1.set_title('(a) Six held-out domains',loc='left',fontsize=11,weight='bold',pad=9)
    ax1.set(yticks=range(6),yticklabels=domains,ylim=(5.62,-.67),xlim=(0,67),
            xlabel='Recording-level Macro-F1 (%)',ylabel='Held-out domain')
    for offset,values,color in zip((-.166,.166),domain,(BLUE,AMBER)):
        bars = ax1.barh(np.arange(6)+offset,values,height=.305,color=color,
                        edgecolor='#293645',linewidth=.5)
        for bar,val in zip(bars,values):
            ax1.text(val+.65,bar.get_y()+bar.get_height()/2,f'{val:.2f}',
                     fontsize=8.4,ha='left',va='center')
    ax1.text(62.3,-.83,'Δ (pp)',fontsize=9,ha='center',va='center',weight='bold')
    for i,delta in enumerate(domain[1]-domain[0]):
        ax1.text(62.3,i,f'{delta:+.2f}'.replace('-','−'),ha='center',va='center',
                 fontsize=8.8)

    ax2.set_title('(b) Seed means',loc='left',fontsize=11,weight='bold',pad=9)
    ax2.set(xlim=(-.47,2.47),ylim=(0,70),xticks=range(3),xticklabels=seeds,
            xlabel='Training seed',ylabel='Recording-level Macro-F1 (%)')
    for shift,values,color in zip((-.215,.215),seed,(BLUE,AMBER)):
        bars = ax2.bar(np.arange(3)+shift,values,.36,color=color,edgecolor='#293645',linewidth=.5)
        for bar,val in zip(bars,values):
            ax2.text(bar.get_x()+bar.get_width()/2,val+1.4,f'{val:.2f}',
                     fontsize=8.4,ha='center',va='bottom')
    for i,delta in enumerate(seed[1]-seed[0]):
        ax2.text(i,max(seed[:,i])+8.6,f'Δ {delta:+.2f} pp'.replace('-','−'),
                 ha='center',va='bottom',fontsize=8.45)
    fig.legend([Patch(fc=c,ec='#293645',lw=.5) for c in (BLUE,AMBER)],
               ['Full DARM','Calibrated DARM (PtP = 0.25)'],loc='lower center',
               ncol=2,frameon=False,bbox_to_anchor=(.53,.019),fontsize=9.2)
    fig.canvas.draw()
    assert np.allclose(ax1.get_position().bounds[1::2],ax2.get_position().bounds[1::2])
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original_figures',type=Path)
    args = parser.parse_args()
    figures = ROOT/'02_Figures'
    qa = ROOT/'qa'
    vector = qa/'vector'
    vector.mkdir(exist_ok=True)
    original = args.original_figures
    figure7(original/'figure7.png',figures/'figure7.png',ROOT/'03_Supplementary_Material'/'figureS5.png')
    figure9(original/'figure9.png',figures/'figure9.png')
    fig = figure8(original.parent/'03_Supplementary_Material'/'figure8.csv')
    fig.savefig(figures/'figure8.png',dpi=DPI)
    fig.savefig(vector/'figure8.pdf')
    fig.savefig(vector/'figure8.svg')
    plt.close(fig)


if __name__ == '__main__':
    main()
