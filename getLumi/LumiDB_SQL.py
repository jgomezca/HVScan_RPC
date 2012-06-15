import sys

import cx_Oracle

import coral
from RecoLuminosity.LumiDB import sessionManager,lumiTime,inputFilesetParser,csvSelectionParser,selectionParser,csvReporter,argparse,CommonUtil,lumiCalcAPI,lumiReport,lumiCorrections

import service

conn_string = service.getCxOracleConnectionString(service.secrets['connections']['pro'])

def formatDelivered(lumidata,resultlines,scalefactor=1.0,isverbose=False):
    '''
    input:  {run:[lumilsnum(0),cmslsnum(1),timestamp(2),beamstatus(3),beamenergy(4),deliveredlumi(5),calibratedlumierror(6),(bxidx,bxvalues,bxerrs)(7),(bxidx,b1intensities,b2intensities)(8),fillnum(9)]}
    '''
    result=[]
    fieldnames = ['Run:Fill', 'N_LS', 'Delivered(/ub)','UTCTime','E(GeV)']

    for rline in resultlines:
        result.append(rline)

    for run in lumidata.keys():
        lsdata=lumidata[run]
        if not lsdata :
            result.append([run,'n/a','n/a','n/a','n/a'])
            continue
        nls=len(lsdata)
        fillnum=0
        # if lsdata[0][9]:
        #     fillnum=lsdata[0][9]
        totlumival=sum([x[5] for x in lsdata])
        beamenergyPerLS=[float(x[4]) for x in lsdata]
        avgbeamenergy=0.0
        if len(beamenergyPerLS):
            avgbeamenergy=sum(beamenergyPerLS)/len(beamenergyPerLS)
        runstarttime='n/a'
        if nls!=0:
            runstarttime=lsdata[0][2]
            runstarttime=runstarttime.strftime("%m/%d/%y %H:%M:%S")
        if isverbose:
            selectedls='n/a'
            if nls:
                selectedls=[(x[0],x[1]) for x in lsdata]
            result.append([str(run)+':'+str(fillnum),nls,totlumival*scalefactor,runstarttime,avgbeamenergy, str(selectedls)])
        else:
            result.append([str(run)+':'+str(fillnum),nls,totlumival*scalefactor,runstarttime,avgbeamenergy])
    # sortedresult=sorted(result,key=lambda x : int(x[0].split(':')[0]))

    return result

def formatOverview(lumidata,resultlines,scalefactor=1.0,isverbose=False):
    '''
    input:
    lumidata {run:[lumilsnum(0),cmslsnum(1),timestamp(2),beamstatus(3),beamenergy(4),deliveredlumi(5),recordedlumi(6),calibratedlumierror(7),(bxidx,bxvalues,bxerrs)(8),(bxidx,b1intensities,b2intensities)(9),fillnum(10)]}
    resultlines [[resultrow1],[resultrow2],...,] existing result row
    '''
    result=[]
    fieldnames = ['Run:Fill', 'DeliveredLS', 'Delivered(/ub)','SelectedLS','Recorded(/ub)']

    for rline in resultlines:
        result.append(rline)
        
    for run in lumidata.keys():
        lsdata=lumidata[run]
        if lsdata is None:
            result.append([run,'n/a','n/a','n/a','n/a'])
            continue
        nls=len(lsdata)
        fillnum=0

        deliveredData=[x[5] for x in lsdata]
        recordedData=[x[6] for x in lsdata if x[6] is not None]
        totdeliveredlumi=0.0
        totrecordedlumi=0.0
        if len(deliveredData)!=0:
            totdeliveredlumi=sum(deliveredData)
        if len(recordedData)!=0:
            totrecordedlumi=sum(recordedData)
        selectedcmsls=[x[1] for x in lsdata if x[1]!=0]
        if len(selectedcmsls)==0:
            selectedlsStr='n/a'
        else:
            selectedlsStr = CommonUtil.splitlistToRangeString(selectedcmsls)
        result.append([str(run)+':'+str(fillnum),nls,totdeliveredlumi*scalefactor,selectedlsStr,totrecordedlumi*scalefactor])
    # sortedresult=sorted(result,key=lambda x : int(x[0].split(':')[0]))
    
    return result

