#!/usr/bin/env python

import sys
import os
import re
from datetime import datetime
from dateutil.parser import parse as dateparse

if not (sys.version_info.major == 3 and sys.version_info.minor >= 8):
    print("Required Python 3.8 or later")
    exit(0)

from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

ap = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
ap.add_argument("files", nargs="*")
ap.add_argument("--pre-skip", action="store", dest="pre_skip",
                type=int, default=0,
                help="specify the number of results in the begging to skip.")
ap.add_argument("--post-skip", action="store", dest="post_skip",
                type=int, default=0,
                help="specify the number of results in the end to skip.")
ap.add_argument("-m", action="store", dest="mode",
                default="sysbench", choices=["sysbench", "openssl", "linpack"],
                help="specify a mode of the log file.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="enable verbose mode.")
opt = ap.parse_args()

# value
if opt.mode == "sysbench":
    #     events per second:  1199.80
    re_value = re.compile("^\s+events per second:\s+([\d\.]+)")
elif opt.mode == "openssl":
    # rsa 2048 bits 0.000770s 0.000024s   1299.1  41156.4
    re_value = re.compile("^rsa 2048 bits\s+([\d\.]+)s\s+([\d\.]+)s\s+([\d\.]+)\s+([\d\.]+)")
elif opt.mode == "linpack":
    print("linkpack, not supported yet.")
    exit(0)
## Sleep: 2021-11-16T15:59:23
re_sleep = re.compile("^## Sleep: ([\d\-T:]+)")
## Start: 2021-11-16T15:59:23
re_start_test = re.compile("^## Start: ([\d\-T:]+)")
re_end_test = re.compile("^## End\s+: ([\d\-T:]+)")
re_start_bench = re.compile("^Start test (\d+): ([\d\-T:]+)")
re_end_bench = re.compile("^End\s+test (\d+): ([\d\-T:]+)")
## nb_threads: 4
re_threads = re.compile("^nb_threads: (\d+)")

# log file name: appNNN-xxxx
# e.g. app128-YXBwMTI4LmxvZw==
G = {}
file_no = 0
for f in opt.files:
    file_no += 1
    with open(f) as fd:
        g = { "filename": f, "nb_tests": 0 }
        val_list = []
        test_time_delta = []
        time_delta_between_tests = []
        # read lines and take data.
        for line in fd:
            if (r := re_value.search(line)):
                if opt.mode == "sysbench":
                    val_list.append(float(r.group(1)))
                elif opt.mode == "openssl":
                    val_list.append([float(r.group(3)), float(r.group(4))])
            elif (r := re_threads.search(line)):
                g["nb_threads"] = int(r.group(1))
            elif (r := re_sleep.search(line)):
                g["sleep"] = r.group(1)
            elif (r := re_start_test.search(line)):
                g["start_test"] = r.group(1)
            elif (r := re_end_test.search(line)):
                g["end_test"] = r.group(1)
                g["test_time"] = str(dateparse(g["end_test"]) -
                                     dateparse(g["start_test"]))
            elif (r := re_start_bench.search(line)):
                start_bench_dt = dateparse(r.group(2))
                if r.group(1) != "1":
                    time_delta_between_tests.append(
                            (start_bench_dt - end_bench_dt).seconds)
            elif (r := re_end_bench.search(line)):
                g["nb_tests"] += 1
                end_bench_dt = dateparse(r.group(2))
                test_time_delta.append((end_bench_dt - start_bench_dt).seconds)
        # check and fix the entries.
        if len(val_list) == 0:
            print(f"ERROR: any value for {opt.mode} don't exist in the log.")
            exit(0)
        if opt.pre_skip:
            val_list = val_list[opt.pre_skip:]
        if opt.post_skip:
            val_list = val_list[:-opt.post_skip]
        if len(val_list) == 0:
            print("ERROR: the result become zero by skipping. "
                  "must specify pre_skip or post_skip properly.")
            exit(0)
        if opt.mode == "sysbench":
            g["eps"] = round(sum(val_list)/len(val_list), 2)
        elif opt.mode == "openssl":
            g["sign_s"] = round(sum([v[0] for v in val_list])/len(val_list), 1)
            g["verify_s"] = round(sum([v[1] for v in val_list])/len(val_list), 1)
        g["test_time_delta"] = test_time_delta
        g["time_delta_between_tests"] = time_delta_between_tests
        g["units"] = 0
        base = os.path.basename(f)
        if base.startswith("app") and "-" in base:
            g["units"] = int(base[3:base.index("-")])
        G[file_no] = g

# print result.
if opt.mode == "sysbench":
    fmt = "{:>3} {:>2} {:>2} {:>7} {:19} {:19} {:8}"
    hdr = ["un", "ts", "th", "val", "start", "end", "elaps"]
    vkey = [ "units", "nb_tests", "nb_threads", "eps",
          "start_test", "end_test", "test_time" ]
elif opt.mode == "openssl":
    fmt = "{:>3} {:>2} {:>2} {:>6} {:>8} {:19} {:19} {:8}"
    hdr = ["un", "ts", "th", "sign/s", "verify/s", "start", "end", "elaps"]
    vkey = [ "units", "nb_tests", "nb_threads", "sign_s", "verify_s",
          "start_test", "end_test", "test_time" ]

print(fmt.format(*hdr))
def tt(v):
    print(v)
    return 0

for k,v in sorted(G.items(), key=lambda x: x[1]["units"]):
    print(fmt.format(*[ v[p] for p in vkey ]))
    if opt.verbose:
        print(f"    file : {v['filename']}")
        print(f"    sleep: {v['sleep']}")
        print(f"    test time: {v['test_time_delta']}")
        print(f"    td btw tests: {v['time_delta_between_tests']}")


