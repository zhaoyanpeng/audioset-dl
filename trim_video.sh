#!/usr/bin/sh

root=$MYHOME/data/audioset/csv/
root=./

nohup python trim_video.py >> $root/trim_video.out 2>&1 &