def formatRecorded(lumidata,resultlines,scalefactor=1.0,isverbose=False):
    '''
    input:  {run:[lumilsnum(0),cmslsnum(1),timestamp(2),beamstatus(3),beamenergy(4),deliveredlumi(5),recordedlumi(6),calibratedlumierror(7),{hltpath:[l1name,l1prescale,hltprescale,efflumi]}(8),bxdata(9),beamdata(10),fillnum(11)]}
    '''
    result=[] # [run,ls,hltpath,l1bitname,hltpresc,l1presc,efflumi]
    for rline in resultlines:
        result.append(rline)
         
    for run in sorted(lumidata):#loop over runs
        rundata=lumidata[run]
        if rundata is None:
            result.append([str(run),'n/a','n/a','n/a','n/a','n/a','n/a','n/a'])
            continue
        fillnum=0
        if rundata[0][11]:
            fillnum=rundata[0][11]
        for lsdata in rundata:
            efflumiDict=lsdata[8]# this ls has no such path?
            if not efflumiDict:
                continue
            cmslsnum=lsdata[1]
            recorded=lsdata[6]
            if not recorded:
                recorded=0.0
            for hltpathname in sorted(efflumiDict):
                pathdata=efflumiDict[hltpathname]
                l1name=pathdata[0]
                if l1name is None:
                    l1name='n/a'
                else:
                    l1name=l1name.replace('"','')
                l1prescale=pathdata[1]
                hltprescale=pathdata[2]
                lumival=pathdata[3]
                if lumival is not None:
                    result.append([str(run)+':'+str(fillnum),cmslsnum,hltpathname,l1name,hltprescale,l1prescale,recorded*scalefactor,lumival*scalefactor])
                else:
                    result.append([str(run)+':'+str(fillnum),cmslsnum,hltpathname,l1name,hltprescale,l1prescale,recorded*scalefactor,'n/a'])
    # fieldnames = ['Run:Fill','LS','HLTpath','L1bit','HLTpresc','L1presc','Recorded(/ub)','Effective(/ub)']
    
    return result

