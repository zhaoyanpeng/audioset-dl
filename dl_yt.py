import multiprocessing
import subprocess
import requests
import time

home = "/home/yanpengz/"
root = "/net/nfs2.mosaic/yann/"
vroot = f"{root}/data/audioset/video/"
csv_root = f"{root}/data/audioset/csv/"

#with open(f"{root}/data/audioset/download_archive.txt", 'w') as fr:
#    fr.write("")

command = [
    "youtube-dl", #"-k",
    "-f", '\'(bestvideo[ext=mp4]/bestvideo/best)+(bestaudio[ext=m4a]/bestaudio/best)\'', 
    "--download-archive", f"{root}/data/audioset/download_archive.txt",
    "--write-sub", "--write-auto-sub", "--sub-lang en", #"--all-subs", "--embed-sub",
    "--write-info-json", "--write-all-thumbnail",  #"--add-metadata",
]

def read_ytids(ifile):
    ytid_set = list()
    with open(ifile, 'r') as fr:
        for ytid in fr:
            ytid_set.append(ytid.strip())
    return ytid_set

ifile = f"{csv_root}/ytid_all_segments.csv"
ifile = f"{csv_root}/ytid_balanced_segments.csv"
ytids = read_ytids(ifile) #[:100]
vroot = f"{home}/data/audioset/video/" 
#ytids = ["zx43ZN4pQNw", "G0-aBZ84Vdm", "G0-aBZ84V-g", "2bjqJiBNoUo"] #, "8Qn52i0WPdA", "DgFAdR4-a_0", "RojiFmAmAsc", "zR40A3JGKGo"]

def mp_worker(ytid):
    pid = multiprocessing.current_process()
    url = f"https://www.youtube.com/watch?v={ytid}"
    
    arg = ["-o", f"\'{vroot}/{ytid}.f%(format_id)s.%(ext)s\'", url]
    arg = command + arg

    ret = subprocess.run(" ".join(arg), capture_output=True, shell=True, text=True)
    out, err = ret.stdout, ret.stderr
    #print(f"{' '.join(arg)}\n\n{arg}\n\n{out}\n\n{err}\n")
    #print(f"{' '.join(arg)}\n{out}\t{err} ")

def mp_handler(param_list, nprocess=1, secs=30):
    p = multiprocessing.Pool(nprocess)
    r = p.map_async(mp_worker, param_list)
    if multiprocessing.current_process().name == 'MainProcess':
        k, c = 50, 0
        n = len(param_list)
        while not r.ready():
            c += 1 
            print(f"{r._number_left}", end=" ")
            #print(f"{r._value.count(None)}")
            if c % k == 0: print()
            time.sleep(secs)
    #print(f"{r.get()}")
    r.wait()
    p.close()
    p.join()

if __name__ == '__main__':
    mp_handler(ytids, nprocess=54)

