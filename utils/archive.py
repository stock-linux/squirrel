import os

def extractPkgArchive(archive):
    os.system('tar -xf ' + archive + ' --strip-components=1')