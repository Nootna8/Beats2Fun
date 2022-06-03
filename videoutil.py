import re
import subprocess
from subprocess import Popen, PIPE, STDOUT
from concurrent.futures import ThreadPoolExecutor
import datetime

import os
import sys
from glob import glob
import fnmatch
import math
import random
from turtle import position
from matplotlib.pyplot import title

import util

from pydub import AudioSegment
from pydub.utils import audioop

import util

video_formats = ['.mp4', '.wmv', '.mov', '.m4v', '.mpg', '.avi', '.flv']

def ffmpeg_run(pts_in, filters, pts_out, silent = True, expected_length = 0, description = None, bar_pos=None, block=True):
    cmd_pts = ['ffmpeg', '-hide_banner -y'] + pts_in
    
    if filters:
        if len(filters) > 10:
            filters_file = util.get_tmp_file('txt')
            with open(filters_file, 'w') as tf:
                tf.write(';\n'.join(filters))
            cmd_pts.append('-filter_complex_script "{}"'.format(filters_file))    
        else:
            cmd_pts.append('-filter_complex "{}"'.format(';'.join(filters)))
        
    cmd_pts += pts_out
    cmd = ' '.join(cmd_pts)
    retcode = -1
    output = []

    # if util.debug_flag:
        # print(cmd)

    try:
        error_msg = None
        
        if not silent:
            print(cmd)
            os.system(cmd)
            return True

        pbar = None
        last_pos = 0
        if expected_length:
            bar_end = math.ceil(expected_length)
            pbar = util.Utqdm(total=math.ceil(expected_length), desc=description, position=bar_pos)
        
        regx = re.compile(r"time=([\d\:\.]+)")

        if not block:
            print(cmd)
            with subprocess.Popen(cmd) as p:
                p.wait()
                retcode = p.returncode
                if retcode != 0 and not error_msg:
                    error_msg = "Invalid return code"
        else:
            with subprocess.Popen(cmd, stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True) as p:
                for l in p.stdout:
                    if 'No decoder surfaces left' in l:
                        p.terminate()
                        error_msg = l
                    if 'Error' in l:
                        p.terminate()
                        error_msg = l
                    
                    output.append(l)
                    
                    status_line = regx.search(l)
                    if status_line and pbar:
                        current_time = from_timestamp(status_line[1])
                        newseconds = round(current_time - last_pos)
                        pbar.update(newseconds)
                        last_pos += newseconds

                p.wait()
                retcode = p.returncode
                if retcode != 0 and not error_msg:
                    error_msg = "Invalid return code"

        if error_msg:
            raise Exception(error_msg)

        if pbar and last_pos != bar_end:
            pbar.update(bar_end - last_pos)
        
    except BaseException as e:
        if retcode == 255:
            raise Exception("Canceled")

        print("Exception during ffmpeg: {}, Errorcode: {}, Output: {}".format(cmd, retcode, "\n".join(output)))
        raise e

def ffprobe_run(pts_in):
    cmd_pts = ['ffprobe', '-v error'] + pts_in
    cmd = ' '.join(cmd_pts)
    retcode = -1

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        retcode = result.returncode
        if retcode != 0:
            raise Exception("Invalid return code")
        return result.stdout.strip().decode("utf-8")
    except BaseException as e:
        print("Exception during ffprobe: {}, Errorcode: {}".format(cmd, retcode))
        raise e

def videos_get(vid_folder, vids_deep, num_vids, num_threads=4):
    videos = []

    for vf in vid_folder.split(';'):
        if vids_deep:
            for root, dirs, files in os.walk(vf):
                for f in files:
                    for ext in video_formats:
                        if f.endswith(ext):
                            videos.append(vf + '/' + f)
        else:
            for f in os.listdir(vf):
                for ext in video_formats:
                    if f.endswith(ext):
                        videos.append(vf + '/' + f)
        

        

        #for ext in video_formats:
        #    matches = list(fnmatch.filter(files, '*' + ext))
        #    for m in matches:
        #        videos.append(vf + '/' + m)
            #videos += glob(vf + "/*" + ext)
            #if vids_deep:
            #    videos += glob(vf + "/**/*" + ext, recursive=True)
        
    if num_vids > 0:
        random.shuffle(videos)
        videos = videos[:num_vids]
    
    print('Found {} videos'.format(len(videos)))
    
    video_states = []
    
    with util.Utqdm(total=len(videos), desc="Video clip analasys") as pbar:
        def callback(result):
            pbar.update()
            util.handle_tqdm_out()
                    
        futures = []
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for v in videos:
                future = executor.submit(videos_analyze_thread, {'video': v})
                future.add_done_callback(callback)
                futures.append(future)

            for future in futures:
                try:
                    r = future.result()
                    if r:
                        video_states.append(r)
                except BaseException as e:
                    for f in futures:
                        f.cancel()
                    raise e
            

    random.shuffle(video_states)
    return video_states

