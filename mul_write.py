import multiprocessing
import subprocess
import requests
import datetime
import time, re
import math

err_file = "mul_write.out"

def mp_worker(item):
    return item, item + 1

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
            #print(f"{r._number_left}", end=" ")
            if c % k == 0: print()
            time.sleep(secs)
    r.wait()
    p.close()
    p.join()

if __name__ == '__main__':
    ytids = list(range(15))
    mp_handler(ytids, nprocess=5, secs=3)

