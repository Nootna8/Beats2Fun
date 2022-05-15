import os
import sys
import math

import util
util.init_app_mode()

import argparse
from gooey import Gooey, GooeyParser
from halo import Halo
from tqdm import tqdm

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.colors import LinearSegmentedColormap
from colour import Color

import beatutil
import videoutil

color_list = [
    (0,    Color('#000000').rgb),
    (0.01, Color('#1E90FF').rgb),
    (2/5,  Color('#00FFFF').rgb),
    (3/5,  Color('#00FF00').rgb),
    (4/5,  Color('#FFFF00').rgb),
    (5/5,  Color('#FF0000').rgb)
]
color_ramp = LinearSegmentedColormap.from_list( 'my_list', color_list )

def plot(options, input, output='show'):
    numoptions = len(options)
   
    figure, axis = plt.subplots(numoptions, figsize = (16,numoptions))
    #figure.subplots_adjust(top=0.7)

    for i, o in enumerate(options):

        beats = beatutil.find_beats(input, o)[1]
        density = beatutil.beat_density(beats, 60)

        if numoptions > 1:
            myaxis = axis[i]
        else:
            myaxis = axis

        #myaxis.set_title(o['name'])
        myaxis.imshow([density], cmap=color_ramp, interpolation = 'bilinear', aspect='auto')
        myaxis.axis('off')
    
    if output == 'show':
        plt.show()
    else:
        plt.savefig(output)

    plt.clf()

    
def run(input, show, output):
    spinner = 'dots'
    if app_mode == 'goo':
        spinner = {'interval': 1000, 'frames': ['.', '..', '...']}

    options = beatutil.find_options(input)
    if not options:
        print("No beats options found")
        return False

    if output:
        plot(options, input, output)
        if show:
            img = mpimg.imread(output)
            plt.axis('off')
            imgplot = plt.imshow(img)
            plt.show()
    else:
        plot(options, input)
    
    return True

@Gooey(progress_regex=r"(?P<current>\d+)/(?P<total>\d+)",
      progress_expr="current / total * 100",
      timing_options = {'show_time_remaining':True},
      default_size=(610, 650),
      image_dir=util.get_resource(''))
def main():
    parser = GooeyParser(description='Generates heatmap for a funscript')
    

    file_types = list(map(lambda x: x.file_desc, beatutil.loaded_parsers))
    exts = []
    for f in file_types:
        exts += f.split('|')[1].split(',')
    file_types.insert(0, 'All ({})|{}'.format(', '.join(exts), ';'.join(exts)))
    file_types.append('All files|*')

    parser.add_argument(
        'beatinput',
        help='Path to the input',
        widget='FileChooser',
        metavar="Input",
        gooey_options={
            'message': "Pick your input",
            'wildcard': '|'.join(file_types)
        }
    )

    parser.add_argument(
        'output',
        help='Where to store the heatmap image file (optional)',
        widget='FileChooser',
        metavar="Output",
        default='',
        nargs='?'
        #gooey_options={
        #    'message': "Pick your video",
        #    'wildcard': "Video (*.mp4,*.ssc)|*.mp4"
        #}
    )
    
    # parser.add_argument('-width', metavar="Width", default='100', help='Output image width', type=int, widget='IntegerField')
    parser.add_argument('-show', metavar="Show", help='Opens the generated heatmap when done', action='store_false', default=True)
    
    args = parser.parse_args()
    result = run(**vars(args))
    
    if not result:
        sys.exit(1)
    
if __name__ == "__main__":
    main()