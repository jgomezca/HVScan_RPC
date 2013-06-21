import sys
import os
import re
import time
import json
import datetime
import dateutil.tz

import popconUtils
try:
    import cx_Oracle
except ImportError, e: 
    print "Cannot import cx_Oracle:", e 

import service


conn_dict = service.secrets['connections']['pro']
conn_string = service.getCxOracleConnectionString(conn_dict)


class popconSQL:
    
 def __init__(self):
    self.__popconUtils = popconUtils.PopConUtils()
    
 def get_default_date(self, what): 
    today_sec = time.time()+86500
    today_tuple = time.gmtime(today_sec)
    today = str(today_tuple[1]) + "/" + str(today_tuple[2]) + "/" + str(today_tuple[0])

    yesterday_sec = today_sec - 86400
    yesterday_tuple = time.gmtime(yesterday_sec)
    yesterday = str(yesterday_tuple[1]) + "/" + str(yesterday_tuple[2]) + "/" + str(yesterday_tuple[0])

    three_days_ago_sec = today_sec - (86400*3)
    three_days_ago_tuple = time.gmtime(three_days_ago_sec)
    three_days_ago  = str(three_days_ago_tuple[1]) + "/" + str(three_days_ago_tuple[2]) + "/" + str(three_days_ago_tuple[0])

    one_month_ago_sec = today_sec - (86400*30)
    one_month_ago_tuple = time.gmtime(one_month_ago_sec)
    one_month_ago  = str(one_month_ago_tuple[1]) + "/" + str(one_month_ago_tuple[2]) + "/" + str(one_month_ago_tuple[0])

    if (what == 'today'):
        return today
    if(what == 'yesterday'):
        return yesterday
    if(what == 'three_days_ago'):
        return three_days_ago
    if(what == 'one_month_ago'):
        return one_month_ago

 def transform_date(self, what='31 May, 2009'):
    time_tuple = time.strptime(what, "%d %B, %Y")
    time_transformed = str(time_tuple[1])+'/'+str(time_tuple[2])+'/'+str(time_tuple[0])
    return time_transformed
 
 def PopConCronjobTailFetcherStatus(self, authfile="./auth.xml",serviceName="EcalDCSO2O"):
    conn = cx_Oracle.connect(conn_string)
    try:
    	start = time.time()
        curs = conn.cursor()
        curs.arraysize = 256
        sqlstr = """
            select 
            CMS_COND_31X_POPCONLOG.logtails.filename as filename,
	    CMS_COND_31X_POPCONLOG.logtails.short_tail as short_tail	
            from 
            CMS_COND_31X_POPCONLOG.logtails 
	    where filename like '%"""+serviceName+"""%'
        """
        curs.prepare(sqlstr)
        curs.execute(sqlstr)
	result	=	{}
        for rows_ in curs:
		serviceName		=	rows_[0].replace(".log","")
		short_tail  		=       rows_[1]
            	error_check = 1
            	if self.isTimeConsistent(logTail=short_tail):
                	error_check     =       0
		result[serviceName]	=	error_check
	return result
    finally:
        conn.close()
         
 def PopConCronjobTailFetcher(self, authfile="./auth.xml", search_string=""):
    if search_string == "" or \
       search_string == "where filename='EcalLaserExpressTimeBasedO2O.log'" or \
       search_string == "where filename='EcalDAQO2O.log'" or \
       search_string == "where filename='SiStripDetVOffTimeBasedO2O.log'" or \
       search_string == "where filename='RunInfoStart.log'" or \
       search_string == "where filename='OfflineDropBox.log'" or \
       search_string == "where filename='EcalPedestalsTimeBasedO2O.log'" or \
       search_string == "where filename='EcalDCSO2O.log'" or \
       search_string == "where filename='RunInfoStop.log'" or \
       search_string == "where filename='EcalLaserTimeBasedO2O.log'":
       conn = cx_Oracle.connect(conn_string)
       #map_detector    =   ['Pixel','Alig','Ecal','DT','Run','RPC','CSC','SiStrip','HLT']
       try:
           start = time.time()
           curs = conn.cursor()
           curs.arraysize = 256
           sqlstr = """
               select 
               CMS_COND_31X_POPCONLOG.logtails.filename as filename,
               86400000 * (cast(sys_extract_utc(CMS_COND_31X_POPCONLOG.logtails.crontime) as date) - to_date('01-01-1970','DD-MM-YYYY')) as crontime, 
               /* 86400000 * (cast(sys_extract_utc(CMS_COND_31X_POPCONLOG.logtails.prevcrontime) as date) -
               to_date('01-01-1970','DD-MM-YYYY')) as prevcrontime,*/
               CMS_COND_31X_POPCONLOG.logtails.short_tail as short_tail,
               CMS_COND_31X_POPCONLOG.logtails.long_tail as long_tail
               from 
               CMS_COND_31X_POPCONLOG.logtails
               {0}
               /*where rownum < 6 and 
               filename='/cmsnfshome0/nfshome0/popcondev/RunInfoJob/CMSSW_2_1_0/src/CondTools/RunInfo/test/L1Scaler.log'*/
               order by crontime desc 
           """.format(search_string)
             #print "\nPopConCronjobTailFetcher:\n",sqlstr,"\n"
           curs.prepare(sqlstr)
           curs.execute(sqlstr)
           name_of_columns = []
           for fieldDesc in curs.description: 
               name_of_columns.append(fieldDesc[0])
           rows = {}
           rows['name_of_columns'] = name_of_columns
           rows["aaData"] = {}
           #print "\nPopConCronjobTailFetcher:\n",int((time.time()-start)*1000),"\n"
           list   =   []
           for rows_ in curs:
               short_tail  =       rows_[2]
               one_row     =       []
               map_detector    =   rows_[0].replace(".log","")
               map_detector    =   map_detector.replace("PopCon","")

               try:
                   rows["aaData"][map_detector]
               except:
                   rows["aaData"][map_detector]=[]

               #one_row = [str(col).replace("\n","<br>") for col in rows_]
               date_seconds    =   int(str((rows_[1]))[0:-3])
               date_info   =   "<b>Crontime (ms)</b>"+str(rows_[1])+"<br><b>Crontime (hr)</b>:"+time.strftime('%d/%m/%y %H:%M:%S', time.gmtime(date_seconds))
               first_row   =   "<b>Filename:</b>"+str(rows_[0])+"<br><hr>"+date_info+"<hr><b>Short Tail:</b><br>"+rows_[2].replace("\n","<br>")   
               one_row =   [first_row,str(rows_[3]).replace("\n","<br>")]
               error_check = 1
               if self.isTimeConsistent(logTail=short_tail):
                   error_check     =       0
               one_row.append({"error": error_check})
               rows["aaData"][map_detector].append(one_row)
           return rows
       finally:
           conn.close()
    else:
        raise SystemExit

 def checkLongTail(self,authfile="./auth.xml",serviceName='OfflineDropBox'):
    conn = cx_Oracle.connect(conn_string)
    try:
    	start = time.time()
        curs = conn.cursor()
        curs.arraysize = 256
        sqlstr = """
            select 
            CMS_COND_31X_POPCONLOG.logtails.filename as filename,
	    CMS_COND_31X_POPCONLOG.logtails.short_tail as short_tail,
	    CMS_COND_31X_POPCONLOG.logtails.long_tail as long_tail
            from 
            CMS_COND_31X_POPCONLOG.logtails 
	    where filename like '%"""+serviceName+"""%'
        """
        curs.prepare(sqlstr)
        curs.execute(sqlstr)
	result	=	{}
        for rows_ in curs:
		serviceName		=	rows_[0].replace(".log","")
		long_tail  		=       str(rows_[2])
            	error_check = 1
	check_errror = long_tail.lower().find('error')
	check_warning = long_tail.lower().find('warning')
	if(check_errror > -1 ):
		return {serviceName:2} 
	elif (check_warning > -1):
		return {serviceName:1}
	else:
		return {serviceName:0}
		
	return check_errror,check_warning
    finally:
        conn.close()
    pass
        
 def isTimeConsistent(self, logTail=None, tolerance=0.5, minInterval=60*60*2):
    '''The normal gap is the maximum latency between 2 consecutive jobs
    in the latest 5. The delta time is the difference between the latest job
    and the current time. If this delta is smaller than a 50% more than
    the normal gap, we consider the time is consistent (not an error).
    If, otherwise, is higher than the normal gap but still smaller than
    the minInterval, we still consider the time is consistent. In other case,
    return an error.

    The minInterval is meant to not to raise false positives for run-based O2Os
    which could be triggered at any time (and therefore there is no relation
    between the latencies of the latest runs/jobs).

    On the other hand, the tolerance is meant to allow for a safety margin
    before marking time-based O2O as in error state. They run at 2 hour
    interval, so if the next one does not finish within 3 hours, we raise.

    Therefore the minInterval should be less than the minimum expected latency
    including the tolerance margin. The minInterval should be larger than
    the minimum of the expected latencies of all time-based jobs.

    TODO: Check the run value in the header of the short tail for
    run-based O2Os in order to avoid false positives by checking the start/stop
    time of the run (e.g. if we have several short runs followed by
    a very long run).
    '''

    tStamps = self.__popconUtils.logToTimeStamps(logTail)

    # Get the current time in UTC as an aware datetime
    utcnow = datetime.datetime.utcnow()
    utcnow = utcnow.replace(tzinfo = dateutil.tz.tzutc())

    tDelta = utcnow - tStamps[-1]
    #tNormalGap = tStamps[-1] - tStamps[-2]
    tNormalGap = max([tStamps[-1] - tStamps[-2], tStamps[-2] - tStamps[-3],tStamps[-3] - tStamps[-4]])
    if tDelta.seconds < tNormalGap.seconds * tolerance + tNormalGap.seconds:
        return True
    elif tDelta.seconds < minInterval:
        return True
    else:
        return False
        
 def popconActivityHisto(self, authfile="./auth.xml", account="CMS_COND_31X_DT", start_date="", end_date=""):
    if start_date == '':
        start_date = self.get_default_date('one_month_ago')
    else:
        start_date = self.transform_date(start_date)
        
    if end_date == '':
        end_date = self.get_default_date('today')
    else:
        end_date = self.transform_date(end_date)

    #start_date  =   "11/23/2009"
    #end_date    =   "12/16/2009"

    conn = cx_Oracle.connect(conn_string)
    try:
        start = time.time()
        curs = conn.cursor()
        curs.arraysize = 256
        """
        When you will use this methods with start_date and end_date params,
        change curs.execute(sqlstr) into curs.execute(sqlstr, (start_date,
        end_date)) and sqlstr line ('+start_date+'... into %s (same with
        end_date)
        """
        sqlstr = """
            select 
            ACCOUNT,
            /*HOUR,*/
            DAY,
            FREQUENCY 
            from 
            /*p_con_hits_hourly_new */
            """+str(conn_dict['account'])+""".p_con_hits_daily_new
            where 
            trunc(to_date(DAY, 'yyyy:mm:dd')) between to_date('"""+start_date+"""', 'MM/DD/YYYY') and to_date('"""+end_date+"""', 'MM/DD/YYYY') and
            ACCOUNT like '%"""+account+"""%' 
            /*and rownum <435*/
            order by ACCOUNT,DAY
        """
        #print conn_string
        #print "sqlstro_popconActivityHisto:",sqlstr

        curs.execute(sqlstr)

        rows = {}
        for row in curs.fetchall():
            try:
                rows[row[0]]
            except KeyError:
                rows[row[0]] = {}
            rows[row[0]].update({row[1]:row[2]})
        return rows
    finally:
        conn.close()

 def get_quotaInfo(self, authfile="./auth.xml"):
    conn = cx_Oracle.connect(conn_string)
    try:
        curs = conn.cursor()
        sqlstr = """
            select 
            to_char(CHECKTIME,'yyyy:mm:dd'),
            USED,
            LIMIT
            from  """+str(conn_dict['account'])+""".quotainfo 
            order by CHECKTIME 
        """
        print sqlstr
        curs.execute(sqlstr)
        rows                =   curs.fetchall()
        return rows
    finally:
        conn.close()

 def get_IOVTAGs(self, authfile="./auth.xml"):
    conn = cx_Oracle.connect(conn_string)
    try:
        curs = conn.cursor()
        sqlstr = """
            select distinct IOVTAG 
            from  """+str(conn_dict['account'])+""".cond_log_view 
            where trunc(sysdate, 'hh24') - trunc(exectime, 'hh24') < 180
        """
        curs.execute(sqlstr)
        rows = curs.fetchall()
        return rows
    finally:
        conn.close()

 def get_DESTINATIONDBs(self, authfile="./auth.xml"):
    conn = cx_Oracle.connect(conn_string)
    try:
        curs = conn.cursor()
        sqlstr = """
            select distinct DESTINATIONDB 
            from  """+str(conn_dict['account'])+""".cond_log_view 
            where trunc(sysdate, 'hh24') - trunc(exectime, 'hh24') < 90
        """
        curs.execute(sqlstr)
        rows = curs.fetchall()
        return rows
    finally:
        conn.close()

 def get_ACCOUNTs(self, authfile="./auth.xml"):
    conn = cx_Oracle.connect(conn_string)
    try:
        curs = conn.cursor()
        sqlstr = """
            select distinct ACCOUNT 
            from p_con_hits_daily_new   
        """
        curs.execute(sqlstr)
        rows = curs.fetchall()
        return rows
    finally:
        conn.close()

 # SQL INJECTION
 def PopConRecentActivityRecorded(self, authfile="./auth.xml", rownumbers = 100, account="", payloadcontainer="", iovtag="", start_date="", end_date=""):
    if start_date == '':
        start_date = self.get_default_date('three_days_ago')
    else:
        start_date = self.transform_date(start_date)
        
    if end_date == '':
        end_date = self.get_default_date('today')
    else:
        end_date = self.transform_date(end_date)

    #@TODO: SQLInjection
    time_constraints = """
        trunc(exectime) 
        between 
        to_date('"""+start_date+"""', 'MM/DD/YYYY') and 
        to_date('"""+end_date+"""', 'MM/DD/YYYY') 
    """
    conn = cx_Oracle.connect(conn_string)
    try:
        start = time.time()
        curs = conn.cursor()
	sqlstr = """
		SELECT
		logid,
		iovtimetype,
		to_char(exectime,'DD-MM-YY ') || to_char(exectime, 'HH24:MI:SS') as exectime,
		iovtag, 
            	payloadcontainer,
            	payloadname, 
            	destinationdb, 
            	execmessage,
        	lastsince,
    	        payloadindex,
        	provenance,
    	        usertext,
                payloadtoken
		FROM """+str(conn_dict['account'])+""".cond_log_view
		WHERE logid >= (SELECT
				MAX(logid)
				FROM """+str(conn_dict['account'])+""".cond_log_view
				)-"""+str(rownumbers-1)+"""
		and destinationdb like '%"""+account+"""%'
	       	and payloadcontainer like '%"""+payloadcontainer+"""%'
		and iovtag like '%"""+iovtag+"""%'
		ORDER BY """+str(conn_dict['account'])+""".cond_log_view.logid desc				
	"""
        #print "sqlstr:",sqlstr
        #rows = curs.execute(sqlstr, (start_date, end_date, '%' + account + '%',
        #    '%' + payloadcontainer + '%', '%' + iovtag + '%'))

        #print "sqlstr:",sqlstr
        rows = curs.execute(sqlstr)
        #rows    =   curs.fetchall()
        #print "\n"+str(int((time.time()-start)*1000))
        name_of_columns = []
        for fieldDesc in curs.description:     
            name_of_columns.append(fieldDesc[0])
        rows = {}
        data = curs.fetchall()
        i=0
        for row in data:
            row = list(row)
            conn_str = row[6]
            #make the last part of connection string upper case
            #conn_str = conn_str[:conn_str.rindex('/')] + conn_str[conn_str.rindex('/'):].upper()
            row[6] = conn_str
            data[i] = row
            i += 1
        #rows['name_of_columns']     =   name_of_columns
	false = 'false'
	true = 'true'
	rows['aaSorting'] = [[ 0, "desc" ]]
        rows['aaColumns'] = [{"sTitle": "LOG ID", "bSortable" :true},{"sTitle": "IOV TIME TYPE", "bSortable" : false },{"sTitle": "EXEC TIME", "bSortable" : true, "sType": "custdate"},{"sTitle": "IOV TAG", "bSortable" : true},{"sTitle": "Payload container", "bSortable" : true},{"sTitle": "Payload Name", "bSortable" : true},{"sTitle": "DESTINATION DB", "bSortable" : false},{"sTitle": "Exec Mess", "bSortable" : false},{"sTitle": "Last Since", "bSortable" : true},{"sTitle": "PAYLOAD INDEX", "bSortable" : false},{"sTitle": "Prov.", "bSortable" : false},{"sTitle": "USER TEXT", "bSortable" : false},{"sTitle": "PAYLOAD TOKEN", "bSortable" : false}]
        rows['aaColumns'] = [{"sTitle": "ID", "bSortable" :true},{"sTitle": "T-type", "bSortable" : false },{"sTitle": "Exec-time", "bSortable" : true, "sType": "custdate"},{"sTitle": "TAG", "bSortable" : true},{"sTitle": "Container", "bSortable" : true},{"sTitle": "Name", "bSortable" : true},{"sTitle": "Destination DB", "bSortable" : false},{"sTitle": "St.", "bSortable" : false},{"sTitle": "Last-Since", "bSortable" : true},{"sTitle": "Index", "bSortable" : false},{"sTitle": "Prov.", "bSortable" : false},{"sTitle": "USER TEXT", "bSortable" : false},{"sTitle": "PAYLOAD TOKEN", "bSortable" : false}]
        rows["aaData"] = {}
        rows["aaData"] = [map(str,rows_) for rows_ in data]
        #print "\n",int((time.time()-start)*1000)
        return rows
    finally:
        conn.close()
    
