import os
from glob import glob
import fnmatch
from zipfile import ZipFile
from .beatmapparser import BeatmapParser

file_desc = 'Osu beatmap (*.osu, *.osz)|*.osu;*.osz"'

def get_beats(beatmap):
    all_beat_times = []
    
    beatmap.build_beatmap()
    
    for t in beatmap.beatmap['timingPoints']:
        all_beat_times.append(t['offset'])
        
    for h in beatmap.beatmap["hitObjects"]:
        if h['startTime'] not in all_beat_times:
            all_beat_times.append(h['startTime'])
        
    all_beat_times.sort()
    return list(map(lambda x: x / 1000, all_beat_times))
    
def find_beatmap(input, option=None):
    files = os.listdir(input)
    simsearch =fnmatch.filter(files, '*.osu')
    if len(simsearch) == 0:
        return False

    if not option:
        parser = BeatmapParser()
        parser.parseFile(input + '/' + simsearch[0])
        return (input + '/' + simsearch[0], parser)
    
    for s in simsearch:
        parser = BeatmapParser()
        parser.parseFile(input + '/' + s)
        bm = parser.beatmap

        if option['level'] != bm.get('OverallDifficulty'):
            continue
        if option['version'] != bm.get('Version'):
            continue

        return (input + '/' + s, parser)

    False

def handle_input(bmresult):
    filename, ext = os.path.splitext(bmresult[0])
    if not ext == '.osu':
        return False
    
    parser = bmresult[1]
    
    song = parser.beatmap.get('AudioFilename')
    if not song:
        return False
        
    song = os.path.dirname( bmresult[0] ) + '/' + song
    if not os.path.isfile(song):
        return False

    return (song, get_beats(parser))

def process_input(input, option=None):
    if not os.path.exists(input):
        return False

    if not os.path.isfile(input):
        bmresult = find_beatmap(input, option)
        if not bmresult:
            return False
    
    filename, ext = os.path.splitext(input)
        
    if ext == '.osz':
        with ZipFile(input, 'r') as zipObj:
           zipObj.extractall('tmp/osu')
           
        bmresult = find_beatmap('tmp/osu', option)
        if not input:
            return False
    elif ext == '.osu':
        parser = BeatmapParser()
        parser.parseFile(input)
        bmresult = (input, parser)
    else:
        return False
        
    return handle_input(bmresult)

def find_options(input):
    if not os.path.exists(input):
        return False

    filename, ext = os.path.splitext(input)

    if not os.path.isfile(input):
        files = os.listdir(input)
        simsearch =fnmatch.filter(files, '*.osu')
    elif ext == '.osz':
        with ZipFile(input, 'r') as zipObj:
           zipObj.extractall('tmp/osu')
           files = os.listdir('tmp/osu')
           simsearch =fnmatch.filter(files, '*.osu')
    else:
        return False
        
    ret = []

    for s in simsearch:
        parser = BeatmapParser()
        parser.parseFile(input + '/' + s)
        bm = parser.beatmap

        ret.append({
            'level':  bm.get('OverallDifficulty'),
            'version': bm.get('Version'),
            'name': '{} - {}'.format(bm.get('OverallDifficulty'), bm.get('Version'))
        })

    ret.sort(key=lambda x: x['level'], reverse=False)

    return ret