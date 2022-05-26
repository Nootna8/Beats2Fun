import os
from . import BeatInput, BeatOption, BeatList

file_desc = 'Beat txt (*.txt)|*.txt"'
class TXTParser(BeatInput):
    file_desc = file_desc
    extensions = ['.txt', '.ssc']

    def __init__(self, path):
        if not os.path.exists(path):
            raise Exception("{} does not exist".format(path))
        self.path = path

        if os.path.isfile(path):
            self.read_file(path)

    def read_file(self, path):
        super().read_file(path)
        with open(input) as f:
            beats = list(map(lambda x: float(x.strip()), f.readlines()))

        if len(beats) > 0:
            option = BeatOption(-1, '')
            option.beat_list = BeatList(beats)
            self.options.append(option)

    @staticmethod
    def write_file(option, path):
        with open(path + ".txt", 'w') as b:
            for beat in option.beat_list.beats:
                b.write(str(beat.start) + "\n")

def process_input(input, option=None):
    if not os.path.isfile(input):
        return False
    filebase, ext = os.path.splitext(input)
    
    if ext != '.txt':
        input = filebase + '.txt'
        if not os.path.isfile(input):
            return False

    with open(input) as f:
        beats = list(map(lambda x: float(x.strip()), f.readlines()))
        f.close()
        if len(beats) > 0:
            return beats

    return False

def find_options(input):
    return False

def write_beats(beats, output_name):
    with open(output_name + ".txt", 'w') as b:
        b.write("\n".join(map(str, beats)))
        b.close()