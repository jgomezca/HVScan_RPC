export SCRAM_ARCH=slc5_amd64_gcc462
source /afs/cern.ch/cms/cmsset_default.sh
CMSSW_RELEASE=CMSSW_6_0_0_pre6
CMSSW_REL=/afs/cern.ch/cms/$SCRAM_ARCH/cms/cmssw/$CMSSW_RELEASE/

pushd $CMSSW_REL >/dev/null
eval `scramv1 runtime -sh`
popd >/dev/null

