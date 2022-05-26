import os

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.colors import LinearSegmentedColormap
from colour import Color

import util

import parsers.parsefs
import parsers.parseosu
import parsers.parsesm
import parsers.parsetxt

loaded_parsers = [
    parsers.parsefs,
    parsers.parseosu,
    parsers.parsesm,
    parsers.parsetxt
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

def find_beatinput(beatinput, song_required):
    parser = parsers.parsesm.SMParser(beatinput)
    return parser
    

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