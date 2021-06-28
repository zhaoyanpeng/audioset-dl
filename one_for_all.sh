#!/usr/bin/bash

if [ -z "$OUTPUT_PATH" ]; then
    OUTPUT_PATH=$MYHOME
fi
root=$OUTPUT_PATH
echo $root $OUTPUT_PATH $1 

args=$1

home=/home/yanpengz/data/
root=$home
args="--home $root --nprocess 45 --chunk_e 50 --portion unbalanced --peeprate 30"
nohup python one_for_all.py $args >> $root/one_for_all.out 2>&1 &

#python one_for_all.py $args 
#>> $root/one_for_all.out 2>&1 &
