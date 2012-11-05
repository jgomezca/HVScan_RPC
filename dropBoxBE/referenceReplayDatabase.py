#!/usr/bin/env python2.6

import sys
#import optparse
import subprocess
import json
import datetime

import conditionDatabase
from conditionError import ConditionError

defaultMasterDB = 'sqlite_file:replayReference.db'
defaultArchID = 'CH31'
endArchiveID = 'CK02'
defaultInputFile = 'replayTags.json'

connectionPrefix = 'oracle://cms_orcon_prod/'

class ReplayMaster( object ):
    def __init__(self, databaseConnection ):
        self.db = databaseConnection
    
    def executeAndLog(self, command, verbose=False):
        # processing
        if( verbose ):
           print "Executing command :'%s'" %(command)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (stdoutdata, stderrdata) =  process.communicate()
        retcode = process.returncode

        if ( retcode != 0 and stderrdata != None) : # we got an error, report it
            if(stdoutdata != None ):
                print "ERROR: %s" %(stdoutdata)
            if(stderrdata != None ):
                print "ERROR: %s" %(stderrdata)
            return False

        else: # no error ... so far ... :(
            if(stdoutdata != None ):
                # todo: parse stdout and see if it contains other errors
                if 'An exception of category' in stdoutdata :
                    print "ERROR: %s" %(stdoutdata)
                    return False
                else: # no error here, log and return success
                    print "DEBUG: %s" %(stdoutdata)
                    return True

                # no stdout received ... todo: decide whether this is an error (log and return false if so)
            return True

    def importTags(self, fileName, archiveID ):
        tagData = json.load( open( fileName ) )
        _fwLoad = conditionDatabase.condDB.FWIncantation()
        authPath = ''
        rdbms = conditionDatabase.condDB.RDBMS( authPath )

        now = datetime.datetime.now()
        print 'Starting processing at:',now
        for connStr,tags in tagData.items():
            # first re-compose the connection string to point to the snapshot storage
            prefix = "oracle://cms_orcon_prod/"
            if(connStr.find(connectionPrefix)==0):
                print "==> Processing tags in database:'%s'" %(connStr)
                accountName = connStr[len(connectionPrefix):len(connStr)]
                connStr = "frontier://FrontierArc/"+accountName+"_"+archiveID
                print "Reading from ARCHIVE database using FronTier. Connection string:'%s'" %(connStr)
                prodConnStr = "frontier://FrontierArc/"+accountName+"_"+endArchiveID
                print "Reading from ARCHIVE database using FronTier. Connection string:'%s'" %(prodConnStr)
                try:
                    db0 = rdbms.getReadOnlyDB( str(connStr) )  
                    iov0 = conditionDatabase.IOVChecker( db0 )
                    db1 = rdbms.getReadOnlyDB( str(prodConnStr) )  
                    for tag in tags:
                        lastSince = 1
                        print "Processing tag:'%s'" %(tag)
                        try:
                            db0.startReadOnlyTransaction()
                            tagList0 = db0.allTags().strip().split()
                            db0.commitTransaction()
                            if( tag in tagList0 ):
                                iov0.load( tag )
                                lastSince = iov0.lastSince()

                            print 'Last Since=%d' %(lastSince)
                            db1.startReadOnlyTransaction()
                            tagList1 = db1.allTags().strip().split()
                            db1.commitTransaction()
                            if( tag in tagList1 ):                                
                                command = "cmscond_export_iov" + \
                                          " -s " + prodConnStr + \
                                          " -d " + self.db + \
                                          " -t " + tag + \
                                          " -b " + str(lastSince) 

                                if( not self.executeAndLog( command, True ) ):
                                    print 'Execution stopped beacuse of errors.'
                                    return False
                            else:
                                print "Tag:'%s' has not been found in '%s'" %(tag,prodConnStr)
                                
                        except RuntimeError as err:
                            print "Error: ",err
                            print "Skipping tag:'%s' in account:'%s'" %(tag,connStr) 
                        except ConditionError as err:
                            print "Error: ",err
                            print "Skipping tag:'%s' in account:'%s'" %(tag,connStr)        
                except ConditionError as err:
                    print "Error: ",err
                    print "Skipping tags in account:'%s'" %(connStr) 
                    print ""
            else:
                print "==> Skipping tags in non-production account:'%s'" %(connStr)
        print 'Tag list fully processed.'
        now = datetime.datetime.now()
        print 'End of processing at:',now
        return True


def main():

    #parser = optparse.OptionParser(usage =
    #    'Usage: %prog <file> [<file> ...]\n'
    #)

    #parser.add_option('-d', '--DB',
    #    dest = 'db',
    #    default = defaultMasterDB,
    #    help = 'Specify the database. Default: %default',
    #)

    #parser.add_option('-i', '--import',
    #    dest = 'inputFile',
    #    help = 'import data sets from an account/tag list ',
    #)

    #parser.add_option('-P', '--authPath',
    #    dest = 'authPath',
    #    default = defaultAuthPath,
    #    help = 'Authentication Path. Default: %default',
    #)

    #parser.add_option('-a', '--archID',
    #    dest = 'archID',
    #    default = defaultArchID,
    #    help = 'Archive ID to be used as a source. Will be remapped on the source database from the input list during the import',
    #)

    #(options, arguments) = parser.parse_args()

    
    #if(not options.inputFile== None):
        #masterDB = ReplayMaster( options.db )
        #if( not masterDB.importTags( options.inputFile, options.archID, options.authPath ) ):
        #    return -1
        #return 0

    #print "ERROR: no main option submitted (--import)"
    #return -1
    
    masterDB = ReplayMaster( defaultMasterDB )
    if( not masterDB.importTags( defaultInputFile, defaultArchID ) ):
        return -1
    return 0

           
if __name__ == '__main__':
    sys.exit(main())

