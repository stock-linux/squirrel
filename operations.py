import os
from utils.db import checkPkgExists, checkPkgInstalled, getPkgBranch, getPkgFile, getPkgInfo, registerPkg, unregisterPkg
from utils.logger import *

import requests
import sys
import tempfile
import utils.archive as archive
import utils.config as config

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
    print()

def get(packages):
    for package in packages:
        packageExists = checkPkgExists(package)
        if not packageExists:
            logError("package '" + package + "' does not exist in repos !")
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

        if len(pkgInfo['rundeps']) > 0:
            logInfo('Getting package dependencies...')

        for d in pkgInfo['rundeps']:
            installPkg(d, getPkgInfo(d))
        
        if len(packages) == 1:
            print('---------------')
            print("Package '" + pkgInfo['name'] + "':")
            print("===> Version: " + pkgInfo['version'])
            print("===> Author: " + pkgInfo['author'])
            print("===> Maintainer: " + pkgInfo['maintainer'])
            print("===> Source: " + pkgInfo['source'])
            if 'url' in pkgInfo:
                print("===> Homepage: " + pkgInfo['url'])
            print('---------------')
            
        installPkg(package, pkgInfo)
    pass

def installPkg(package, pkgInfo):
    print()
    tempDir = tempfile.TemporaryDirectory('squirrel-' + package)
    os.chdir(tempDir.name)
    downloadPkg(getPkgBranch(package)[list(getPkgBranch(package).keys())[0]] + '/bins/' + pkgInfo['name'] + '-' + pkgInfo['version'] + '.tar.xz', package)
    if 'ROOT' not in os.environ:
        os.environ['ROOT'] = '/'
    os.chdir(os.environ['ROOT'])
    archive.extractPkgArchive(tempDir.name + '/' + pkgInfo['name'] + '-' + pkgInfo['version'] + '.tar.xz')
    if checkPkgInstalled(package):
        unregisterPkg(package)
    registerPkg(package, pkgInfo['version'])
    os.popen('mv .TREE ' + config.localPath + list(getPkgBranch(package).keys())[0] + '/' + package + '.tree')

def update(package):
    pass

def info(package):
    pass

def upgrade():
    pass