import numpy as np
import copy, time, json
from collections import Counter, defaultdict

""" trying to balance the unbalanced AudioSet training set.
"""

def read_candidate(dist_file, topk, ytid_dict, start=0):
    recalls = []
    samples = set()
    all_labels = Counter()
    samples_per_label = defaultdict(list)
    extra_samples = set()
    with open(dist_file, "r") as fr:
        for line in fr:
            line = json.loads(line)
            k, v = list(line.items())[0]
            extra_samples.add(k)

            label_k = set(ytid_dict[k][0][2])
            labels = set([
                fid for name, _ in v[start : topk + start] for fid in ytid_dict[name][0][2] 
            ])
            recall = len(label_k - (label_k - labels)) / len(label_k)
            recalls.append(recall)
            
            new_samples = set([name for name, _ in v[start : topk + start]])
            for name in new_samples:
                if name in samples:
                    continue
                for label in ytid_dict[name][0][2]:
                    samples_per_label[label].append(name)
                    all_labels[label] += 1
                samples.add(name) #.update(new_samples)
    #         print(recall)
    #         break
    mean_recall = np.mean(recalls)
    std_recall = np.std(recalls)
    
    counts = list(all_labels.values())
    mean_cnt = np.mean(counts)
    std_cnt = np.std(counts)
    print(mean_recall, std_recall, mean_cnt, std_cnt, min(counts), max(counts))
    return samples_per_label, extra_samples

def save_balanced(dict_data, ofile):
    with open(ofile, "w") as fw:
        json.dump(dict_data, fw, indent=2)

def balance_fast(samples_per_label, nper_label, ytid_dict, inc=0., interval=10, extra_samples=set()):
    samples = {k: set() for k in samples_per_label.keys()}
    nlabel = len(samples)
    niter, ilabel = 0, 0
    last_time = time.time()
    
    while True:
        breakout = False
        labels = sorted(samples_per_label.keys(), key=lambda x: len(samples_per_label[x]))
        for _, label in enumerate(labels):
            nsample = len(samples_per_label[label])
            if nsample != 0 and len(set(samples_per_label[label]) | samples[label]) <= nper_label:
                breakout = True
                break
        
        if not breakout:
            break
        ilabel += 1
        
        for sample in samples_per_label[label]:
            invalid = 0
            for slabel in ytid_dict[sample][0][2]:
                old_len = len(samples[slabel])
                new_len = old_len if sample in samples[slabel] else old_len + 1
                if new_len > nper_label:
                    invalid += 1
            if invalid > 0:
                continue
            for slabel in ytid_dict[sample][0][2]:
                samples[slabel].add(sample)

        removed = set(samples_per_label[label])
        for k, v in samples_per_label.items():
            if len(v) == 0: 
                continue
