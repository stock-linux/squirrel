import os
from utils.db import checkPkgExists, checkPkgInstalled, getPkgFile, getPkgInfo
from utils.logger import *

import requests
import sys
import tempfile

def downloadPkg(url, packageName):
    file_name = url.split('/')[-1]

    with open(file_name, "wb") as f:
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')

        if total_length is None: # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=8192):
                dl += len(data)
                f.write(data)
                done = int(100 * dl / total_length)
                sys.stdout.write("\rDownloading package '" + packageName + "' " + str(done) + "%")    
                sys.stdout.flush()

def get(packages):
    for package in packages:
        packageExists = checkPkgExists(package)
        if not packageExists:
            logError("package '" + package + "' does not exist in repos !")
            return 1

        packageInstalled = checkPkgInstalled(package)
        if packageInstalled:
            logInfo("package '" + package +"' is already installed.")
            needInstall = input("Do you want to reinstall the package ? (Y/N) ")
            needInstall = needInstall.lower()

            if needInstall != 'y':
                return 1

    for package in packages:
        print('[+] ' + package)
    print()
    permission = input('Do you really want to install these packages ? (Y/N) ')
    permission = permission.lower()

    if permission != 'y':
        return 1
    
    logInfo("Getting packages infos...")
    for package in packages:
        packageInfoPath = getPkgFile(package)

        if packageInfoPath == None:
            logError("There are some errors in repos for the package '" + package + "' ! Call an admin.")

        pkgInfo = getPkgInfo(package)

        if len(packages) == 1:
            print('---------------')
            print("Package '" + pkgInfo['name'] + "':")
            print("===> Version: " + pkgInfo['version'])
            print("===> Author: " + pkgInfo['author'])
            print("===> Maintainer: " + pkgInfo['maintainer'])
            if 'url' in pkgInfo:
                print("===> Homepage: " + pkgInfo['url'])
            print('---------------')

        tempDir = tempfile.TemporaryDirectory('squirrel-' + package)
        os.chdir(tempDir.name)
        downloadPkg(pkgInfo['source'], package)
        print()
        print(os.listdir())

    pass

def update(package):
    pass

def info(package):
    pass

def upgrade():
    pass