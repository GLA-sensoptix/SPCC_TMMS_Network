# local import
from datetime import time
from python_functions import datParser as parser
from python_functions.query import Query
from python_functions.files import getListOfFiles, saveFile, removeFile


# external library import
import json
import os
import pandas as pd
from io import BytesIO
import base64

# db credentials
dbHost = 'localhost' # host database
dbName = 'thm_insight' # name database
dbUser = 'postgres' # user database;
dbPort = 5432 # post database;
dbPassword = 'root' # password databse
# dataFolder = 'C:/Users/Public/Documents/ModbusRegistryDisplay'
tempFolder = 'temp/'
saveFolder = 'save/'
globalFile = 'tempFile'

# functions to update data between two dates
def MOD(event, context):
    return
    # todo : add function to mod between two dates on local 

def parseHeaders(event, context):
    return
    # todo: add function to parse header on local 


def insertData(event, context):
    return
    # todo: add function to insert data from file on local 



def ETL(dataFolder):
    queryManager = Query(dbHost, dbName, dbUser, dbPort, dbPassword)
    configs = queryManager.getConfigs()  # retrieve all configs from table configs
    # print('{} configs retrieved from database'.format(len(configs)))
    for config in configs:
        rawFilesList = []
        confId, fileName, lastTreatment, ftpType, ftpIp, ftpUser, ftpPassword, ftpDirectory, configTable, toMove, regexVariables, timezone = config[
            :12]
        parsingConfig = config[12:]
        # print('===============')
        # print('Treatment of file [ id : {} , filename : {}, last treatment: {} , timezone: {} ]'.format(
        #     confId, fileName, lastTreatment, timezone))
        # the name of bucket folder
        baseFilename = fileName.split('.')[0]
        backupFolder = "{}_{}".format(confId, baseFilename)
        # initialise ftp connection and get list of files
        try:
            rawFilesList = getListOfFiles(dataFolder, fileName, regexVariables) # todo : implement get list of files local 
        except Exception as v:
            print('Error retrieving files: ', v)
            continue
        if len(rawFilesList) == 0:
            print('no file to process')
        else:
            pass
            # print('file to process : ', rawFilesList)
        for file in rawFilesList:
            newData = []
            # print(file)
            # parse file and get newData
            try:
                parsingName, specific, config = parsingConfig
                data = parser.parseFile(parsingName, specific, config, dataFolder+'/'+file)
                # print(data.head(5))
                configuration = pd.read_json(json.dumps(configTable))
                newData = parser.getNewData(data, configuration, lastTreatment)
                # print('End of parsing : {} new rows retrieved'.format(len(newData)))
            except Exception as e:
                print('Error parsing file : ', e)
                try:
                    response = saveFile(dataFolder, saveFolder+'failed'+"/"+backupFolder, file)
                    # print('file saved to failed bucket')
                    if toMove == True and response == True:
                        removeFile(file)
                        
                    continue
                except:
                    continue
            if (len(newData) > 0):
                try:
                    # get last data of data
                    lastDate = newData.index.max()
                    # print(lastDate)
                    # insert value and update last_treatment
                    queryManager.insertValues(
                        newData, confId, timezone, lastDate)
                    # print('Insertion success : {} new rows inserted'.format(
                    #     len(newData)))
                except Exception as e:
                    print("Error inserting new values : ", e)
                    try:
                        response = saveFile(dataFolder, saveFolder+'failed'+"/"+backupFolder, file)
                        # print('file saved to failed bucket')
                        if toMove == True and response == True:
                            removeFile(file)
                        continue
                    except:
                        continue
                try:
                    response = saveFile(dataFolder, saveFolder+'success'+"/"+backupFolder, file)
                    # print('file saved to success bucket')
                    if toMove == True and response == True:
                        removeFile(file)
                except Exception as e:
                    print(e)
                    try:
                        response = saveFile(dataFolder, saveFolder+'failed'+"/"+backupFolder, file)
                        # print('file saved to failed bucket')
                        if toMove == True and response == True:
                            removeFile(file)
                        continue  # go to next iterration
                    except:
                        continue
            else:
                if toMove == True:
                    removeFile(file)


if __name__ == "__main__":
    ETL()