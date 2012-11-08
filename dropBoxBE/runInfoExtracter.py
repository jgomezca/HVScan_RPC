#!/usr/bin/env python

import os, sys, re, copy
import subprocess
import json
import tarfile

import metadata
import conditionDatabase
from conditionError import ConditionError

errRe = re.compile( '^ERROR: ')
warnRe = re.compile( '^WARNING: ' )

#dataFolder = '/afs/cern.ch/work/g/govi/dropbox'
dataFolder = '/tmp/ramdisk'

class RunInfoExtracter(object):


    def scanLog(self):
        _fwLoad = conditionDatabase.condDB.FWIncantation()
        delRe = re.compile( '^----- new cronjob started for Offline  at -----$')
        hltRe = re.compile('DEBUG: Next run to be processed by HLT (\S+)')
        promptRe = re.compile('DEBUG: Next run to be processed by Tier-0 (\S+)')
        expRe0 = re.compile('^INFO: We are going to export the sqlite file "(\S+)", using the metadata file "(\S+)"')
        expRe1 = re.compile('INFO: destDB: "(\S+)", inputtag: "(\S+)", tag: "(\S+)", from "(\S+)" \(run = "(\d+)",lumi =')
        dupRe0 = re.compile('INFO: Preparing to duplicate IOV with since value "(\d+)" from the source tag "(\S+)" on the destination tag "(\S+)" with new IOV since value "(\d+)" coming from "(\S+)"')
        dupRe1 = re.compile('INFO: Preparing to duplicate IOV with since value "(\d+)" from the source tag "(\S+)" on the destination tag "(\S+)" with the same IOV since value, since the value "(\d+)" coming from "(\S+)" is smaller')
        started = False

        lfn = "/afs/cern.ch/cms/DB/conddb/test/dropbox/replay/LogSelection.log"
        #lfn = "LogSelection.log"
        logFile = open(lfn, 'r')
        lineCount = 0
        newItem = False
        time = ''
        data = {}
        fileName = ''
        synch = ''
        lastSince = None
        fileCount = 0
        expCount = 0
        dupCount = 0
        hltVal = -2
        promptVal = -2
        filename = None
        for lineIn in logFile.xreadlines():
            line = lineIn.strip()

            if newItem:
                newItem = False
                time = line
                print 'Processing dropbox run at: %s' %(time)
                continue

            delMatch = delRe.match(line)
            if delMatch:
                started = True
                newItem = True
                hltVal = None
                promptVal = None
                continue
            if not started:
                continue
            hltMatch = hltRe.match(line)
            if hltMatch:
                hltVal = hltMatch.group(1)
                continue
            promptMatch = promptRe.match(line)
            if promptMatch:
                promptVal = promptMatch.group(1)
                continue
            exportMatch = expRe0.match(line)
            if exportMatch:
                export = True
                filename = exportMatch.group(1)
                                
                fileData = []
                data[filename] = fileData
                if hltVal is not None: 
                    data[filename].append(('dropbox_run','hlt',hltVal))
                if promptVal is not None: 
                    data[filename].append(('dropbox_run','prompt',promptVal))

                fileCount += 1
                tarfilename = filename[:-3]+'.tar.bz2'
                print 'opening tarfile %s' %(tarfilename)
                #if not os.path.exists(os.path.join(dataFolder,tarfilename)):
                #    print 'file %s does not exist.' %(os.path.join(dataFolder,tarfilename))
                #    continue
                #tarFile = tarfile.open(os.path.join(dataFolder, tarfilename))
                #names = tarFile.getnames()
                #if len(names) != 2:
                #    raise Exception('%s: Invalid number of files in tar file.', fileName)
                #baseFileName = names[0].rsplit('.', 1)[0]
                #dbFileName = '%s.db' % baseFileName
                #txtFileName = '%s.txt' % baseFileName
                #if set([dbFileName, txtFileName]) != set(names):
                #    raise Exception('%s: Invalid file names in tar file.', fileName)
                #md = json.loads(metadata.port(tarFile.extractfile(txtFileName).read()))
                #synch = md['destinationTags'].items()[0][1]['synchronizeTo']
                #tag = md['destinationTags'].items()[0][0]
                #with open('/tmp/replayRequest.db', 'wb') as f:
                #    f.write(tarFile.extractfile(dbFileName).read())
                #tarFile.close()
                #rdbms = conditionDatabase.condDB.RDBMS( '' )
                #db = rdbms.getReadOnlyDB( str('sqlite_file:/tmp/replayRequest.db') )  
                #iov = conditionDatabase.IOVChecker( db )
                #db.startReadOnlyTransaction()
                #tagList = db.allTags().strip().split()
                #db.commitTransaction()
                #if not tag in tagList:
                #    continue
                #iov.load( tag )
                #lastSince = iov.lastSince()
                #db.closeSession()
                continue
            expDetails = expRe1.match(line)
            if expDetails:
                expCount += 1
                if synch == 'hlt' or synch == 'prompt':
                    sincValue = expDetails.group(5)
                    if lastSince <= sincValue:
                        data[filename].append(('export',synch,sincValue))
                continue
            dupS0 = dupRe0.match(line)
            if dupS0:
                dupCount += 1
                data[filename].append(('duplicate',dupS0.group(5),dupS0.group(4)))
                continue
            dupS1 = dupRe1.match(line)
            if dupS1:
                dupCount += 1
                data[filename].append(('duplicate',dupS1.group(5),dupS1.group(4)))
                continue
            lineCount +=1
        print 'File processed %d exports %d duplicates %d' %(fileCount,expCount,dupCount)
        with open('runInfoFromLog.json','wb') as f:
            json.dump(data,f)            
                

               
extracter = RunInfoExtracter()
extracter.scanLog()


        
