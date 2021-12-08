import pandas as pd
import numpy as np
import pytz
tempFolder = 'tmp/'


def parseFile(parsingName, specific, config, file, retrieveData=True):
    # if not specific parse with all parameters
    data = None
    header = None
    if(not specific):
        header = config.get("header", None)
        skipcolumns = config.get("skipcolumns", [])
        skiprows = config.get("skiprows", [])
        date_columns = config.get("column_date", [])
        separator = config.get("separator", ",")
        orientation = config.get("orientation", "vertical")
        # skip rows and columns
        data = pd.read_csv(
            file,
            sep=separator,
            header=header,
            skiprows=skiprows,
            low_memory=False,
            error_bad_lines=False,
            memory_map=True,
            warn_bad_lines=True,
        )
        # print(parsingName)
        data = data.drop(columns=skipcolumns)
        # rotate data if vertical
        if(orientation == 'vertical'):
            data = data.T
        sizeDate = len(date_columns)
        if(sizeDate) > 0:
            if(sizeDate > 1):
                for columnDate in date_columns[1:]:
                    if(header is not None):
                        data[date_columns[0]] = pd.to_datetime(
                            data[date_columns[0]] + ' ' + data[columnDate], errors='coerce')
                    else:
                        data[data.columns[date_columns[0]]] = pd.to_datetime(
                            data[data.columns[date_columns[0]]] + ' ' + data[data.columns[columnDate]], errors='coerce')
            else:
                if(header is not None):
                    data[date_columns[0]] = pd.to_datetime(
                        data[date_columns[0]])
                else:
                    data[data.columns[date_columns[0]]] = pd.to_datetime(
                        data[data.columns[date_columns[0]]], errors='coerce')

            data = data.loc[data.index.dropna()]
            if(header is not None):
                data = data.set_index(data[date_columns[0]])
                data = data.drop(columns=date_columns)
            else:
                data = data.set_index(data[data.columns[date_columns[0]]])
                data = data.drop(data.columns[date_columns], axis=1, inplace=True)

    else:
        if parsingName == 'GEO':
            colnames = ['DATE', 'TIME', 'SENSORS', 'X', 'Y', 'Z']
            data = pd.read_csv(file, sep=';', skiprows=[
                               0], names=colnames, parse_dates=[['DATE', 'TIME']], header=None, dayfirst=True)
            data = data.pivot(index='DATE_TIME', columns='SENSORS')
            data.columns = ['_'.join(reversed(col)).strip()
                            for col in data.columns.values]
            data = data.loc[data.index.dropna()]

    if (data is not None):
        if(header):
            if(retrieveData):
                return data
            else:
                return [i for i in data.columns]
        else:
            if(retrieveData):
                return data
            else:
                return [i for i in range(len(data.columns))]


def getNewData(table, configuration, minDate=None, maxDate=None):
    splittedTable = []
    if(minDate is not None and maxDate is not None):
        splittedTable = table[(table.index > minDate) &
                              (table.index < maxDate)]
    elif(minDate is not None):
        splittedTable = table[(table.index > minDate)]
    elif(maxDate is not None):
        splittedTable = table[(table.index < maxDate)]
    else:
        splittedTable = table
    if len(splittedTable) > 0:
        # select from configuration only 'alias' and 'variableId'
        config_alias_id = configuration[["alias", "variable_id"]]
        # Dictionnary where we will associate aliase to there variable_id. ex: {'A': 1}
        alias_to_id = dict()
        # We generate the dictionnary here
        for key, val in zip(config_alias_id["alias"].to_numpy(), config_alias_id["variable_id"].to_numpy()):
            alias_to_id[key] = val
        config_alias = config_alias_id["alias"].to_numpy()
        current_alias = splittedTable.columns.to_numpy()
        filterExist = np.isin(config_alias, current_alias)
        config_alias = config_alias[filterExist]
        if(len(config_alias) > 0):
            # Selection only column that are aliasses
            light_table = splittedTable[config_alias]
            # Converte alias column to id column (we juste change names because of 'alias_to_id' dict)
            light_table = light_table.rename(columns=alias_to_id)
            # we add a new columns 'TIMESTAMP' based on the index column (it will be use full for the melt function)
            light_table["TIMESTAMP"] = light_table.index
            # using melt function to modify the shape of the matrix
            result = light_table.melt(id_vars=["TIMESTAMP"])
            # adding as index, the column 'TIMESTAMP' because melt function create it's own index
            result = result.set_index('TIMESTAMP')
            result = result.dropna()
            return result
        return []
    else:
        return []