def get_media_length(input):
    return float(ffprobe_run(['-show_entries format=duration', '-of csv="p=0"', '-i "{}"'.format(input)]))

def videos_analyze_thread(v):
    start_skip = 10
    end_skip = 10

    try:
        result = ffprobe_run([
            '-select_streams v',
            '-show_entries format=duration',
            '-show_entries stream=width,height',
            '-of csv="p=0"',
            '-i "{}"'.format(v['video'])
        ]).split("\n")
        resolution = list(map(int, result[0].strip().split(',')))
        length = float(result[1].strip())
        
        
    except BaseException as e:
        print('Failed analyzing video: {}'.format(v['video']))
        raise e

    ret = {
        'full_length': length,
        'start_at': start_skip,
        'end_at': length - end_skip,
        'usable_length': length - start_skip - end_skip,
        'video': v['video'],
        'width': resolution[0],
        'height': resolution[1]
    }
        
    return ret
    
def clips_get(videos, beats, fps, volume):
    frame_time = 1 / fps
    video_index = 0
    beat_clips = []
    framenr = 0

    output_length = beats[-1]

    for v in videos:
        v['clips'] = []
    
    for beat_index in util.Utqdm(range(len(beats) - 1), desc="Clip assignment"):
        beat_start = beats[beat_index]
        beat_end = beats[beat_index + 1]
        beat_duration = beat_end - beat_start

        last_frame_time = framenr * frame_time
        missing_frames = math.floor((beat_end - last_frame_time) / frame_time)

        if video_index >= len(videos):
            video_index = 0
            random.shuffle(videos)

        video_state = videos[video_index]
        video_index += 1

        beat_pos = beat_start / output_length

        found = False
        tries = len(videos)
        while not found:
            if tries <= 0:
                print("Failed finding clip for beat: {} - {}".format(beat_start, beat_end))
                return False

            beat_pos_osffset = util.clamp(beat_pos + (random.random() * 0.2 - 0.1), 0, 1)

            clip_start = video_state['start_at'] + (video_state['usable_length'] * beat_pos_osffset)
            clip_end = clip_start + beat_duration

            if clip_end > video_state['full_length']:
                video_index += 1
                if video_index >= len(videos):
                    video_index = 0
                video_state = videos[video_index]
                tries -= 1
                continue
            
            for c in video_state['clips']:
                if c['clip_start'] >= clip_start and c['clip_end'] <= clip_start:
                    video_index += 1
                    if video_index >= len(videos):
                        video_index = 0
                    video_state = videos[video_index]
                    tries -= 1
                    continue

                if c['clip_start'] >= clip_end and c['clip_end'] <= clip_end:
                    video_index += 1
                    if video_index >= len(videos):
                        video_index = 0
                    video_state = videos[video_index]
                    tries -= 1
                    continue
            
            found = True
                

        clip = {
            'index': beat_index,

            'beat_start': beat_start,
            'beat_end': beat_end,
            'duration': beat_duration,
            
            'video': video_state['video'],
            'video_state': video_state,
            'clip_start': clip_start,
            'clip_end': clip_end,
            
            'frame': framenr,
            'framecount': missing_frames,
            'volume': volume
        }

        beat_clips.append(clip)
        video_state['clips'].append(clip)
        framenr += missing_frames
        
        util.handle_tqdm_out()
        
        # TODO scene detection
    
    return beat_clips

def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def clips_generate_batched(beat_clips, fps, resolution, bitrate='3M', batch_size=10, num_threads=4, cuda=False, pre_seek=0):
    videos_file_name = util.get_tmp_file('txt')
    videos_file = open(videos_file_name, 'w')
    
    frame_time = 1 / fps
    video_clips = {}
    for i,b in enumerate(beat_clips):
        videos_file.write("file '{}.mp4'\n".format(i))

        if b['video'] not in video_clips:
            video_clips[b['video']] = []
        video_clips[b['video']].append(b)

    batches = []

    for v,all_clips in video_clips.items():
        all_clips.sort(key=lambda x: x['clip_start'])
        for clips in batch(all_clips, batch_size):
            
            #can_cuda = cuda
            #if can_cuda and clips[0]['video_state']['width'] > 4096:
            #    can_cuda = False

            batches.append({
                'video': v,
                'clips': clips,
                'fps': fps,
                'resolution': resolution,
                'bitrate': bitrate,
                'cuda': cuda,
                'pre_seek': pre_seek
            })

    videos_file.close()

    threaded = True
        
    with util.Utqdm(total=len(batches), desc="Splitting videos") as pbar:
        futures = []

        def callback(result):
            pbar.update()


        if not threaded:
            for c in batches:
                callback(clips_generate_batched_thread(c))
                pbar.update()
                return False
        else:

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                
                shared_vars = {}

                if cuda:
                    shared_vars['cuda_sessions'] = 0

                for c in batches:
                    future = executor.submit(clips_generate_batched_thread, c, shared_vars)
                    future.add_done_callback(callback)
                    futures.append(future)

                for future in futures:
                    try:
                        res = future.result()
                    except BaseException as e:
                        for f in futures:
                            f.cancel()
                        raise e

    return videos_file_name


