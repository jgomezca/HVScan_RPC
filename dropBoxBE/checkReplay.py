#!/usr/bin/env python2.6

import sys
import json

import conditionDatabase
import config

referenceDBConnStr = "sqlite_file:/afs/cern.ch/cms/DB/conddb/test/dropbox/replay/replayReference.db"
replayMaster = "sqlite_file:/afs/cern.ch/cms/DB/conddb/test/dropbox/replay/replayMaster.db"
replayDBConnStr = "oracle://cms_orcoff_prep/CMS_COND_DROPBOX"



def main():

    # The skipped tags are the ones from prep at the moment
    prepTags = []

    with open('replayTags.json', 'rb') as f:
        replayTags = json.load(f)

    for destinationDatabase in replayTags:
        if destinationDatabase.startswith('oracle://cms_orcoff_prep/'):
            for t in replayTags[destinationDatabase]:
                prepTags.append(str(t))
                print "WARNING: Tag %s has been targeted to PREP DB in the replay files." %(t)

    conf = config.replay()
    _fwLoad = conditionDatabase.condDB.FWIncantation()
    rdbms = conditionDatabase.condDB.RDBMS( conf.authpath )
    # reference
    print 'opening reference DB...'
    referenceDB = rdbms.getReadOnlyDB( referenceDBConnStr )
    referenceDB.startReadOnlyTransaction()
    refTagList = referenceDB.allTags().strip().split()
    referenceDB.commitTransaction()
    print 'Found %d tags in reference.' %(len(refTagList)) 
    #replay
    print 'opening replay DB...'
    replayDB = rdbms.getReadOnlyDB( replayDBConnStr )
    replayDB.startReadOnlyTransaction()
    replayTagList = replayDB.allTags().strip().split()
    #replayTagList = [x for x in replayTagList if x not in skippedTags]
    replayDB.commitTransaction()
    print 'Found %d tags in replay.' %(len(replayTagList)) 

    if not len(refTagList)==len(replayTagList):
        print 'ERROR: Tag size content is different'
    missingTags = []
    for tag in refTagList:
        if not tag in replayTagList:
            print "ERROR: Reference Tag %s has not been found in the replay database." %(tag)
            missingTags.append( tag )
    for tag in replayTagList:
        if not tag in refTagList:
            if not tag in prepTags:
                print "ERROR: Replay tag %s has not been found in the reference database." %(tag)

    refIov = conditionDatabase.IOVChecker( referenceDB )
    replayIov = conditionDatabase.IOVChecker( replayDB  )
    numberOfErrors = 0
    numberOfComparison = 0
    for tag in refTagList:
        if tag in missingTags:
            continue
        numberOfComparison += 1
        refIov.load( tag )
        refSize = refIov.size()
        replayIov.load( tag )
        replaySize = replayIov.size()
        print "**** Checking Tag %s" %(tag)
        print "     Size in ref DB: %d; in replay: %d" %(refSize,replaySize)
        refIovs = refIov.getAllSinceValues()
        replayIovs = replayIov.getAllSinceValues()
        if not refIovs == replayIovs:
            timeType = refIov.timetype()
            error = True
            print '     ERROR: IOV content is different'
            print "     List of different elements:"
            numberOfErrors += 1
            printElem = False
            kLowMask = 0XFFFFFFFF
            for i in range(max(refSize,replaySize)):
                ref = ''
                rep = ''
                if i<refSize:
                    refElem = refIovs[i]
                    if str(timeType) == 'lumiid':
                        lumiBlock = refElem & kLowMask
                        refElem = refElem >> 32
                        ref = "%s/%s" %(refElem,lumiBlock)
                    else:
                        ref = str(refElem)
                if i<replaySize:
                    repElem = replayIovs[i]
                    if str(timeType) == 'lumiid':
                        lumiBlock = repElem & kLowMask
                        repElem = repElem >> 32
                        rep = "%s/%s" %(repElem,lumiBlock)
                    else:
                        rep = str(repElem)
                if not ref == rep:
                    printElem = True
                if printElem:
                    print '        Elem[%d] ref=%s     replay=%s' %(i,ref,rep)
        else:
            print '     Comparison OK.'
    print "\n" 
    print "Tags compared:%d. Found with difference:%s" %(numberOfComparison,numberOfErrors)
    referenceDB.closeSession()
    replayDB.closeSession()
    return 0
           
if __name__ == '__main__':
    sys.exit(main())

