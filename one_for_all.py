import multiprocessing
import subprocess
import requests
import datetime
import time, re
import math, os
import argparse

from collections import defaultdict

# Data path options
parser = argparse.ArgumentParser()
parser.add_argument('--home', default='/home/yanpengz/', type=str, help='')
parser.add_argument('--csv_root', default='./csv/', type=str, help='')
parser.add_argument('--nprocess', default=1, type=int, help='')
parser.add_argument('--peeprate', default=100000, type=int, help='')
parser.add_argument('--portion', default="unbalanced", type=str, help='')
parser.add_argument('--chunk_b', default=0, type=int, help='')
parser.add_argument('--chunk_e', default=3000000, type=int, help='')
cfg = parser.parse_args()
# constants
home = cfg.home 
csv_root = cfg.csv_root 
suffix = f"{cfg.chunk_b}_{cfg.chunk_e}" 
# save paths 
part = f"{cfg.portion}_{suffix}" 
vroot = f"{home}/data/{part}/video/"
froot = f"{home}/data/{part}/frame/"
croot = f"{home}/data/{part}/clip/"
aroot = f"{home}/data/{part}/audio/"
# youtube ids
csv_all = ["balanced_train_segments.csv", "eval_segments.csv", "unbalanced_train_segments.csv"]
csv_balanced = ["balanced_train_segments.csv", "eval_segments.csv"]
csv_unbalanced = ["unbalanced_train_segments.csv"]
# save files
err_file = f"{home}/data/{part}/err_ytid.txt"
archive_file = f"{home}/data/{part}/download_archive.txt"
dl_command = [
    "youtube-dl", #"-k",
    "-f", '\'(bestvideo[ext=mp4]/bestvideo/best)+(bestaudio[ext=m4a]/bestaudio/best)\'', 
    "--download-archive", archive_file,
] # https://stackoverflow.com/a/67300109 

def prepare(cfg, verbose=False):
    paths = [vroot, froot, croot, aroot]
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)

    if verbose: 
        print(cfg)
        for name in paths + [err_file, archive_file]:
            print(name)

    if cfg.portion == "unbalanced":
        return csv_unbalanced
    elif cfg.portion == "balanced":
        return csv_balanced
    else:
        return csv_all

def destroy(debug=False):
    with open(archive_file, 'w') as fr:
        fr.write("") # rewrite download record 
    if not debug:
        ret = subprocess.run(
            " ".join(["rm", f"{vroot}/*"]), capture_output=True, shell=True, text=True
        )
    #ret = subprocess.run(
    #    " ".join(["rm", f"{froot}/*"]), capture_output=True, shell=True, text=True
    #)

def collect_ytid(csv_list):
    ids = defaultdict(list)
    nrow = 0
    for fname in csv_list:
        ifile = f"{csv_root}/{fname}"
        with open(ifile, "r") as fr:
            for _ in range(3):
                next(fr)
            for irow, row in enumerate(fr):
                row = row.split(", ")
                ids[row[0].strip()].append(
                    (row[1].strip(), row[2].strip(), row[3].strip().split(","))
                )
                nrow += 1
    print(f"total {nrow} examples.")
    return list(ids.keys()), ids

def dl_video(ytid):
    """ download a video
    :param ytid: (ytid, [(start_time, end_time, [label0, label1, ...])]) 
    """
    name = ytid[0] 
    url = f"https://www.youtube.com/watch?v={name}"
    ofile = f"\'{vroot}/{name}.f%(format_id)s.%(ext)s\'"
    ofile = f"\'{vroot}/{name}.%(ext)s\'"

    arg = dl_command + ["-o", ofile, url]
    ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)

    out, err = ret.stdout, ret.stderr
    ofile = re.search("Merging\sformats\sinto\s\"(.+)\"", out) 
    ofile = ofile.groups()[0] if ofile else None
    return out, err, ofile

