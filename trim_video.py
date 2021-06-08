import os, sys, time
import multiprocessing
import subprocess
import requests
import datetime
import time

from csv import reader, writer, DictReader
from collections import defaultdict

home = "/home/yanpengz/"
root = "/net/nfs2.mosaic/yann/"
vroot = f"{root}/data/audioset/video/"
csv_root = f"{root}/data/audioset/csv/"

csv_all = ["balanced_train_segments.csv", "eval_segments.csv", "unbalanced_train_segments.csv"]
csv_balanced = ["balanced_train_segments.csv", "eval_segments.csv"]
csv_unbalanced = ["unbalanced_train_segments.csv"]

def collect_ytid(csv_list):
    ids = defaultdict(list)
    nrow = 0
    for fname in csv_list:
        ifile = f"{csv_root}/{fname}"
        with open(ifile, "r") as fr:
            for _ in range(3):
                next(fr)
            csv_reader = reader(fr, delimiter=",")
            for irow, row in enumerate(csv_reader):
                ids[row[0].strip()].append(
                    (row[1].strip(), row[2].strip())
                )
                nrow += 1
    print(f"total {nrow} examples.")
    return list(ids.keys()), ids

def check_ext(iroot):
    exts = defaultdict(list)
    for root, dir, files in os.walk(iroot):
        for file in files:
            name, ext = os.path.splitext(file)
            exts[ext].append(name)
    return exts

def trim_videos(csv_list, iroot, key=".mp4"):
    exist_set = defaultdict(list)
    _, id_clip = collect_ytid(csv_balanced)
    exts_dict = check_ext(iroot)
    for fname in exts_dict[key]:
        fid = fname.split(".")[0]
        if fid not in id_clip: continue
        exist_set[fid].append(fname + key)
        for clip in id_clip[fid]:
            exist_set[fid].append(clip)
    print(f"total {len(exist_set)} videos.")
    return exist_set

def check_ret(iroot, ytids):
    print("\n#######")
    for ytid in ytids:
        name = f"{iroot}/{ytid[0].split('.')[0]}.p0.mp4"
        if not os.path.isfile(name):
            print(ytid)

vroot = f"{home}/data/audioset/video/" 
oroot = f"{home}/data/audioset/clip/"

def mp_worker(ytid):
    """ extract positive clip and create up to 2 background clips
    :param ytid: (file_name, (start_time, end_time)) 
    """
    pid = multiprocessing.current_process()
    
    inf = f"{vroot}/{ytid[0]}"
    b, e = [float(s) for s in ytid[1]]
    name = f"{oroot}/{ytid[0].split('.')[0]}"
    #name = f"{oroot}/{os.path.splitext(ytid[0])[0]}"
    
    # video length: https://superuser.com/a/769628 
    arg = ["ffprobe", inf, "-show_format 2>&1", "|", "sed -n -E 's/duration=([0-9]+).*/\\1/p'"]
    ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
    out, err = ret.stdout, ret.stderr
    m = float(out) # duration
    #b, e = max(0, b), min(e, m) 
    #print(ss, to, m, inf)

    commands = [
        [
            "ffmpeg -y", f"-i {inf}", "-filter_complex", 
            f"\"[0:v]trim=start={b}:end={e},setpts=PTS-STARTPTS[a];" +
            f"[0:a]atrim=start={b}:end={e},asetpts=PTS-STARTPTS[b]\"",
            "-map '[a]'", "-strict -2", f"{name}.p0.mp4", 
            "-map '[b]'", "-strict -2", f"{name}.p0.m4a" 
        ] # slow (reencoding) but more accurate in a single command
    ] # https://superuser.com/a/723519

    # the below results in inaccurate cuts: https://superuser.com/a/1131088
    # be careful about ss option: https://superuser.com/a/377407; https://trac.ffmpeg.org/wiki/Seeking
    #ss, to = [str(datetime.timedelta(seconds=s)) for s in (b, e)]
    #commands = [
    #    ["ffmpeg", f"-ss {ss}", f"-i {inf}", f"-to {to}", "-y", "-map 0:v -c copy", f"{name}.p0.mp4"],
    #    ["ffmpeg", f"-ss {ss}", f"-i {inf}", f"-to {to}", "-y", "-map 0:a -c copy", f"{name}.p0.m4a"]
    #] 
    
    # random background (non-event) clips
    # extract a clip from left & right of the event clip, respectively
    c, margin, min_len, nclip = 0, 3, 5, 2
    #commands = []
    b = b - margin
    e = e + margin
    for i in range(10000): # break when reaching the maximum # of clips
        # left side
        if b - 0 >= min_len:
            l = max(0, b - 10)
            t = b - l
            ss = str(datetime.timedelta(seconds=l))
            b = l - margin
            #print(ss, t)
            commands.append([
                "ffmpeg -y", f"-ss {ss}", f"-i {inf}", f"-t 00:00:{t:02}", "-map 0", f"{name}.n{c}.mp4"
            ]) # https://trac.ffmpeg.org/wiki/Map
            c += 1
            if c >= nclip: break
        # right side
        if m - e >= min_len:
            l = e
            ss = str(datetime.timedelta(seconds=l))
            t = min(10, m - l)
            e = l + t + margin
            #print(ss, t)
            commands.append([
                "ffmpeg -y", f"-ss {ss}", f"-i {inf}", f"-t 00:00:{t:02}", "-map 0", f"{name}.n{c}.mp4"
            ]) # https://trac.ffmpeg.org/wiki/Map
            c += 1
            if c >= nclip: break
        if (b - 0 < min_len and m - e < min_len) or (c > nclip):
            break # 

    for arg in commands:
        #print(" ".join(arg))
        ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
        out, err = ret.stdout, ret.stderr
        #print(ss, to, out, err, yid)

def mp_handler(param_list, nprocess=1, secs=30):
    """
    :param param_list: [ytid]
    :param nprocess: int
    :param secs: check pool status every #secs
    """
    p = multiprocessing.Pool(nprocess)
    r = p.map_async(mp_worker, param_list)
    if multiprocessing.current_process().name == 'MainProcess':
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
    #ytids = list(ytids.values())[:100]
    ytids = list(ytids.values())
    mp_handler(ytids, nprocess=54)
    check_ret(oroot, ytids)

