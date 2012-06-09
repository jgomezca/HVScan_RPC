export SCRAM_ARCH=slc5_amd64_gcc462
source /afs/cern.ch/cms/cmsset_default.sh

# CMSSW_RELEASE must be exported for get_cmsswReleas()
export CMSSW_RELEASE=CMSSW_5_2_5
CMSSW_REL=/afs/cern.ch/cms/$SCRAM_ARCH/cms/cmssw/$CMSSW_RELEASE/

pushd $CMSSW_REL >/dev/null
eval `scramv1 runtime -sh`
popd >/dev/null

PI_USER=`whoami`
PI_PORT=8087
PI_file_dir=/tmp/PayloadInspector_$CMSSW_RELEASE\_$PI_USER\_$PI_PORT/
mkdir -p $PI_file_dir
export PI_file_dir_plot_trend=$PI_file_dir/plot-trend
mkdir -p $PI_file_dir_plot_trend
export PI_file_dir_plot=$PI_file_dir/plot
mkdir -p $PI_file_dir_plot
export PI_file_dir_html=$PI_file_dir/html
mkdir -p $PI_file_dir_html
export PI_file_dir_xml=$PI_file_dir/xml
mkdir -p $PI_file_dir_xml
export PI_file_dir_json=$PI_file_dir/json
mkdir -p $PI_file_dir_json
export PI_file_dir_tmp=$PI_file_dir/tmp
mkdir -p $PI_file_dir_tmp

