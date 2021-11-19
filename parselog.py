#!/usr/bin/env python

import sys
import os
import re
import shutil
from datetime import datetime
from dateutil.parser import parse as dtparse

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
ap.add_argument("--move", action="store", dest="logdir",
                help="specify the log directory to rename the file "
                    "based on the string of the log_file in the log file.")
ap.add_argument("-v", action="store_true", dest="verbose",
                help="enable verbose mode.")
opt = ap.parse_args()

# cpu_units: 128
re_cpu_units = re.compile("^cpu_units: (\d+)")
# nb_threads: 4
re_threads = re.compile("^nb_threads: (\d+)")
# log_file: /iox_data/logs/app20211117T204305x1.log
re_log_file = re.compile("^log_file: (.+)")
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
## whole test
re_start_test = re.compile("^## Start: ([\d\-T:\.]+)")
re_end_test = re.compile("^## End\s+: ([\d\-T:\.]+)")
## each test
re_start_bench = re.compile("^Start test (\d+): ([\d\-T:\.]+)")
re_end_bench = re.compile("^End\s+test (\d+): ([\d\-T:\.]+)")

def tdconv(td, minutes: bool=False) -> str:
    if minutes:
        return (datetime.min + td).strftime("%M:%S.%f")[:9]
    else:
        return f"{td.seconds:02}.{td.microseconds:06}"

# log file name: appNNN-xxxx
# e.g. app128-YXBwMTI4LmxvZw==
G = {}
file_no = 0
for f in opt.files:
    file_no += 1
    with open(f) as fd:
        g = { "filename": f, "nb_tests": 0, "cpu_units": 0 }
        val_list = []
        single_test_time = []
        span_between_tests = []
        end_bench_dt = -1   # for calculating time span of two tests.
        # read lines and take data.
        for line in fd:
            if (r := re_log_file.search(line)):
                if opt.logdir:
                    # if opt.logdir, rename it and stop to parse remaining.
                    if not os.path.exists(opt.logdir):
                        os.makedirs(opt.logdir)
                    dst = f"{opt.logdir}/{os.path.basename(r.group(1))}"
                    if os.path.exists(dst):
                        print(f"{dst} exists already")
                        exit(0)
                    shutil.move(f, f"{dst}")
                    print(f"Renamed: {dst} from {f}")
                    break
            elif (r := re_value.search(line)):
                if opt.mode == "sysbench":
                    val_list.append(float(r.group(1)))
                elif opt.mode == "openssl":
                    val_list.append([float(r.group(3)), float(r.group(4))])
            elif (r := re_cpu_units.search(line)):
                g["cpu_units"] = int(r.group(1))
            elif (r := re_threads.search(line)):
                g["nb_threads"] = int(r.group(1))
            elif (r := re_sleep.search(line)):
                g["sleep"] = r.group(1)
            elif (r := re_start_test.search(line)):
                # start time for the whole test.
                g["start_test"] = r.group(1)
                g["start_test_short"] = r.group(1)[:19]
            elif (r := re_end_test.search(line)):
                # end time for the whole test.
                g["end_test"] = r.group(1)
                g["end_test_short"] = r.group(1)[:19]
                g["test_time"] = tdconv(dtparse(g["end_test"]) -
                                        dtparse(g["start_test"]), minutes=True)
            elif (r := re_start_bench.search(line)):
                # start time for a single test.
                start_bench_dt = dtparse(r.group(2))
                if end_bench_dt != -1:
                    span_between_tests.append(
                            tdconv(start_bench_dt - end_bench_dt))
            elif (r := re_end_bench.search(line)):
                # end time for a single test.
                g["nb_tests"] += 1
                end_bench_dt = dtparse(r.group(2))
                single_test_time.append(tdconv(
                        end_bench_dt - start_bench_dt))
        else:
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
            g["single_test_time"] = single_test_time
            g["span_between_tests"] = span_between_tests
            if g["cpu_units"] == 0:
                # set cpu_units somewhow
                base = os.path.basename(f)
                if base.startswith("app") and "-" in base:
                    # i.e. old naming.
                    try:
                        g["cpu_units"] = int(base[3:base.index("-")])
                    except:
                        # ignore
                        pass
            G[file_no] = g

# rename only if opt.logdir
if opt.logdir:
    exit(0)

# print result.
if opt.mode == "sysbench":
    hdrfmt = "{:>4} {:>2} {:>2} {:>7} {:19} {:19} {:8}"
    hdr = ["unit", "ts", "th", "eps", "start", "end", "elaps"]
    fmt = "{:>4} {:>2} {:>2} {:>7.2f} {:19} {:19} {:8}"
    vkey = [ "cpu_units", "nb_tests", "nb_threads", "eps",
          "start_test_short", "end_test_short", "test_time" ]
elif opt.mode == "openssl":
    hdrfmt = "{:>4} {:>2} {:>2} {:>6} {:>8} {:19} {:19} {:8}"
    hdr = ["unit", "ts", "th", "sign/s", "verify/s", "start", "end", "elaps"]
    fmt = "{:>4} {:>2} {:>2} {:>6} {:>8} {:19} {:19} {:8}"
    vkey = [ "cpu_units", "nb_tests", "nb_threads", "sign_s", "verify_s",
          "start_test_short", "end_test_short", "test_time" ]

print(hdrfmt.format(*hdr))
def tt(v):
    print(v)
    return 0

for k,v in sorted(G.items(), key=lambda x: x[1]["cpu_units"]):
    print(fmt.format(*[ v[p] for p in vkey ]))
    if opt.verbose:
        print(f"    file : {v['filename']}")
        print(f"    sleep: {v['sleep']}")
        print(f"    test time: {v['single_test_time']}")
        print(f"    span btw tests: {v['span_between_tests']}")


