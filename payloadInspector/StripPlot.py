import CfgFileGenerator
import PlotsNamesCreator
import os.path
import os
import lastIOVSince

class StripPlot:
    
    def __init__(self, dbName, tag, since = (1,), fileType = 'png', directory = './', png = ''):
        self.dbName = dbName
        self.tag = tag
        self.since = since
        self.fileType = fileType
        self.png = png
        if not os.access(directory, os.R_OK | os.W_OK):
            raise IOError('Directory %s doesn\'t have enough permissions.' % directory)
        else:
            self.directory = directory
            
    def validateIOVIntervals(self, iovn):
        iov = lastIOVSince.LastIOVSince(dbName = self.dbName)        
        for el in iov.iovSequence(tag = self.tag).elements:
            n = int(iovn)
            if n >= el.since() and n <= el.till():
                return el.since()
        return 1
        
    def get_files(self):
        list = {}
        iovs = self.since.split(';')
        for i in iovs:
            if i != '' and i != None and i != '0':
                ii = int(i)
                names = PlotsNamesCreator.generateNames(tag = self.tag, since = self.validateIOVIntervals(ii), fileType = self.fileType)
                for n in names:
                    list[n] = i
        return list
        
        
    def get(self):
        pngname = '%s%s' % (self.directory , self.png)
        if self.png != '' and os.path.exists(pngname) and os.path.isfile(pngname):
            return open(pngname).read()
        else:
            vsince = str(self.validateIOVIntervals(self.since))
            files = PlotsNamesCreator.generateNames(self.tag, vsince, self.fileType)
            generate = False
            for file in files:#check if files that should be generated already exist
                name = '%s%s' % (self.directory, file)
                if file == '' or not os.path.exists(name) or not os.path.isfile(name):
                    generate = True
                    break;
            if generate:
                cfgfile = CfgFileGenerator.generateCfg(self.dbName, self.tag, vsince, self.directory)
                os.system('pushd %s; cmsRun %s; popd' % (self.directory, cfgfile))
                if self.png != '' and os.path.exists(pngname) and os.path.isfile(pngname):
                    return open(pngname).read()
                elif os.path.exists('%s%s' % (self.directory, files[0])) and os.path.isfile('%s%s' % (self.directory, files[0])):
                    return open('%s%s' % (self.directory, files[0])).read()
                else:
                    raise ValueError('File not found.')
            else:
                if len(files) > 0:
                    return open('%s%s' % (self.directory, files[0])).read()
                else:
                    raise ValueError('unable to generate files for given parameters.')
              
    def get_name(self):
        return self.directory + PlotsNamesCreator.generateNames(self.tag, str(self.validateIOVIntervals(self.since)), self.fileType)[0]
                