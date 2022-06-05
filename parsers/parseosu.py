import os
from glob import glob
import fnmatch
from zipfile import ZipFile
from .beatmapparser import BeatmapParser
from . import BeatInput, BeatOption, BeatList
import util

file_desc = 'Osu beatmap (*.osu, *.osz)|*.osu;*.osz"'
class OSUBeatOption(BeatOption):
    parser: BeatmapParser

    def __init__(self, parser):
        super().__init__(parser.beatmap.get('OverallDifficulty'), parser.beatmap.get('Version'))
        self.parser = parser

    def load(self):
        beat_times = []
        self.parser.build_beatmap()
        bm = self.parser.beatmap

        beat_times = [x['offset'] for x in bm['timingPoints']] + [x['startTime'] for x in bm["hitObjects"]]
        # Unique values
        beat_times = list(set(beat_times))
        
        beat_times.sort()
        beat_times = list(map(lambda x: x / 1000, beat_times))

        self.beat_list = BeatList(beat_times)
class OSUParser(BeatInput):
    file_desc = file_desc
    extensions = ['.osu', '.osz']

    def read_file(self, path):
        super().read_file(path)
        filename, ext = os.path.splitext(path)
        
        if ext == '.osz':
            with ZipFile(path, 'r') as zipObj:
                zipObj.extractall(util.get_tmp_dir() + '/osu')
            self.read_dir(util.get_tmp_dir() + '/osu')

        if ext == '.osu':
            parser = BeatmapParser()
            parser.parseFile(path)
            self.options.append(OSUBeatOption(parser))
            file_dir = os.path.dirname(path)
            self.song = file_dir + "/" + parser.beatmap.get('AudioFilename')
            self.name = parser.beatmap.get('Artist') + ' - ' + parser.beatmap.get('Title')

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