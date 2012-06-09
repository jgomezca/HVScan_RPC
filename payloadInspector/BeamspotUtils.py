import EcalUtils
import EcalCondDB
import os


class BeamspotPlot(EcalUtils.EcalPlot):

    def __init__(self, dbName='', tag='', since='', fileType='png', directory='./'):
        """Init a default data."""
        self._dbName = dbName
        self._tag = tag
        self._since = since.strip().split(';')[0]
        self._until = since.strip().split(';')[-1]
        self._directory = directory
        #self._name = get_name(get_formated_db_name(dbName), tag, since, fileType)
        #self._name = get_name(tag, since, fileType)
        self._fileType = fileType
        self._name = self._tag + '_' + self._since + '_' + self._until + '.' + self._fileType

    def get_directory(self):
        #return os.path.join(basedir, dbName)
        return get_directory(dbName = self._dbName, tag = self._tag, since = self._since.split(';')[0], fileType = self._fileType, basedir = self._directory)

    def _create(self):
        ecalCondDB = EcalCondDB.EcalCondDB(self._dbName)
        ecalCondDB.trendPlot(self._tag, int(self._since), int(self._until), os.path.join(self._directory, self._tag + '_' + self._since + '_' + self._until))