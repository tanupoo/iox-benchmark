#!/usr/bin/env python

import sys

def expand_units(units_str: str) -> str:
    units_list = []
    try:
        for u in units_str.split():
            if "x" in u:
                arr = u.split("x")
                units = [arr[0]]
                for i in arr[1:]:
                    units *= int(i)
                units_list.extend(units)
            else:
                int(u) # just a test
                units_list.append(u)
        return " ".join(units_list)
    except ValueError:
        print(f"'{u}' is invalid.", file=sys.stderr)
        return ""

if __name__ == "__main__":
    test_vector = [
        "128 64 32",
        "16x4",
        "8x2x3",
        "32 128x3 16x3x2 512",
        "128 u 32",
        "128 x 32",
    ]
    if sys.argv[1] == "test":
        for v in test_vector:
            print(f"{v} => {expand_units(v)}")
    else:
        print(expand_units(" ".join(sys.argv[1:])))
