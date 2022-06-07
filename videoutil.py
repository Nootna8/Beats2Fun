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

def ffmpeg_run(pts_in, filters, pts_out, silent = True, expected_length = 0, description = None, bar_pos=None, block=True, line_callback=None, ignore_errors=False):
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
            with subprocess.Popen(cmd, stdout=PIPE, stderr=STDOUT, bufsize=1, encoding='utf-8') as p:
                for l in p.stdout:
                    if line_callback:
                        line_callback(l)

                    if 'No decoder surfaces left' in l:
                        p.terminate()
                        error_msg = l
                    if not ignore_errors and 'Error' in l:
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

    return {
        'command': cmd,
        'retcode': retcode,
        'output': output
    }

def ffprobe_run(pts_in, suppress_errors=True):
    cmd_pts = ['ffprobe']
    if suppress_errors:
        cmd_pts.append('-v error')
    cmd_pts += pts_in
    cmd = ' '.join(cmd_pts)
    retcode = -1

    try:
        # result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
    
    for i,b in enumerate(util.Utqdm(beats[:-1], desc="Overlaying beat sounds")):
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
        '-c:v {}'.format(util.video_ctx.video_codec),
        '-map [v{}]'.format(vnum)
    ]
    
    if keep_audio:
        pts_out.append('-map 0:a')

    pts_out.append('"{}"'.format(output))
    ffmpeg_run(pts_in, filters, pts_out, expected_length=expected_length, description="Applying beat circles")
        
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