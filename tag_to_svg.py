#!/usr/bin/env python3

import os
import sys
import argparse
import glob
import math
from PIL import Image
import numpy as np


# Thanks to https://stackoverflow.com/a/54547257
def dir_path(file_path):
    if os.path.isfile(file_path):
        return file_path
    else:
        raise argparse.ArgumentTypeError(f'Supplied argument "{file_path}" is not a valid file path.')


parser = argparse.ArgumentParser(
    description='A script to convert pre-generated apriltag .png files into SVG format.',
    epilog='Example: "python tag_to_svg.py tagStandard52h13/tag52_13_00007.png tag52_13_00007.svg --size=20mm"'
)
parser.add_argument(
    '--tag_family', type=str, choices=['tag16h5', 'tag25h9', 'tag36h11', 'tagCircle21h7', 'tagCircle49h12', 'tagCustom48h12', 'tagStandard41h12', 'tagStandard52h13'],
    default='tag36h11',
    help='The apriltag family to use for the tag generation.'
)
parser.add_argument(
    '--tag_id', type=str, default='0-10',
    help='The ID of the apriltag to generate(ex. "0"/"0,1,2"/"0-5").'
)
parser.add_argument(
    '--cols', type=int, default=3,
    help='The number of tags to generate per row.'
)
parser.add_argument(
    '--tag_size', type=float, default=37.5,
    help='The size of a tag [mm]'
)
parser.add_argument(
    '--margin', type=float, default=5,
    help='The spacing between tags [mm]'
)
parser.add_argument(
    '--out_file', type=str, default='output.svg', 
    help='The path to the SVG output file.'
)

'''
parser.add_argument(
    'tag_file', type=dir_path, 
    help='The path to the apriltag png you want to convert.'
)
parser.add_argument(
    '--size', type=str, required=False, default='20mm', dest="svg_size", 
    help='The size (edge length) of the generated svg such as "20mm" "2in" "20px"'
)
'''

def gen_rgba(rbga):
    (_r, _g, _b, _raw_a) = rbga
    _a = _raw_a / 255
    return f'rgba({_r}, {_g}, {_b}, {_a})'

def gen_apriltag_svg(width, height, pixel_array, size):
    def gen_gridsquare(row_num, col_num, pixel):
        _rgba = gen_rgba(pixel)
        _id = f'box{row_num}-{col_num}'
        return f'\t<rect width="1" height="1" x="{row_num}" y="{col_num}" fill="{_rgba}" id="{_id}"/>\n'

    svg_text = '<?xml version="1.0" standalone="yes"?>\n'
    svg_text += f'<svg width="{size}" height="{size}" viewBox="0,0,{width},{height}" xmlns="http://www.w3.org/2000/svg">\n'
    for _y in range(height):
        for _x in range(width):
            svg_text += gen_gridsquare(_x, _y, pixel_array[_x, _y])
    svg_text += '</svg>\n'

    return svg_text

def gen_apriltags_svg(tag_images, tag_size, margin, cols):
    tag_n_cols = cols
    tag_n_rows = math.ceil(len(tag_images) / cols)
    svg_width = (tag_size + (2*margin)) * cols + margin
    svg_height = (tag_size + (2*margin)) * tag_n_rows + margin
    print(f'Creating SVG with size: {svg_width}x{svg_height}')
    print(f'Number of tags: {len(tag_images)}')
    print(f'Number of columns: {tag_n_cols}')
    print(f'Number of rows: {tag_n_rows}')
    print(f'Tag size: {tag_size}mm')
    print(f'Margin: {margin}mm')
    
    svg_text = '<?xml version="1.0" standalone="yes"?>\n'
    svg_text += f'<svg width="{svg_width}mm" height="{svg_height}mm" viewBox="0,0,{svg_width},{svg_height}" xmlns="http://www.w3.org/2000/svg">\n'
    for i, (tag_name, tag_image) in enumerate(tag_images.items()):
        row = i // tag_n_cols
        col = i % tag_n_cols
        x = col * (tag_size + (2*margin)) + margin
        y = row * (tag_size + (2*margin)) + margin
        pix_height, pix_width = [tag_size/v for v in tag_image.shape[:2]]
        print(f'{tag_name}: posiiton ({x}, {y}), pix_size ({pix_width}, {pix_height})')
        for _y in range(tag_image.shape[0]):
            for _x in range(tag_image.shape[1]):
                _rgba = gen_rgba(tag_image[_y, _x])
                _rgb_hex = '#' + ''.join([f'{v:02x}' for v in tag_image[_y, _x][:3]])
                _id = f'{tag_name}-{_x}-{_y}'
                svg_text += f'\t<rect width="{pix_width}" height="{pix_height}" x="{x+_x*pix_width}" y="{y+_y*pix_height}" id="{_id}" style="fill:{_rgb_hex};stroke:#000000;stroke-width:0.0"/>\n'
        # tag_idを描画
        svg_text += f'\t<text x="{x+tag_size/2}" y="{y+tag_size+(0.8*margin)}" font-size="{margin*0.8}" font-family="monospace" text-anchor="middle" fill="#5EEF5E">{tag_name}</text>\n'
        # 枠を描画
        svg_text += f'\t<rect width="{tag_size+margin+margin}" height="{tag_size+margin+margin}" x="{x-margin}" y="{y-margin}" fill="none" stroke="#888888" stroke-width="1"/>\n'
        
    svg_text += '</svg>\n'
    return svg_text

def main():
    args = parser.parse_args()
    apriltag_svg = None
    tag_all = glob.glob(f'{args.tag_family}/*_*.png')
    if ',' in args.tag_id:
        tag_ids = [int(id) for id in args.tag_id.split(',')]
    elif '-' in args.tag_id:
        start, end = args.tag_id.split('-')
        tag_ids = [id for id in range(int(start), int(end)+1)]
    else:
        tag_ids = [int(args.tag_id)]

    tag_images = {}
    for tag_id in tag_ids:
        tag_file = [file for file in tag_all if file.endswith(f'_{tag_id:05d}.png')]
        if len(tag_file) == 0:
            print(f'Error: Could not find tag file for tag_id: {tag_id}')
            continue
        tag_file = tag_file[0]
        tag_name = os.path.basename(tag_file).split('.')[0]
        if os.path.exists(tag_file) == False:
            print(f'Error: Could not find tag file: {tag_file}')
            continue
        pil_image = Image.open(tag_file)
        tag_images[tag_name] = np.array(pil_image)
    
    apriltags_svg = gen_apriltags_svg(tag_images, args.tag_size, args.margin, args.cols)
    assert apriltags_svg is not None, 'Error: Failed to create SVG.'

    with open(args.out_file, 'w') as fp:
        fp.write(apriltags_svg)

    print(f'Output SVG file: {args.out_file} with size: {args.out_file}')

if __name__ == "__main__":
    main()
