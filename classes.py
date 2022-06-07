import os
import random
import json
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from turtle import update
from parsers import Beat

import util
import videoutil
import math

class VideoContext:
    fps: int
    resolution: str
    volume: float
    bitrate: str
    threads: int
    frame_time: float
    video_codec: str

    def __init__(self, fps, resolution, volume, bitrate, threads, video_codec) -> None:
        self.fps = fps
        self.resolution = resolution
        self.volume = volume
        self.bitrate = bitrate
        self.threads = threads
        self.frame_time = 1/self.fps
        self.video_codec = video_codec
class LoadedVideo:
    file: str
    width: int
    height: int
    length: float
    audio_channels: int
    clips: list['VideoClip']
    start_at: float
    end_at: float
    usable_duration: float

    def __init__(self, file):
        self.file = file
        result = videoutil.ffprobe_run([
            '-show_entries format=duration',
            '-show_entries stream=width,height,codec_type,channels',
            '-print_format json',
            '-i "{}"'.format(self.file)
        ])

        result = json.loads(result)

        #if not result or "streams" not in result or len(result["streams"]) == 0 or "format" not in result :
        #    raise Exception("(Video {} might be corrupt) Failed to get video length".format(file))

        vid_stream = [s for s in result["streams"] if s["codec_type"] == "video"][0]
        audio_streams = [s for s in result["streams"] if s["codec_type"] == "audio"]
        if len(audio_streams) > 0:
            self.audio_channels = audio_streams[0]["channels"]
        
        self.width = vid_stream["width"]
        self.height = vid_stream["height"]
        self.length = float(result["format"]["duration"])
        trim_length = 10
        self.start_at = trim_length
        self.end_at = self.length - trim_length
        self.usable_duration = self.end_at - self.start_at

        self.clips = []
    
    def usable(self):
        # Todo fix by making smarter
        if self.width %2 > 0 or self.height %2 > 0:
            return False

        if self.usable_duration < 1:
            return False

        return True

    def add_clip(self, position, beat: Beat, framecount):
        usable_spaces = []
        search_range = 0.3

        if len(self.clips) == 0:
            usable_spaces.append((self.start_at, self.end_at))
        else:
            if self.clips[0].start > self.start_at:
                usable_spaces.append((self.start_at, self.clips[0].start))
            for i,c in enumerate(self.clips[1:]):
                if self.clips[i-1].end < c.start:
                    usable_spaces.append((self.clips[i-1].end, c.start))
            if self.clips[-1].end < self.end_at:
                usable_spaces.append((self.clips[-1].end, self.end_at))

        search_from = self.start_at + (max(0, position - (search_range/2)) * self.usable_duration)
        search_to = self.start_at + (min(1, position + (search_range/2)) * self.usable_duration)
        usable_pieces = []
        for s in usable_spaces:
            space_from = max(s[0], search_from)
            space_to = min(s[1], search_to)
            if space_to - space_from < beat.duration:
                continue

            usable_pieces.append((space_from, space_to))
        
        if len(usable_pieces) == 0:
            return False

        random.shuffle(usable_pieces)
        search_space = usable_pieces[0][1] - usable_pieces[0][0] - beat.duration
        clip_start = usable_pieces[0][0] + (random.random() * search_space)

        clip = VideoClip(self, beat, clip_start, framecount)
        self.clips.append(clip)
        return clip

