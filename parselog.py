#!/usr/bin/env python

import sys
import os
import re
import shutil
from datetime import datetime
from dateutil.parser import parse as dtparse
#graph
import math
import matplotlib.pyplot as plt

if not (sys.version_info.major == 3 and sys.version_info.minor >= 8):
    print("Required Python 3.8 or later")
    exit(0)

from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

ap = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
ap.add_argument("files", nargs="*")
ap.add_argument("--skip-events", action="store", dest="skip_events",
                type=int, default=0,
                help="specify the number of results in the begging to skip.")
ap.add_argument("--post-skip", action="store", dest="post_skip",
                type=int, default=0,
                help="specify the number of results in the end to skip.")
#ap.add_argument("--mode", "-m", action="store", dest="mode",
#                default="sysbench", choices=["sysbench", "openssl", "linpack"],
#                help="specify a mode of the log file.")
ap.add_argument("--move", action="store", dest="logdir",
                help="specify the log directory to rename the file "
                    "based on the string of the log_file in the log file.")
ap.add_argument("--no-stat", action="store_true", dest="no_stat",
                help="disable to show the stat.")
ap.add_argument("-st", "--start-time", action="store", dest="sig_st_time",
                help="specify the start time to take into account.")
ap.add_argument("-et", "--end-time", action="store", dest="sig_et_time",
                help="specify the end time to take into account.")
ap.add_argument("-v", action="count", dest="verbose_level",
                default=0,
                help="increase verbose level.")

# graph options
ap.add_argument("--graph-mode", action="store", dest="graph_mode",
                choices = ["hist-tt", "hist-ibt", "lapse", "clock", "units"],
                help="specify a mode of graph.")
ap.add_argument("--limit-st", action="store", dest="limit_st",
                help="specify a significant timestamp of start to measure.")
ap.add_argument("--limit-et", action="store", dest="limit_et",
                help="specify a significant timestamp of end to measure.")
ap.add_argument("--digits", action="store", dest="digits",
                type=int, default=3,
                help="specify the number of significant digits.")
ap.add_argument("--show-lapse-limit", action="store_true", dest="show_lapse_limit",
                help="specify to show the limit line of lapse.")
ap.add_argument("--interval", action="store", dest="interval",
                type=int, default=20,
                help="specify the number of interval.")
ap.add_argument("--graph-save", action="store", dest="graph_save",
                help="specify the filename of the graph.")

opt = ap.parse_args()

# set significant start/end time
sig_st_time_dt = None
if opt.sig_st_time:
    sig_st_time_dt = dtparse(opt.sig_st_time)
sig_et_time_dt = None
if opt.sig_et_time:
    sig_et_time_dt = dtparse(opt.sig_et_time)
st_bench_dt = None
et_bench_dt = None

#
# parse log file
#

# cpu_units: 128
re_cpu_units = re.compile("^cpu_units: (\d+)")
# nb_threads: 4
re_threads = re.compile("^nb_threads: (\d+)")
# log_file: /iox_data/logs/app20211117T204305x1.log
re_log_file = re.compile("^log_file: (.+)")
# target: sysbench
re_target = re.compile("^target: (.+)")
# value
#     events per second:  1199.80
re_value_sysbench = re.compile("^\s+events per second:\s+([\d\.]+)")
#     rsa 2048 bits 0.000770s 0.000024s   1299.1  41156.4
re_value_openssl = re.compile("^rsa 2048 bits\s+([\d\.]+)s\s+([\d\.]+)s\s+([\d\.]+)\s+([\d\.]+)")
## Sleep: 2021-11-16T15:59:23
re_sleep = re.compile("^## Sleep: ([\d\-T:]+)")
## whole test
re_st_test = re.compile("^## Start: ([\d\-T:\.]+)")
re_et_test = re.compile("^## End\s+: ([\d\-T:\.]+)")
## each test
re_st_bench = re.compile("^Start test (\d+): ([\d\-T:\.]+)")
re_et_bench = re.compile("^End\s+test (\d+): ([\d\-T:\.]+)")

def tdconv(td, minutes: bool=False) -> str:
    if minutes:
        return (datetime.min + td).strftime("%M:%S.%f")[:9]
    else:
        return float(f"{td.seconds:02}.{td.microseconds:06}")

