import os

def extractPkgArchive(archive):
    os.system('tar --same-owner -xhpf ' + archive + ' --strip-components=1')