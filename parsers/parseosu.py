import os
from glob import glob
import fnmatch
from zipfile import ZipFile
from .beatmapparser import BeatmapParser
from . import BeatInput, BeatOption, BeatList
import util

file_desc = 'Osu beatmap (*.osu, *.osz)|*.osu;*.osz'
class OSUBeatOption(BeatOption):
    parser: BeatmapParser

    def __init__(self, parser):
        super().__init__(parser.beatmap.get('OverallDifficulty'), parser.beatmap.get('Version'))
        self.parser = parser

    def load(self):
        beat_times = []
        self.parser.build_beatmap()
        bm = self.parser.beatmap

        beat_times = [x['offset'] for x in bm['timingPoints']] + [x['startTime'] for x in bm["hitObjects"]] + [x['end_time'] for x in bm["hitObjects"] if 'end_time' in x]
        beat_times = [x for x in beat_times if x >= 0]
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