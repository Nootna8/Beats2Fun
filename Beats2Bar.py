import util
util.init_app_mode()

import sys
import os

import concurrent.futures
from gooey import Gooey, GooeyParser
import tempfile

import util
import videoutil
import beatutil
from pydub import AudioSegment
from pydub.utils import audioop
    
    
def apply_beatbar(beats, video, beat_sound, output, video_length):
    if beat_sound == 'none':
        beat_sound = None

    if not output:
        base,ext = os.path.splitext(video)
        output = base + '-bar.mp4'

    if beat_sound:
        vid_file = util.get_tmp_file('mp4')

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:    
            vid_file = util.get_tmp_file('mp4')
            video_future = executor.submit(videoutil.apply_circles, beats, video, False, vid_file, video_length, bar_pos=1)
            audio_future = executor.submit(videoutil.apply_beat_sounds, beats, video, beat_sound, input_length=video_length, bar_pos=0)

            video_result = video_future.result()
            audio_result = audio_future.result()

            if not video_result:
                print('Vid failed')
                return False

            if not audio_result:
                print('Audio failed')
                return False

            videoutil.video_merge_audio(vid_file, audio_result, output, video_length)
            
    else:
        result = videoutil.apply_circles(beats, video, True, output, video_length)
        if not result:
            return False
    
    return True
    
def run(args):
    with util.UHalo(text="Finding beats") as h:
        beats = beatutil.find_beats(args.video)
        if not beats:
            h.fail('No beats found')
            return False
        beats = beats[1]
        h.succeed()
        
    with util.UHalo(text="Fetching video length") as h:
       video_length = videoutil.get_media_length(args.video)
       h.succeed()
    
    result = apply_beatbar(beats=beats, video_length=video_length, **vars(args))
    if not result:
        print('Applying beatbar failed')
        return False
    
    return True

@Gooey(progress_regex=r"(?P<current>\d+)/(?P<total>\d+)",
      progress_expr="current / total * 100",
      timing_options = {'show_time_remaining':True},
      default_size=(610, 650),
      image_dir=util.get_resource(''))
def main():
    parser = GooeyParser(description='Add a beatbar to a music video')
    
    parser.add_argument(
        'video',
        help='Path to into video',
        widget='FileChooser',
        metavar="Input",
        gooey_options={
            'message': "Pick your video",
            'wildcard': "Video ({})|{}".format(', '.join(videoutil.video_formats), ';'.join(videoutil.video_formats))
        }
    )

    parser.add_argument(
        'output',
        help='Where to store the resulting video',
        widget='FileChooser',
        metavar="Output",
        default='',
        nargs='?',
        gooey_options={
            'message': "Select the output video file",
            'wildcard': "Video ({})|{}".format(', '.join(videoutil.video_formats), ';'.join(videoutil.video_formats))
        }
    )
    
    parser.add_argument('-beat_sound', metavar="Beat sound", help='Sound effect to play on each beat (make empty or select "none" to disable)', default='beat')
    
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmpdir:
        util.current_tmp_dir = tmpdir
        result = run(args)
    
    if not result:
        sys.exit(1)
    
if __name__ == "__main__":
    main()