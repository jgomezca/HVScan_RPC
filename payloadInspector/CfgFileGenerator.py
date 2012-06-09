import sys
from sys import *
import getopt
import os
import os.path
import lastIOVSince
#from PlotsNamesCreator import generateNames
import SubdetectorFactory
#import subprocess
###INPUT
##tagStr = 'SiStripLorentzAngle_GR10_v1_express'
##connStr= 'frontier://PromptProd/CMS_COND_31X_STRIP'
##prefix = "SiStrip"
def usage():
    print"""
#Creates cfg file in given directory:
    print generateCfg( db='frontier://PromptProd/CMS_COND_31X_STRIP', tag='SiStripLorentzAngle_GR10_v1_express', since="1", path="./"):

"""

def getRecord(tagStr = 'SiStripLorentzAngle_GR10_v1_express'):
    recordMap = { "SiStripNoiseRcd": "SiStripNoisesRcd",
                  "SiStripClusterThresholdRcd": "SiStripThresholdRcd",
                  "SiStripShiftAndCrosstalkRcd": "SiStripConfObjectRcd",
                  "SiStripBad": "SiStripBadChannelRcd",
                  "SiStripPedestalRcd": "SiStripPedestalsRcd",
                  "SiStripDetVOffRcd": "SiStripDetVOffRcd"
                }
    tagName = tagStr.split("_", 1)[0]
    recordStr = tagName + "Rcd"
    #if recordStr == "SiStripNoiseRcd": recordStr = "SiStripNoisesRcd"
    if recordStr in recordMap: return recordMap[recordStr]
    elif recordStr[0:10] in recordMap: return recordMap[recordStr[0:10]]
    else: return recordStr
#recordStr = getRecord(tagStr)
def fillValues(tagStr = 'SiStripLorentzAngle_GR10_v1_express', since=1):
    tagName = tagStr.split("_", 1)[0]
    recordStr = getRecord(tagStr)
    isLorentzAngle = False
    isNoise = False
    isTreshold = False
    forMonitor = tagName
    forApvGain = ""
    if tagName == "SiStripLorentzAngle":
        isLorentzAngle = True
    elif tagName == "SiStripPedestals" or tagName == "SiStripPedestal":
        forMonitor = "SiStripPedestal"
    elif tagName == "SiStripNoise" or tagName == "SiStripNoises":
        isNoise = True
        forMonitor = "SiStripNoise"
    elif tagName == "SiStripThreshold" or tagName == "SiStripClusterThreshold":
        isThreshold = True
        forMonitor = "SiStripThreshold"
    elif tagName == "SiStripApvGain":
        forApvGain ="""
process.CondDataMonitoring.FillConditions_PSet.Mod_On           = False # Set to True if you want to have single module histograms
        """        
    if forMonitor == "SiStripThreshold":
        forMonitor ="""
process.CondDataMonitoring.Monitor%s = True
process.CondDataMonitoring.Monitor%s = True
        """ %("SiStripLowThreshold", "SiStripHighThreshold")
    elif forMonitor == "SiStripDetVOff":
        forMonitor = "process.CondDataMonitoring.Monitor%s      = True" %"SiStripQuality"
    elif forMonitor[0:10] == "SiStripBad":
        forMonitor = "process.CondDataMonitoring.Monitor%s      = True" %"SiStripQuality"
    elif forMonitor == "SiStripFedCabling":
        forMonitor = "process.CondDataMonitoring.Monitor%s      = True" %"SiStripCabling"
    else:
        forMonitor = "process.CondDataMonitoring.Monitor%s      = True" %forMonitor
        
    execStr = """
process.CondDataMonitoring.OutputFileName = '%s_Run_%s.root'
process.CondDataMonitoring.MonitorSiStripPedestal      = False
process.CondDataMonitoring.MonitorSiStripNoise         = False
process.CondDataMonitoring.MonitorSiStripQuality       = False
process.CondDataMonitoring.MonitorSiStripCabling       = False
process.CondDataMonitoring.MonitorSiStripApvGain       = False
process.CondDataMonitoring.MonitorSiStripLorentzAngle  = False
process.CondDataMonitoring.MonitorSiStripLowThreshold  = False
process.CondDataMonitoring.MonitorSiStripHighThreshold = False
process.CondDataMonitoring.OutputMEsInRootFile         = False

%s

process.CondDataMonitoring.FillConditions_PSet.OutputSummaryAtLayerLevelAsImage           = True
process.CondDataMonitoring.FillConditions_PSet.OutputSummaryProfileAtLayerLevelAsImage    = %s # This should be saved only in case of LA (because for LA no SummaryAtLayerLevel is available)
process.CondDataMonitoring.FillConditions_PSet.OutputCumulativeSummaryAtLayerLevelAsImage = %s
process.CondDataMonitoring.FillConditions_PSet.HistoMaps_On     = False
process.CondDataMonitoring.FillConditions_PSet.TkMap_On         = True # This is just for test until TkMap is included in all classes!!! Uncomment!!!!
process.CondDataMonitoring.FillConditions_PSet.ActiveDetIds_On  = %s # This should be set to False only for Lorentz Angle
%s
""" %(tagStr, since, forMonitor, isLorentzAngle, isNoise, not isLorentzAngle, forApvGain)
    return execStr

