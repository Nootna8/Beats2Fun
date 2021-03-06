import os

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.colors import LinearSegmentedColormap
from colour import Color

import util
import random

import parsers.parsefs
import parsers.parseosu
import parsers.parsesm
import parsers.parsetxt

loaded_parsers = [
    parsers.parsefs.FSParser,
    parsers.parseosu.OSUParser,
    parsers.parsesm.SMParser,
    parsers.parsetxt.TXTParser
]

def find_beats(input, option=None, song_required=False):
    for p in loaded_parsers:
        beats = p.process_input(input, option)
        if not beats:
            continue
        if song_required and not beats[0]:
            continue

        return beats
    
    return False

def find_beatinput(beatinput: str, song_required: bool):
    if beatinput.startswith('rnd:'):
        beatinput = beatinput[4:]
        if not os.path.isdir(beatinput):
            raise Exception("Random only supports folders")

        def is_option(path):
            if not os.path.isdir(path):
                return False

            for p in loaded_parsers:
                if p.supports_input(path):
                    return True

            return False

        options = [ f.path for f in os.scandir(beatinput) if is_option(f.path) ]
        random.shuffle(options)
        beatinput = options[0]
        print("Randomly selected: {}".format(beatinput))

    for p in loaded_parsers:
        if p.supports_input(beatinput):
            return p(beatinput)

    raise Exception("No beats avaiable for: {}".format(os.path.realpath(beatinput)))
    
def file_select_options():
    ret = []
    exts = []
    for p in loaded_parsers:
        exts += p.file_desc.split("|")[1].split(";")
        ret.append(p.file_desc)

    ret = [
        'All beat inputs ({})|{}'.format(', '.join(exts), ';'.join(exts))
    ] + ret

    return '|'.join(ret)

def beat_density(beats, width=100, length=None):
    values = [0 for i in range(width)]
    if length == None:
        length = beats[-1]

    for i,b in enumerate(beats[1:]):
        lastb = beats[i-1]
        duration = b - lastb
        speed = 80 / duration # length / duration
        speed = util.clamp(speed / max_speed, 0, 1)
        
        index = round(b / length * (width-1))
        if values[index] == 0:
            values[index] += speed
            values[index] /= 2
        else:
            values[index] = speed
    
    return values

def find_options(input):
    for p in loaded_parsers:
        options = p.find_options(input)
        if options:
            return options

    return False

color_list = [
    (0,    Color('#000000').rgb),
    (0.01, Color('#1E90FF').rgb),
    (2/5,  Color('#00FFFF').rgb),
    (3/5,  Color('#00FF00').rgb),
    (4/5,  Color('#FFFF00').rgb),
    (5/5,  Color('#FF0000').rgb)
]
color_ramp = LinearSegmentedColormap.from_list( 'my_list', color_list )

def plot_beats(beats, output, song_lenth):
    numoptions = 1
    figure, axis = plt.subplots(numoptions, figsize = (16,numoptions))
    
    density = beat_density(beats, 60, song_lenth)
    
    #figure.subplots_adjust(top=0.7)
    #axis.set_title(output)

    axis.imshow([density], cmap=color_ramp, interpolation = 'bilinear', aspect='auto')
    axis.axis('off')
    plt.savefig(output + '.png')
    plt.clf()