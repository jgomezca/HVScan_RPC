#!/bin/sh
hardware_arch=$1
#slc5_amd64_gcc434
cd /afs/cern.ch/cms/sw/ReleaseCandidates/$hardware_arch
for weekday in mon tue wed thu fri sat sun
do
    for fold in  `ls $weekday`
    do
        cmssw_fold=`ls  $weekday/$fold | grep -E  "^CMSSW_[0-9]+_[0-9]+_X_[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}$" `
        if [ -n "$cmssw_fold" ]; then
            echo $cmssw_fold $hardware_arch $weekday/$fold/$cmssw_fold/lib/$hardware_arch
        fi
        #$weekday $fold
    done
done
