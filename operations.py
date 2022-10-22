import os
from utils.db import checkPkgExists, checkPkgInstalled, getBranchPkgs, getBranches, getPkgBranch, getPkgFile, getPkgInfo, registerPkg, unregisterPkg
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
    # Check if packages names correspond to any branch name
    branchesToGet = []
    packagesToGet = []
    branches = getBranches()
    for branch in branches:
        for package in packages:
            if package == branch:
                branchesToGet.append(branch)
                branchPkgs = getBranchPkgs(branch)
                for branchPkg in branchPkgs:
                    packagesToGet.append(branchPkg)
            else:
                packagesToGet.append(package)

    for package in packagesToGet:
        packageExists = checkPkgExists(package)
        if not packageExists:
            logError("package '" + package + "' does not exist in repos !")
            return 1

    print('-----PACKAGE INSTALLATION-----')
    for package in packagesToGet:
        print('[+] ' + package)

    for branch in branchesToGet:
        print('[+branch] ' + branch)

    print()
    permission = input('Do you really want to install these packages ? (Y/N) ')
    print()
    permission = permission.lower()

    if permission != 'y':
        return 1
    
    logInfo("Getting packages infos...")
    for package in packagesToGet:
        getPkg(package, len(packagesToGet))

def getPkg(package, pkgCount):
    if checkPkgInstalled(package):
        logInfo("package '" + package + "' is already installed.")
        return
    packageInfoPath = getPkgFile(package)

    if packageInfoPath == None:
        logError("There are some errors in repos for the package '" + package + "' ! Call an admin.")

    pkgInfo = getPkgInfo(package)

    if 'rundeps' in pkgInfo and len(pkgInfo['rundeps']) > 0:
        logInfo('Getting package dependencies...')

        for d in pkgInfo['rundeps']:
            if not checkPkgInstalled(d):
                installPkg(d, getPkgInfo(d))
            else:
                logInfo("dependency '" + d + "' is already installed.")
    
    if pkgCount == 1:
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
    print()

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
    logInfo("package '" + package + "' has been successfully installed.")

def remove(packages):
    branchesToRemove = []
    packagesToRemove = []
    branches = getBranches()
    for branch in branches:
        for package in packages:
            if package == branch:
                branchesToRemove.append(branch)
                for package in getBranchPkgs(branch):
                    packagesToRemove.append(package)
            else:
                packagesToRemove.append(package)

    print('-----PACKAGE DELETION-----')
    for package in packagesToRemove:
        print('[-] ' + package)
    for branch in branchesToRemove:
        print('[-branch] ' + branch)

    print()
    permission = input('Do you really want to remove these packages ? (Y/N) ')
    permission = permission.lower()
    print()

    if permission != 'y':
        return 1
    for package in packagesToRemove:
        fileNotFoundCount = 0
        packageBranch = getPkgBranch(package)
        if 'ROOT' not in os.environ:
            os.environ['ROOT'] = '/'
        os.chdir(os.environ['ROOT'])
        treeFile = open(config.localPath + list(packageBranch.keys())[0] + '/' + package + '.tree', 'r')
        dirsToCheck = []
        for line in treeFile.readlines():
            if line.strip() == '.' or line.strip() == './.TREE':
                continue
            if os.path.isdir(line.strip()):
                dirsToCheck.append(line.strip())
            else:
                try:
                    os.remove(line.strip())
                except FileNotFoundError:
                    logError("file '" + line.strip().replace('./', os.environ['ROOT']) + "' not found ! Anyway, continue.")
                    fileNotFoundCount+=1

        for dir in dirsToCheck:
            if len(os.listdir(dir)) == 0:
                os.removedirs(dir)

        unregisterPkg(package)
        os.remove(config.localPath + list(packageBranch.keys())[0] + '/' + package + '.tree')
        os.remove(config.localPath + list(packageBranch.keys())[0] + '/' + package)
        logInfo("package '" + package + "' has been successfully removed.")
        if fileNotFoundCount > 0:
            print('Files not found during deletion: ' + str(fileNotFoundCount))

def info(packages):
    for package in packages:
        download = True
        if checkPkgInstalled(package):
            download = False
        
        packageInfoPath = getPkgFile(package, download)
        pkgInfo = getPkgInfo(package)

        print('-----PACKAGE ' + package + '-----')
        print("===> Name: " + pkgInfo['name'])
        print("===> Version: " + pkgInfo['version'])
        print("===> Author: " + pkgInfo['author'])
        print("===> Maintainer: " + pkgInfo['maintainer'])
        if 'url' in pkgInfo:
            print("===> Homepage: " + pkgInfo['url'])
        print("===> Installed: " + str(checkPkgInstalled(package)))
        
        if download:
            os.remove(packageInfoPath)

        print()

def upgrade():
    pass