def getPlots(connStr = 'frontier://PromptProd/CMS_COND_31X_STRIP', tagStr = 'SiStripLorentzAngle_GR10_v1_express', since=""):
    tagName = tagStr.split("_", 1)[0]
    messageLogger = ""
    messageSelect = ["""
process.MessageLogger = cms.Service("MessageLogger",
    debugModules = cms.untracked.vstring(''),
    Reader = cms.untracked.PSet(
        threshold = cms.untracked.string('INFO')
    ),
    destinations = cms.untracked.vstring('Reader') #Reader, cout
)
""" ,]
    messageLoggerMap = {"SiStripBad": messageSelect[0],
                        "SiStripDetVOff": messageSelect[0],
                        "SiStripFedCabling": messageSelect[0],
                        "default":
"""
process.MessageLogger = cms.Service("MessageLogger",
    debugModules = cms.untracked.vstring(''),
    cout = cms.untracked.PSet(
        threshold = cms.untracked.string('INFO')
    ),
    destinations = cms.untracked.vstring('cout') #Reader, cout
)
"""
    }
    if tagName in messageLoggerMap:
        messageLogger = messageLoggerMap[tagName]
    elif tagName[0:10] == "SiStripBad": messageLogger = messageLoggerMap[tagName[0:10]]
    else:
        messageLogger = messageLoggerMap["default"]

    iov = lastIOVSince.LastIOVSince(dbName = connStr)
    runnmbr =  str(iov.iovSequence(tag = tagStr).timetype())
        
    return """
import FWCore.ParameterSet.Config as cms

process = cms.Process("Reader")

%s

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
)

process.source = cms.Source("EmptyIOVSource",
    firstValue = cms.uint64(%s),
    lastValue = cms.uint64(%s),
    timetype = cms.string('%s'),
    interval = cms.uint64(1)
)

process.poolDBESSource = cms.ESSource("PoolDBESSource",
   BlobStreamerName = cms.untracked.string('TBufferBlobStreamingService'),
   DBParameters = cms.PSet(
        messageLevel = cms.untracked.int32(2),
        authenticationPath = cms.untracked.string('/afs/cern.ch/cms/DB/conddb')
    ),
    timetype = cms.untracked.string('%s'),
    connect = cms.string('%s'),
    toGet = cms.VPSet(cms.PSet(
        record = cms.string('%s'),
        tag = cms.string('%s')
    ))
)

process.DQMStore = cms.Service("DQMStore",
    referenceFileName = cms.untracked.string(''),
    verbose = cms.untracked.int32(1)
)

process.load("DQM.SiStripMonitorSummary.SiStripMonitorCondData_cfi")

%s

process.CondDataMonitoring.SiStripPedestalsDQM_PSet.FillSummaryAtLayerLevel     = True
process.CondDataMonitoring.SiStripNoisesDQM_PSet.FillSummaryAtLayerLevel        = True
process.CondDataMonitoring.SiStripQualityDQM_PSet.FillSummaryAtLayerLevel       = True
process.CondDataMonitoring.SiStripApvGainsDQM_PSet.FillSummaryAtLayerLevel      = True
process.CondDataMonitoring.SiStripLowThresholdDQM_PSet.FillSummaryAtLayerLevel  = True
process.CondDataMonitoring.SiStripHighThresholdDQM_PSet.FillSummaryAtLayerLevel = True

process.CondDataMonitoring.SiStripCablingDQM_PSet.CondObj_fillId       = 'ProfileAndCumul'
process.CondDataMonitoring.SiStripPedestalsDQM_PSet.CondObj_fillId     = 'onlyProfile'
process.CondDataMonitoring.SiStripNoisesDQM_PSet.CondObj_fillId        = 'onlyCumul'
process.CondDataMonitoring.SiStripQualityDQM_PSet.CondObj_fillId       = 'onlyProfile'
process.CondDataMonitoring.SiStripApvGainsDQM_PSet.CondObj_fillId      = 'ProfileAndCumul'
process.CondDataMonitoring.SiStripLorentzAngleDQM_PSet.CondObj_fillId  = 'ProfileAndCumul'
process.CondDataMonitoring.SiStripLowThresholdDQM_PSet.CondObj_fillId  = 'onlyProfile'
process.CondDataMonitoring.SiStripHighThresholdDQM_PSet.CondObj_fillId = 'onlyProfile'

## --- TkMap specific Configurable options:

process.CondDataMonitoring.SiStripCablingDQM_PSet.TkMap_On     = True
process.CondDataMonitoring.SiStripCablingDQM_PSet.TkMapName    = '%sFedCablingTkMap.png'
process.CondDataMonitoring.SiStripCablingDQM_PSet.minValue     = 0.
process.CondDataMonitoring.SiStripCablingDQM_PSet.maxValue     = 6.

process.CondDataMonitoring.SiStripPedestalsDQM_PSet.TkMap_On     = True
process.CondDataMonitoring.SiStripPedestalsDQM_PSet.TkMapName    = '%sPedestalTkMap.png'
process.CondDataMonitoring.SiStripPedestalsDQM_PSet.minValue     = 0.
process.CondDataMonitoring.SiStripPedestalsDQM_PSet.maxValue     = 400.

process.CondDataMonitoring.SiStripNoisesDQM_PSet.TkMap_On     = True
process.CondDataMonitoring.SiStripNoisesDQM_PSet.TkMapName    = '%sNoiseTkMap.png'
process.CondDataMonitoring.SiStripNoisesDQM_PSet.minValue     = 3.
process.CondDataMonitoring.SiStripNoisesDQM_PSet.maxValue     = 9.

process.CondDataMonitoring.SiStripApvGainsDQM_PSet.TkMap_On     = True
process.CondDataMonitoring.SiStripApvGainsDQM_PSet.TkMapName    = '%sApvGainTkMap.png'
process.CondDataMonitoring.SiStripApvGainsDQM_PSet.minValue     = 0.
process.CondDataMonitoring.SiStripApvGainsDQM_PSet.maxValue     = 1.5

process.CondDataMonitoring.SiStripLorentzAngleDQM_PSet.TkMap_On     = True
process.CondDataMonitoring.SiStripLorentzAngleDQM_PSet.TkMapName    = '%sLorentzAngleTkMap.png'
process.CondDataMonitoring.SiStripLorentzAngleDQM_PSet.minValue     = 0.01
process.CondDataMonitoring.SiStripLorentzAngleDQM_PSet.maxValue     = 0.03

process.CondDataMonitoring.SiStripLowThresholdDQM_PSet.TkMap_On     = True
process.CondDataMonitoring.SiStripLowThresholdDQM_PSet.TkMapName     = '%sLowThresholdTkMap.png'
process.CondDataMonitoring.SiStripLowThresholdDQM_PSet.minValue     = 0.
process.CondDataMonitoring.SiStripLowThresholdDQM_PSet.maxValue     = 10.

process.CondDataMonitoring.SiStripHighThresholdDQM_PSet.TkMap_On     = True
process.CondDataMonitoring.SiStripHighThresholdDQM_PSet.TkMapName     = '%sHighThresholdTkMap.png'
process.CondDataMonitoring.SiStripHighThresholdDQM_PSet.minValue     = 0.
process.CondDataMonitoring.SiStripHighThresholdDQM_PSet.maxValue     = 10.

process.CondDataMonitoring.SiStripQualityDQM_PSet.TkMapName='%sQualityTkMap.png'

process.p1 = cms.Path(process.CondDataMonitoring)
""" %(messageLogger, since, since, runnmbr, runnmbr, connStr, getRecord(tagStr), tagStr, fillValues(tagStr=tagStr, since=since),
      tagStr+"_",
      tagStr+"_",
      tagStr+"_",
      tagStr+"_",
      tagStr+"_",
      tagStr+"_",
      tagStr+"_",
      tagStr+"_",
      )

