#!/usr/bin/sh

root=$MYHOME/data/audioset/csv/
root=./

nohup python peep_frame.py >> $root/peep_frame.out 2>&1 &
