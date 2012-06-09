#import CondDBPayloadInspector_backend
import lastIOVSince
import os
import PngGenerator_trigger as pnggen
from optparse import OptionParser
import sqlite3
import config

def generateData(dbName, dir):
    try:
        iov = lastIOVSince.LastIOVSince(dbName = dbName)  
        tags = iov.getTags()
        #cdb = CondDBPayloadInspector_backend.CondDBPayloadInspector()
        for tag in tags:
            #try:
            #print 'analyzing tag %s' % tag
            #if you want to generate the plots for a specific tag
            if tag != 'SiStripPedestals_GR10_v2_hlt':
                print "\n\nTAG:",tag
                continue
            iovs = iov.iovSequence(tag = tag).elements
            for i in iovs:
                #try:
                print 'generating data for: db=%s, tag=%s, since=%s' % (dbName, tag, str(i.since()))
                pnggen.generateData(dbName = dbName, tag = tag, since = str(i.since()), plots = dir)
                #except:
                #    pass
            #except:
            #    pass

    except RuntimeError, e:
        print 'Error making connecting to DB. %s' % str(e)
    #except Exception, e:
    #    print str(e)

        
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-d", "--dbName", dest = "dbName", type = 'string', default = 'cms_orcoff_prod', help = "name of the database.")  
    parser.add_option("-b", "--db-file", dest = "dbfile", type = 'string', default = 'Users.db', help = "name of database file.")  
    parser.add_option('-f', '--folder', dest = 'dir', type = 'string', default = config.folders.plots_dir, help = 'directory name')
    (options, args) = parser.parse_args()
    con = sqlite3.Connection(options.dbfile)
    cur = con.cursor()
    print 'Selecting data from DB..'
    cur.execute('select connStr from users where dbName = ?', (options.dbName, ))
    print 'Data from DB was selected'
    i = cur.fetchone()
    while i:
        #try:
        print 'working on  ' + i[0]
        if i[0].find('31X_STRIP') != -1:# or
        #if i[0].find('31X_ECAL') != -1:
            #print i[0]
            generateData(str(i[0]), options.dir)
        #except:
        #    print 'error while working on ' + i[0]
        #    pass
        #finally:
        i = cur.fetchone()
    #generateAllPngs('oracle://cms_orcoff_prod/CMS_COND_31X_STRIP')
    #generateAllPngs(options.dbName)
