import simfile
from simfile.notes import NoteData
from simfile.timing import Beat, TimingData
from simfile.notes.timed import time_notes
import simfile.notes

import os
from glob import glob
import fnmatch
from . import BeatInput, BeatOption, BeatList

file_desc = 'StepMania simfile (*.sm, *.ssc)|*.sm;*.ssc"'

class SMBeatOption(BeatOption):

    def __init__(self, simfile, chart):
        super().__init__(chart.meter, chart.difficulty)
        self.simfile = simfile
        self.chart = chart

    def load(self):
        beat_times = []

        note_data = NoteData(self.chart)
        timing_data = TimingData(self.simfile, self.chart)
        for timed_note in time_notes(note_data, timing_data):
            if timed_note.note.note_type != simfile.notes.NoteType.TAP:
                continue
            note_time = float(timed_note.time)
            if note_time in beat_times:
                continue
            beat_times.append(note_time)
            
        self.beat_list = BeatList(beat_times)

class SMParser(BeatInput):
    file_desc = file_desc
    extensions = ['.sm', '.ssc']

    def find_song(self, path):
        if self.song:
            return self.song

        file_base = os.path.dirname(path)
        files = os.listdir(file_base)
        songsearch = fnmatch.filter(files, '*.mp3') + fnmatch.filter(files, '*.ogg')
        if len(songsearch) == 0:
            raise Exception("Song not found for: {}".format(simfile))
        
        return file_base + '/' + songsearch[0]

    def read_file(self, path):
        super().read_file(path)
        mysim = simfile.open(path)

        for c in mysim.charts:
            self.options.append(SMBeatOption(mysim, c))

        self.song = self.find_song(path)


def get_beats(smfile, option=None):
    mysim = simfile.open(smfile)
    
    all_beat_times = []
    for c in mysim.charts:

        if option is not None:
            if c.meter != option['level']:
                continue
            if c.difficulty != option['difficulty']:
                continue

        note_data = NoteData(c)
        timing_data = TimingData(mysim, c)
        for timed_note in time_notes(note_data, timing_data):
            if not timed_note.time in all_beat_times and timed_note.note.note_type == simfile.notes.NoteType.TAP:
                all_beat_times.append(timed_note.time)

    all_beat_times.sort()
    return all_beat_times

def handle_input(simfile, option=None):
    filename, ext = os.path.splitext(simfile)
    if not ext in ['.sm', '.ssc']:
        return False
    
    file_base = os.path.dirname(simfile)
    files = os.listdir(file_base)
    songsearch = fnmatch.filter(files, '*.mp3') + fnmatch.filter(files, '*.ogg')
    if len(songsearch) == 0:
        print("Song not found for: {}".format(simfile))
        return False
    
    song = file_base + '/' + songsearch[0]
    
    return (song, get_beats(simfile, option))
    
def find_input(input):
    files = os.listdir(input)
    simsearch =fnmatch.filter(files, '*.ssc') + fnmatch.filter(files, '*.sm')
    if len(simsearch) == 0:
        return False
        
    return input + '/' + simsearch[0]

def process_input(input, option=None):
    if not os.path.exists(input):
        return False

    if os.path.isfile(input):
        return handle_input(input, option)

    if os.path.isdir(input):
        input = find_input(input)
        if not input:
            return False

    return False

def find_options(input):
    if not os.path.exists(input):
        return False

    if not os.path.isfile(input):
        input = find_input(input)
        if not input:
            return False
    
    filename, ext = os.path.splitext(input)
    if not ext in ['.sm', '.ssc']:
        return False
    
    mysim = simfile.open(input)

    ret = []

    for c in mysim.charts:
        ret.append({
            'level':  c.meter,
            'difficulty': c.difficulty,
            'name': '{} - {} - {}'.format(c.meter, c.difficulty, c.description)
        })

    ret.sort(key=lambda x: x['level'], reverse=False)

    return ret

if __name__ == "__main__":
    reader = SMParser("E:\\Songs\\Hardbass Madness 2\\A Girl From the Internet")
    print(reader.song)