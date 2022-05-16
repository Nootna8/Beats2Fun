import tempfile
import os
import sys
import io

from os.path import dirname, abspath

from contextlib import contextmanager
from halo import Halo
import tqdm
import tqdm.utils

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

    custom_ffpmeg = os.path.realpath(os.curdir + '/ffmpeg')
    if os.path.isdir(custom_ffpmeg):
        os.environ["PATH"] += os.pathsep + custom_ffpmeg

def get_app_mode():
    return app_mode

def UHalo(**args):
    spinner = 'dots'
    placement = 'left'
    if app_mode == 'goo':
        spinner = {'interval': 1000, 'frames': ['.', '. .', '. . .']}
        placement = 'right'

    return Halo(spinner=spinner, placement=placement, **args)

tout = None

class Utqdm(tqdm.tqdm):
    def __init__(self, *args, **kwargs):
        
        kwargs = kwargs.copy()
        
        if app_mode == 'goo':
            kwargs['ascii'] = True
            kwargs['ncols'] = 80
            kwargs['gui'] = True
            kwargs['bar_format'] = "{desc}:{percentage:3.0f}% {r_bar}"
        else:
            kwargs['bar_format'] = "{desc:<30}{percentage:3.0f}%|{bar:50}{r_bar}"

        super(Utqdm, self).__init__(*args, **kwargs)

        if app_mode == 'goo':
            self.sp = self.u_status_printer(self.fp)

    @staticmethod
    def u_status_printer(file):
        fp = file
        fp_flush = getattr(fp, 'flush', lambda: None)  # pragma: no cover
        if fp in (sys.stderr, sys.stdout):
            getattr(sys.stderr, 'flush', lambda: None)()
            getattr(sys.stdout, 'flush', lambda: None)()

        def fp_write(s):
            fp.write(tqdm.utils._unicode(s))
            fp_flush()

        last_len = [0]

        def print_status(s):
            len_s = tqdm.utils.disp_len(s)
            fp_write('\n' + s + (' ' * max(last_len[0] - len_s, 0)))
            last_len[0] = len_s

        return print_status


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