class LumiDB_SQL:
    
 def __init__(self):
        self.norm            = 1.0
        self.lumiversion     = '0001'
        self.NBX             = 3564  # number beam crossings
    #self.__popconUtils = popconUtils.PopConUtils()

 def unique(self, seq):
        seen = set()
        seen_add = seen.add
        return [ x for x in seq if x not in seen and not seen_add(x)]
    
 def lslengthsec(self, numorbit, numbx = None):
        #print numorbit, numbx
        if numbx == None:
            numbx = self.NBX
        l = numorbit * numbx * 25.0e-09
        return l

 def getDeliveredLumiForRun(self, authfile="./auth.xml",runNumbers="161222,161223,161224"):

     lumis = {}
     allRuns = []

     # handle request with string for run numbers:
     if type(runNumbers) == type("") or type(runNumbers) == type(u""):
         for runNrIn in runNumbers.split(','):
             if '-' in runNrIn:
                 rStart, rEnd = runNrIn.split('-')
                 allRuns += range( int(rStart), int(rEnd)+1 ) 
             else:
                 allRuns.append( int(runNrIn) )
     # handle requests with lists of run numbers
     elif type(runNumbers) == type([]):
         allRuns = [int(x) for x in runNumbers]
     else:
         print "++> Unknown type for runNumbers found:", type(runNumbers)

     for runNr in allRuns:
         lumis[int(runNr)] = self.getDeliveredLumiForOneRun(authfile, int(runNr))

     # return the json sorted by run numbers:
     return [{'Run':key, 'DeliveredLumi': lumis[int(key)]} for key in sorted(allRuns)]

 def getDeliveredLumiForOneRun(self, authfile, runNumber):

        conn_string1='frontier://LumiCalc/CMS_LUMI_PROD'
        svc=sessionManager.sessionManager(conn_string1,
                                      authpath=authfile,
                                      siteconfpath=None,
                                      debugON=False)
        session=svc.openSession(isReadOnly=True,cpp2sqltype=[('unsigned int','NUMBER(10)'),('unsigned long long','NUMBER(20)')])
    
        # set a few defaults (taken from lumiCalc2.py)
        action  = 'overview' # 'delivered'  'overview' or 'recorded'
        fillnum = None
        begin   = None
        end     = None
        amodetag   = 'PROTPHYS'  # beamChoices=['PROTPHYS','IONPHYS','PAPHYS']
        beamenergy = 3500.
        beamfluctuation = 0.2
        pbeammode   = 'STABLE BEAMS'
        normfactor  = None
        scalefactor = 1.0
        finecorrections=None
        driftcorrections=None

        reqTrg = False
        reqHlt = False
        if action == 'recorded':
           reqTrg = True
           reqHlt = True
        
        irunlsdict={}
        iresults=[]
        if runNumber: # if runnumber specified, do not go through other run selection criteria
            irunlsdict[runNumber]=None

        finecorrections  = None
        driftcorrections = None
        correctionv3     = False
        rruns=irunlsdict.keys()
        schema=session.nominalSchema()
        session.transaction().start(True)
        if correctionv3:
            cterms=lumiCorrections.nonlinearV3()                   
        else: # default            
            cterms=lumiCorrections.nonlinearV2()
        finecorrections=lumiCorrections.correctionsForRangeV2(schema,rruns,cterms) # constant+nonlinear corrections
        driftcorrections=lumiCorrections.driftcorrectionsForRange(schema,rruns,cterms)
        session.transaction().commit()
        
        result = ""
        if action == 'delivered':
            session.transaction().start(True)
            #print irunlsdict
            result=lumiCalcAPI.deliveredLumiForRange(session.nominalSchema(),irunlsdict,amodetag=amodetag,egev=beamenergy,beamstatus=pbeammode,norm=normfactor,finecorrections=finecorrections,driftcorrections=driftcorrections,usecorrectionv2=True)
            session.transaction().commit()

            result = formatDelivered(result,iresults,scalefactor)[0][2]

        if action == 'overview':
           session.transaction().start(True)
           result=lumiCalcAPI.lumiForRange(session.nominalSchema(),irunlsdict,amodetag=amodetag,egev=beamenergy,beamstatus=pbeammode,norm=normfactor,finecorrections=finecorrections,driftcorrections=driftcorrections,usecorrectionv2=True)
           session.transaction().commit()

           # [[Run:Fill,DeliveredLS,Delivered(/ub),SelectedLS,Recorded(/ub)]]
           result = formatOverview(result,iresults,scalefactor)[0][2]

        if action == 'recorded': # recorded actually means effective because it needs to show all the hltpaths...
            hltpath = None
            session.transaction().start(True)
            hltname=hltpath
            hltpat=None
            if hltname is not None:
                if hltname=='*' or hltname=='all':
                    hltname=None
                elif 1 in [c in hltname for c in '*?[]']: #is a fnmatch pattern
                    hltpat=hltname
                    hltname=None
            result=lumiCalcAPI.effectiveLumiForRange(session.nominalSchema(),irunlsdict,hltpathname=hltname,hltpathpattern=hltpat,amodetag=amodetag,egev=beamenergy,beamstatus=pbeammode,norm=normfactor,finecorrections=finecorrections,driftcorrections=driftcorrections,usecorrectionv2=True)
            session.transaction().commit()

            # that doesn't quite work, as it's one row for each HLT path ... :(
            result = formatRecorded(result,iresults,scalefactor)[0][7]
            
        del session
        del svc 

        # print  'got:', result, 'for ', runNumber, 'which is of type', type(runNumber)

        return result

 def getRunNumberExtendedInfo(self, authfile="./auth.xml",runNumbers="161222,161223,161224"):
        conn = cx_Oracle.connect(conn_string)

        return [{'RunNumber':key, 'Run-Info': value} for key, value in runs.items()]

 def getRunNumberInfo(self, authfile="./auth.xml",runNumbers="161222,161223,161224"): 
     conn = cx_Oracle.connect(conn_string)
     jobList = []
     try:
        curs = conn.cursor()
        sqlstr = """
SELECT TO_CHAR(r.runnumber), 
TO_CHAR(r.starttime,'DD-MON-YY HH24:MI'), 
TO_CHAR(r.stoptime,'DD-MON-YY HH24:MI'), 
TO_CHAR(r.lhcfill), TO_CHAR(r.lhcenergy)
FROM CMS_WBM.runsummary r
/*WHERE r.runnumber IN ( """+runNumbers+""")*/
WHERE """+runNumbers+"""
        """
        curs.prepare(sqlstr)
        curs.execute(sqlstr)
        for row in curs:
            job = row
            jobList.append({"Run-Info":{"start":row[1],"stop":row[2],"lhcfill":row[3],"lhcenergy":row[4]},"Run":row[0]})
     except cx_Oracle.DatabaseError, e:
         print "Unexpected error:", str(e) , sys.exc_info()
         raise
     finally:
         conn.close()
         return jobList

 def getRunNumberWhereClause(self, runNumbRance="160614 , 160650-160700, 160789", column_name="r.runnumber"):
    #runNumbRance = map(lambda x: x.strip().replace("-",",") ,runNumbRance.split(","))
    #runNumbRance = ",".join([str(i) for i n range(3,8)])
    query = ""
    #NumbersExpanded = []
    for element in runNumbRance.split(","):
        elements = element.strip().split("-")
        if len(elements) == 1:
            #NumbersExpanded.append(elements[0])
            query += "or ("+ column_name +"=" +elements[0] + ")"   
        else:
            query += "or (({cn} >={x1}) and ({cn} <={x2}))".format(cn=column_name, x1=elements[0], x2=elements[1])
            #for x in xrange(int(elements[0]), int(elements[1])+1):
            #    NumbersExpanded.append(str(x))
    query = query[2:]
    return query #",".join(NumbersExpanded )

 def getRunNumberExpand(self, runNumbRance="160614 , 160650-160700, 160789"):
    #runNumbRance = map(lambda x: x.strip().replace("-",",") ,runNumbRance.split(","))
    #runNumbRance = ",".join([str(i) for i in range(3,8)])
    NumbersExpanded = []
    for element in runNumbRance.split(","):
        elements = element.strip().split("-")
        if len(elements) == 1:
            NumbersExpanded.append(elements[0])    
        else:
            for x in xrange(int(elements[0]), int(elements[1])+1):
                NumbersExpanded.append(str(x))
    return ",".join(NumbersExpanded )

 def getRunNumberString(self, runNumbList=[{'runnumbers': [u'161222', u'161223', u'161224']}]):
     return str(','.join(runNumbList[0]['runnumbers']))

 def getRunNumber(self, authfile="./auth.xml",startTime='23-Mar-11 00:00',endTime='23-Mar-11 14:00'): 
     conn = cx_Oracle.connect(conn_string)
     startTime  =   startTime+":00.000000"
     endTime    =   endTime+":00.000000"
     jobList = []
     runNumb = []
     try:
        curs = conn.cursor()
        sqlstr = """
SELECT TO_CHAR(runtable.runnumber)
FROM CMS_RUNINFO.RUNNUMBERTBL runtable, CMS_WBM.RUNSUMMARY wbmrun
WHERE (
wbmrun.starttime BETWEEN 
TO_TIMESTAMP(:startTime, 'DD-Mon-RR HH24:MI:SS.FF') AND 
TO_TIMESTAMP(:stopTime, 'DD-Mon-RR HH24:MI:SS.FF'))
AND (runtable.sequencename = 'GLOBAL-RUN-COSMIC' OR runtable.sequencename = 'GLOBAL-RUN')
AND (wbmrun.key = '/GLOBAL_CONFIGURATION_MAP/CMS/COSMICS/GLOBAL_RUN' 
OR wbmrun.key = '/GLOBAL_CONFIGURATION_MAP/CMS/CENTRAL/GLOBAL_RUN')
AND runtable.runnumber = wbmrun.runnumber
        """
        #params = {"startTime": startTime.decode(), "stopTime": endTime.decode()}
        params = {"startTime": startTime, "stopTime": endTime}
        #sqlstr=sqlstr.decode()
        curs.prepare(sqlstr)
        curs.execute(sqlstr, params)
        
        #print 'QUERY EXECUTION DONE'
        for row in curs:
            runNumb.append(row[0])
        jobList.append({'runnumbers':runNumb})
     except cx_Oracle.DatabaseError, e:
         print "Unexpected error:", str(e) , sys.exc_info()
         raise
     finally:
         conn.close()
         return runNumb # was: jobList

 def getLumiByRun(self, authfile="./auth.xml",runNumbers="161222,161223,161224"):
     return self.getDeliveredLumiForRun(authfile, runNumbers)

 def getMaxMinString(self,StringNumber="2,5,9,7"):
    maxMinString = StringNumber
    maxMinString=maxMinString.split(',')
    maxMinString.sort()
    maxMinString=maxMinString[0]+"-"+maxMinString[-1]
    return maxMinString

 def test(self, authfile="./auth.xml"): 
    conn = cx_Oracle.connect(conn_string)
    jobList = []
    try:
        curs = conn.cursor()
        sqlstr = """ 
	select rd.value
  from CMS_RUNINFO.runsession_date rd, CMS_RUNINFO.runsession_parameter rp
  where rp.name = 'CMS.LVL0:START_TIME_T' and rp.runnumber = 127981 and rd.runsession_parameter_id = rp.id
  order by rp.id
         """
        #sqlstr = sqlstr.decode()
        curs.prepare(sqlstr)
        curs.execute(sqlstr)
        
        for row in curs:
            job = row[0]
            jobList.append({'job':job})
    except Exception, e:
        print str(e) 
    finally:
        print 'QUERY not DONE'
        conn.close()
        return jobList

