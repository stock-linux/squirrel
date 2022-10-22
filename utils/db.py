from datetime import date
import os, requests, yaml
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

def checkPkgInstalled(package):
    branches = getBranches()

    for branch in branches:
        branchLocalPath = config.localPath + branch + '/'
        branchLocalDBPath = branchLocalPath + 'INDEX'

        installedPackages = readDB(branchLocalDBPath)

        if package in installedPackages:
            return True

    return False

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

def getPkgFile(package, download=True):
    packageBranch = getPkgBranch(package)

    if download:
        os.chdir(config.localPath + list(packageBranch.keys())[0])
        req = requests.get(packageBranch[list(packageBranch.keys())[0]] + '/' + package)
        if req.status_code != 200:
            return None
        infoFile = open(package, 'wb')
        infoFile.write(req.content)
        infoFile.close()
        req.close()

    return config.localPath + list(packageBranch.keys())[0] + '/' + package

def getPkgInfo(package):
    packageBranch = getPkgBranch(package)
    packageInfoPath = getPkgFile(package, False)

    stream = open(packageInfoPath, 'r')
    return yaml.load(stream, Loader=yaml.Loader)

def readDB(path):
    packages = {}
    
    dbFile = open(path, 'r')
    for line in dbFile.readlines():
        packageName = line.split()[0].strip()
        packageVersion = line.split()[1].strip()

        packages[packageName] = packageVersion

    return packages

def registerPkg(package, version):
    branchName = list(getPkgBranch(package).keys())[0]
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
