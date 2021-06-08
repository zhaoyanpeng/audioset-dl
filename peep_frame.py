import os, sys, time
import multiprocessing
import subprocess
import requests
import datetime
import time

from csv import reader, writer, DictReader
from collections import defaultdict

from trim_video import trim_videos

home = "/home/yanpengz/"
root = "/net/nfs2.mosaic/yann/"
vroot = f"{root}/data/audioset/video/"

csv_all = ["balanced_train_segments.csv", "eval_segments.csv", "unbalanced_train_segments.csv"]
csv_balanced = ["balanced_train_segments.csv", "eval_segments.csv"]
csv_unbalanced = ["unbalanced_train_segments.csv"]

vroot = f"{home}/data/audioset/video/" 
oroot = f"{home}/data/audioset/frame/"

def mp_worker(ytid):
    """ extract positive clip and create up to 2 background clips
    :param ytid: (file_name, (start_time, end_time)) 
    """
    pid = multiprocessing.current_process()
    
    inf = f"{vroot}/{ytid[0]}"
    b, e = [float(s) for s in ytid[1]]
    name = f"{oroot}/{ytid[0].split('.')[0]}"
    #name = f"{oroot}/{os.path.splitext(ytid[0])[0]}"
    
    # find 
    arg = ["ffprobe", inf, "-show_format 2>&1", "|", "sed -n -E 's/duration=([0-9]+).*/\\1/p'"]
    ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
    out, err = ret.stdout, ret.stderr
    m = float(out) # duration
    b, e = max(0, b), min(e, m) 
    nframe = int(e - b + 1)
    #print(nframe, b, e, m)
    
    """
    # naive way: https://stackoverflow.com/a/27573049
    # may got warnings when the end_time is close to the end of the video: 
    # here is error info: Output file is empty, nothing was encoded (check -ss / -t / -frames parameters if used)
    commands = [
        [
            "ffmpeg -y", f"-ss {datetime.timedelta(seconds=l)}", f"-i {inf}", 
            "-frames:v 1", "-q:v 2", f"{name}.{nframe}_{l - int(b)}.jpg"
        ] for l in range(int(b), int(e) + 1) 
    ]
    for arg in commands:
        print(" ".join(arg))
        ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
        out, err = ret.stdout, ret.stderr
        print(out, err)
    """
    """
    # https://stackoverflow.com/a/50230567
    # when the end_time is close to the end of the video, this command outputs the same number of frames as the above command, but the 
    # frame sequences are slightly different. here is an example command:
    # ffmpeg -y -ss 0:00:07 -i /home/yanpengz//data/audioset/video//5FNqczmbnKA.f135+140.mp4 -t 0:00:10 -vf fps=1 -q:v 1 xxx_%02d.jpg
    """

    arg = [
        "ffmpeg -y", f"-ss {datetime.timedelta(seconds=int(b))}", f"-i {inf}", 
        "-r 1", f"-t 00:00:{nframe:02}", "-q:v 1", f"{name}.{nframe}_%02d.jpg"
    ] # https://superuser.com/a/729351
    #print(" ".join(arg))
    ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
    out, err = ret.stdout, ret.stderr
    #print(out, err)

def mp_handler(param_list, nprocess=1, secs=30):
    """
    :param param_list: [ytid]
    :param nprocess: int
    :param secs: check pool status every #secs
    """
    p = multiprocessing.Pool(nprocess)
    r = p.map_async(mp_worker, param_list)
    if False and multiprocessing.current_process().name == 'MainProcess':
        k, c = 50, 0
        n = len(param_list)
        while not r.ready():
            c += 1 
            print(f"{r._number_left}", end=" ")
            if c % k == 0: print()
            time.sleep(secs)
    r.wait()
    p.close()
    p.join()

if __name__ == '__main__':
    ytids = trim_videos(csv_balanced, vroot)
    #ytids = list(ytids.values())[:10]
    ytids = list(ytids.values())
    mp_handler(ytids, nprocess=54)

