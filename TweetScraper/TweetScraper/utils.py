import os

def mkdirs(dirs):
    if not os.path.exists(dirs):
        os.makedirs(dirs)