##def main(argv):
####    global tagStr
####    global connStr
####    global prefix
##    localPath = argv[0]
##    try:
##        opts, args = getopt.getopt(argv[1:], "ht:c:p:", ["help", "tag=", "connection=", "prefix="])
##    except getopt.GetoptError, err:
##        # print help information and exit:
##        print str(err) # will print something like "option -a not recognized"
##        usage()
##        sys.exit(2)
##    output = None
##    verbose = False
##
##    tagStr = 'SiStripLorentzAngle_GR10_v1_express'
##    connStr= 'frontier://PromptProd/CMS_COND_31X_STRIP'
##    prefix = "SiStrip"
##
##    for o, a in opts:
##        if o in ("-h", "--help"):
##            usage()
##            print "labas!"
##            sys.exit()
##        if o in ("-t", "--tag"):
##            tagStr = a
##        else:
##            tagStr = 'SiStripLorentzAngle_GR10_v1_express'
##        if o in ("-c", "--connection"):
##            connStr = a
##        else:
##            connStr = 'frontier://PromptProd/CMS_COND_31X_STRIP'
##        if o in ("-p", "--prefix"):
##            prefix = a
##        else:
##            prefix = "SiStrip"
####        else:
####            assert False, "unhandled option"



def generateCfg( db="", tag="", since="" ,path="./"):
    """
Generates cfg file
    """
    
    tagName = tag.split("_", 1)[0]
    cfgFileEnding = {"SiStripBad" :"""
process.SiStripQualityESProducer = cms.ESProducer("SiStripQualityESProducer",
   ReduceGranularity = cms.bool(False),
   PrintDebugOutput = cms.bool(False),
   UseEmptyRunInfo = cms.bool(False),
   ListOfRecordToMerge = cms.VPSet(cms.PSet(
   record = cms.string('SiStripBadChannelRcd'),
   tag = cms.string('')
   ))
)

process.stat = cms.EDAnalyzer("SiStripQualityStatistics",
    TkMapFileName = cms.untracked.string(''),
    dataLabel = cms.untracked.string('')
)

process.e = cms.EndPath(process.stat)
    """,
                     "SiStripDetVOff":"""
process.SiStripQualityESProducer = cms.ESProducer("SiStripQualityESProducer",
   ReduceGranularity = cms.bool(False),
   PrintDebugOutput = cms.bool(False),
   UseEmptyRunInfo = cms.bool(False),
   ListOfRecordToMerge = cms.VPSet(cms.PSet(
   record = cms.string('SiStripDetVOffRcd'),
   tag = cms.string('')
   ))
)

process.stat = cms.EDAnalyzer("SiStripQualityStatistics",
    TkMapFileName = cms.untracked.string(''),
    dataLabel = cms.untracked.string('')
)

process.e = cms.EndPath(process.stat)
    """,
                     "SiStripFedCabling":
"""
process.SiStripQualityESProducer = cms.ESProducer("SiStripQualityESProducer",
   ReduceGranularity = cms.bool(False),
   PrintDebugOutput = cms.bool(False),
   UseEmptyRunInfo = cms.bool(False),
   ListOfRecordToMerge = cms.VPSet(cms.PSet(
   record = cms.string('SiStripDetCablingRcd'),
   tag = cms.string('')
   ))
)

process.sistripconn = cms.ESProducer("SiStripConnectivity")

process.stat = cms.EDAnalyzer("SiStripQualityStatistics",
    TkMapFileName = cms.untracked.string(''),
    dataLabel = cms.untracked.string('')
)

process.reader = cms.EDAnalyzer("SiStripFedCablingReader")

process.e = cms.EndPath(process.stat*process.reader)
"""
                     }
    execStr = getPlots(connStr=db, tagStr=tag, since=since)
    if tagName in cfgFileEnding: execStr = execStr + cfgFileEnding[tagName]
    elif  tagName[0:10] in cfgFileEnding: execStr = execStr + cfgFileEnding[tagName[0:10]] 

    #subprocess.call('rm %s_cfg.py'% tag, shell=True)
    cfgFileName = '%s_cfg_%s.py'%(tag, since)
    #cfgFileName = SubdetectorFactory.getNames(dbName = db, tag = tag, since = since, fileType = 'py', basedir = path)[0]
    #f = open("%s%s" %(path, cfgFileName), 'w')
    f = open(os.path.join(path, cfgFileName), 'w')
    f.write(execStr)
    f.close