class VideoClip:
    video: LoadedVideo
    beat: Beat
    start: float
    end: float
    framecount: int
    clip_file: str
    ffresult: dict

    def __init__(self, video, beat, start, framecount):
        self.video = video
        self.beat = beat
        self.start = start
        self.end = self.start + self.beat.duration
        self.framecount = framecount
        self.clip_file = '{}/{}.mp4'.format(util.get_tmp_dir(), self.beat.index)

    def ffmpeg_options(self, vctx: VideoContext, subindex):
        cmd_in = [
            '-ss {}'.format(videoutil.timestamp(max(0, self.start))),
            '-t {}'.format(self.beat.duration + 0.5),
            '-i "{}"'.format(self.video.file),
        ]
        filters = ['fps={}'.format(vctx.fps)]
        cmd_out = []

        res_pts = list(map(int, vctx.resolution.split(':')))
        if res_pts[0] != self.video.width or res_pts[1] != self.video.height:
            ratio1 = res_pts[0] / res_pts[1]
            ratio2 = self.video.width / self.video.height

            if ratio1 == ratio2:
                filters.append('scale={}'.format(vctx.resolution))
            else:
                if abs(ratio1-ratio2) > 0.4:
                    filters.append('scale={}:force_original_aspect_ratio=decrease'.format(vctx.resolution))
                    filters.append('pad={}:(ow-iw)/2:(oh-ih)/2'.format(vctx.resolution))
                else:
                    filters.append('scale={}:force_original_aspect_ratio=increase'.format(vctx.resolution))
                    filters.append('crop={}'.format(vctx.resolution))

        cmd_out += [
            '-vf "{}"'.format(','.join(filters)),
            '-map {}:v'.format(subindex),
            '-vframes {}'.format(self.framecount)
        ]

        if vctx.volume > 0:
            cmd_out += [
                '-ac 2',
                '-ar:a 48000',
                '-af "atrim=duration={length},apad=whole_dur={length}:packet_size=64"'.format(length = vctx.frame_time * self.framecount),
                #'-af "atrim=duration={length}"'.format(length = vctx.frame_time * self.framecount),
                '-shortest',
                '-avoid_negative_ts make_zero',
                # '-fflags +genpts',
                '-map {}:a'.format(subindex),
                '-c:a aac',
                '-b:a 192k'
            ]
            
        cmd_out +=[
            '-b:v {}'.format(vctx.bitrate),
            '-c:v {}'.format('libx264'),
            self.clip_file
        ]

        return (cmd_in, filters, cmd_out)
    
    def test_file(self):
        if not os.path.exists(self.clip_file):
            raise Exception('Clip "{}" was not created'.format(self.clip_file))
        
        try:
            cmd = [
                '-count_frames',
                '-show_entries stream=nb_read_frames,channels,codec_type,duration',
                '-print_format json',
                '-i {}'.format(self.clip_file)
            ]
            result = json.loads(videoutil.ffprobe_run(cmd))
            framecount = -1
            channels = -1
            audio_lenth = -1
            video_length = -1
            for s in result['streams']:
                if s['codec_type'] == 'video':
                    if framecount == -1:
                        framecount = int(s['nb_read_frames'])
                        video_length = float(s['duration'])
                if s['codec_type'] == 'audio':
                    if channels == -1:
                        channels = s['channels']
                        audio_lenth = float(s['duration'])

            if util.video_ctx and util.video_ctx.volume > 0:
                if channels > 2:
                    raise Exception("Too many audio channels: {}".format(channels))
                #if audio_lenth != video_length:
                #    raise Exception("Audio / Video length not matching {} - {}".format(audio_lenth, video_length))

            if not framecount:
                error = videoutil.ffprobe_run(cmd, False)
                raise Exception("Packet count error: {}".format(error))
        except Exception as e:
            raise Exception("(Clip check error {} might be corrupt, try again) Clip: {}, Error: {}".format(self.video.file, self.clip_file, str(e))) from e

        if framecount != self.framecount:
            raise Exception("(Clip check error {} might be corrupt, try again) {} has {} frames instead of the requested {}".format(self.video.file, self.clip_file, framecount, self.framecount))

