#!/usr/bin/bash

root=$MYHOME/data/audioset/csv/
root=./

args=$1
args="--nprocess 1 --chunk_e 5 --portion unbalanced"

nohup python one_for_all.py $args >> $root/one_for_all.out 2>&1 &
