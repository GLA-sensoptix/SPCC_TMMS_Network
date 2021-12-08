import re
from dateutil.parser import parse

def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def getFileExtension(file):
    splitted = file.split('.')
    return splitted[-1], ''.join(splitted[:-1])

def getPrefix(type, file):
    splitted = re.split('_|-| ', file)
    if(type =='both'):
        return ''.join(splitted[1:-1]), splitted[0], splitted[-1]
    if(type=='prefix'):
        return ''.join(splitted[:1]), splitted[0]
    if(type =='suffix'):
        return ''.join(splitted[:-1]), splitted[-1]
    return None, None
        

def getFilesWithPrefix(prefix, fileName, allFiles):
    prefixDate = prefix == 2
    extension, noExtensionName = getFileExtension(fileName)
    noPrefixName, _  = getPrefix('prefix', noExtensionName)
    resultFiles = []
    for file in allFiles:
        currentExtension, currentName = getFileExtension(file)
        if extension == currentExtension:
                currentNoPrefixName, prefix  = getPrefix('prefix', currentName)
                if currentNoPrefixName == noPrefixName:
                    if prefixDate and is_date(prefix):
                        resultFiles.append(file)
                    if not prefixDate:
                        resultFiles.append(file)
    return resultFiles

def getFilesWithSuffix(suffix, fileName, allFiles):
    suffixDate = suffix == 2
    extension, noExtensionName = getFileExtension(fileName)
    noSuffixName, _  = getPrefix('suffix', noExtensionName)
    resultFiles = []
    for file in allFiles:
        currentExtension, currentName = getFileExtension(file)
        if extension == currentExtension:
                currentNoSuffixName, suffix  = getPrefix('suffix', currentName)
                if currentNoSuffixName == noSuffixName:
                    if suffixDate and is_date(suffix):
                        resultFiles.append(file)
                    if not suffixDate:
                        resultFiles.append(file)
    return resultFiles

def getFilesWithBoth(suffix, prefix, fileName, allFiles):
    # check if suffix and prefix needs to be dates
    suffixDate = suffix == 2
    prefixDate = prefix == 2
    # retrieve extension and filename without extension
    extension, noExtensionName = getFileExtension(fileName)
    noPrefixName, _ ,_  = getPrefix('both', noExtensionName)
    resultFiles = []
    for file in allFiles:
        currentExtension, currentName = getFileExtension(fileName)
        if extension == currentExtension:
            currentNoPrefixName, prefix , suffix  = getPrefix('both', currentName)
            if currentNoPrefixName == noPrefixName:
                if suffixDate and prefixDate and is_date(prefix) and is_date(suffix):
                    resultFiles.append(file)
                if suffixDate and not prefixDate and is_date(suffix):
                    resultFiles.append(file)
                if not suffixDate and prefixDate and is_date(prefix):
                    resultFiles.append(file)
                if not suffixDate and not prefixDate:
                    resultFiles.append(file)
    return resultFiles

            

def getRegexFilesList(regexVariables, fileName, allFiles):
    # suffix can be 0 = No suffix , 1 = suffix with text and 2 = suffix with date
    # so first we initialize with 0
    suffix = 0
    prefix = 0
    try:
        if regexVariables is not None:
            if(regexVariables.get('prefix') is not None):
                if(regexVariables.get('prefix').get('checked') == True):
                    prefix=1
                    if(regexVariables.get('prefix').get('varchecked') == True):
                        prefix=2
            if(regexVariables.get('suffix') is not None):
                if(regexVariables.get('suffix').get('checked') == True):
                    suffix=1
                    if(regexVariables.get('suffix').get('varchecked') == True):
                        suffix=2
    except Exception as e:
        print('Invalid Regex Found', e)
        pass
    if (suffix == 0 and prefix == 0):
        if(fileName in allFiles):
            return [fileName]
        else:
            return []
    if (suffix >=1 and prefix == 0):
        return getFilesWithSuffix(suffix, fileName, allFiles)
    if (suffix >=1 and prefix >=1 ): 
        return getFilesWithBoth(suffix, prefix, fileName, allFiles)
    if(suffix == 0 and prefix >= 1):
        return getFilesWithPrefix(suffix, prefix, fileName, allFiles)

    
        

