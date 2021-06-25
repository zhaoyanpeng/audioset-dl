#!/usr/bin/bash

if [ -z "$OUTPUT_PATH" ]; then
    OUTPUT_PATH=$MYHOME
fi
root=$OUTPUT_PATH
echo $root $OUTPUT_PATH $1 

args=$1
#args="--nprocess 1 --chunk_e 5 --portion unbalanced"

nohup python one_for_all.py $args >> $root/one_for_all.out 2>&1 &

#python one_for_all.py $args 
#>> $root/one_for_all.out 2>&1 &
