import os

file_desc = 'Beat txt (*.txt)|*.txt"'

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