# Beats2Fun

Inspired by: https://www.reddit.com/r/AutoPMVs/

To run these set of tools either install Beats2Fun from the releases page: https://github.com/Nootna8/Beats2Fun/releases

To run the application manually, make you to have:
 - Python: https://www.python.org/downloads/
 - Git: https://git-scm.com/downloads
 - Ffmpeg: https://www.gyan.dev/ffmpeg/builds/

```
git clone https://github.com/Nootna8/Beats2Fun
cd Beats2Fun
pip install -r requirements.txt
python Beats2Fun.py
```

All tools include a commandline interface and a graphical interface. Be default the GUI will always open

Supported file types are:
 - StepMania simfiles (.ssc, .sm) Search for songs here: https://search.stepmaniaonline.net/
 - Osu beatmap files (.osz, .osu) Search for songs here: https://osu.ppy.sh/beatmapsets
 - Funscript files (.funscript) Search here: https://discuss.eroscripts.com/
 - Beat txt files (.txt) Can be used with: https://github.com/FredTungsten/ScriptPlayer


## Beats2Fun

![Beats2Fun](https://i.ibb.co/FV0WD3H/Capture.png)

```
usage: Beats2Fun.py [-h] [-recurse] [-no_cuda] [-clip_dist Clip distance] [-fps FPS] [-num_vids Video amount]
                    [-beatbar]
                    Input Video folder

Make a PMV based on a simfile

positional arguments:
  Input                 Path to input (Chart folder / file / music file)
  Video folder          Folder containg your input videos (.mp4, .wmv)

optional arguments:
  -h, --help            show this help message and exit
  -recurse              Search videos recursively
  -clip_dist Clip distance
                        Minimal clip distance in seconds
  -fps FPS              Output video FPS
  -num_vids Video amount
                        How many videos to randomly select from the Video folder (0 means all)
  -beatbar              Add a beatbar to the output video
```

## Beats2Bar

![Beats2Bar](https://i.ibb.co/tqBZ08k/Capture.png)

```
usage: Beats2Bar.py [-h] [-beat_sound Beat sound] Input [Output]

Add a beatbar to a music video

positional arguments:
  Input                 Path to into video
  Output                Where to store the resulting video

optional arguments:
  -h, --help            show this help message and exit
  -beat_sound Beat sound
                        Sound effect to play on each beat (make empty or select "none" to disable)
```

## Beats2Map

![Beats2Bar](https://i.ibb.co/GsvPrcy/Capture.png)

```
usage: Beats2Map.py [-h] [-show] Input [Output]

Generates heatmap for a funscript

positional arguments:
  Input       Path to the input
  Output      Where to store the heatmap image file (optional)

optional arguments:
  -h, --help  show this help message and exit
  -show       Opens the generated heatmap when done
```