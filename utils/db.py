from datetime import date
from packaging.version import Version, LegacyVersion
import os, requests, urllib, urllib.request, yaml
import utils.config as config

def checkPkgExists(package):
    branches = getBranches()
    
    for branch in branches:
        branchPath = config.distPath + branch + '/'
        branchDBPath = branchPath + 'INDEX'

        packages = readDB(branchDBPath)
        if package in packages:
            return True

    return False

def createFile(path):
    open(path, 'x').close()

def checkPkgInstalled(package, chroot):
    if chroot != None:
        index = readDB(chroot + '/INDEX')
        if index == None:
            os.makedirs(branchLocalPath, exist_ok=True)
            createFile(chroot + '/INDEX')
            return False     
        if package in index:
            return True
        
        return False

    branches = getBranches()

    for branch in branches:
        branchLocalPath = config.localPath + branch + '/'
        branchLocalDBPath = branchLocalPath + 'INDEX'

        installedPackages = readDB(branchLocalDBPath)
        if installedPackages == None:
            os.makedirs(branchLocalPath, exist_ok=True)
            createFile(branchLocalDBPath)
            return False
        if package in installedPackages:
            return True

    return False

def checkVersionUpdate(package):
    pkgBranch = getPkgBranch(package)
    pkgInfo = getPkgInfo(package, None, False, False)
    distPackages = readDB(config.distPath + list(pkgBranch.keys())[0] + '/INDEX')
    if Version(distPackages[package]) > Version(pkgInfo['version']):
        return True

def getBranches():
    branches = {}

    configFile = open(config.configPath + 'branches', 'r')
    for line in configFile.readlines():
        branchName = line.split()[0].strip()
        branchURL = line.split()[1].strip()

        branches[branchName] = branchURL

    return branches

def getBranchPkgs(branch):
    packages = {}
    indexPath = getBranchIndex(branch)
    indexFile = open(indexPath, 'r')
    for line in indexFile:
        packages[line.split()[0].strip()] = line.split()[1].strip()

    return packages

def getBranchIndex(branch):
    return config.distPath + branch + '/INDEX'

def getPkgBranch(package):
    branches = getBranches()

    for branch in branches:
        branchDistPath = config.distPath + branch + '/'
        branchDistDBPath = branchDistPath + 'INDEX'

        packages = readDB(branchDistDBPath)

        if package in packages:
            return {branch: branches[branch]}

def getPkgFile(package, chroot, download=True, distant=False):
    chrootPath = ''
    if chroot != None:
        chrootPath = chroot
    packageBranch = getPkgBranch(package)
    if download:
        if not distant:
            os.makedirs(chrootPath + '/' + config.localPath + list(packageBranch.keys())[0], exist_ok=True)
            os.chdir(chrootPath + '/' + config.localPath + list(packageBranch.keys())[0])
            req = urllib.request.urlopen(packageBranch[list(packageBranch.keys())[0]] + '/' + package)
            infoFile = open(package, 'wb')
            infoFile.write(req.read())
            infoFile.close()
            req.close()
            chrootPath += '/'
            return chrootPath + config.localPath + list(packageBranch.keys())[0] + '/' + package
        if distant:
            os.makedirs(chrootPath + '/' + config.distPath + list(packageBranch.keys())[0], exist_ok=True)
            os.chdir(chrootPath + '/' + config.distPath + list(packageBranch.keys())[0])
            req = urllib.request.urlopen(packageBranch[list(packageBranch.keys())[0]] + '/' + package)
            infoFile = open(package, 'wb')
            infoFile.write(req.read())
            infoFile.close()
            req.close()
            chrootPath += '/'
            return chrootPath + config.distPath + list(packageBranch.keys())[0] + '/' + package
    return chrootPath + config.localPath + list(packageBranch.keys())[0] + '/' + package

def getPkgInfo(package, chroot, download=True, distant=False):
    packageBranch = getPkgBranch(package)
    packageInfoPath = getPkgFile(package, chroot, download, distant)

    pkg_file = open(packageInfoPath, 'r')

    record_build = False
    opened_brackets = 0
    info = {}
    bracket_name = ""
    for line in pkg_file.readlines():
        if line.startswith("#") or line == "" or line == "\n":
            continue
        if "(" not in line or line.split(': ')[0] == "description":
            if not record_build:
                info[line.split(": ")[0].strip()] = line.split(": ")[1].strip()
            else:
                if line.replace('\n','').strip() != ")" or (")" in line and opened_brackets > 1):
                    info[bracket_name] += line
        else:
            record_build = True
            opened_brackets += 1
            if opened_brackets > 1:
                info[bracket_name] += line
            else:
                bracket_name = line.split("(")[0].strip()
            if not bracket_name in info:
                info[bracket_name] = ""  

        if ")" in line:
            opened_brackets -= 1
    if distant:
        os.remove(packageInfoPath)
    return info

def readDB(path):
    packages = {}
    try:
        dbFile = open(path, 'r')
    except FileNotFoundError:
        return None
    for line in dbFile.readlines():
        packageName = line.split()[0].strip()
        packageVersion = line.split()[1].strip()

        packages[packageName] = packageVersion

    return packages

def registerPkg(package, version, chroot):
    branchName = list(getPkgBranch(package).keys())[0]
    localDB = None
    if chroot != None:
        localDB = open(chroot + '/INDEX', 'a')
    else:
        localDB = open(config.localPath + '/' + branchName + '/INDEX', 'a')
    localDB.write(package + " " + version + " " + date.today().strftime("%Y-%m-%d") + '\n')
    localDB.close()

def unregisterPkg(package):
    branchName = list(getPkgBranch(package).keys())[0]
    with open(config.localPath + '/' + branchName + '/INDEX', "r") as f:
        lines = f.readlines()
    with open(config.localPath + '/' + branchName + '/INDEX', "w") as f:
        for line in lines:
            if not line.startswith(package):
                f.write(line)
