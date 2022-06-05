from classes import VideoPool
from parsers import BeatInput, BeatList, BeatOption
import util
util.init_app_mode()

import sys

from gooey import Gooey, GooeyParser
import argparse
from tqdm import tqdm
from plyer import notification

import concurrent.futures
import os
import re
import subprocess
from subprocess import Popen, PIPE, STDOUT
import tempfile
import time

from classes import *
import videoutil
import beatutil
import parsers.parsefs
import parsers.parsetxt

class Beats2FunTask:
    tasks = []
    output_name = None
    last_output: str
    next_output: str
    
    beat_input: BeatInput
    beat_option: BeatOption
    filtered_beats: BeatList

    length: float
    vctx: VideoContext

    def add_task(self, task, last=False):
        self.tasks.append({'task': task, 'last': last})

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

        self.vctx = VideoContext(
            self.fps,
            self.resolution,
            self.volume,
            self.bitrate,
            self.threads
        )

        self.add_task(self.task_load_beat_input)
        self.add_task(self.task_load_videos)
        self.add_task(self.task_generate_clips)
        self.add_task(self.task_merge_clips, self.volume == 0 and not self.beatbar)
        if self.volume > 0:
            self.add_task(self.task_add_song, not self.beatbar)

        if self.beatbar:
            self.add_task(self.task_add_beatbar, True)

        self.add_task(self.task_generate_beat_files)

    def run(self):
        self.output_task = False
        for t in self.tasks:
            self.output_task = t["last"]
            t["task"]()

    def task_load_beat_input(self):
        self.beat_input = beatutil.find_beatinput(self.beatinput, song_required=True)
        self.beat_option = self.beat_input.get_option(self.level)
        self.beat_option.load()
        self.length = videoutil.get_media_length(self.beat_input.song)
        self.filtered_beats = self.beat_option.beat_list.reduce_beats(self.clip_dist, self.beat_dist).start_end(self.length)
        self.output_name = re.sub('[^A-Za-z0-9\\-\\s_\\[\\]\\(\\)]+', '', self.beat_input.name)

    def task_load_videos(self):
        self.video_pool = VideoPool(self.vid_folder)
        found = self.video_pool.find_videos(self.recurse, self.vctx, self.num_vids)
        print("Found {} videos".format(found))
        self.video_pool.assign_clips(self.filtered_beats, self.vctx)

    def task_generate_clips(self):
        self.last_output = self.video_pool.generate_clips(self.batch, self.vctx)

    def get_next_output(self):
        if self.output_task:
            return self.output_folder + "/" + self.output_name + ".mp4"
        else:
            return util.get_tmp_file("mp4")

    def task_merge_clips(self):
        self.next_output = self.get_next_output()
        if self.volume == 0:
            videoutil.ffmpeg_run([
                '-f concat',
                '-i "{}"'.format(self.last_output),
                '-i "{}"'.format(self.beat_input.song)
            ], None, [
                '-map 0:v',
                '-map 1:a',
                '-c:a aac',
                '-c:v h264_nvenc',
                '"{}"'.format(self.next_output)
            ], expected_length=self.length, description="Merging clips")

        else:
            videoutil.ffmpeg_run([
                '-f concat',
                '-i "{}"'.format(self.last_output),
            ], None, [
                '-c:a aac',
                '-c:v h264_nvenc',
                '"{}"'.format(self.next_output)
            ], expected_length=self.length, description="Merging clips")

        self.last_output = self.next_output

    def task_add_song(self):
        self.next_output = self.get_next_output()

        videoutil.ffmpeg_run([
            '-i "{}"'.format(self.last_output),
            '-i "{}"'.format(self.beat_input.song)
        ], ["[0:a][1:a]amix=inputs=2:weights={} 1[ma]".format(self.volume)], [
            '-map 0:v',
            '-map [ma]',
            '-c:a aac',
            '-c:v copy',
            '"{}"'.format(self.next_output)
        ], expected_length=self.length, description="Adding music")

        self.last_output = self.next_output

    def task_add_beatbar(self):
        self.next_output = self.get_next_output()
        tmp_vid = util.get_tmp_file('mp4')

        with concurrent.futures.ThreadPoolExecutor() as executor:

            video_future = executor.submit(videoutil.apply_circles, self.beat_option.beat_list.beats, self.last_output, False, tmp_vid, bar_pos=0)
            audio_future = executor.submit(videoutil.apply_beat_sounds, self.beat_option.beat_list.beats, self.beat_input.song, bar_pos=1, beat_sound=self.beatbar_sound, beat_volume=self.beatbar_volume)

            video_result = video_future.result()
            audio_result = audio_future.result()

            if not video_result or not audio_result:
                raise Exception("Adding beatbar failed")

        videoutil.ffmpeg_run([
            '-i "{}"'.format(tmp_vid),
            '-i "{}"'.format(audio_result)
        ], [], [
            '-map 0:v',
            '-map 1:a',
            '-c:a copy',
            '-c:v copy',
            '"{}"'.format(self.next_output)
        ], expected_length=self.length, description="Merging beat video and beat audio")

        self.last_output = self.next_output

    def task_generate_beat_files(self):
        parsers.parsetxt.TXTParser.write_file(self.beat_option, self.output_folder + "/" + self.output_name)
        parsers.parsefs.FSParser.write_file(self.beat_option, self.output_folder + "/" + self.output_name)
        # beatutil.plot_beats(self.all_beats, self.output_folder + self.output_name, self.length)

