#!/usr/bin/bash

OUTPUT_PATH=./
if [ -z "$OUTPUT_PATH" ]; then
    OUTPUT_PATH=$MYHOME
fi
root=$OUTPUT_PATH
echo $root $OUTPUT_PATH $1 

exit 0

args="--home $root --keepdata true --nprocess 5 --chunk_e 5 --portion unbalanced --peeprate 3"
nohup python audioset_dl.py $args >> $root/audioset_dl.out 2>&1 &