G = []
target = None
data_no = 0
for f in opt.files:
    data_no += 1
    re_value = None
    with open(f) as fd:
        g = { "filename": f, "nb_tests": 0, "cpu_units": 0,
             "ott_set": [], # one_test_time (ott)
             "one_test_time": [],
             "interval_btw_tests": [],
             }
        val_list = []
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
            elif (r := re_target.search(line)):
                target = r.group(1)
                if target == "sysbench":
                    re_value = re_value_sysbench
                elif target == "openssl":
                    re_value = re_value_openssl
                elif target == "linpack":
                    print("ERROR: linkpack, not supported yet.")
                    exit(0)
            elif target == "sysbench" and (r := re_value_sysbench.search(line)):
                val_list.append(float(r.group(1)))
            elif target == "openssl" and (r := re_value_openssl.search(line)):
                val_list.append([float(r.group(3)), float(r.group(4))])
            elif (r := re_cpu_units.search(line)):
                g["cpu_units"] = int(r.group(1))
            elif (r := re_threads.search(line)):
                g["nb_threads"] = int(r.group(1))
            elif (r := re_sleep.search(line)):
                g["sleep"] = r.group(1)
            elif (r := re_st_test.search(line)):
                # start time for the whole test.
                if opt.sig_st_time:
                    g["st_test"] = opt.sig_st_time
                    g["st_test_short"] = opt.sig_st_time
                else:
                    g["st_test"] = r.group(1)
                    g["st_test_short"] = r.group(1)[:19]
            elif (r := re_et_test.search(line)):
                # end time for the whole test.
                if opt.sig_et_time:
                    g["et_test"] = opt.sig_et_time
                    g["et_test_short"] = opt.sig_et_time
                else:
                    g["et_test"] = r.group(1)
                    g["et_test_short"] = r.group(1)[:19]
                # test time(tt) in string, NN.NNNNNN
                g["tt"] = tdconv(dtparse(g["et_test"]) -
                                 dtparse(g["st_test"]), minutes=False)
            elif (r := re_st_bench.search(line)):
                # start time for a single test.
                st_bench = r.group(2)
                st_bench_dt = dtparse(st_bench)
                if et_bench_dt and (sig_st_time_dt is None or
                                    st_bench_dt >= sig_st_time_dt):
                    #print("S", et_bench_dt, sig_st_time_dt, st_bench_dt, sig_st_time_dt)
                    if g["nb_tests"] > 0:
                        g["interval_btw_tests"].append(
                                tdconv(st_bench_dt - et_bench_dt))
            elif (r := re_et_bench.search(line)):
                # end time for a single test.
                et_bench = r.group(2)
                et_bench_dt = dtparse(et_bench)
                if st_bench_dt and (sig_et_time_dt is None or
                                    et_bench_dt <= sig_et_time_dt):
                    #print("E", st_bench_dt, sig_et_time_dt, et_bench_dt, sig_et_time_dt)
                    g["nb_tests"] += 1
                    g["ott_set"].append({ "st": st_bench, "et": et_bench })
                    g["one_test_time"].append(tdconv(et_bench_dt - st_bench_dt))
                    if len(g["ott_set"]) != len(g["one_test_time"]):
                        raise ValueError("ERROR: len of ott_set != one_test_time")
                    if len(g["one_test_time"]) != 1+len(g["interval_btw_tests"]):
                        raise ValueError("ERROR: len mismatch, ott != ibt+1"
                                        f"{g['one_test_time']} != "
                                        f"{g['interval_btw_tests']}+1")
        else:
            # check and fix the entries.
            if len(val_list) == 0:
                print(f"ERROR: any value for {target} don't exist in the log.")
                exit(0)
            if opt.skip_events:
                val_list = val_list[opt.skip_events:]
            if opt.post_skip:
                val_list = val_list[:-opt.post_skip]
            if len(val_list) == 0:
                print("ERROR: the result become zero by skipping. "
                    "must specify skip_events or post_skip properly.")
                exit(0)
            if target == "sysbench":
                g["eps"] = round(sum(val_list)/len(val_list), 2)
            elif target == "openssl":
                g["sign_s"] = round(sum([v[0] for v in val_list])/len(val_list), 1)
                g["verify_s"] = round(sum([v[1] for v in val_list])/len(val_list), 1)
            if g["cpu_units"] == 0:
                # NOTE: this is for old style.
                # the units was taken from the name of the log file.
                base = os.path.basename(f)
                if base.startswith("app") and "-" in base:
                    # i.e. old naming.
                    try:
                        g["cpu_units"] = int(base[3:base.index("-")])
                    except:
                        # ignore
                        pass
            g["data_no"] = data_no
            G.append(g)

