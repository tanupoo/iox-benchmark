#!/usr/bin/env python

import sys
import re
from datetime import datetime, timedelta
from dateutil.parser import parse as dtparse
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, SecondLocator

"""
unit ts th     eps start               end                 elaps   
  64 20  1  183.24 2021-11-19T15:50:00 2021-11-19T15:53:21 03:21.208
    file : log/64x12/app20211119T153927x2.log
    sleep: 2021-11-19T15:44:34
    test time: [10.047928, 10.087482, 10.054598, 10.069346, 10.029773, 10.067683, 10.037717, 10.044905, 10.017575, 10.049297, 10.046205, 10.03976, 10.124311, 10.039547, 10.057836, 10.038811, 10.059954, 10.060637, 10.067109, 10.037607]
    span btw tests: [0.012666, 0.001657, 0.011592, 0.001385, 0.001908, 0.002286, 0.001445, 0.002587, 0.009669, 0.005291, 0.001376, 0.005873, 0.001718, 0.015675, 0.008777, 0.001466, 0.010058, 0.001941, 0.019041]
"""

re_head = re.compile("^\s*(\d+)\s+(\d+)\s+(\d+)\s+([\d\.]+)\s+"
                     "([^\s]+)\s+([^\s]+)")
re_tt = re.compile("^\s+test time: \[([\d\.,\s]+)\]")
re_tbt = re.compile("^\s+span btw tests: \[([\d\.,\s]+)\]")

def gettd(tstr):
    # convert tstr (e.g."00.000") into timedelta.
    tt_sec, tt_usec = tstr.split(".")
    return timedelta(seconds=int(tt_sec), microseconds=int(tt_usec))

G = []
data_no = -1
for line in sys.stdin:
    if (r := re_head.search(line)):
        label = r.group(1)
        st = dtparse(r.group(5))
        et = dtparse(r.group(6))
    elif (r := re_tt.search(line)):
        tt = r.group(1).replace(",","").split()
    elif (r := re_tbt.search(line)):
        tbt = r.group(1).replace(",","").split()
        # make a data set
        data_no += 1
        t_list = [st, st+gettd(tt[0])]
        for i,k in enumerate(tbt):
            t_list.append(t_list[1+i] + gettd(k) + gettd(tt[1+i]))
        G.append({
                "label": label,
                "x": t_list,
                "y": [ len(t_list) - data_no for i in t_list ],
                })

fig = plt.figure(figsize=(8,5))
ax1 = fig.add_subplot(1,1,1)
lines = []
for v in G:
    lines += ax1.plot(v["x"], v["y"], label=v["label"], marker="x")

ax1.set_xlabel("Timestamp")
ax1.set_ylabel("CPU Units")
ax1.axes.yaxis.set_ticklabels([])

ax1.grid(visible=True, axis="x", which="major")
ax1.grid(visible=True, axis="x", which="minor", color="black", alpha=.2)
plt.minorticks_on()
ax1.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
ax1.xaxis.set_major_locator(MinuteLocator(byminute=range(60)))
ax1.xaxis.set_minor_locator(SecondLocator(bysecond=[10,20,30,40,50]))
#fig.autofmt_xdate()
#fig.autofmt_xdate(rotation=90)
plt.setp(ax1.get_xticklabels(), rotation=90, ha="center")

ax1.legend(lines, [i.get_label() for i in lines], bbox_to_anchor=(1.0,0.8))
fig.tight_layout()
plt.savefig("graph.png")
plt.show()
