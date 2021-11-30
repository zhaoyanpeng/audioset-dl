#!/usr/bin/sh

root=$MYHOME/data/audioset/csv/
root=./

nohup python filter_out.py >> $root/filter_out.out 2>&1 &
