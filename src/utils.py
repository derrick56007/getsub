import os
from ntpath import basename

def mkdir(d):
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def basename_without_ext(path):
    return ".".join(basename(path).split(".")[:-1])