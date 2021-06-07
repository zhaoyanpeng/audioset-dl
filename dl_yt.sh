#!/usr/bin/sh

root=$MYHOME/data/audioset/csv/

nohup python dl_yt.py >> $root/dl_yt.out 2>&1 &
