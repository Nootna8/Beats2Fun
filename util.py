import tempfile
import os
import sys
import io

from os.path import dirname, abspath

from contextlib import contextmanager
from halo import Halo
from tqdm import tqdm

current_tmp_dir = False
global app_mode
app_mode = None

def get_tmp_file(ext):
    if not current_tmp_dir:
        raise "No tmp dir set"

    temp_name = next(tempfile._get_candidate_names())
    return os.path.realpath(os.path.join(current_tmp_dir, temp_name + '.' + ext))

def get_tmp_dir():
    if not current_tmp_dir:
        raise "No tmp dir set"
    return current_tmp_dir

def init_app_mode():
    global app_mode
    app_mode = 'plain'

    if "--ignore-gooey" in sys.argv:
        app_mode = 'goo'
    elif len(sys.argv) >= 2:
        sys.argv.append("--ignore-gooey")

def get_app_mode():
    return app_mode

def UHalo(**args):
    spinner = 'dots'
    if app_mode == 'goo':
        spinner = {'interval': 1000, 'frames': ['.', '. .', '. . .']}

    return Halo(spinner=spinner, **args)

tout = None

class Utqdm(tqdm):
    def __init__(self, iterable=None, **args):
        if app_mode == 'goo':
            super().__init__(iterable=iterable, **args, ascii=True)
        else:
            super().__init__(iterable=iterable, **args)
            
        #tout = io.StringIO()
        
        #if app_mode != 'goo':
        #    super().__init__(iterable=iterable, **args)
        #else:
        #    super().__init__(iterable=iterable, **args, file=tout)

    def __del__(self):
        #tout.close()
        #tout = None
        super().__del__()

def handle_tqdm_out():
    if tout:
        tout.seek(0)
        text = tout.read().strip()
        tout.truncate(0)
        if len(text) > 2:
            print(text)

def clamp(n, smallest, largest): 
    return max(smallest, min(n, largest))
    
def get_resource(name):
    d = dirname(abspath(__file__))
    ret = os.path.realpath(d  + "/Resources/" + name)
    return ret
