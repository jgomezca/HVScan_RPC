"""Util classes for histo, plot, compare, xml backend methods."""

import re
import os, os.path

import EcalCondDB
import StaticFile

def get_files(dbName, tag, since = '1', fileType = 'png', basedir = './', prefix = ''):
    name = tag + '_' + str(since) + '.' + fileType
    return [name, ]
        
def get_directory(dbName, tag = '', since = '1', fileType = 'png', basedir = './'):
    return os.path.join(str(basedir), str(dbName), str(tag), str(since))

class EcalFile(StaticFile.StaticFile):
    
    def __init__(self, dbName='', tag='', since='', fileType='png', directory='./'):
        """Init a default data."""
        self._dbName = dbName
        self._tag = tag
        self._since = since.strip().split(';')[0]
        self._directory = directory
        #self._name = get_name(get_formated_db_name(dbName), tag, since, fileType)
        #self._name = get_name(tag, since, fileType)
        self._fileType = fileType
        self._name = get_files(dbName = self._dbName, tag = self._tag, 
                                            since = self._since, fileType = self._fileType, basedir = self._directory)[0]
        #StaticFile.__init__(self.__name, self.__directory)
        
    def get_directory(self):
        return get_directory(dbName = self._dbName, tag = self._tag, since = self._since,
                            fileType = self._fileType, basedir = self._directory)
        
class EcalPlot(EcalFile):
    '''Class for plot (creating is implemented in EcalCondDB).'''    
    
    def _create(self):
        '''Create a plot. File type is defined automaticaly by object name extension.'''
        ecalCondDB = EcalCondDB.EcalCondDB(self._dbName)
        ecalCondDB.plot(self._tag, self._since, os.path.join(
            self._directory, self._name))

class EcalHisto(EcalFile):
    """Class for histo (creating is implemented in EcalCondDB)."""
    def _create(self):
        """Create a histo. File type is defined automaticaly by object name
        extension (but in a moment only ROOT is possible)."""
        ecalCondDB = EcalCondDB.EcalCondDB(self._dbName)
        ecalCondDB.histo(self._tag, self._since, os.path.join(self._directory, self._name))

class EcalXML(EcalFile):
    def _create(self):
        """Creates an XML file from EcalCondDB."""
        if not os.path.isdir(self._directory):
            os.makedirs(self._directory)
        ecalCondDB = EcalCondDB.EcalCondDB(self._dbName)
        #print "class XML _create",self._directory
        ecalCondDB.dumpGzippedXML(self._tag, self._since, os.path.join(
            self._directory, self._name))
            
    def get(self):
        if self.exists():
            return open(self.get_full_name()).read()
        else:
            self._create()
            return open(self.get_full_name()).read()

