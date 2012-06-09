import os.path
import PngGenerator_trigger as pnggen 
import SubdetectorFactory
import time

def get_directory(dbName = '', tag = '', since = '', fileType = 'png', basedir = './'):
    return os.path.join(basedir, dbName, tag, since)

class StaticFile:
    """StaticFile is an object that represents a single data instance (plot, compare,
    histo and so on). """
    def __init__(self, name='', directory=''):
        '''StaticFile constructor.
        
        @param name name of the file
        @param directory full path to file excluding name		
        @return Nothing'''
        self._name = name
        self._directory = directory

    def get_files(self):
        '''Returns name of the file this class represents enclosed in a list ( [] ).'''
        name = tag + '_' + str(since) + '.' + fileType
        return [name, ]
        
    def exists(self, name = ''):
        '''Checks if file exists.
        
        @param name name of the file to check. By default name is the one passed in constructor. 
        If name == "", or None => name = default name.		
        @return True if file exists. False if it doesn't.'''
        if name == '' or name == None:
            name = self._name
        fullname = os.path.join(self._directory, name)
        return os.path.isfile(fullname)

    def get_name(self):
        '''Returns name of the file.'''
        return self._name
        
    def get_names(self):
        '''Returns name of the file this class represents as a list ( [] ).'''
        return [self.get_name(), ]
        
    def get_directory(self):
        #return os.path.join(basedir, dbName)
        return get_directory(dbName = self._dbName, tag = self._tag, since = self._since, fileType = self._fileType, basedir = self._directory)
        
    def get_full_name(self):
        return os.path.join(self._directory, self.get_name())

    def _get_content(self):
        """Return file content."""
        #with open(os.path.join(self._directory, self._name), 'r+b') as f:
            #@TODO: check if ROOT file has \n at the end
            #return f.read()

        return open(os.path.join(self._directory, self._name), 'rb').read()


    def _temp_name(self, filename):
        return str(self._name) + '.temp'
        
    def _create_temps(self, dir = None):
        if dir == None:
            dir = self._directory
        for i in self.get_names():
            tmpfile = os.path.join(dir, self._temp_name(filename = i))
            if tmpfile != None and not os.path.isfile(tmpfile):
                open(tmpfile, 'w').close()
                
    def _delete_temps(self, dir = None):
        if dir == None:
            dir = self._directory
        for i in self.get_names():
            tmpfile = os.path.join(dir, self._temp_name(filename = i))
            if tmpfile != None and os.path.isfile(tmpfile):
                os.remove(tmpfile)

    def create(self):
        #raise Exception('asdasd')
        if not self.exists(name = ''):
            #path = SubdetectorFactory.getDirectory(dbName = self._dbName, tag = self._tag, since = self._since
            #                                        , fileType = self._fileType, basedir = self._directory)
            path = self._directory
            #raise Exception('debug, dir:' + str(os.path.isdir(path)))
            if not os.path.isdir(path):                
                os.makedirs(path)
                os.chmod(path, 0777)
            self._create()
    
    #DEBUG, remove this method in favor of smarter cache control
    def has_to_be_generated(self):
        return self._tag.lower().find('strip') == -1
        #return True
            
                
    def get(self, get_fname = False):
        '''Extracts data from file. Calls the data generator script if the file doesn't exist.
        
        @return Contents of the file.'''
        if self.exists():
            if not get_fname:
                return self._get_content()
            else:
                return self.get_full_name()
        elif self.has_to_be_generated():
            pnggen.generateData(plot = self)
            if not get_fname and self.exists():
                return self._get_content()
            elif self.exists():
                return self.get_full_name()
        '''if not os.path.isfile(self._temp_name(self._name)):
            #generateData(dbName = self._dbName, tag = self._tag, since = self._since, plots = self._directory)
            pnggen.generateData(plot = self)
            if self.exists():
                return self._get_content()'''
        #raise Exception('found temp: ' + self._temp_name(self.get_name()))
        return None