class VideoPool:
    folders = []
    videos = []
    video_files = []
    videoindex = 0
    clips = []

    def __init__(self, video_folders):
        self.folders = video_folders.split(',')
        self.futures = []

    def find_videos(self, recursive, vctx, amount):
        self.videos = []
        self.video_files = []
        self.videoindex = 0

        for vf in self.folders:
            if recursive:
                for root, dirs, files in os.walk(vf):
                    for f in files:
                        for ext in videoutil.video_formats:
                            if f.endswith(ext):
                                self.video_files.append(root + '/' + f)
            else:
                for f in os.listdir(vf):
                    for ext in videoutil.video_formats:
                        if f.endswith(ext):
                            self.video_files.append(vf + '/' + f)

        if amount > 0:
            random.shuffle(self.video_files)
            self.video_files = self.video_files[:amount]

        self.analyze_videos(vctx)
        return len(self.videos)

    def analyze_videos(self, vctx):
        self.videos = []
        self.videoindex = 0

        with util.Utqdm(total=len(self.video_files), desc="Video analasys") as pbar:
            with ThreadPoolExecutor(max_workers=vctx.threads) as executor:
                futures = [executor.submit(self.analyze_videos_thread, v, pbar) for v in self.video_files]    

                for future in futures:
                    try:
                        future.result()
                    except BaseException as e:
                        for f in futures:
                            f.cancel()
                        raise e

        self.videos = [x for x in self.videos if x.usable()]
        random.shuffle(self.videos)

    def analyze_videos_thread(self, video, pbar):
        self.videos.append(LoadedVideo(video))
        pbar.update()

    def next_video(self) -> LoadedVideo:
        self.videoindex += 1

        if self.videoindex >= len(self.videos):
            random.shuffle(self.videos)
            self.videoindex = 0

        return self.videos[self.videoindex]

    def assign_clips(self, beat_list, vctx):
        self.clips = []
        length = beat_list.beats[-1].end
        framenr = 0

        for b in beat_list.beats:

            last_frame_time = framenr * vctx.frame_time
            missing_frames = math.floor((b.end - last_frame_time) / vctx.frame_time)
            if missing_frames == 0:
                continue

            tries = len(self.videos)
            beat_pos = b.start / length

            while tries > 0:
                v = self.next_video()
                clip = v.add_clip(beat_pos, b, missing_frames)
                if not clip:
                    tries -= 1
                    continue
                
                self.clips.append(clip)
                framenr += missing_frames
                break

            if tries == 0:
                raise Exception("(Please try again or add more videos) Failed finding clip for beat : {} - {} - {}".format(b.index, b.start, b.end))
    
    def generate_clips(self, batch, vctx):
        num_clips = 0
        for v in self.videos:
            v.clips.sort(key=lambda x: x.start)
            num_clips += len(v.clips)

        self.futures = []

        with util.Utqdm(total=num_clips, desc="Splitting videos") as pbar:
            with ThreadPoolExecutor(max_workers=2) as executor2:
                with ThreadPoolExecutor(max_workers=vctx.threads) as executor:
                    for v in self.videos:
                        for b in util.batch(v.clips, batch):
                            future = executor.submit(self.generate_clips_thread, b, pbar, vctx, executor2)
                            self.futures.append(future)
                    
                    for future in self.futures:
                        try:
                            futures2 = future.result()
                            for f in futures2:
                                f.result()
                        except BaseException as e:
                            executor2.shutdown(True, cancel_futures=True)
                            executor.shutdown(True, cancel_futures=True)
                            raise e
        
        videos_file_name = util.get_tmp_file('txt')
        with open(videos_file_name, 'w') as f:
            for i in range(num_clips):
                f.write("file '{}.mp4'\n".format(i))

        return videos_file_name

    def generate_clips_thread(self, clips, pbar, vctx, executor):
        cmd_in = []
        filters = []
        cmd_out = []

        for i,c in enumerate(clips):
            clip_in, clip_filters, clip_out = c.ffmpeg_options(vctx, i)
            cmd_in += clip_in
            filters += clip_filters
            cmd_out += clip_out
        
        
        def line_callback(l):
            if 'final ratefactor' in l:
                pbar.update(1)

        try:
            result = videoutil.ffmpeg_run(cmd_in, None, cmd_out, True, line_callback=line_callback, ignore_errors=True)
            for c in clips:
                c.ffresult = result
        except Exception as e:
            raise Exception("Clipping error {}, try again".format(str(e))) from e

        

        return [executor.submit(c.test_file) for c in clips]
class PMVideo:
    output_path = None
