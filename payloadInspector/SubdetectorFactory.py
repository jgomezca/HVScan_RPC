import StripUtils
import EcalUtils
import StaticFile
import HcalUtils
import BeamspotUtils
import re
import os.path
import EcalCondDB
import xmldump

__striptag = '.*STRIP'
__ecaltag = '.*ECAL'
__rpctag = '.*RPC'
__hcaltag = '.*HCAL'
__beamspottag = '.*BEAMSPOT'

def get_formated_db_name(dbName):
    """Return formated dbName (each '/' and '://' is replaced by '_')."""
    return re.sub(r'(://|/)', '_', dbName)  

def getDirectory(dbName, tag = '', since = '', fileType = 'png', basedir = './', default = False, shortName = None):
    if default:
        return  StaticFile.get_directory(get_formated_db_name(dbName), tag = tag, since = since, fileType = fileType, basedir = basedir)
    if re.match(__striptag, os.path.basename(dbName)) != None:
        return StripUtils.get_directory(dbName = get_formated_db_name(dbName), tag = tag, since = since, fileType = fileType, basedir = basedir) 
    elif re.match(__hcaltag, os.path.basename(dbName)) != None:
        return HcalUtils.get_directory(dbName = get_formated_db_name(dbName), tag = tag, since = since, fileType = fileType, basedir = basedir) 
    else:# re.match(__ecaltag, os.path.basename(dbName)) != None or re.match(__rpctag, os.path.basename(dbName)) != None:
        return EcalUtils.get_directory(dbName = get_formated_db_name(dbName), tag = tag, since = since, fileType = fileType, basedir = basedir) 
    return StaticFile.get_directory(get_formated_db_name(dbName), tag = tag, since = since, fileType = fileType, basedir = basedir) 

def getPlotInstance(dbName, tag, since = '1', fileType = 'png', directory = './', image = '', shortName = None):
    '''Returns Plot class instance depending on dbName parameter. Other parameters are required to create instance of Plot class'''
    #print directory
    if shortName is not None:
        dir = getDirectory(dbName = shortName, tag = tag, since = since, fileType = fileType, basedir = directory)
    else:
        dir = getDirectory(dbName = dbName, tag = tag, since = since, fileType = fileType, basedir = directory)
    #raise Exception('asdasdasdlal761523476152351263alla' + str(dir))
    if re.match(__striptag, os.path.basename(dbName)) != None:
        return StripUtils.StripPlot(dbName = dbName, tag = tag, since = since, 
                                   fileType = fileType, directory = dir, png = image)
    elif re.match(__hcaltag, os.path.basename(dbName)) != None:
        return HcalUtils.HcalPlot(dbName = dbName, tag = tag, since = since, 
                                   fileType = fileType, directory = dir, png = image)
    else:# re.match(__ecaltag, os.path.basename(dbName)) != None or re.match(__rpctag, os.path.basename(dbName)) != None:
        return EcalUtils.EcalPlot(dbName = dbName, tag = tag, since = since,
                                  fileType = fileType, directory = dir)
    return EcalUtils.EcalPlot(dbName = dbName, tag = tag, since = since,
                                  fileType = fileType, directory = dir)
                                  
def getTrendPlotInstance(dbName, tag, since = '1', fileType = 'png', directory = './'):
    '''Returns Plot class instance depending on dbName parameter. Other parameters are required to create instance of Plot class'''
    #print directory
    dir = getDirectory(dbName = dbName, tag = tag, since = since, fileType = fileType, basedir = directory)
    #raise Exception('asdasdasdlal761523476152351263alla' + str(dir))
    if re.match(__beamspottag, os.path.basename(dbName)) != None:
        return BeamspotUtils.BeamspotPlot(dbName = dbName, tag = tag, since = since, 
                                   fileType = fileType, directory = dir)
    return None
        
def getSummaryInstance(dbName, tag, since = '1'):
    '''Returns class, that returns summary specific to given subdetector'''
    ecalCondDB = EcalCondDB.EcalCondDB(dbName = dbName)
    payload = ecalCondDB.get_payload(tag, since)
    return payload
    
def getHistoInstance(dbName, tag, since = '1', fileType = 'png', directory = './'):
    '''Returns class, that handles histo request specific to dbName.'''
    dir = getDirectory(dbName = dbName, tag = tag, since = since, fileType = fileType, basedir = directory)
    return EcalUtils.EcalHisto(dbName = dbName, tag = tag, since = since, fileType = fileType, directory = dir)
    
def getXMLInstance(dbName, tag, since = '1', fileType = 'tar.gz', directory = './', shortName = None):
    #dir = getDirectory(dbName = dbName, tag = tag, since = since, fileType = fileType, basedir = directory)
    #return EcalUtils.EcalXML(dbName = dbName, tag = tag, since = since, fileType = fileType, directory = dir)
    #ecalCondDB = EcalCondDB.EcalCondDB(dbName = dbName)
    #payload = ecalCondDB.get_payload(tag, since)
    #return payload
    if shortName is not None:
        dir = getDirectory(dbName = shortName, tag = tag, since = since, fileType = fileType, basedir = directory)
    else:
        dir = getDirectory(dbName = dbName, tag = tag, since = since, fileType = fileType, basedir = directory)
    #if re.match(__ecaltag, os.path.basename(dbName)) != None:        
    #    return EcalUtils.EcalXML(dbName = dbName, tag = tag, since = since, fileType = fileType, directory = dir)
    return xmldump.XMLDump(dbName = dbName, tag = tag, since = since, fileType = fileType, directory = dir)
 
    
def getNames(dbName, tag, since = '1', fileType = 'png', basedir = './'):
    '''Usage: getNames(dbName, tag, since, fileType, basedir) -> []'''
    if re.match(__striptag, os.path.basename(dbName)) != None:
        return StripUtils.get_files(dbName = dbName, tag = tag, since = since, 
                                           fileType = fileType, basedir = basedir)
    elif re.match(__hcaltag, os.path.basename(dbName)) != None:
        return HcalUtils.get_files(dbName = dbName, tag = tag, since = since, 
                                           fileType = fileType, basedir = basedir)
    else:# re.match(__ecaltag, os.path.basename(dbName)) != None or re.match(__rpctag, os.path.basename(dbName)) != None:
        return EcalUtils.get_files(dbName = dbName, tag = tag, since = since, 
                                           fileType = fileType, basedir = basedir)
    return ''