if __name__ == "__main__":
    popconSQL  = popconSQL()
    print popconSQL.PopConCronjobTailFetcherStatus("./auth.xml",serviceName="EcalDCSO2O")
    print popconSQL.checkLongTail(authfile="./auth.xml",serviceName='OfflineDropBox')
    #popconSQL.PopConCronjobTailFetcher("./auth.xml")
    #print popconSQL.popconActivityHisto()
    #print popconSQL.PopConCronjobTailFetcher2()
#   short_tail="""
#    ----- new cronjob started for BeamSpot at -----\nMon Feb 22 11:30:01 CET 2010\n----- new cronjob started for BeamSpot at -----\nMon Feb 22 11:40:04 CET 2010\n----- new cronjob started for BeamSpot at -----\nMon Feb 22 11:50:04 CET 2010\n----- new cronjob started for BeamSpot at -----\nMon Feb 22 12:00:02 CET 2010\n----- new cronjob started for BeamSpot at -----\nMon Feb 22 12:10:01 CET 2010
#        """
#    print short_tail
#    if popconSQL.isTimeConsistent(logTail=short_tail, tolerance=0.2, minInterval=0):
#        print 'Consistent'
#    else:
#        print 'Not consistent'
    #print popconSQL.get_DESTINATIONDBs("./auth.xml")
    #popconSQL.extract("auth.xml")
    #print popconSQL.PopConRecentActivityRecorded()
    #print popconSQL.get_quotaInfo()
    
