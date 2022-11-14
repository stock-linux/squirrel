import os
from utils.db import checkPkgExists, checkPkgInstalled, checkVersionUpdate, getBranchPkgs, getBranches, getPkgBranch, getPkgFile, getPkgInfo, readDB, registerPkg, unregisterPkg
from utils.logger import *

import requests, urllib, urllib.request
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

def get(packages, noIndex, acceptInstall, chroot):
    sync()
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
    for package in packages:
        if not package in packagesToGet and not package in branchesToGet:
            packagesToGet.append(package)

    for package in packagesToGet:
        packageExists = checkPkgExists(package)
        if not packageExists:
            logError("package '" + package + "' does not exist in repos !")
            exit(1)

    print('-----PACKAGE INSTALLATION-----')
    for package in packagesToGet:
        print('[+] ' + package)

    for branch in branchesToGet:
        print('[+branch] ' + branch)

    print()
    if not acceptInstall:
        permission = input('Do you really want to install these packages ? (Y/N) ')
        print()
        permission = permission.lower()
    else:
        permission = 'y'

    if permission != 'y':
        exit(1)
    
    logInfo("Getting packages infos...")
    for package in packagesToGet:
        print('Getting "' + package + '"')
        getPkg(package, len(packagesToGet), noIndex, chroot)

def getPkg(package, pkgCount, noIndex, chroot, update=False):
    sync()
    if checkPkgInstalled(package, chroot) and not update:
        logInfo("package '" + package + "' is already installed.")
        return
    packageInfoPath = getPkgFile(package, chroot)

    if packageInfoPath == None:
        logError("There are some errors in repos for the package '" + package + "' ! Call an admin.")

    pkgInfo = getPkgInfo(package, chroot)
            
    if 'rundeps' in pkgInfo:
        for d in pkgInfo['rundeps'].split():
            getPkg(d, len(pkgInfo['rundeps']) + 1, False, chroot)
    if pkgCount == 1:
        print('---------------')
        print("Package '" + pkgInfo['name'] + "':")
        print("===> Version: " + pkgInfo['version'])
        if 'author' in pkgInfo:
            print("===> Author: " + pkgInfo['author'])
        if 'maintainer' in pkgInfo:
            print("===> Maintainer: " + pkgInfo['maintainer'])
        print("===> Source: " + pkgInfo['source'])
        if 'url' in pkgInfo:
            print("===> Homepage: " + pkgInfo['url'])
        print('---------------')
    
    installPkg(package, pkgInfo, noIndex, chroot)
    runPost(pkgInfo, chroot)
    print()

def installPkg(package, pkgInfo, noIndex, chroot):
    sync()
    print()
    tempDir = tempfile.TemporaryDirectory('squirrel-' + pkgInfo['name'])
    os.chdir(tempDir.name)
    downloadPkg(getPkgBranch(pkgInfo['name'])[list(getPkgBranch(pkgInfo['name']).keys())[0]] + '/bins/' + pkgInfo['name'] + '-' + pkgInfo['version'] + '.tar.xz', pkgInfo['name'])
    if 'ROOT' not in os.environ:
        os.environ['ROOT'] = '/'
    os.chdir(os.environ['ROOT'])
    archive.extractPkgArchive(tempDir.name + '/' + pkgInfo['name'] + '-' + pkgInfo['version'] + '.tar.xz')
    if checkPkgInstalled(pkgInfo['name'], chroot):
        unregisterPkg(pkgInfo['name'])
    
    registerPkg(pkgInfo['name'], pkgInfo['version'], chroot)
    if chroot == None:
        os.popen('mv .TREE ' + config.localPath + list(getPkgBranch(pkgInfo['name']).keys())[0] + '/' + pkgInfo['name'] + '.tree')
    else:
        os.popen('mv .TREE ' + chroot + '/' + config.localPath + list(getPkgBranch(pkgInfo['name']).keys())[0] + '/' + pkgInfo['name'] + '.tree')

    logInfo("package '" + pkgInfo['name'] + "' has been successfully installed.")

