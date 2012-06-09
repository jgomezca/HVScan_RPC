import StripUtils
from StaticFile import StaticFile
from ArgumentValidator import get_validated

class StaticData:
    
    def __init__(self, dbName, tag, since, fileType, directory, file):
        self.__db = dbName
        self.__tag = tag
        self.__since = since
        self.__type = fileType
        self.__dir = directory
        self.__reqfile = file
        if self.__reqfile in (None, ''): 
            self.__files.extend(self.get_names())
        else:
            self.__files.append(StaticFile(self.__reqfile, self.__dir))
    
    def get_names(self):
        pass
        
    def get_name(self):
        return self.get_names()[0]
        
    def get_directory(self):
        pass
        
    def exists(self, name = ''):
        if name in (None, ''):
            files = self.__files
        else:
            files = [StaticFile(name, self.__dir), ]
        rez = True
        for i in files:
            if not i.exists():
                rez = False
                break
        return rez
        
    def __temp_name(self, filename):
        pass
        
    def __create_temps(self):
        for i in self.get_names():
            tmpfile = os.path.join(self.get_directory(), self.__temp_name(filename = i))
            if tmpfile != None and not os.path.isfile(tmpfile):
                open(tmpfile, 'w').close()
        
    def __delete_temps(self):
        for i in self.get_names():
            tmpfile = os.path.join(self.get_directory(), self.__temp_name(filename = i))
            if tmpfile != None and os.path.isfile(tmpfile):
                os.remove(tmpfile)
        
    def __get_content(self):
        return open(os.path.join(self.__directory, self.__name), 'r+b').read()
        
    def create(self):
        if not self.exists(name = ''):
            self.__create_temps()
            self.__create_pngs()
            self.__delete_temps()
            
    
        
    