# rename only if opt.logdir
if opt.logdir:
    exit(0)

#
# graph
#
def round_half_up(n, ndigits=0):
    if ndigits:
        n *= pow(10,ndigits)
    if (n > 0 and n - math.floor(n) < 0.5):
        n = math.floor(n)
    else:
        n = math.ceil(n)
    if ndigits:
        n /= pow(10,ndigits)
    return n

def mkgraph_lapse_do(K):
    # graph
    fig = plt.figure(figsize=(12,5))
    ax1 = fig.add_subplot(1,1,1)
    x_max_list = []
    lines = []
    #for k,v in K.items():
    for k,v in sorted(K.items(), key=lambda x: x[0]):
        lines += ax1.plot(v["x"], v["y"], label=k, marker="+")
        x_max_list.append(v["x"][-1])
    if opt.show_lapse_limit:
        limit = max([v["nb_tests"] for v in G])*10
        ax1.axvline(x=limit*1.02, color="red", linewidth=.5, alpha=0.7)
        ax1.axvline(x=limit*1.01, color="blue", linewidth=.5, alpha=0.7)

    ax1.set_xlabel("Lapse")
    ax1.set_ylabel("CPU Units")
    plt.xticks(range(0, int(max(x_max_list)+10),opt.interval))
    ax1.axes.yaxis.set_ticklabels([])

    plt.minorticks_on()
    ax1.grid(visible=True, axis="x", which="major")
    ax1.grid(visible=True, axis="x", which="minor", color="black", alpha=.3)

    plt.xlim(left=0)
    plt.setp(ax1.get_xticklabels(), rotation=90, ha="center")

    ax1.legend(lines, [i.get_label() for i in lines], bbox_to_anchor=(1.0,1.0))
    fig.tight_layout()
    return plt

def mkgraph_lapse(G):
    K = {}
    for v in G:
        g = K.setdefault(v["cpu_units"], {
                # clock the end time of each event.
                # NOTE: 0, ott1, ibt1, ott2, ibt2, ott3
                "x": [0, float(v["one_test_time"][0])],
                "y": [len(v["one_test_time"]) - v["data_no"]
                      for _ in range(1+len(v["one_test_time"]))],
                })
        for i,n in enumerate(v["interval_btw_tests"]):
            g["x"].append(g["x"][1+i] + float(n) +
                          float(v["one_test_time"][i+1]))
    return mkgraph_lapse_do(K)

def mkgraph_clock(G):
    # get a minimum st.
    origin = min([dtparse(v["st_test"]) for v in G])
    K = {}
    for v in G:
        st = (dtparse(v["st_test"]) - origin).total_seconds()
        g = K.setdefault(v["cpu_units"], {
                # clock the end time of each event.
                # NOTE: 0, ott1, ibt1, ott2, ibt2, ...
                "x": [st, st+float(v["one_test_time"][0])],
                "y": [len(v["one_test_time"]) - v["data_no"]
                      for _ in range(1+len(v["one_test_time"]))],
                })
        for i,n in enumerate(v["interval_btw_tests"]):
            g["x"].append(g["x"][1+i] + float(n) +
                          float(v["one_test_time"][i+1]))
    return mkgraph_lapse_do(K)

def mkgraph_hist_tt(G):
    K = {}
    if opt.limit_st:
        limit_st_dt = dtparse(opt.limit_st)
    if opt.limit_et:
        limit_et_dt = dtparse(opt.limit_et)
    for i,v in enumerate(G):
        g = K.setdefault(v["cpu_units"], {
                "data_no": 1+i,
                "hist_tt": {},
                })
        st = dtparse(v["st_test"])
        for j,ott in enumerate(v["ott_set"]):
            if opt.limit_st and dtparse(ott["st"]) <= limit_st_dt:
                continue
            if opt.limit_et and dtparse(ott["et"]) >= limit_et_dt:
                continue
            n = round_half_up(float(v["one_test_time"][j]), opt.digits)
            g["hist_tt"].setdefault(n, 0)
            g["hist_tt"][n] += 1
    # graph
    fig = plt.figure(figsize=(8,6))
    ax1 = fig.add_subplot(1,1,1)
    tweak = len(K.items())
    for k,v in K.items():
        ax1.scatter(v["hist_tt"].keys(),
                    [i+(v["data_no"]/tweak) for i in v["hist_tt"].values()],
                    label=k,
                    marker="o",
                    s=4)
    ax1.set_xlabel("Test Time")
    ax1.set_ylabel("Number of Events")
    plt.legend()
    fig.tight_layout()
    return plt

