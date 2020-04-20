# vim: et:ts=4:sw=4:fenc=utf-8

import os
import re

import matplotlib as mpl
import matplotlib.pyplot as plt

def make_unique(fn):
    res = fn
    pat = re.compile("\d+$")
    while os.path.exists(res):
        name, ext = os.path.splitext(res)
        mat = pat.search(name)
        if mat is None:
            if name[-1] != "_":
                name += "_"
            name += "0"
        else:
            prev = mat.group(0)
            new_num = int(prev) + 1
            len_prev = len(prev)
            len_new = max(len_prev, len(str(new_num)))
            name = name[:-len_prev]
            name = ("{}{:0" + str(len_new) + "d}").format(name, new_num)
        res = name + ext
    return res


