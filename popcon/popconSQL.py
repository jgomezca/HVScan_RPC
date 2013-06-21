import sys
import os
import re
import time
import json
import datetime
import dateutil.tz

import popconUtils

import service
import database

connection = database.Connection(service.secrets['connections']['pro'])


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

    rows = connection.fetch('''
        select 
            CMS_COND_31X_POPCONLOG.logtails.filename as filename,
            CMS_COND_31X_POPCONLOG.logtails.short_tail as short_tail
        from 
            CMS_COND_31X_POPCONLOG.logtails 
        where filename like :s
    ''', ('%' + serviceName + '%', ))

    result = {}
    for row in rows:
        error_check = 1
        if self.isTimeConsistent(logTail = row[1]):
            error_check = 0

        result[row[0].replace(".log", "")] = error_check

    return result
         
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

       rows = connection.fetch('''
            select 
                CMS_COND_31X_POPCONLOG.logtails.filename as filename,
                86400000 * (cast(sys_extract_utc(CMS_COND_31X_POPCONLOG.logtails.crontime) as date) - to_date('01-01-1970','DD-MM-YYYY')) as crontime, 
                CMS_COND_31X_POPCONLOG.logtails.short_tail as short_tail,
                CMS_COND_31X_POPCONLOG.logtails.long_tail as long_tail
            from 
                CMS_COND_31X_POPCONLOG.logtails
            {0}
            order by crontime desc 
       '''.format(search_string))

       ret = {}
       ret['name_of_columns'] = ['FILENAME', 'CRONTIME', 'SHORT_TAIL', 'LONG_TAIL']
       ret["aaData"] = {}
       for row in rows:
           one_row = []
           map_detector = row[0].replace(".log","").replace("PopCon","")

           try:
               ret["aaData"][map_detector]
           except:
               ret["aaData"][map_detector]=[]

           date_seconds = int(str((row[1]))[0:-3])
           date_info = "<b>Crontime (ms)</b>"+str(row[1])+"<br><b>Crontime (hr)</b>:"+time.strftime('%d/%m/%y %H:%M:%S', time.gmtime(date_seconds))
           first_row = "<b>Filename:</b>"+str(row[0])+"<br><hr>"+date_info+"<hr><b>Short Tail:</b><br>"+row[2].replace("\n","<br>")   
           one_row = [first_row,str(row[3]).replace("\n","<br>")]
           error_check = 1
           if self.isTimeConsistent(logTail = row[2]):
               error_check = 0
           one_row.append({"error": error_check})
           ret["aaData"][map_detector].append(one_row)
       return ret

    else:
        raise SystemExit

 def checkLongTail(self,authfile="./auth.xml",serviceName='OfflineDropBox'):

    rows = connection.fetch('''
        select 
            CMS_COND_31X_POPCONLOG.logtails.filename as filename,
            CMS_COND_31X_POPCONLOG.logtails.short_tail as short_tail,
            CMS_COND_31X_POPCONLOG.logtails.long_tail as long_tail
        from 
            CMS_COND_31X_POPCONLOG.logtails 
        where filename like :s
    ''', ('%' + serviceName + '%', ))

    for row in rows:
        serviceName = row[0].replace(".log","")
        long_tail = str(row[2])

    check_errror = long_tail.lower().find('error')
    check_warning = long_tail.lower().find('warning')

    if check_errror > -1:
        return { serviceName: 2 }
    elif check_warning > -1:
        return { serviceName: 1 }
    else:
        return { serviceName: 0 }

    return check_errror, check_warning

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

    """
    When you will use this methods with start_date and end_date params,
    change curs.execute(sqlstr) into curs.execute(sqlstr, (start_date,
    end_date)) and sqlstr line ('+start_date+'... into %s (same with
    end_date)
    """
    rows = connection.fetch('''
        select ACCOUNT, DAY, FREQUENCY 
        from CMS_COND_31X_POPCONLOG.p_con_hits_daily_new
        where
            trunc(to_date(DAY, 'yyyy:mm:dd')) between to_date(:s, 'MM/DD/YYYY') and to_date(:s, 'MM/DD/YYYY')
            and ACCOUNT like :s
        order by ACCOUNT,DAY
    ''', (start_date, end_date, '%' + account + '%'))

    ret = {}
    for row in rows:
        try:
            ret[row[0]]
        except KeyError:
            ret[row[0]] = {}
        ret[row[0]].update({row[1]:row[2]})
    return ret

 def PopConRecentActivityRecorded(self, authfile="./auth.xml", rownumbers = 100, account="", payloadcontainer="", iovtag="", start_date="", end_date=""):
    rows = connection.fetch('''
        select
            logid, iovtimetype, to_char(exectime,'DD-MM-YY ') || to_char(exectime, 'HH24:MI:SS') as exectime,
            iovtag, payloadcontainer, payloadname, destinationdb, execmessage,
            lastsince, payloadindex, provenance, usertext, payloadtoken
        from
            CMS_COND_31X_POPCONLOG.cond_log_view
        where
            logid >= (
                SELECT MAX(logid)
                FROM CMS_COND_31X_POPCONLOG.cond_log_view
            ) - :s
            and destinationdb like :s
            and payloadcontainer like :s
            and iovtag like :s
        order by CMS_COND_31X_POPCONLOG.cond_log_view.logid desc
    ''', (
        rownumbers - 1,
        '%' + account + '%',
        '%' + payloadcontainer + '%',
        '%' + iovtag + '%',
    ))

    ret = {}
    false = 'false'
    true = 'true'
    ret['aaSorting'] = [[ 0, "desc" ]]
    ret['aaColumns'] = [{"sTitle": "LOG ID", "bSortable" :true},{"sTitle": "IOV TIME TYPE", "bSortable" : false },{"sTitle": "EXEC TIME", "bSortable" : true, "sType": "custdate"},{"sTitle": "IOV TAG", "bSortable" : true},{"sTitle": "Payload container", "bSortable" : true},{"sTitle": "Payload Name", "bSortable" : true},{"sTitle": "DESTINATION DB", "bSortable" : false},{"sTitle": "Exec Mess", "bSortable" : false},{"sTitle": "Last Since", "bSortable" : true},{"sTitle": "PAYLOAD INDEX", "bSortable" : false},{"sTitle": "Prov.", "bSortable" : false},{"sTitle": "USER TEXT", "bSortable" : false},{"sTitle": "PAYLOAD TOKEN", "bSortable" : false}]
    ret['aaColumns'] = [{"sTitle": "ID", "bSortable" :true},{"sTitle": "T-type", "bSortable" : false },{"sTitle": "Exec-time", "bSortable" : true, "sType": "custdate"},{"sTitle": "TAG", "bSortable" : true},{"sTitle": "Container", "bSortable" : true},{"sTitle": "Name", "bSortable" : true},{"sTitle": "Destination DB", "bSortable" : false},{"sTitle": "St.", "bSortable" : false},{"sTitle": "Last-Since", "bSortable" : true},{"sTitle": "Index", "bSortable" : false},{"sTitle": "Prov.", "bSortable" : false},{"sTitle": "USER TEXT", "bSortable" : false},{"sTitle": "PAYLOAD TOKEN", "bSortable" : false}]
    ret["aaData"] = [map(str,row) for row in rows]
    return ret
    
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
    #popconSQL.extract("auth.xml")
    #print popconSQL.PopConRecentActivityRecorded()
    