#             if sample in v:
#                 v.remove(sample)
            v[:] = set(v) - removed
        nsample = len(set(samples[label]))
        print(f"{ilabel}-th label {label} ({nsample}) done {time.time() - last_time:.2f}s.")
        last_time = time.time()

    for k, v in samples_per_label.items():
        if len(samples[k]) >= nper_label:
            v[:] = []
        if len(v) > nper_label:
            samples_per_label[k] = sorted(v, key=lambda x: len(ytid_dict[x][0][2]))
    for k, v in samples.items():
        if len(v) != len(set(v)): # check duplicates
            raise ValueError(f"duplicate samples in `samples`") 
    cnts = [len(v) for k, v in samples.items()]
    print(min(cnts), max(cnts), cnts)
    cnts = [len(samples_per_label[k]) for k, v in samples.items()]
    print(min(cnts), max(cnts), cnts)
    
    last_cnt = sum([len(v) for k, v in samples_per_label.items()])
    nmax_label = max([len(v) for k, v in samples.items()])
    nmax_label = int(nmax_label * (1 + inc))
    print(f"nper_label {nper_label} is reset to {nmax_label} {time.time() - last_time:.2f}s")
    nper_label = nmax_label
    last_time = time.time()
    
    while True:
        candidates = None
        labels = sorted(samples.keys(), key=lambda x: len(samples[x]))

        for ilabel, label in enumerate(labels):
            if len(samples_per_label[label]) == 0:
                continue # no more samples for this label to be added

            ninvalid = set()
            candidates = [] # find the sample with the min invalid
            for isample, sample in enumerate(samples_per_label[label]):
                invalid = 0
                for slabel in ytid_dict[sample][0][2]:
                    old_len = len(samples[slabel])
                    new_len = old_len if sample in samples[slabel] else old_len + 1
                    if new_len > nper_label:
                        invalid += 1
                candidates.append(
                    (isample, invalid)
                )
                if invalid == 0:
                    candidates = [(isample, invalid)]
                    break
                ninvalid.add(invalid)
                #if len(ninvalid) >= 2 and min(ninvalid) == 1:
                #    pass 
            candidates.sort(key=lambda x: x[1]) # all candidate samples
            break
        
        cur_label = label

        if candidates is not None:
            isample, invalid = candidates[0] # minimum invalid sample
            sample = samples_per_label[cur_label][isample]

            if invalid < len(ytid_dict[sample][0][2]):
                for slabel in ytid_dict[sample][0][2]:
                    samples[slabel].add(sample)

            # all invalid samples
            invalid_samples = [sample]
            for isample, invalid in candidates[1:]:
                sample = samples_per_label[cur_label][isample]
                if invalid < len(ytid_dict[sample][0][2]):
                    continue
                invalid_samples.append(sample)
            
            invalid_samples = set(invalid_samples)
            for k, v in samples_per_label.items():
                if len(v) == 0: 
                    continue
                v[:] = [x for x in v if x not in invalid_samples]
#                for sample in invalid_samples:
#                    if sample in v:
#                        v.remove(sample)
        else:
            break
        niter += 1
        done = sum([len(v) == nper_label for k, v in samples.items()])
        if nlabel - done == 0:
            break # len(v) == nper_label may not be reached

        if time.time() - last_time >= interval:
            remained = sum([len(v) != 0 for k, v in samples_per_label.items()])
            this_cnt = sum([len(v) for k, v in samples_per_label.items()])
            nremoved = last_cnt - this_cnt
            last_cnt = this_cnt
            temp_samples = set()
            for k, v in samples.items():
                temp_samples.update(v)   
            nsample = len(temp_samples)
            print(f"# remained {remained}\t# done {done}\t# sample {nsample}\t# removed {nremoved} iter {niter}")
            last_time = time.time()
    
    def count_sample(samples):
        temp_samples = set()
        for k, v in samples.items():
            temp_samples.update(v)   
        nsample = len(temp_samples)
        print(f"# sample {nsample}")
    
    count_sample(samples)

    for sample in extra_samples:
        for slabel in ytid_dict[sample][0][2]:
            samples[slabel].add(sample)  

    count_sample(samples)

    for k, v in samples.items():
        samples[k] = list(v)
    
    return samples

def main_balance():
    csv_root = "/net/nfs2.mosaic/yann/data/audioset/csv"
    ytid_file = f"{csv_root}/all.idx"
    ytid_dict = json.load(open(ytid_file, "r"))
    
    topk = 512
    dist_file = "/home/yanpengz/data/audioset/bimodal_00071478.512"
    candidates = [read_candidate(dist_file, topk, ytid_dict)]

    samples_per_label = copy.deepcopy(candidates[0][0])
    extra_samples = copy.deepcopy(candidates[0][1])
    for k, v in samples_per_label.items():
        samples_per_label[k] = sorted(v, key=lambda x: len(ytid_dict[x][0][2]))
    
    for k, v in samples_per_label.items():
        if len(v) != len(set(v)): # check duplicates
            raise ValueError(f"duplicate samples") 

    interval = 5
    nper_label = 25000 
    balanced = balance_fast(
        samples_per_label, nper_label, ytid_dict, interval=interval, extra_samples=extra_samples
    )

    ofile = f"{dist_file}.{int(nper_label / 1000)}k"
    save_balanced(balanced, ofile)

if __name__ == '__main__':
    main_balance() 
    pass
