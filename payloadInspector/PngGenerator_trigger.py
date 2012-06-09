from optparse import OptionParser
import SubdetectorFactory
import os

def _create(self):
    '''Create a plot. File type is defined automaticaly by object name extension.'''
    ecalCondDB = EcalCondDB.EcalCondDB(self._dbName)
    #print "\n###self._directory: ",self._directory
    ecalCondDB.plot(self._tag, self._since, os.path.join(self._directory, self._name))

def createPlot(dbName = None, tag = None, since = None, plots = None, plot = None):
    if plot == None and dbName != None and tag != None and since != None and plots != None:
        plot = SubdetectorFactory.getPlotInstance(dbName = dbName, tag = tag, since = since, 
                                       fileType = 'png', directory = plots)
    #while (not plot.exists(name = '')):
    
    plot.create()
    #if tag == 'SiStripDetVOff_GR10_v1_prompt_100705V0':
    #    raise Exception('MUAHAHHAHAHHAHAH')
    
#def createHisto(dbName = None, tag = None, since = None, histodir = None, histoobj = None):
#    if histoobj == None and dbName != None and tag != None and since != None and histodir != None:
#        histo = SubdetectorFactory.getHistoInstance(dbName = dbName, tag = tag, since = since, )
    
def generateData(dbName=None, tag=None, since=None, plots=None, plot=None):
    if plot != None:
        createPlot(plot = plot)
    elif dbName != None and tag != None and since != None and plots != None:
        createPlot(dbName = dbName, tag = tag, since = since, plots = plots)
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-d', '--db', dest = 'db', type = 'string', default = 'cms_orcoff_prod', help = 'source database')
    parser.add_option('-a', '--account', dest = 'acc', type = 'string', default = '', help = 'db account')
    parser.add_option('-t', '--tag', dest = 'tag', type = 'string', default = '', help = 'tag name')
    parser.add_option('-s', '--since', dest = 'since', type = 'string', default = '1', help = 'IOV value')
    parser.add_option('-r', '--directory', dest = 'dir', type = 'string', default = os.popen('csh start.csh plotsdir').read().strip(), help = 'directory name')
    options = parser.parse_args()[0]
    #plots = os.popen('csh start.csh plotsdir').read().strip()
    generateData(dbName = 'oracle://%s/%s' % (options.db, options.acc), tag = options.tag, since = options.since, plots = options.dir)
    
           
