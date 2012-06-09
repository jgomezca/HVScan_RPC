import CfgFileGenerator
import os.path
import os
import lastIOVSince
import ArgumentValidator
import StaticFile
import glob

def get_files(dbName, tag, since = '1', fileType = 'png', basedir = './', prefix = 'SiStrip'):
    #return PlotsNamesCreator.generateNames(tag = self.tag, 
    #        since = ArgumentValidator.validateIOV(self.dbName, self.tag, ii), fileType = self.fileType)
    '''newTags = []
    tagsWithoutPrefix = []
    tagName = tag.split("_", 1)[0]
    if fileType != "": 
        fileType = "." + fileType
    if fileType in ('cfg', 'py'):
        return ['%s_cfg_%s.py'%(tag, since),]
    tagsWithoutPrefix.append(tagName.replace(prefix, "", 1))
    if tagsWithoutPrefix[0] == "Pedestals" or tagsWithoutPrefix[0] == "Pedestals":
        tagsWithoutPrefix[0] = "Pedestal"
    elif tagsWithoutPrefix[0] == "Noise" or tagsWithoutPrefix[0] == "Noises":
        tagsWithoutPrefix[0] = "Noise"
    elif tagsWithoutPrefix[0] == "Threshold" or tagsWithoutPrefix[0] == "ClusterThreshold":
        tagsWithoutPrefix = ["LowThreshold", "HighThreshold"]
    elif tagsWithoutPrefix[0][0:3] == "Bad" or tagsWithoutPrefix[0] == "DetVOff":
        tagsWithoutPrefix[0] = "Quality"
    for t in tagsWithoutPrefix:
        newTags.append(str(tag)+"_"+str(t)+ "TkMap_Run_"+str(since)+str(fileType))
    #newTags.append(str(tagWithoutPrefix)+ "TkMap_Run_"+str(since)+str(fileType))
    return newTags'''
    #raise Exception('glob rez:' + str([os.path.basename(x) for x in glob.glob(os.path.join(basedir, '*.%s' % fileType))]))
    #if tag == 'SiStripLorentzAngle_GR10_v1_offline_100609V0':
    #    raise Exception([os.path.basename(x) for x in glob.glob(os.path.join(basedir, '*.%s' % fileType))])
    return [os.path.basename(x) for x in glob.glob(os.path.join(basedir, '*.%s' % fileType))]
    
def get_directory(dbName, tag = '', since = '1', fileType = 'png', basedir = './'):
    return os.path.join(str(basedir), str(dbName), str(tag), str(since))       


class StripFile(StaticFile.StaticFile):

    def __init__(self, dbName, tag, since = '', fileType = 'png', directory = './', png = ''):
        self._dbName = dbName
        self._tag = tag
        self._since = since
        self._fileType = fileType
        self._png = png
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
        self._directory = directory
            
    def get_names(self):
        return get_files(dbName = self._dbName, tag = self._tag, 
                                            since = self._since, fileType = self._fileType, basedir = self._directory)
                                            
    def get_directory(self):
        #return get_directory(dbName = self._dbName, tag = self._tag, since = self._since,
        #                    fileType = self._fileType, basedir = self._directory)
        return self._directory
                            
    def exists(self, name = None):
        #return get_files(dbName = self._dbName, tag = self._tag, 
        #                                    since = self._since, fileType = self._fileType, basedir = self._directory)
        if not name in (None, ''):
            return os.path.isfile(os.path.join(self.get_directory(), name))
        elif os.path.isdir(self.get_directory()):
            #raise Exception('asdasd'+str(os.listdir(self.get_directory())))
            return len(self.get_names()) > 0
        return False
        '''rez = True
        names = []
        if name in (None, ''):
            if self._png != None and self._png != '':
                names = (self._png, )
            else:
                names = self.get_names()
        else:
            names = (name, )
        for i in names:
            nm = os.path.join(self._directory, i)
            if not os.path.isfile(nm):
                rez = False
        return rez'''
               
            

 
class StripPlot(StripFile):
    
    def _create(self):
        cfgfile = CfgFileGenerator.generateCfg(self._dbName, self._tag, self._since, self._directory)
        #if self._tag == 'SiStripDetVOff_GR10_v1_prompt_100705V0':
        dir = os.getcwd()
        #raise Exception('Found TAG: cd %s; cmsRun %s; cd %' % (self._directory, cfgfile, dir))
        #raise Exception('lala' + 'pushd %s; cmsRun %s; popd' % (self._directory, cfgfile))
        os.system('pushd %s; cmsRun %s; popd' % (self._directory, cfgfile)) 