def peep_frame(ytid, vfile, fps=0.25):
    """ extract frames from a given video 
    :param ytid: (ytid, [(start_time, end_time, [label0, label1, ...])]) 
    """
    name = ytid[0] 
    b, e = [float(s) for s in ytid[1][0][:2]]

    # find the length of the video 
    arg = ["ffprobe", vfile, "-show_format 2>&1", "|", "sed -n -E 's/duration=([0-9]+).*/\\1/p'"]
    ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
    out, err = ret.stdout, ret.stderr
    m = float(out) # duration

    b, e = max(0, b), min(e, m) 
    nframe = int(e - b + 1)
    real_nframe = math.ceil(nframe * fps)
    #print(nframe, b, e, m, real_nframe)
    
    auto = False
    if not auto: # see potential issues with this method in `peep_frame.py' 
        num_step = 3 
        len_step = (e  - b) / num_step 
        timestamps =  [b + i * len_step for i in range(num_step + 1)]
        #timestamps = range(int(b), int(e) + 1, int(1/fps))
        commands = [[
            "ffmpeg -y", f"-ss {datetime.timedelta(seconds=l)}", f"-i {vfile}",  
            "-frames:v 1", "-q:v 1", f"{froot}/{name}.{int(1/fps)}.{num_step + 1}_{i + 1:02}.jpg"
            ] for i, l in enumerate(timestamps) #enumerate([0, 6, 12]) #
        ]
        status = [False for _ in range(len(commands))]
        for i, arg in enumerate(commands):
            #print(" ".join(arg))
            ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
            out, err = ret.stdout, ret.stderr
            if out.strip() == "":
                status[i] = True 
            #print(out, err)
        return status
    else: # incorrect outputs, but why?
        #nframe += math.ceil(real_nframe - nframe * fps)
        # peep and save frames 
        arg = [
            "ffmpeg -y", f"-ss {datetime.timedelta(seconds=int(b))}", f"-i {vfile}", 
            f"-r {fps}", f"-t 00:00:{nframe:02}", "-q:v 1", f"{froot}/{name}.{int(1/fps)}.{real_nframe}_%02d.jpg"
        ] # https://superuser.com/a/729351
        #print(" ".join(arg))
        ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
        out, err = ret.stdout, ret.stderr
        return out, err

def clip_video(ytid, vfile):
    """ extract positive clip and create up to 2 background clips
    :param ytid: (ytid, [(start_time, end_time, [label0, label1, ...])]) 
    """
    name = ytid[0] 
    b, e = [float(s) for s in ytid[1][0][:2]]
    
    # video length: https://superuser.com/a/769628 
    arg = ["ffprobe", vfile, "-show_format 2>&1", "|", "sed -n -E 's/duration=([0-9]+).*/\\1/p'"]
    ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
    out, err = ret.stdout, ret.stderr
    m = float(out) # duration

    commands = [
        [
            "ffmpeg -y", f"-i {vfile}", "-filter_complex", 
            f"\"[0:v]trim=start={b}:end={e},setpts=PTS-STARTPTS[a];" +
            f"[0:a]atrim=start={b}:end={e},asetpts=PTS-STARTPTS[b]\"",
            "-map '[a]'", "-strict -2", f"{croot}/{name}.p0.mp4", 
            "-map '[b]'", "-strict -2", f"{croot}/{name}.p0.mp3" 
        ] # slow (reencoding) but more accurate in a single command
    ] # https://superuser.com/a/723519

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
                "ffmpeg -y", f"-ss {ss}", f"-i {vfile}", f"-t 00:00:{t:02}", "-map 0", f"{croot}/{name}.n{c}.mp4"
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
                "ffmpeg -y", f"-ss {ss}", f"-i {vfile}", f"-t 00:00:{t:02}", "-map 0", f"{croot}/{name}.n{c}.mp4"
            ]) # https://trac.ffmpeg.org/wiki/Map
            c += 1
            if c >= nclip: break
        if (b - 0 < min_len and m - e < min_len) or (c > nclip):
            break # 
    main_out, main_err = None, None
    for i, arg in enumerate(commands):
        #print(" ".join(arg))
        ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
        out, err = ret.stdout, ret.stderr
        if i == 0:
            main_out, main_err = out, err
    return main_out, main_err

def collect_clip(ytid, vfile):
    """
    :param ytid: (ytid, [(start_time, end_time, [label0, label1, ...])]) 
    """
    name = ytid[0] 
    b, e = [float(s) for s in ytid[1][0][:2]]
    # probe the length of the video
    arg = ["ffprobe", vfile, "-show_format 2>&1", "|", "sed -n -E 's/duration=([0-9]+).*/\\1/p'"]
    ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
    out, err = ret.stdout, ret.stderr
    m = float(out) # duration

    b, e = max(0, b), min(e, m)
    clips = [[b, e, "p0"]] # the gold clip

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
            clips.append([l, l + t, f"n{c}"])
            c += 1
            if c >= nclip: break
        # right side
        if m - e >= min_len:
            l = e
            ss = str(datetime.timedelta(seconds=l))
            t = min(10, m - l)
            e = l + t + margin
            #print(ss, t)
            clips.append([l, l + t, f"n{c}"])
            c += 1
            if c >= nclip: break
        if (b - 0 < min_len and m - e < min_len) or (c > nclip):
            break # 
    return clips

def clip_audio(ytid, vfile, clips):
    """
    :param ytid: (ytid, [(start_time, end_time, [label0, label1, ...])]) 
    """
    name = ytid[0] 
    main_out, main_err = None, None
    for iclip, (b, e, flag) in enumerate(clips):
        arg = [
            "ffmpeg -y", f"-i {vfile}", "-filter_complex", 
            f"\"[0:a]atrim=start={b}:end={e},asetpts=PTS-STARTPTS[b]\"",
            "-map '[b]'", "-strict -2", f"{aroot}/{name}.{flag}.mp3" 
        ] # https://superuser.com/a/723519
        #print(" ".join(arg))
        ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
        out, err = ret.stdout, ret.stderr
        if iclip == 0:
            main_out, main_err = out, err
    return main_out, main_err

