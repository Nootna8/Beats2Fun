import os
import json
from . import BeatInput, BeatOption, BeatList

file_desc = 'Funscript (*.funscript, *.json)|*.funscript;*.json"'

class FSParser(BeatInput):
    file_desc = file_desc
    extensions = ['.funscript', '.json']

    def __init__(self, path):
        if not os.path.exists(path):
            raise Exception("{} does not exist".format(path))
        self.path = path

        if os.path.isfile(path):
            self.read_file(path)

    def read_file(self, path):
        super().read_file(path)

        with open(input) as f:
            data = json.load(f)
            f.close()
            if 'actions' in data:
                beats = list(map(lambda b: b['at'] / 1000, data['actions']))

        if len(beats) > 0:
            option = BeatOption(-1, '')
            option.beat_list = BeatList(beats)
            self.options.append(option)

    @staticmethod
    def write_file(option, path):
        funscript = {
            'version': '1.0',
            'inverted': False,
            'range': 90,
            'actions': []
        }

        flag = True
        for b in option.beat_list.beats:
            pos = 10
            if flag:
                pos = 90

            flag = not flag

            funscript['actions'].append({
                'at': round(b.start * 1000),
                'pos': pos
            })

        with open(path + '.funscript', 'w') as fs:
            fs.write(json.dumps(funscript))
            fs.close()

def process_input(input, option=None):
    filebase, ext = os.path.splitext(input)
    
    if ext != '.funscript':
        input = filebase + '.funscript'
        if not os.path.isfile(input):
            return False

    with open(input) as f:
        data = json.load(f)
        f.close()
        if 'actions' in data:
            beats = list(map(lambda b: b['at'] / 1000, data['actions']))
            if len(beats) > 0:
                return (None, beats)

    return False

def find_options(input):
    if os.path.isfile(input):
        base = os.path.basename(input)
        filename, ext = os.path.splitext(base)

        return [{
            'level': 0,
            'name': filename
        }]
        files = os.listdir(input)
        fssearch =fnmatch.filter(files, '*.funscript')
    
    return False

def write_beats(beats, output_name):
    funscript = {
        'version': '1.0',
        'inverted': False,
        'range': 90,
        'actions': []
    }

    flag = True
    for b in beats:
        pos = 10
        if flag:
            pos = 90

        flag = not flag

        funscript['actions'].append({
            'at': round(b * 1000),
            'pos': pos
        })

    with open(output_name + '.funscript', 'w') as fs:
        fs.write(json.dumps(funscript))
        fs.close()