def mkgraph_hist_ibt(G):
    K = {}
    if opt.limit_st:
        limit_st_dt = dtparse(opt.limit_st)
    if opt.limit_et:
        limit_et_dt = dtparse(opt.limit_et)
    for i,v in enumerate(G):
        g = K.setdefault(v["cpu_units"], {
                "data_no": 1+i,
                "hist_ibt": {},
                })
        st = dtparse(v["st_test"])
        for j,ott in enumerate(v["ott_set"]):
            # NOTE: st1, et1, ibt1, st2, et2, ibt2, ...
            # [st1, st2]
            # [et1, et2]
            # [ibt1, ibt2]
            if opt.limit_st and dtparse(ott["st"]) <= limit_st_dt:
                continue
            if opt.limit_et and dtparse(ott["et"]) >= limit_et_dt:
                continue
            n = round_half_up(float(v["interval_btw_tests"][j]), opt.digits)
            g["hist_ibt"].setdefault(n, 0)
            g["hist_ibt"][n] += 1
    # graph
    fig = plt.figure(figsize=(8,6))
    ax1 = fig.add_subplot(1,1,1)
    #for k,v in sorted(G.items(), key=lambda x: int(x[0]), reverse=True):
    tweak = len(K.items())
    for k,v in K.items():
        ax1.scatter(v["hist_ibt"].keys(),
                    [i+(v["data_no"]/tweak) for i in v["hist_ibt"].values()],
                    label=k,
                    marker="o",
                    s=4)
    ax1.set_xlabel("Interval b/w Tests")
    ax1.set_ylabel("Number of Events")
    plt.legend()
    fig.tight_layout()
    return plt

if opt.graph_mode is not None:
    ret = None
    if opt.graph_mode== "hist-tt":
        ret = mkgraph_hist_tt(G)
    elif opt.graph_mode == "hist-ibt":
        ret = mkgraph_hist_ibt(G)
    elif opt.graph_mode == "lapse":
        ret = mkgraph_lapse(G)
    elif opt.graph_mode == "clock":
        ret = mkgraph_clock(G)
    elif opt.graph_mode == "units":
        pass
    elif opt.graph_mode is not None:
        raise RuntimeError("ERROR: should not come here.")
        exit(-1)
    if ret:
        if opt.graph_save:
            ret.savefig(opt.graph_save)
        ret.show()

# print result.
# NOTE: enumerate number is set into "ID" 
if target == "sysbench":
    if opt.verbose_level == 0:
        hdrfmt = "{:>2} {:>4} {:>7} {:8}"
        hdr = ["ID", "Unit", "EPS", "Lapse"]
        fmt = "{:>2} {:>4} {:>7.2f} {:8}"
        vkey = ["cpu_units", "eps", "tt"]
    else: # opt.verbose_level > 0
        hdrfmt = "{:>2} {:>4} {:>2} {:>2} {:>7} {:19} {:19} {:8}"
        hdr = ["ID", "Unit", "TS", "TH", "EPS", "Start", "End", "Lapse"]
        fmt = "{:>2} {:>4} {:>2} {:>2} {:>7.2f} {:19} {:19} {:8}"
        vkey = ["cpu_units", "nb_tests", "nb_threads", "eps",
            "st_test_short", "et_test_short", "tt"]
elif target == "openssl":
    hdrfmt = "{:>2} {:>4} {:>2} {:>2} {:>6} {:>8} {:19} {:19} {:8}"
    hdr = ["ID", "Unit", "TS", "TH", "Sign/s", "Verify/s", "Start", "End", "Lapse"]
    fmt = "{:>2} {:>4} {:>2} {:>2} {:>6} {:>8} {:19} {:19} {:8}"
    vkey = [ "cpu_units", "nb_tests", "nb_threads", "sign_s", "verify_s",
          "st_test_short", "et_test_short", "tt" ]

if not opt.no_stat:
    print(hdrfmt.format(*hdr))
    for i,v in enumerate(sorted(G, key=lambda x: x["cpu_units"])):
        print(fmt.format(1+i, *[ v[p] for p in vkey ]))
        if opt.verbose_level >= 2:
            print(f"    Filename : {v['filename']}")
            print(f"    Sleep Time: {v['sleep']}")
            print(f"    Test Time: {v['one_test_time']}")
            print(f"    Interval btw Tests: {v['interval_btw_tests']}")
            print(f"    Timestamp Set: {v['ott_set']}")


