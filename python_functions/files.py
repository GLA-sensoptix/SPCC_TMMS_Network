from python_functions import utils
from datetime import datetime
from shutil import copyfile

import os


def getListOfFiles(dataFolder, fileName, regexVariables):
    try:
        directory = os.listdir(dataFolder,)
        allFiles = []
        for elem in directory:
            # check if it is a file
            if elem.split('.')[0] != "" and len(elem.split('.')) >= 2:
                allFiles.append(elem)
        if(len(allFiles) > 0):
            resultFiles = utils.getRegexFilesList(
                regexVariables, fileName, allFiles)
            return resultFiles
        return allFiles
    except Exception as e:
        raise e


def saveFile(sourcepath, destpath, filename ):
    try:
        # # print(destpath)
        # now = datetime.now()
        # dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")
        # currentFilename = dt_string + "_" + filename
        # isExist = os.path.exists(destpath)
        # if not isExist:
            # os.makedirs(destpath)
        # copyfile(sourcepath+'/'+filename, destpath+'/'+currentFilename)
        return True
    except Exception as e:
        raise e


def removeFile():
    return
