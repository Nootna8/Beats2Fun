import simfile
from simfile.notes import NoteData
from simfile.timing import Beat, TimingData
from simfile.notes.timed import time_notes
import simfile.notes

import os
from glob import glob
import fnmatch

file_desc = 'StepMania simfile (*.sm, *.ssc)|*.sm;*.ssc"'

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