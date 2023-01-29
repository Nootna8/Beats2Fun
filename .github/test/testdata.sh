#!/bin/bash

mkdir data
unzip "Stamina Alley Part 1.zip" -d data
ffmpeg -f lavfi -i color=color=red -t 120 data/red.mp4
ffmpeg -f lavfi -i color=color=green -t 120 data/green.mp4
ffmpeg -f lavfi -i color=color=blue -t 120 data/blue.mp4
ffmpeg -f lavfi -i color=color=purple -t 120 data/purple.mp4
ffmpeg -f lavfi -i color=color=black -t 120 data/black.mp4
ffmpeg -f lavfi -i color=color=white -t 120 data/white.mp4