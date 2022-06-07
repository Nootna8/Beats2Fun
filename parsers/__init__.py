import os
import random
class Beat:
    start: float
    end: float
    duration: float
    index: int
    beat_nr: int

    def __init__(self, start, end, index, beat_nr=None):
        if start >= end:
            raise Exception("Start time: {} is bigger then end time {}".format(start, end))

        self.start = start
        self.end = end
        self.duration = end - start
        self.index = index
        self.beat_nr = beat_nr
        
class BeatList:
    beats: list
    max_speed = 530

    def __init__(self, beat_times, beat_nrs=None):
        self.beats = []
        
        for i,b in enumerate(beat_times[:-1]):
            next_beat = beat_times[i+1]
            beat_nr = None
            if beat_nrs:
                beat_nr = beat_nrs[i]
            self.beats.append(Beat(b, next_beat, i, beat_nr))
    
    def start_end(self, length):
        new_beats = []
        new_beat_nrs = []
        
        if self.beats[0].start != 0:
            new_beats.append(0)
            new_beat_nrs.append(None)
        
        for i,beat in enumerate(self.beats):
            new_beats.append(beat.start)
            new_beat_nrs.append(beat.beat_nr)

        if new_beats[-1] != length:
            new_beats.append(length)
            new_beat_nrs.append(None)
        
        return BeatList(new_beats, new_beat_nrs)

    def reduce_beats(self, min_distance=0.4, beat_dist=None):
        new_beats = [self.beats[0].start]
        new_beat_nrs = [self.beats[0].beat_nr]

        for beat in self.beats[1:]:
            if beat_dist and beat.beat_nr and beat.beat_nr % beat_dist == 0:
                new_beats.append(beat.start)
                new_beat_nrs.append(beat.beat_nr)
                continue

            if beat.start - new_beats[-1] > min_distance:
                new_beats.append(beat.start)
                new_beat_nrs.append(beat.beat_nr)
                continue

        return BeatList(new_beats, new_beat_nrs)

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
    level: float
    version: str
    name: str
    beat_list: BeatList
    
    def __init__(self, level, version):
        self.level = level
        self.version = version
        self.name = '{} - {}'.format(self.level, self.version)

class BeatInput:
    path: str
    song: str
    extensions = []
    options: list[BeatOption]
    file_desc = ''
    name: str

    def __init__(self, path):
        if not os.path.exists(path):
            raise Exception("{} does not exist".format(path))
        self.path = path
        self.options = []

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
        if level in ['min', 'max', 'rnd']:
            self.options.sort(key=lambda x: x.level)
            if level == 'max':
                return self.options[-1]
            if level == 'min':
                return self.options[0]
            if level == 'rnd':
                random.shuffle(self.options)
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