#!/bin/bash
SCRAM_ARCH=$1
RELEASE=$2

#SCRAM_ARCH=slc5_amd64_gcc434
#RELEASE=CMSSW_5_0_0

export CMSSW_RELEASE_BASE=/afs/cern.ch/cms/${SCRAM_ARCH}/cms/cmssw/${RELEASE}
UNAME=`uname`
if [ "$UNAME" == "Linux" ]; then
   for plug in ${CMSSW_RELEASE_BASE}/lib/${SCRAM_ARCH}/pluginCondCore*Plugins.so; do nm -C $plug 2>&1 | sed "/nm: .* Plugins.so\': No such file/ d" | grep "vtable for DataProxy<" | sed "s/^.* DataProxy<//g" | sed "s/>$//g";done
else
   for plug in ${CMSSW_RELEASE_BASE}/lib/${SCRAM_ARCH}/pluginCondCore*Plugins.so; do ssh lxplus "nm -C $plug 2>&1" | sed "/nm: .* Plugins.so\': No such file/ d" | grep "vtable for DataProxy<" | sed "s/^.* DataProxy<//g" | sed "s/>$//g";done
fi
#for plug in ${CMSSW_RELEASE_BASE}/lib/${SCRAM_ARCH}/pluginCondCore*Plugins.so; do nm -C $plug 2>&1 | sed "/nm: .* Plugins.so\': No such file/ d" | grep "vtable for DataProxy<" | sed "s/^.* DataProxy<//g" | sed "s/>$//g";done