if __name__ == "__main__":
    LumiDB_SQL	= LumiDB_SQL()
    #print LumiDB_SQL.getRunNumber()
    #runNumbersString    =   LumiDB_SQL.getRunNumberWhereClause(runNumbRance="160001-160010")
    runNumbList         =   LumiDB_SQL.getRunNumber(startTime='22-Mar-11 00:00', endTime='23-Mar-11 10:00')
    runNumbersString    =   LumiDB_SQL.getRunNumberString(runNumbList=runNumbList)
    runNumbersString    =   LumiDB_SQL.getMaxMinString(StringNumber=runNumbersString)
    runNumbersString    =   LumiDB_SQL.getRunNumberWhereClause(runNumbRance=runNumbersString,column_name='runnum')
    #print runNumbersString
    #print LumiDB_SQL.getRunNumberExtendedInfo(runNumbers=runNumbersString)
    #runNumbList         =   LumiDB_SQL.getRunNumber(startTime='22-Mar-11 00:00', endTime='23-Mar-11 10:00')
    #runNumbersString    =   LumiDB_SQL.getRunNumberString(runNumbList=runNumbList)
    #print LumiDB_SQL.getRunNumberInfo(runNumbers=runNumbersString)
    #runNumbersString = LumiDB_SQL.getRunNumberExpand(runNumbRance="161224")
    #print LumiDB_SQL.getLumiByRun(runNumbers=runNumbersString)
    #print LumiDB_SQL.getRunNumberExtendedInfo(runNumbers=runNumbersString)
    print LumiDB_SQL.getDeliveredLumiForRun(runNumbers=runNumbersString)
