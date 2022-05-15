import util
util.init_app_mode()

import sys

from gooey import Gooey, GooeyParser
from tqdm import tqdm
from plyer import notification

import concurrent.futures
import os
import subprocess
from subprocess import Popen, PIPE, STDOUT
import tempfile

import videoutil
import beatutil
import parsers.parsefs
import parsers.parsetxt

def write_beatfiles(beats, output_name, song_lenth):
    parsers.parsetxt.write_beats(beats, output_name)
    parsers.parsefs.write_beats(beats, output_name)
    beatutil.plot_beats(beats, output_name, song_lenth)

def get_song_length(song):
    result = subprocess.run('ffprobe -v quiet -show_entries format=duration -of csv="p=0" "%s"' % (song), stdout=subprocess.PIPE)
    return float(result.stdout.strip())
    
def process_beats(beats, song_length, clip_dist):
    if beats[0] == 0:
        del beats[0]

    # Push birst beat
    beat_times = [0]

    for b in beats:
        diff = b - beat_times[-1]
        if diff <= clip_dist:
            continue

        beat_times.append(b)  

    # Push last beat
    beat_times.append(song_length)
    
    return beat_times

def detect_input(input):
    return beatutil.find_beats(input, song_required=True)
    
def make_pmv(beatinput, vid_folder, fps, recurse, clip_dist, num_vids, beatbar):
    with util.UHalo(text="Checking input") as h:
        detected_input = detect_input(beatinput)
        if not detected_input:
            h.fail('No usable input detected')
            return False
        else:
            song = detected_input[0]
            song_lenth = get_song_length(song)
            all_beat_times = detected_input[1]
            output_name = os.path.splitext(os.path.basename(song))[0] + '-PMV'
            h.succeed('Input - Song: {} - Beatcount: {}, - Output: {} '.format(song, len(all_beat_times), output_name))

    if not os.path.exists('out'):
        os.mkdir('out')

    output_file = 'out/{}.mp4'.format(output_name)
    
    with util.UHalo(text="Getting and processing beats") as h:
        beats_reduced = process_beats(all_beat_times, song_lenth, clip_dist)
        h.succeed()
    
    videos = videoutil.videos_get(vid_folder, recurse, num_vids)
    if not videos:
        print('No videos')
        return False
    
    clips = videoutil.clips_get(videos, beats_reduced, fps)
    if not clips:
        print('No clips')
        return False

    videos_file = videoutil.clips_generate_batched(clips, fps)
    if not videos_file:
        print('Generating clips failed')
        return False

    if beatbar:
        vid_file_1 = util.get_tmp_file('mp4')
        vid_file_2 = util.get_tmp_file('mp4')

        videoutil.clips_merge(vid_file_1, None, videos_file, song_lenth)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            video_future = executor.submit(videoutil.apply_circles, all_beat_times, vid_file_1, False, vid_file_2, bar_pos=1)
            audio_future = executor.submit(videoutil.apply_beat_sounds, all_beat_times, song, bar_pos=0)

            video_result = video_future.result()
            audio_result = audio_future.result()

            if not video_result or not audio_result:
                return False

            videoutil.video_merge_audio(vid_file_2, audio_result, output_file, song_lenth)
    else:
        videoutil.clips_merge(output_file, song, videos_file, song_lenth)

    with util.UHalo(text="Witing beat files") as h:
        write_beatfiles(all_beat_times, 'out/' + output_name, song_lenth)
        h.succeed()
        
    print(output_name + " is done")
    
    notification.notify(
        title = "Beats2Fun",
        message = output_name + " is done",
        timeout = 5)
    
    return True

@Gooey(progress_regex=r"(?P<current>\d+)/(?P<total>\d+)",
      progress_expr="current / total * 100",
      timing_options = {'show_time_remaining':True},
      default_size=(610, 650),
      image_dir=util.get_resource(''))
def main():
    parser = GooeyParser(description='Make a PMV based on a simfile')
    
    parser.add_argument(
        'beatinput',
        help='Path to input (Chart folder / file / music file)',
        widget='FileChooser',
        metavar="Input",
        gooey_options={
            'message': "Pick your input",
            'wildcard': "Simfile (*.sm,*.ssc)|*.sm;*.ssc|Osu beatmap (*.osu,*.osz)|*.osu;*.osz|Music (*.mp3,*.ogg,*.wav)|*.mp3;*.ogg;*.wav"
        }
    )

    parser.add_argument(
        'vid_folder',
        help='Folder containg your input videos (.mp4, .wmv)',
        widget='DirChooser',
        metavar="Video folder",
        gooey_options={
            'message': "Pick video folder"
        }
    )
    
    parser.add_argument('-recurse', metavar="Search resursive", help='Search videos recursively', action='store_true')
    parser.add_argument('-clip_dist', metavar="Clip distance", default=0.4, help='Minimal clip distance in seconds', type=float, widget='DecimalField')
    parser.add_argument('-fps', metavar="FPS", default=25, help='Output video FPS', type=int, widget='IntegerField')
    parser.add_argument('-num_vids', metavar="Video amount", default=0, help='How many videos to randomly select from the Video folder (0 means all)', type=int, widget='IntegerField')
    parser.add_argument('-beatbar', metavar="Beatbar", help='Add a beatbar to the output video', action='store_true')

    args = parser.parse_args()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        util.current_tmp_dir = tmpdir
        result = make_pmv(**vars(args))
    
    if not result:
        sys.exit(1)
    
if __name__ == "__main__":
    main()