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
            elif "to" in u:
                arr = u.split("to")
                if len(arr) > 3:
                    raise ValueError("ERROR: in AtoB case, "
                                     "'to' can be used at once.")
                max_value = int(arr[1])
                units = [int(arr[0])]
                while units[-1] < max_value:
                    units.append(units[-1]*2)
                if units[-1] != max_value:
                    raise ValueError("ERROR: in AtoB case, "
                                     "B must be a multiple of 2 of A.")
                units_list.extend(units)
            else:
                int(u) # just a test
                units_list.append(u)
        return " ".join([str(i) for i in units_list])
    except ValueError:
        print(f"'{u}' is invalid.", file=sys.stderr)
        return ""

if __name__ == "__main__":
    test_vector = [
        ( "128 64 32", "128 64 32" ),
        ( "16x4",      "16 16 16 16" ),
        ( "4to64",     "4 8 16 32 64" ),
        ( "8x2x3",     "8 8 8 8 8 8 8 8" ),
        ( "32 128x3 16x3x2 512", "32 128 128 128 16 16 16 16 16 16 512" ),
        ( "128 u 32", ""), # error
        ( "128 x 32", ""), # error
    ]
    if sys.argv[1] == "test":
        for iv,ov in test_vector:
            print(f"{iv} => {expand_units(iv)} =? {ov}")
    else:
        print(expand_units(" ".join(sys.argv[1:])))
