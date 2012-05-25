import sys
import os
import re
import time
import json
import datetime

#import popconUtils
try:
    import cx_Oracle
except ImportError, e: 
    print "Cannot import cx_Oracle:", e 

import service

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
    
 def extract(self, authfile="./auth.xml"):
    return service.getSecrets()['connections']['pro']

 def lslengthsec(self, numorbit, numbx = None):
        #print numorbit, numbx
        if numbx == None:
            numbx = self.NBX
        l = numorbit * numbx * 25.0e-09
        return l

 def getDeliveredLumiForRun(self, authfile="./auth.xml",runNumbers="161222,161223,161224"):
        conn_dict = self.extract(authfile)
        conn_string = conn_dict['user'] + '/' + conn_dict['password'] + '@' + conn_dict['db_name']
        conn = cx_Oracle.connect(str(conn_string))
        runs = {}
        lumis = {}
        try:
            curs = conn.cursor()
            sqlstr = """SELECT runnum, beamstatus, instlumi, numorbit
            FROM CMS_LUMI_PROD.LUMISUMMARY
            WHERE """+runNumbers+"""
            and lumiversion = '"""+self.lumiversion+"""'"""
            #print sqlstr
            #sqlstr=sqlstr.decode()
            #print sqlstr
            curs.prepare(sqlstr)
            #params = {"runNumbers": runNumbers.decode()}
            curs.execute(sqlstr)
            #ddprint 'QUERY EXECUTION DONE'
            #print curs.fetchall()
            for row in curs:
                runs_lumi = runs.get(row[0], [])
                runs_lumi.append( {"BeamStatus":row[1],"InstantaneousLumi":row[2],"NumberOfOrbit":row[3]} )
                runs[row[0]] = runs_lumi
            
            for run in runs:
                delLumi = lumis.get(run , 0.0)
                for lumi in runs[run]:
                    lstime = self.lslengthsec(lumi["NumberOfOrbit"])
                    delLumi = delLumi + lumi["InstantaneousLumi"]*self.norm*lstime
                lumis[run] = delLumi
        except cx_Oracle.DatabaseError, e:
            print "Unexpected error:", str(e) , sys.exc_info()
            raise
        except Exception, e:
            print "Unexpected error:", str(e) , sys.exc_info()
        finally:
            conn.close()
            return [{'Run':key, 'DeliveredLumi': value} for key, value in lumis.items()]

 def getRunNumberExtendedInfo(self, authfile="./auth.xml",runNumbers="161222,161223,161224"):
        conn_dict = self.extract(authfile)
        conn_string = conn_dict['user'] + '/' + conn_dict['password'] + '@' + conn_dict['db_name']
        conn = cx_Oracle.connect(str(conn_string))
        try:
            curs = conn.cursor()
            sqlstr = """
            WITH 
            runsummary AS (
            SELECT rp.name, rp.runnumber,
            CASE
            WHEN rp.name = 'CMS.LVL0:START_TIME_T'
            THEN (SELECT TO_CHAR(value, 'DD-MON-YY HH24:MI:SS.FF6 TZR') FROM CMS_RUNINFO.runsession_date WHERE runsession_parameter_id = rp.id)
            ELSE NULL
            END AS start_time,
            CASE
            WHEN rp.name = 'CMS.LVL0:STOP_TIME_T'
            THEN (SELECT TO_CHAR(value, 'DD-MON-YY HH24:MI:SS.FF6 TZR') FROM CMS_RUNINFO.runsession_date WHERE runsession_parameter_id = rp.id)
            ELSE NULL
            END AS stop_time,
            CASE
            WHEN rp.name = 'CMS.SCAL:FILLN'
            THEN (SELECT TO_CHAR(value) FROM CMS_RUNINFO.runsession_string WHERE runsession_parameter_id = rp.id)
            ELSE NULL
            END AS fill,
            CASE
            WHEN rp.name = 'CMS.SCAL:EGEV'
            THEN (SELECT TO_CHAR(value) FROM CMS_RUNINFO.runsession_string WHERE runsession_parameter_id = rp.id)
            ELSE NULL
            END AS energy
            FROM CMS_RUNINFO.runsession_parameter rp
            WHERE (rp.name = 'CMS.SCAL:FILLN'
            OR rp.name = 'CMS.SCAL:EGEV'
            OR rp.name like 'CMS.LVL0:%_TIME_T')
            )
            SELECT r.name, r.runnumber, r.start_time, r.stop_time, r.fill, r.energy
            FROM runsummary r
            /*WHERE r.runnumber IN("""+runNumbers+""")*/
            WHERE """+runNumbers+"""
            ORDER BY r.runnumber
            """
            #print sqlstr
            #sqlstr=sqlstr.decode()
            curs.prepare(sqlstr)
            curs.execute(sqlstr)
            #print curs.fetchall()
            runs = {}
            for row in curs:
                runs_values = runs.get(row[1], {})
                fills = runs_values.get("lhcfill", [])
                energies = runs_values.get("energy", [])
                if row[0] == 'CMS.LVL0:START_TIME_T':
                    runs_values["start"] = row[2]
                if row[0] == 'CMS.LVL0:STOP_TIME_T':
                    runs_values["stop"] = row[3]
                if row[0] == 'CMS.SCAL:FILLN':
                    fills.append(row[4])
                if row[0] == 'CMS.SCAL:EGEV':
                    energies.append(row[5])
                runs_values.update(lhcfill=fills)
                runs_values.update(energy=energies)
                runs[row[1]] = runs_values
            for run in runs:
                runs[run].update(lhcfill=self.unique(runs[run]['lhcfill']))
                runs[run].update(energy=self.unique(runs[run]['energy']))
        except cx_Oracle.DatabaseError, e:
            print "Unexpected error:", str(e) , sys.exc_info()
            raise
        except Exception, e:
            print "Unexpected error:", str(e) , sys.exc_info()
            raise
        finally:
            conn.close()
            return [{'RunNumber':key, 'Run-Info': value} for key, value in runs.items()]

 def getRunNumberInfo(self, authfile="./auth.xml",runNumbers="161222,161223,161224"): 
     conn_dict = self.extract(authfile)
     conn_string = conn_dict['user'] + '/' + conn_dict['password'] + '@' + conn_dict['db_name']
     conn = cx_Oracle.connect(str(conn_string))
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
     conn_dict = self.extract(authfile)
     conn_string = conn_dict['user'] + '/' + conn_dict['password'] + '@' + conn_dict['db_name']
     conn = cx_Oracle.connect(str(conn_string))
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
         return jobList

 def getLumiByRun(self, authfile="./auth.xml",runNumbers="161222,161223,161224"):
        conn_dict = self.extract(authfile)
        conn_string = conn_dict['user'] + '/' + conn_dict['password'] + '@' + conn_dict['db_name']
        conn = cx_Oracle.connect(str(conn_string))
        jobList =   []        
        try:
            curs = conn.cursor()
            sqlstr = """
            SELECT runnum , cmslsnum, flag, \"COMMENT\"
            FROM CMS_LUMI_PROD.LUMIVALIDATION
            WHERE """+runNumbers+"""
            ORDER BY runnum
            """
            print sqlstr
            curs.prepare(sqlstr)
            curs.execute(sqlstr)
            #print curs.fetchall()
            runs={}
            for row in curs:
                runs_lumi = runs.get(row[0], [])
                runs_lumi.append( {"lumisection":row[1],"flag":row[2],"comment":row[3]} )
                runs[row[0]] = runs_lumi
                jobList.append({"LumiByRun":{"lumisection":row[1],"flag":row[2],"comment":row[3]},"Run":row[0]}) #check 
        except cx_Oracle.DatabaseError, e:
            print "Unexpected error:", str(e) , sys.exc_info()
            raise
        except Exception, e:
            print "Unexpected error:", str(e) , sys.exc_info()
        finally:
            conn.close()
            #return jobList
            return [{'Run':key, 'Lumi': value} for key, value in runs.items()]

 def getMaxMinString(self,StringNumber="2,5,9,7"):
    maxMinString = StringNumber
    maxMinString=maxMinString.split(',')
    maxMinString.sort()
    maxMinString=maxMinString[0]+"-"+maxMinString[-1]
    return maxMinString

 def test(self, authfile="./auth.xml"): 
    conn_dict = self.extract(authfile)
    conn_string = conn_dict['user'] + '/' + conn_dict['password'] + '@' + conn_dict['db_name']
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