@Gooey(tabbed_groups=True,
      required_cols=1,
      optional_cols=2,
      progress_regex=r"(?P<current>\d+)/(?P<total>\d+)",
      progress_expr="current / total * 100",
      timing_options = {'show_time_remaining':True},
      default_size=(550, 650),
      image_dir=util.get_resource(''))
def main():
    parser = GooeyParser(
        description='Make a PMV based on a simfile',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'beatinput',
        help='Path to input, chart folder / file / music file',
        widget='FileChooser',
        metavar="Input",
        gooey_options={
            'message': "Pick your input",
            'wildcard': "Simfile (*.sm,*.ssc)|*.sm;*.ssc|Osu beatmap (*.osu,*.osz)|*.osu;*.osz|Music (*.mp3,*.ogg,*.wav)|*.mp3;*.ogg;*.wav"
        }
    )

    parser.add_argument(
        'vid_folder',
        help='Folder containg your input videos, .mp4, .wmv, .... Use multiple folder by splitting them with folder1;folder2;folder3',
        widget='DirChooser',
        metavar="Video folder",
        gooey_options={
            'message': "Pick video folder"
        }
    )
    
    parser.add_argument(
        '-output_folder',
        help='Where to store the output videos / scripts',
        widget='DirChooser',
        metavar="Output folder",
        default="out",
        gooey_options={
            'message': "Pick output folder"
        }
    )

    parser.add_argument('-num_vids',    metavar="Video amount",     default=0, help='How many videos to randomly select from the Video folder, 0=all', type=int, widget='IntegerField')
    parser.add_argument('-recurse',     metavar="Search resursive", help='Search videos recursively', action='store_true')
    parser.add_argument('-clip_dist',   metavar="Clip distance",    default=0.4, help='Minimal clip distance in seconds', type=float, widget='DecimalField')
    parser.add_argument('-beat_dist',   metavar="Beat distance",    type=float)
    parser.add_argument('-volume',      metavar="Clip volume",      default=0.0, help='Keep the original clip audio', type=float, widget='DecimalField')
    parser.add_argument('-level',       metavar="Chart level",      default='min', help='What difficilty to pick from the chart, min/max/LEVEL', type=str)

    beatbar_group = parser.add_argument_group("BeatBar Options")
    beatbar_group.add_argument('-beatbar',         metavar="Beatbar",          help='Add a beatbar to the output video', action='store_true')
    beatbar_group.add_argument('-beatbar_sound',   metavar="Beatbar sound",    help='What sound effect to use (none to disable)', default='beat')
    beatbar_group.add_argument('-beatbar_volume',  metavar="Beatbar volume",   help='Beat sound volume multiplier (db)', default=0, type=float, widget='DecimalField')

    quality_group = parser.add_argument_group("Quality Options")   
    quality_group.add_argument('-fps',         metavar="FPS",              default=25, help='Output video FPS', type=int, widget='IntegerField')
    quality_group.add_argument('-resolution',  metavar="Resolution",       default='1280:720', help='Output video Resolution')
    quality_group.add_argument('-bitrate',     metavar="Bit rate",         default='3M', help='Output video bitrate, higher numer is higher quality')
    
    performance_group = parser.add_argument_group("Performance Options")
    performance_group.add_argument('-batch',       metavar="Batch size",       default=10, type=int, help='How many clips to split per thread', widget='IntegerField')
    performance_group.add_argument('-threads',     metavar="Thread count",     default=4, type=int, help='How many threads to use while generating', widget='IntegerField')
    performance_group.add_argument('-cuda',        metavar="GPU Acceleration", help='Use Nvidia GPU Acceleration', action='store_true')
    performance_group.add_argument('-pre_seek',    metavar="Seek buffer", default=0,   help='Use when clips start forzen', type=int)
    performance_group.add_argument('-debug',       metavar="Debug", help='Show debug messages', action='store_true')

    
    if util.app_mode == 'pre_goo':
        parser.set_defaults(**util.config_load('Beats2Fun.last'))

    args = parser.parse_args()

    if util.app_mode == 'goo':    
        util.config_save('Beats2Fun.last', vars(args))

    if args.cuda and args.batch > 1:
        print("When using cuda, '-batch 1' is required")
        sys.exit(1)

    pts = args.resolution.split(':')
    if len(pts) != 2 or (int(pts[0]) %2) > 0 or (int(pts[1]) %2) > 0:
        print("Unusable resolution: {}".format(args.resolution))
        sys.exit(1)
    
    #with tempfile.TemporaryDirectory() as tmpdir:
    util.current_tmp_dir = 'tmp'
    start_time = time.time()
    # result = make_pmv(**vars(args))

    if args.debug:
        util.debug_flag = True

    runner = Beats2FunTask(**vars(args))

    try:
        runner.run()
    except BaseException as e:
        if util.debug_flag:
            raise e
        else:
            print("An error occured: {}".format(str(e)))
        sys.exit(1)

    print(runner.last_output + " is done")
    try:
        notification.notify(
            title = "Beats2Fun",
            message = runner.last_output + " is done",
            timeout = 5)
    except:
        pass

    if util.app_mode != 'goo':
        print('Generation took: {}'.format(videoutil.timestamp(time.time() - start_time)))
    print('Cleanup ...')
    
if __name__ == "__main__":
    main()