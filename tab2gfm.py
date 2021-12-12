#!/usr/bin/env python

import sys

"""
ID Unit     EPS Lapse   
 1   16  130.61 201.993250
 2   16  133.09 202.082445
 3   32  256.35 201.003944
 4   64  510.75 200.588916
 5  128 1030.06 200.362681


ID Unit TS TH     EPS Start               End                 処理時間   
 1   64 20  1   97.80 2021-11-20T01:40:00 2021-11-20T01:43:23 202.770128
 2   64 20  1   98.03 2021-11-20T01:40:00 2021-11-20T01:43:23 202.603824
 3   64 20  1   96.82 2021-11-20T01:40:00 2021-11-20T01:43:23 202.734949
 4   64 20  1   96.91 2021-11-20T01:40:00 2021-11-20T01:43:23 202.766551
 5   64 20  1   97.32 2021-11-20T01:40:00 2021-11-20T01:43:23 202.741718
 6   64 20  1   97.74 2021-11-20T01:40:00 2021-11-20T01:43:22 202.419813
"""

buf = sys.stdin.read().splitlines()
hdr = buf[0]
for n in [
        ("Lapse","処理時間"),
        ("TS","回数"),
        ("Start","開始時刻"),
        ("End","終了時刻")]:
    hdr = hdr.replace(n[0], n[1])
hdr = hdr.split()
th = None
if "TH" in hdr:
    th = hdr.index("TH")
    print(th)
    hdr.pop(th)
ncol = len(hdr)
print("|", "|".join(hdr), "|")
print(f"|{'|'.join(['---']*ncol)}|")
for line in buf[1:]:
    cols = line.split()
    if th is not None:
        cols.pop(th)
    print("|", "|".join(cols), "|")
