#!/usr/bin/env python2.6

import sys
import json

import conditionDatabase
import config

referenceDBConnStr = "sqlite_file:/afs/cern.ch/cms/DB/conddb/test/dropbox/replay/replayReference.db"
replayDBConnStr = "oracle://cms_orcoff_prep/CMS_COND_DROPBOX"



def main():

    # The skipped tags are the ones from prep at the moment
    skippedTags = set([])

    with open('replayTags.json', 'rb') as f:
        replayTags = json.load(f)

    for destinationDatabase in replayTags:
        if destinationDatabase.startswith('oracle://cms_orcoff_prep/'):
            skippedTags.update(replayTags[destinationDatabase])

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
    replayTagList = [x for x in replayTagList if x not in skippedTags]
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
            print "ERROR: Replay tag %s has not been found in the reference database." %(tag)

    refIov = conditionDatabase.IOVChecker( referenceDB )
    replayIov = conditionDatabase.IOVChecker( replayDB  )
    numberOfErrors = 0
    numberOfComparison = 0
    for tag in refTagList:
        error = False
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
        if not refSize == replaySize:
            error = True
        if not refIovs == replayIovs:
            error = True
            #for iov in replayIovs:
            #    if not iov in refIovs:
            #       print "     Iov element %s from replay has not been found in the reference." %(iov)
            #for iov in refIovs:
            #    if not iov in replayIovs:
            #       print "     Iov element %s from reference has not been found in the replay." %(iov)
        if error:
            print '     ERROR: IOV content is different'
            print "     List of different elements:"
            numberOfErrors += 1
            for i in range(max(refSize,replaySize)):
                ref = ''
                rep = ''
                if i<refSize:
                    ref = str(refIovs[i])
                if i<replaySize:
                    rep = str(replayIovs[i])
                if not ref == rep:
                    print '        Elem[%d] ref=%s replay=%s' %(i,ref,rep)
        else:
            print '     Comparison OK.'
    print "\n" 
    print "Tags compared:%d. Found with difference:%s" %(numberOfComparison,numberOfErrors)
    referenceDB.closeSession()
    replayDB.closeSession()
    return 0
           
if __name__ == '__main__':
    sys.exit(main())

