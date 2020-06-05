import os

def mkdir(d):
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)