def clips_generate_batched_thread(myargs, shared_vars):
    cmd_in = []
    cmd_out = []

    cuda_dec = myargs['cuda']
    cuda_enc = myargs['cuda']

    if cuda_enc and shared_vars['cuda_sessions'] >= 3:
        cuda_enc = False
    if cuda_dec and myargs['clips'][0]['video_state']['width'] > 4096:
        cuda_dec = False

    if not cuda_enc and not cuda_dec:
       myargs['cuda'] = False 
    
    if cuda_enc:
        shared_vars['cuda_sessions'] = shared_vars['cuda_sessions'] + 1

    if cuda_dec:
        cmd_in += ['-hwaccel cuda', '-hwaccel_output_format cuda']
    if myargs['cuda']:
        cmd_in.append('-extra_hw_frames 12')

    for i,c in enumerate(myargs['clips']):
        cmd_in += [
            '-ss {}'.format(timestamp(max(0, c['clip_start'] - myargs['pre_seek']))),
            '-t {}'.format(c['duration'] + myargs['pre_seek'] + 0.5),
            '-i "{}"'.format(myargs['video']),
        ]

        if myargs['pre_seek']:
            cmd_in.append('-ss {}'.format(timestamp(myargs['pre_seek'])))

        filters = [
            'fps={}'.format(myargs['fps'])
        ]

        if myargs['cuda']:
            if not cuda_dec:
                filters.append('format=nv12,hwupload_cuda')

            filters.append('scale_cuda={}:force_original_aspect_ratio=1'.format(myargs['resolution']))

            if not cuda_enc:
                filters.append('hwdownload,format=nv12')
                
            #'hwdownload,format=nv12',
            #'pad={}:(ow-iw)/2:(oh-ih)/2'.format(myargs['resolution'])
            
        else:
            filters += [
                'scale={}:force_original_aspect_ratio=1'.format(myargs['resolution']),
                'pad={}:(ow-iw)/2:(oh-ih)/2'.format(myargs['resolution'])
            ]

        cmd_out += [
            '-vf "{}"'.format(','.join(filters)),
            '-map {}:v'.format(i),
            '-vframes {}'.format(c['framecount']),
            #'-vsync cfr',
            #'-video_track_timescale 60000'
        ]

        if c['volume'] > 0:
            cmd_out += [
                '-af atrim=duration={}'.format((1/myargs['fps'])*c['framecount']),
                '-map {}:a'.format(i),
                '-c:a aac',
                '-b:a 192k'
            ]

        if cuda_enc:
            cmd_out.append('-c:v h264_nvenc')
            
        cmd_out +=[
            '-b:v {}'.format(myargs['bitrate']),
            '{}/{}.mp4'.format(util.get_tmp_dir(), c['index'])
        ]
    
    ffmpeg_run(cmd_in, None, cmd_out, True)

    for c in myargs['clips']:
        clip_out = '{}/{}.mp4'.format(util.get_tmp_dir(), c['index'])
        if not os.path.isfile(clip_out):
            raise Exception("Failed splitting {}, {} was not found".format(myargs['video'], clip_out))

        framecount = int(ffprobe_run([
            '-select_streams v:0',
            '-count_packets',
            '-show_entries stream=nb_read_packets',
            '-of csv=p=0',
            '-i "{}"'.format(clip_out)]
        ))

        if framecount != c['framecount']:
            raise Exception("{} has {} frames instead of the requestes {}".format(clip_out, framecount, c['framecount']))

    if cuda_enc:
        shared_vars['cuda_sessions'] = max(0, shared_vars['cuda_sessions'] - 1)
    
    return myargs


def clips_merge(output, audio, vids_file, expected_length):
    cmd_in = [
        '-f concat',
        '-i "{}"'.format(vids_file)
    ]

    if audio:
        cmd_in.append('-i "{}"'.format(audio))

    filters = []
    cmd_out = ['-map 0:v']
    
    if audio:
        cmd_out.append('-map 1:a')
        cmd_out.append('-c:a aac')

    # cmd_out.append('-c copy')
    cmd_out.append('-c:v h264_nvenc')
    
    cmd_out.append('"{}"'.format(output))

    ffmpeg_run(cmd_in, filters, cmd_out, expected_length=expected_length, description="Merging clips together", block=True)

