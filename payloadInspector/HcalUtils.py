
import re
import os, os.path

import EcalCondDB
import StaticFile

import re

hgains = re.compile('.*HcalGains.*')
hpeds = re.compile('.*HcalPedestals.*')

def get_files(dbName, tag, since = '1', fileType = 'png', basedir = './', prefix = ''):
    ecalCondDB = EcalCondDB.EcalCondDB(dbName)
    tok = ecalCondDB.get_token(tag = tag, since = since)
    if hgains.match(tok):
        return [tag + '_' + str(since) + '_Gain_0.' + fileType, 
                tag + '_' + str(since) + '_Gain_1.' + fileType,
                tag + '_' + str(since) + '_Gain_2.' + fileType,
                tag + '_' + str(since) + '_Gain_3.' + fileType]
    elif hpeds.match(tok):
        return [tag + '_' + str(since) + '_PedestalWidth_0.' + fileType, 
                tag + '_' + str(since) + '_PedestalWidth_1.' + fileType,
                tag + '_' + str(since) + '_PedestalWidth_2.' + fileType,
                tag + '_' + str(since) + '_PedestalWidth_3.' + fileType,
                tag + '_' + str(since) + '_Pedestal_0.' + fileType, 
                tag + '_' + str(since) + '_Pedestal_1.' + fileType,
                tag + '_' + str(since) + '_Pedestal_2.' + fileType,
                tag + '_' + str(since) + '_Pedestal_3.' + fileType]
    else:
        return [tag + '_' + str(since) + '.' + fileType]


def get_directory(dbName, tag = '', since = '1', fileType = 'png', basedir = './'):
    return os.path.join(str(basedir), str(dbName), str(tag), str(since))
    
class HcalFile(StaticFile.StaticFile):
    
    def __init__(self, dbName='', tag='', since='', fileType='png', directory='./', png = ''):
        """Init a default data."""
        self._dbName = dbName
        self._tag = tag
        self._since = since.strip().split(';')[0]
        self._directory = directory
        #self._name = get_name(get_formated_db_name(dbName), tag, since, fileType)
        #self._name = get_name(tag, since, fileType)
        self._fileType = fileType
        self._name = ''
        if png != '':
            self._name = png   
        else:
            #self._name = PlotsNamesCreator.generateNames(self.tag, since, self.fileType)
            files = get_files(dbName = self._dbName, tag = self._tag, 
                                            since = self._since, fileType = self._fileType, basedir = directory)
            if len(files) > 0:                
                for i in files:
                    if i.lower().find('tkmap') != -1:
                        self._name = i
                if self._name == '':
                    self._name = files[0]
            else:
                self._name = ''
        #StaticFile.__init__(self.__name, self.__directory)
        
    def get_directory(self):
        return get_directory(dbName = self._dbName, tag = self._tag, since = self._since,
                            fileType = self._fileType, basedir = self._directory)
                            
    def get_names(self):
        return get_files(dbName = self._dbName, tag = self._tag, 
                                            since = self._since, fileType = self._fileType, basedir = self._directory)
        
class HcalPlot(HcalFile):
    '''Class for plot (creating is implemented in EcalCondDB).'''    
    
    def _create(self):
        '''Create a plot. File type is defined automaticaly by object name extension.'''
        ecalCondDB = EcalCondDB.EcalCondDB(self._dbName)
        ecalCondDB.plot(self._tag, self._since, os.path.join(
            self._directory, '%s_%s' % (self._tag, self._since)))
