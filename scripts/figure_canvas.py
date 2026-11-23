import json
import os
import shutil
from functools import lru_cache
from pathlib import Path
from math import atan2, cos, sin, pi
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCALE = 4
BLUE = '#0066cb'
INK = '#192433'
PALE = '#dceef9'
RED = '#a42e34'
ORANGE = '#f8c466'
GREY = '#53677e'
DPI = 600

@lru_cache
def font(size, bold=False, serif=False):
    name = ('timesbd' if bold else 'times') if serif else ('arialbd' if bold else 'arial')
    path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / (name + '.ttf')
    return ImageFont.truetype(str(path), size * SCALE)

def scaled(box):
    return tuple(round(value * SCALE) for value in box)

class Canvas:
    def __init__(self, width, height):
        self.im = Image.new('RGB', scaled((width, height)), 'white')
        self.draw = ImageDraw.Draw(self.im)

    def text(self, x, y, label, size=23, bold=False, serif=False, color=INK, anchor='mm'):
        if '\n' in label:
            self.draw.multiline_text(scaled((x, y)), label, font=font(size, bold, serif),
                                     fill=color, align='center', spacing=6*SCALE, anchor=anchor)
        else:
            self.draw.text(scaled((x, y)), label, font=font(size, bold, serif), fill=color, anchor=anchor)

    def rect(self, box, fill='white', outline=GREY, width=2, radius=0):
        if radius:
            self.draw.rounded_rectangle(scaled(box), radius=radius*SCALE, fill=fill,
                                        outline=outline, width=width*SCALE)
        else:
            self.draw.rectangle(scaled(box), fill=fill, outline=outline, width=width*SCALE)

    def line(self, points, color=GREY, width=3):
        self.draw.line([scaled(point) for point in points], fill=color, width=width*SCALE, joint='curve')

    def arrow(self, points, color=BLUE, width=3, dashed=False):
        if dashed:
            for a, b in zip(points, points[1:]):
                dx, dy = b[0]-a[0], b[1]-a[1]
                length = (dx*dx+dy*dy)**0.5
                for offset in range(0, int(length), 17):
                    end = min(offset + 10, length)
                    self.line([(a[0]+dx*offset/length,a[1]+dy*offset/length),
                               (a[0]+dx*end/length,a[1]+dy*end/length)], color, width)
        else:
            self.line(points, color, width)
        a,b=points[-2:]
        angle=atan2(b[1]-a[1],b[0]-a[0])
        tip=[b]+[(b[0]-12*cos(angle+sign*pi/6),b[1]-12*sin(angle+sign*pi/6)) for sign in (-1,1)]
        self.draw.polygon([scaled(p) for p in tip], fill=color)

    def paste(self, asset, left, top, width, height):
        if asset.size != scaled((width,height)):
            asset = asset.resize(scaled((width,height)),Image.Resampling.LANCZOS)
        self.im.paste(asset,scaled((left,top)))

    def save(self, path):
        self.im.save(path, dpi=(DPI,DPI), optimize=True)

def source_crop(source, num, full_w, full_h, box):
    with Image.open(source/f'figure{num}.png') as img:
        x0,y0,x1,y1=box
        coordinates=(round(x0*img.width/full_w),round(y0*img.height/full_h),
                     round(x1*img.width/full_w),round(y1*img.height/full_h))
        return img.crop(coordinates).convert('RGB')

def paired(source, num, ref_size, regions, labels, path, panel_size,
           legend=None, legend_width=None):
    w,h=panel_size
    margin=25
    gap=36
    legend_asset = source_crop(source,num,*ref_size,legend) if legend else None
    lw = legend_width or 650
    lh = round(lw*legend_asset.height/legend_asset.width) if legend_asset else 0
    c=Canvas(2*margin+2*w+gap, 76+h+lh)
    rectangles=[]
    for i,(box,label) in enumerate(zip(regions,labels)):
        x=margin+i*(w+gap)
        asset=source_crop(source,num,*ref_size,box)
        source_ratio=asset.width/asset.height
        if abs(source_ratio-w/h)>0.075:
            raise ValueError(f'Unexpected crop aspect for Figure {num}: {source_ratio:.3f}, {w/h:.3f}')
        c.text(x,25,f'({chr(97+i)}) {label}',25,True,anchor='lm')
        c.paste(asset,x,54,w,h)
        rectangles.append((x,54,w,h))
    assert rectangles[0][1:] == rectangles[1][1:]
    if legend:
        c.paste(legend_asset,round((2*margin+2*w+gap-lw)/2),h+61,lw,lh)
    c.save(path)
    return rectangles