def runPost(pkgInfo, chroot):
    if 'post' in pkgInfo:
        if chroot == None:
            os.system(pkgInfo['post'])
        else:
            real_root = os.open("/", os.O_PATH)
            os.chroot(chroot)
            os.chdir('/')
            os.system(pkgInfo['post'])
            os.chdir(real_root)
            os.chroot(".")
            # Back to old root
            os.close(real_root)
    else:
        pass
    
def remove(packages, noIndex):
    branchesToRemove = []
    packagesToRemove = []
    branches = getBranches()
    for branch in branches:
        for package in packages:
            if package == branch:
                branchesToRemove.append(branch)
                for package in getBranchPkgs(branch):
                    if checkPkgInstalled(package, None):
                        packagesToRemove.append(package)
            else:
                if not noIndex and not checkPkgInstalled(package, None):
                    print("error: package '" + package + "' is not installed.")
                    exit(1)
                if not package in packagesToRemove:
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
            if os.path.isdir(line.strip()) and not os.path.islink(line.strip()):
                dirsToCheck.append(line.strip())
            else:
                try:
                    os.remove(line.strip())
                except FileNotFoundError:
                    logError("file '" + line.strip().replace('./', os.environ['ROOT'] + '/') + "' not found ! Anyway, continue.")
                    fileNotFoundCount+=1

        for dir in dirsToCheck:
            if len(os.listdir(dir)) == 0:
                os.removedirs(dir)

        if not noIndex:
            unregisterPkg(package)
        os.remove(config.localPath + list(packageBranch.keys())[0] + '/' + package + '.tree')
        os.remove(config.localPath + list(packageBranch.keys())[0] + '/' + package)
        logInfo("package '" + package + "' has been successfully removed.")
        if fileNotFoundCount > 0:
            print('Files not found during deletion: ' + str(fileNotFoundCount))

def info(packages):
    sync()
    for package in packages:
        download = True
        if checkPkgInstalled(package, None):
            download = False
        legacyLocalPath = config.localPath
        packageInfoPath = getPkgFile(package, None, download)
        pkgInfo = getPkgInfo(package, None, True, True)
        config.localPath = legacyLocalPath
        print('-----PACKAGE ' + package + '-----')
        print("===> Name: " + pkgInfo['name'])
        if not checkPkgInstalled(package, None):
            print("===> Version: " + pkgInfo['version'])
        else:
            print("===> Version: [installed: " + readDB(config.localPath + list(getPkgBranch(package).keys())[0] + '/INDEX')[package] + "][distant: " + pkgInfo['version'] + "]")
        if 'description' in pkgInfo:
            print("===> Description: " + pkgInfo['description'])
        if 'author' in pkgInfo:
            print("===> Author: " + pkgInfo['author'])
        if 'maintainer' in pkgInfo:
            print("===> Maintainer: " + pkgInfo['maintainer'])
        if 'url' in pkgInfo:
            print("===> Homepage: " + pkgInfo['url'])
        print("===> Installed: " + str(checkPkgInstalled(package, None)))
        
        if download:
            os.remove(packageInfoPath)

        print()

def upgrade():
    sync()
    installedPackages = []
    for branch in getBranches():
        branchInstalledPackages = readDB(config.localPath + branch + '/INDEX')
        installedPackages.extend(branchInstalledPackages)

    toUpdatePackages = []
    for package in installedPackages:
        if checkVersionUpdate(package):
            toUpdatePackages.append(package)

    if len(toUpdatePackages) <= 0:
        logInfo("system is up to date.")
        return

    print("-----SYSTEM UPGRADE-----")
    for package in toUpdatePackages:
        print("[U] " + package)

    print()

    permission = input('Do you really want to upgrade the system ? (Y/N) ')
    permission = permission.lower()
    print()

    if permission != 'y':
        return 1

    for package in toUpdatePackages:
        getPkg(package, len(toUpdatePackages), False, None, True)

def sync():
    for branch in getBranches():
        os.makedirs(config.distPath + branch, exist_ok=True)
        os.chdir(config.distPath + branch)
        request = urllib.request.urlopen(getBranches()[branch] + '/INDEX')
        writer = open('INDEX', 'wb')
        writer.write(request.read())
        writer.close()
        request.close()
