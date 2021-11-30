import os, sys, time
import multiprocessing
import subprocess
import requests
import datetime
import time
import json
import copy

import numpy as np

from tqdm import tqdm
from csv import reader, writer, DictReader
from collections import defaultdict

""" create AudioSet data splits.
"""

home = "/home/yanpengz/"
root = "/net/nfs2.mosaic/yann/"
vroot = f"{root}/data/audioset/video/"
csv_root = f"{root}/data/audioset/csv/"

csv_all = ["balanced_train_segments.csv", "eval_segments.csv", "unbalanced_train_segments.csv"]
csv_balanced = ["balanced_train_segments.csv", "eval_segments.csv"]
csv_unbalanced = ["unbalanced_train_segments.csv"]

#######
# read into ytids 
#######
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
                    #(row[1].strip(), row[2].strip(), row[3].strip().split(",")) # 1730437 valid
                    (row[1].strip(), row[2].strip(), row[3].strip('" \n').split(",")) 
                )
                nrow += 1
    print(f"total {nrow} examples.")
    return list(ids.keys()), ids

#######
# 1. read into train ids and filter out speech & music categories
#######
def read_ontology_dict():
    ontology_file = f"{csv_root}/ontology.json"
    ontology = json.loads(open(ontology_file, "r").read())
    ontology_dict = dict()
    for onto in ontology:
        sid = onto["id"]
        if sid in ontology_dict:
            raise KeyError(f"duplicate sound class `{sid}`")
        ontology_dict[sid] = onto
    return ontology_dict

def excluded_cls(seeds):
    ontology = read_ontology_dict()
    excluded_set = set()
    seeds = copy.deepcopy(seeds)
    while len(seeds) > 0:
        seed = seeds.pop(0)
        excluded_set.add(seed)
        child_ids = ontology[seed]["child_ids"]
        seeds += child_ids
    return excluded_set

#######
# 2. filter out speech & music categories
#######
def collect_valid_ytids(cv_list, excluded_seed, ofile=None):
    excluded_set = excluded_cls(excluded_seed)
    ytids = set()
    _, id_clip = collect_ytid(cv_list)
    for k, v in tqdm(id_clip.items()):
        flag = [x in excluded_set for x in v[0][2]]
        if not any(flag):
            ytids.add(k)
    print(f"total {len(ytids)} valid ytids.")
    if ofile is not None:
        print(f"writting {len(ytids)} valid ytids into {ofile}")
        ytid_dict = {k: id_clip[k] for k in ytids}
        with open(ofile, "w") as fw:
            json.dump(ytid_dict, fw, indent=2)
    return ytids

#######
# 3. build .npz index
#######
def build_npz_map(root, filter_dict, ofile=None):
    cnt = 0
    pos = len(root)
    npz_dict = defaultdict(dict)
    for root, dir, files in os.walk(root):
        if len(dir) > 0:
            continue
        sub_dir =  root[pos + 1:]
        print(sub_dir, root, dir, len(files))

        key = sub_dir.rsplit("/", 1)[-1].split("_")[0]
        for ifile, fname in tqdm(enumerate(files)):
            ytid = fname.split(".", 1)[0]
            if filter_dict.get(ytid, 0) == 0:
                continue # invalid
            npz_dict[ytid][key] = f"{sub_dir}/{fname}"

        """   if ifile > 10:
                break
        print(npz_dict)
        break
        cnt += 1
        if cnt > 400:
            break
        pass
        """ 
    if ofile is not None:
        print(f"writting {len(npz_dict)} indexes into {ofile}")
        #json_str = json.dumps(npz_dict, indent=2)
        #
        #with open(ofile, "r") as fr:
        #    xx = json.load(fr)
        #
        with open(ofile, "w") as fw:
            json.dump(npz_dict, fw, indent=2)
    return npz_dict

#######
# 3. build .src index: the raw image and audio files
#######
def build_src_map(root, filter_dict, ofile=None):
    cnt = 0
    pos = len(root)
    npz_dict = defaultdict(dict)
    for root, dir, files in os.walk(root):
        if len(dir) > 0:
            continue
        sub_dir =  root[pos + 1:]
        parent, folder = sub_dir.split("/")
        if folder not in ["aclip", "frame"]:
            pass #continue
        print(parent, sub_dir, root, dir, len(files))

        key = folder #sub_dir.rsplit("/", 1)[-1].split("_")[0]
        islist = True if "_" not in key else False 
        for ifile, fname in tqdm(enumerate(files)):
            if "p0" not in fname:
                continue # keep the positive
            ytid, fstem = fname.split(".", 1)
            if filter_dict.get(ytid, 0) == 0:
                continue # invalid
            
            if not islist:
                npz_dict[ytid][key] = f"{fstem}"
            else:
                npz_dict[ytid]["dir"] = parent 
                file_list = npz_dict[ytid].get(key, [])
                file_list.append(fstem)
                npz_dict[ytid][key] = file_list

        """    if ifile > 20:
                break
        print(npz_dict)
        #break
        cnt += 1
        if cnt > 400:
            break
        pass
        """ 
    if ofile is not None:
        print(f"writting {len(npz_dict)} indexes into {ofile}")
        #json_str = json.dumps(npz_dict, indent=2)
        #
        #with open(ofile, "r") as fr:
        #    xx = json.load(fr)
        #
        with open(ofile, "w") as fw:
            json.dump(npz_dict, fw, indent=2)
    return npz_dict

