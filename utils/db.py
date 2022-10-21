from datetime import date
import os, requests, yaml
import utils.config as config

def checkPkgExists(package):
    branches = getBranches(config.configPath + 'branches')
    
    for branch in branches:
        branchPath = config.distPath + branch + '/'
        branchDBPath = branchPath + 'INDEX'

        packages = readDB(branchDBPath)
        if package in packages:
            return True

    return False

def checkPkgInstalled(package):
    branches = getBranches(config.configPath + 'branches')

    for branch in branches:
        branchLocalPath = config.localPath + branch + '/'
        branchLocalDBPath = branchLocalPath + 'INDEX'

        installedPackages = readDB(branchLocalDBPath)

        if package in installedPackages:
            return True

    return False

def getBranches(configFilePath):
    branches = {}

    configFile = open(configFilePath, 'r')
    for line in configFile.readlines():
        branchName = line.split()[0].strip()
        branchURL = line.split()[1].strip()

        branches[branchName] = branchURL

    return branches

def getPkgBranch(package):
    branches = getBranches(config.configPath + 'branches')

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
    reader = open(config.localPath + '/' + branchName + '/INDEX', 'r')
    writer = open(config.localPath + '/' + branchName + '/INDEX', 'w')
    for line in reader.readlines():
        if not line.startswith(package):
            writer.write(line)

    reader.close()
    writer.close()
