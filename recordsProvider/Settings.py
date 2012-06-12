"""
Settings
========
"""
import datetime

HARDWARE_ARCHITECTURES = ['slc5_amd64_gcc434','slc5_amd64_gcc451', 'slc5_ia32_gcc434', 'slc5_amd64_gcc462']
HARDWARE_ARCHITECTURES_UPDATED = datetime.date(2012, 5, 14)

SOFTWARE_RELEASE_NAME_PATTERN = "^CMSSW_(\d+)_(\d+)_(\d+)(?:_pre(\d+))?$"
RELEASES_PATH = "/afs/cern.ch/cms/{hardware_architecture}/cms/cmssw" #cmspath + ...
CACHE_DIR = 'cache'