def write_all_valid_ytids():
    excluded_seed = ["/m/09x0r", "/m/04rlf"] # speech & music 309190 left
    excluded_seed = [] # 2084320 left, total 2084320 
    ofile = f"{csv_root}/all.idx" 
    #ofile = None
    valid_ytids = collect_valid_ytids(csv_all, excluded_seed, ofile)

def write_all_index_ytids_npz():
    npz_root = f"{home}/data/audioset"
    ofile = f"{csv_root}/all_npz.map" 

    filter_file = f"{csv_root}/all.map.filter"
    filter_dict = json.load(open(filter_file, "r"))

    build_npz_map(npz_root, filter_dict, ofile)

def write_all_index_ytids_src():
    src_root = f"{home}/data/audioset"
    ofile = f"{csv_root}/all_src.map" 

    filter_file = f"{csv_root}/all.map.filter"
    filter_dict = json.load(open(filter_file, "r"))

    build_src_map(src_root, filter_dict, ofile)

def make_splits(is_npz=True, full=False, flag=""):
    ytid_file = f"{csv_root}/all.idx"
    ytid_dict = json.load(open(ytid_file, "r"))
    
    prefix = "npz" if is_npz else "src"
    npz_file = f"{csv_root}/all_{prefix}.map"
    npz_dict = json.load(open(npz_file, "r"))

    keep = True if (is_npz or (not is_npz and full)) else False

    def filter_out(cv_list, ofile):
        ytid_set, _ = collect_ytid(cv_list)
        with open(ofile, "w") as fw:
            for ytid in tqdm(ytid_set):
                if ytid in ytid_dict and ytid in npz_dict \
                    and "aclip" in npz_dict[ytid] and "frame" in npz_dict[ytid]:

                    if not keep and ("aclip_128" not in npz_dict[ytid] or "frame_224" not in npz_dict[ytid]):
                        continue

                    bos, eos, labels = ytid_dict[ytid][0][:3]
                    metadata = {"id": ytid, "bos": bos, "eos": eos, "labels": labels}
                    for k, v in npz_dict[ytid].items():
                        if isinstance(v, list):
                            v.sort() # 
                    new_dict = copy.deepcopy(npz_dict[ytid])
                    new_dict.update(metadata)
                    
                    json.dump(new_dict, fw)
                    fw.write("\n")

    root = f"{home}/data/audioset"

    if len(flag) > 0:
        prefix = f"{prefix}_{flag}"
    
    ifile = "eval_segments.csv"
    ofile = f"{root}/{prefix}_{ifile}"
    filter_out([ifile], ofile)

    ifile = "balanced_train_segments.csv"
    ofile = f"{root}/{prefix}_{ifile}"
    filter_out([ifile], ofile)

    ifile = "unbalanced_train_segments.csv"
    ofile = f"{root}/{prefix}_{ifile}"
    filter_out([ifile], ofile)

def check_npz():
    #npz_file = f"{csv_root}/all.map"
    npz_file = f"{csv_root}/all.map.filter"
    npz_dict = json.load(open(npz_file, "r"))
    
    invalid_dict = defaultdict(str)
    for k, v in tqdm(npz_dict.items()):
        if v == 0:
            invalid_dict[k] = 0
    """
    for k, v in tqdm(npz_dict.items()):
        err_type = None 
        #print(k, v)
        if "frame" not in v:
            err_type = "frame"
        elif "aclip" not in v:
            err_type = "aclip"
        if err_type is not None:
            invalid_dict[k] = err_type 
    """
    print(f"total {len(invalid_dict)} invalid samples")

def mp_worker(ytid, root=f"{home}/data/audioset"):
    """ (ytid, {"frame": /path/to/frame, "aclip": /path/to/audio})
    """
    try:
        ytid, v = ytid
        if "frame" not in v or "aclip" not in v:
            return ytid, 0

        images = np.load(f"{root}/{v['frame']}")
        images = [images[key] for key in images.files if len(images[key]) > 0]
        if len(images) == 0:
            return ytid, 0

        audios = np.load(f"{root}/{v['aclip']}")
        if audios["flag"].shape[0] < 200: # less than 2 seconds
            return ytid, 0
        return ytid, 1
    except Exception as e:
        print(f"oops: {e}")
        return ytid[0], 0

def mp_handler(npz_root=f"{home}/data/audioset", nprocess=1, secs=30, k=sys.maxsize):
    """
    """
    err_file = f"{csv_root}/all.map.filter"
    param_list = list(build_npz_map(npz_root).items())[:k]
    print(f"total {len(param_list)} videos to check.")
    p = multiprocessing.Pool(nprocess)
    def write_err(results):
        result_dict = {k: v for k, v in results}
        with open(err_file, 'w') as fw:
            json.dump(result_dict, fw, indent=2)
            #for name, status in results:
            #    f.write(f"{name} {status}\n")
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
    #write_all_valid_ytids()
    #mp_handler(nprocess=56, secs=30)
    #check_npz()
    #write_all_index_ytids_npz() # total 1730437 valid ytids.
    #write_all_index_ytids_src() # writting 1749819 indexes.
    #make_splits(is_npz=False)
    make_splits(is_npz=False, full=True, flag="full")
    pass