def timestamp(seconds):
    minutes = seconds // 60
    hours = minutes // 60
    whole_seconds = math.floor(seconds)
    ms = (seconds - whole_seconds) / 100
    return "%02d:%02d:%02d.%02d" % (hours, minutes % 60, whole_seconds % 60, ms)

def from_timestamp(timestamp):
    date_time = datetime.datetime.strptime(timestamp, "%H:%M:%S.%f")
    a_timedelta = date_time - datetime.datetime(1900, 1, 1)
    return a_timedelta.total_seconds()

def apply_beat_sounds(beats, input, beat_sound='beat', input_length=None, bar_pos=None, beat_volume=0):
    filename, ext = os.path.splitext(input)

    if ext in video_formats:
        temp_name = util.get_tmp_file('wav')
        ffmpeg_run(['-i "{}"'.format(input)], None, [temp_name], expected_length=input_length, description="Extracting audio", bar_pos=bar_pos)
        input = temp_name

    video_audio_0 = AudioSegment.from_file(input)
    if '.' not in beat_sound:
        beat_sound = 'Resources/{}.mp3'.format(beat_sound)
    
    beat_sound_0 = AudioSegment.from_file(beat_sound) + beat_volume
    
    video_audio_s, beat_sound_s = AudioSegment._sync(video_audio_0, beat_sound_0)
    video_audio_b = bytearray(video_audio_s._data)
    beat_sound_b = beat_sound_s._data
    
    for i,b in enumerate(util.Utqdm(beats[:-1], desc="Overlaying beat sounds", position=bar_pos)):
        pos = len(video_audio_s[:b.start * 1000]._data)
        
        video_sample = video_audio_b[pos:pos + len(beat_sound_b)]
        
        merged_sample = audioop.add(
            video_sample,
            beat_sound_b,
            beat_sound_s.sample_width
        )
        
        video_audio_b[pos:pos + len(beat_sound_b)] = merged_sample
   
    temp_name = util.get_tmp_file('mp4a')

    video_audio = video_audio_s._spawn(video_audio_b)
    file_handle = video_audio.export(temp_name, format="adts")
    return temp_name

def apply_circles(beats, video, keep_audio, output, expected_length = 0, bar_pos=None):
    filters = []
    pts_in = [
        '-i "{}"'.format(video),
        '-i "Resources/circle.png"',
        '-i "Resources/end_circle.png"'
    ]
    
    filters.append('[2]scale=32:32[circleend]')
    
    num_beats = min(80, len(beats))
    beat_circles = []
    for n in range(num_beats):
        beat_circles.append({ 'index': n, 'beats': [] })
        filters.append('[1]scale=32:32[circle{}]'.format(n))
    
    circle_index = 0
    for i,b in enumerate(beats):
        beat_circles[circle_index]['beats'].append(b.start)
        
        circle_index += 1
        if circle_index >= num_beats:
            circle_index = 0
    
    vnum = 0
    filters.append('[0]drawbox=0:ih*0.75:iw:50:color=black@0.7:t=fill[v{}]'.format(vnum+1))
    vnum += 1
    
    # Beat circle receiver overlay
    filters.append('[v{}][circleend]overlay=40:(H*0.75)+8[v{}]'.format(
        vnum,
        vnum+1
    ))
    vnum += 1
    
    # Moving beat circles
    for c in beat_circles:
        if len(c['beats']) == 0:
            continue
            
        x_expression = c['beats'][0]
        for beat_from in c['beats'][1:]:
            beat_to = beat_from - 5
            
            x_expression = ' if(between(t,{beat_to},{beat_from}),{beat_from},{x_expression}) '.format(
                beat_to=round(beat_to, 3),
                beat_from=round(beat_from, 3),
                x_expression=x_expression
            )
            
        filters.append("[v{vin}][circle{i}]overlay=y=(H*0.75)+8:x='40+(W/5)*({x_expression}-t)':[v{vout}]".format(
            x_expression = x_expression,
            vin = vnum,
            vout = vnum+1,
            beat = b,
            i = c['index']
        ))
        vnum += 1
        
    pts_out = [
        '-c:v h264_nvenc',
        '-map [v{}]'.format(vnum)
    ]
    
    if keep_audio:
        pts_out.append('-map 0:a')

    pts_out.append('"{}"'.format(output))
    ffmpeg_run(pts_in, filters, pts_out, expected_length=expected_length, description="Applying beat circles", bar_pos=bar_pos)
        
    return True

def video_merge_audio(video, audio, output, input_length):
    ffmpeg_run([
        '-i "{}"'.format(video),
        '-i "{}"'.format(audio)
    ], None, [
        '-map 0:v',
        '-map 1:a',
        '-c:v copy',
        '-c:a copy',
        '"{}"'.format(output)
    ], expected_length=input_length, description="Merging video and audio")