##    localPath = sys.path[0]
##    print localPath
#    os.system('cd %s |cmsenv'% localPath) 
##    subprocess.call('cd %s |cmsenv'% localPath, shell=True)
##    subprocess.call('cmsenv', shell=True)
##    subprocess.call('cmsRun %s_cfg.py'% tagStr, shell=True)
#    tagSmall = tagName.replace(prefix, "", 1)
#    print tagSmall
    #subprocess.call('mv %sTkMap_Run_1.png %s.png'% (tagSmall, tagStr), shell=True)
    return cfgFileName
##cfgFileGen = CfgFileGenerator()
##cfgFileGen.generateCfg( db='frontier://PromptProd/CMS_COND_31X_STRIP', tag='SiStripThreshold_GR10_v1_hlt', since="1", path="./")
##
##
##cfgFileGen.saveCfg(path = "./") #saves cfg file to path
##cfgFileGen.generateNames() # ["SiStripThreshold_GR10_v1_hlt_HighThresholdTkMap_Run_1.png", "SiStripThreshold_GR10_v1_hlt_Low_HighThresholdTkMap_Run_1.png"]

if __name__ == "__main__":
    tags ="""
    AlCaRecoTriggerBits_SiStripDQM_v2_express
    runinfo_start_31X_hlt_100419V0_SiStripFedCabling_GR10_v1_hlt_100419V0
    SiStripApvGain_FromParticles_GR10_v1_express
    SiStripApvLatency_GR10_v1_hlt
    SiStripBadChannel_FromOfflineAnalysis_GR10_v1_express
    SiStripBadChannel_FromOfflineCalibration_GR10_v1_express
    SiStripBadChannelsFromO2O_CRAFT09_DecMode_ForTrackerSim
    SiStripBadComponents_OfflineAnalysis_HotStrips_GR09_31X_v2_offline
    SiStripBadFiber_Ideal_31X_v2
    SiStripBadModule_2009_v1_express
    SiStripBadStrip_FromOnlineDQM_V1
    SiStripClusterThreshold_GR10_v1_express
    SiStripDetVOff_GR10_v1_express
    SiStripFedCabling_GR10_v1_hlt
    SiStripLatency_GR10_v2_hlt
    SiStripLorentzAngle_GR10_v1_express
    SiStripNoise_GR10_v1_hlt_100705V0_SiStripApvGain_GR10_v1_hlt_100705V0
    SiStripNoise_GR10_v1_hlt
    SiStripNoises_Ideal_PeakMode_31X_v2
    SiStripPedestal_CRAFT09_DecMode_ForTrackerSim
    SiStripPedestals_GR10_v1_hlt
    SiStripShiftAndCrosstalk_GR10_v1_offline
    SiStripThreshold_GR10_v1_hlt
    """.split()
    for t in tags:
        print generateCfg( db='frontier://PromptProd/CMS_COND_31X_STRIP', tag=t, since="1", path="./")