def collect_frame(ytid, vfile, clips, num_step=3, fps=0.25): 
    """
    :param ytid: (ytid, [(start_time, end_time, [label0, label1, ...])]) 
    """
    name = ytid[0] 
    main_status = [False]
    for iclip, (b, e, flag) in enumerate(clips):
        nframe = int(e - b + 1)
        real_nframe = math.ceil(nframe * fps)

        len_step = (e  - b) / num_step 
        timestamps =  [b + i * len_step for i in range(num_step + 1)]
        #timestamps = range(int(b), int(e) + 1, int(1/fps))
        commands = [[
            "ffmpeg -y", f"-ss {datetime.timedelta(seconds=l)}", f"-i {vfile}",  
            "-frames:v 1", "-q:v 1", f"{froot}/{name}.{flag}.{int(1/fps)}.{num_step + 1}_{i + 1:02}.jpg"
            ] for i, l in enumerate(timestamps) #enumerate([0, 6, 12]) #
        ]
        status = [False for _ in range(len(commands))]
        for i, arg in enumerate(commands):
            #print(" ".join(arg))
            ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
            out, err = ret.stdout, ret.stderr
            if out.strip() == "":
                status[i] = True 
            #print(out, err)
        if iclip == 0:
            main_status = status 
    return main_status

def rm_video(vfile):
    """
    :param vfile: str: the video file
    """
    if not os.path.isfile(vfile):
        return None, None 
    arg = ["rm", vfile]
    ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
    #print(" ".join(arg), ret)
    return ret.stdout, ret.stderr

def mp_worker(ytid):
    """
    :param ytid: (ytid, [(start_time, end_time, [label0, label1, ...])]) 
    """
    name = ytid[0] 
    try: # download
        #if name != "---1_cCGK4M":
        #    return name, 0 # debug 
        vfile = f"{vroot}/{name}.mp4" 
        if not os.path.isfile(vfile):
            out, err, vfile = dl_video(ytid)
        #print(ytid, vfile)
    except Exception as e:
        vfile = None
        print(f"Err in downloading {name}: {e}")
        pass
    if vfile is None: 
        return name, 0
    
    save_video = False
    if not save_video: 
        try: # clip extraction
            clips = collect_clip(ytid, vfile)
        except Exception as e:
            print(f"Err in clip extraction {name}: {e}")
            clips = []
            pass

        try: # frame extraction
            status = collect_frame(ytid, vfile, clips)
            assert isinstance(status, list)
            flag = int(all(status))
        except Exception as e:
            print(f"Err in frame extraction {name}: {e}")
            flag = 0
            pass
        
        try: # audio clip
            out, err = clip_audio(ytid, vfile, clips)
            flag = flag & (out.strip() == "")
            #print(f"f{flag}", f"\n-->>>\n{out.strip()}\n{err.strip()}\n<<<--")
        except Exception as e:
            print(f"Err in audio clipping {name}: {e}")
            flag = 0
            pass
    else:
        try: # frame extraction
            status = peep_frame(ytid, vfile)
            assert isinstance(status, list)
            flag = int(all(status))
        except Exception as e:
            print(f"Err in frame extraction {name}: {e}")
            flag = 0
            pass
        
        try: # video clip
            out, err = clip_video(ytid, vfile)
            flag = flag & (out.strip() == "")
            print(f"f{flag}", f"\n-->>>\n{out.strip()}\n{err.strip()}\n<<<--")
        except Exception as e:
            print(f"Err in video clipping {name}: {e}")
            flag = 0
            pass
    
    try: # video remove
        if flag == 1: # further take care
            out, err = rm_video(vfile)
    except Exception as e:
        print(f"Err in deleting video {name}: {e}")
        pass
    return name, flag 

def mp_handler(param_list, nprocess=1, secs=30):
    """
    :param param_list: [ytid]
    :param nprocess: int
    :param secs: check pool status every #secs
    """
    p = multiprocessing.Pool(nprocess)
    def write_err(results):
        with open(err_file, 'w') as f:
            for name, status in results:
                f.write(f"{name} {status}\n")
    r = p.map_async(mp_worker, param_list, callback=write_err)
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
    csv_data = prepare(cfg, True)
    destroy(False)
    _, dict_ytids = collect_ytid(csv_data)
    ytids = list(dict_ytids.items())[cfg.chunk_b : cfg.chunk_e]
    mp_handler(ytids, nprocess=cfg.nprocess, secs=cfg.peeprate)

