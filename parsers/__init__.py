import os
#from .. import util

class Beat:
    start: float
    end: float
    duration: float
    index: int

    def __init__(self, start, end, index):
        if start >= end:
            raise Exception("Start can not be after end")

        self.start = start
        self.end = end
        self.duration = end - start
        self.index = index
        
class BeatList:
    beats: list
    max_speed = 530

    def __init__(self, beat_times):
        self.beats = []
        
        for i,b in enumerate(beat_times[:-1]):
            next_beat = beat_times[i+1]
            self.beats.append(Beat(b, next_beat, i))
    
    def start_end(self, length):
        new_beats = []
        if self.beats[0].start != 0:
            new_beats.append(0)
        
        for i,beat in enumerate(self.beats):
            new_beats.append(beat.start)

        if new_beats[-1] != length:
            new_beats.append(length)
        
        return BeatList(new_beats)

    def reduce_beats(self, min_distance=0.4):
        new_beats = [self.beats[0].start]
        last_beat = self.beats[0]

        for i,beat in enumerate(self.beats):
            if beat.start - last_beat.start < min_distance:
                continue
            
            new_beats.append(beat.start)
            last_beat = self.beats[i-1]

        return BeatList(new_beats)

    def get_density(self, width=100, length=None):
        values = [0 for i in range(width)]
        if length == None:
            length = self.beats[-1].end

        for b in self.beats:
            speed = 80 / b.duration # length / duration
            speed = util.clamp(speed / self.max_speed, 0, 1)
            
            index = round(b / length * (width-1))
            if values[index] == 0:
                values[index] += speed
                values[index] /= 2
            else:
                values[index] = speed
        
        return values

class BeatOption:
    level = -1
    version = ''
    name = ''
    beat_list = None
    
    def __init__(self, level, version):
        self.level = level
        self.version = version
        self.name = '{} - {}'.format(self.level, self.version)

class BeatInput:
    path = None
    song = None
    extensions = []
    options = []
    file_desc = ''

    def __init__(self, path):
        if not os.path.exists(path):
            raise Exception("{} does not exist".format(path))
        self.path = path

        if os.path.isdir(path):
            self.read_dir(path)
        if os.path.isfile(path):
            self.read_file(path)

    @classmethod
    def supports_input(cls, path):
        if not os.path.exists(path):
            return False

        if os.path.isfile(path):
            filename, ext = os.path.splitext(path)
            return ext in cls.extensions
        
        files = os.listdir(path)
        for f in files:
            filename, ext = os.path.splitext(f)
            if ext in cls.extensions:
                return True

        return False

    @staticmethod
    def write_file(option, path):
        raise Exception("Not implemented")

    def get_option(self, level=None):
        if level in ['min', 'max']:
            self.options.sort(key=lambda x: x.level)
            if level == 'max':
                return self.options[-1]
            if level == 'min':
                return self.options[0]


        for o in self.options:
            if level and level != str(o.level):
                continue
            return o

        raise Exception("Level {} not found for chart {}".format(level, self.path))

    def read_dir(self, path):
        files = os.listdir(path)
        for f in files:
            for e in self.extensions:
                if f.endswith(e):
                    self.read_file(path + '/' + f)

    def read_file(self, path):
        filename, ext = os.path.splitext(path)
        if ext not in self.extensions:
            raise Exception("{} not supported for beat reading".format(path))