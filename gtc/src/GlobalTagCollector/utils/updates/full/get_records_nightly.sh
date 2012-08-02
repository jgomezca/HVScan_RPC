#!/bin/bash
hardware_arch=$1
nightly_path=$2
#slc5_amd64_gcc434
base_path=/afs/cern.ch/cms/sw/ReleaseCandidates/$hardware_arch
export CMSSW_RELEASE_BASE=$base_path
for plug in ${CMSSW_RELEASE_BASE}/$nightly_path/pluginCondCore*Plugins.so
    do nm -C $plug 2>&1 | sed "/nm: .* Plugins.so\': No such file/ d" | grep "vtable for DataProxy<" | sed "s/^.* DataProxy<//g" | sed "s/>$//g"
done