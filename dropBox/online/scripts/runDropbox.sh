#!/bin/bash

DOMAINNAME=`dnsdomainname`

if [[ ${DOMAINNAME} == "cern.ch" ]]
then
    MODE="OFFLINE"
elif [[ ${DOMAINNAME} == "cms" ]]
then
    MODE="ONLINE"
else
    echo "ERROR! Unknown mode."
    exit 1
fi

if [[ ${MODE} == "ONLINE" ]]
then
    BASEDIR=/nfshome0/pocondev
    #BASEDIR=/nfshome0/poconpro
    if [[ $1 == "local" ]]
    then                                       # ONLINE LOCAL
        export SCRAM_ARCH=slc5_amd64_gcc462
        CMSSWDIR=/data/cmssw
        RELEASEDIR=${CMSSWDIR}/cms/cmssw
    else                                       # ONLINE NOT LOCAL
        export SCRAM_ARCH=slc5onl_amd64_gcc462
        CMSSWDIR=/opt/cmssw
        RELEASEDIR=${CMSSWDIR}/cms/online
    fi
elif [[ ${MODE} == "OFFLINE" ]]
then                                           # OFFLINE
    BASEDIR=`pwd`  ## /home/`whoami`
    TASK=scripts
    export SCRAM_ARCH=slc5_amd64_gcc462
fi

DIR=${BASEDIR}
RELEASE=CMSSW_5_2_6
source /afs/cern.ch/cms/cmsset_default.sh
cd /afs/cern.ch/cms/${SCRAM_ARCH}/cms/cmssw/${RELEASE}/src
eval `scramv1 runtime -sh`
cd - 2>&1 >/dev/null

export TNS_ADMIN=/afs/cern.ch/cms/DB/conddb

# for the new authentication system:
# export COND_AUTH_SYS=1
export COND_AUTH_PATH=/afs/cern.ch/cms/DB/conddb/test/dropbox

export PYTHONPATH=${PYTHONPATH}:${DIR}

if [[ ${MODE} == "OFFLINE" ]]
then
    python ${DIR}/modules/Dropbox.py #>> /tmp/test.log 2>&1
else
    echo "ToDo"
fi
