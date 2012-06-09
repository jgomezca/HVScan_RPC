import EcalCondDB
import tarfile
import StaticFile
import os, os.path

class XMLDump(StaticFile.StaticFile):
    def __init__(self, dbName, tag, since, fileType, directory):
        self._dbName = dbName
        self._tag = tag
        self._since = since
        self._fileType = fileType
        self._directory = directory
        self._name = tag + '_' + str(since) + '.' + fileType
        self._xmlname = tag + '_' + str(since) + '.xml'
    
    def get_directory(self):
        return self._directory
    
    def dump(self):
        if not os.path.isdir(self.get_directory()):
            os.umask(0)
            os.makedirs(self.get_directory(), mode = 0775)
        ecalCondDB = EcalCondDB.EcalCondDB(dbName = self._dbName)
        payload = ecalCondDB.get_payload(self._tag, int(self._since))
        return payload.dumpXML(os.path.join(self.get_directory(), self._xmlname))
 
    def gzip(self, file):
        if not os.path.isdir(self.get_directory()):
            os.umask(0)
            os.makedirs(self.get_directory(), mode = 0775)
        tar = tarfile.open(self.get_full_name(), "w|gz")
        tar.add(file, arcname = os.path.basename(file), recursive = False)
        tar.close()
        
    def get(self):
        if self.exists():
            return open(self.get_full_name()).read()
        else:
            xml = self.dump()
            if self._fileType.lower() in ('gzip', 'tar.gz'):
                self.gzip(file = xml)
                return open(self.get_full_name()).read()
            else:
                return open(xml).read()
        