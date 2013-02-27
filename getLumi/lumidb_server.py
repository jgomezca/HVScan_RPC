"""
Lumidb backend application
Author: Antonio Pierro, antonio.pierro@cern.ch, Salvatore Di Guida, Aidas Tilmantas, Andreas Pfeiffer
"""

import os
import re
import time
import subprocess
import csv
import logging
import cStringIO

import cherrypy
import cx_Oracle
import coral

import service
import cache


cachedCSVFilesExpirationTime = 60 * 60 * 4 # 4 hours


@cache.csvFiles.cacheCall(None, cachedCSVFilesExpirationTime)
def getCSVFileForRun(run):
    localLumiFile = "/data/files/getLumi/lc2-%i.csv" % (run,)

    cmd = "export PYTHONPATH=/data/utilities/lib/python2.6/site-packages/:$PYTHONPATH;"
    cmd += "cd /afs/cern.ch/cms/slc5_amd64_gcc472/cms/cmssw/CMSSW_6_2_0_pre1/src/ ; eval `scram run -sh` ; "
    cmd += "lumiCalc2.py -r %i -o %s overview ;" % (run, localLumiFile)
    logging.debug('using cmd '+cmd)
    result = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]

    if "[INFO] No qualified run found, do nothing" in ''.join(result):
        logging.info("lumiCalc2 found no data for run %i " % (run,) )
        return ''

    elif not os.path.exists(localLumiFile):
        logging.error("no CSV file from lumicalc for run %i " % (run,) )
        return ''

    else:
        with open(localLumiFile,'r') as lumiFile:
            return lumiFile.read()


class LumiDB:
    errorMessage =" Error!!! Incorrect parameters! Possible arguments are:"\
                                  "    \n?Runs=xxx,xxx,xxx,....."\
                                  "    \n?Runs=xxx,xxx-xxx,....."\
                                  "    \n?Runs=xxx-xxx,..."\
                                  "    \n?Runs=[xxx,xxx-xxx,....]"\
                                  "    \nSame with the ?runList=....."\
                                  "    \nAvoid any whitespace!!"\
                                  "    \nxxx - ONLY NUMBERS!!!!"
    dateErrorMessage =" Error!!! Incorrect date! Required format is:  day-month-year-hours:minutes Example 01-Oct-10-00:00"

    def __init__(self):
        self.recent_activity_result = ''

        self.timeRe = re.compile('^\d{2}-[A-Za-z]{3}-\d{2}-\d{2}:\d{2}$')

    @cherrypy.expose
    def help(self):
        return self.showHelp()

    @cherrypy.expose
    def up(self):
        return service.setResponseJSON( [] )

    # root method
    @cherrypy.expose
    def index(self, **kwargs) :
        if 'help' in kwargs :
            return self.showHelp( )
        if 'up' in kwargs :
            return self.up( )

        return service.setResponseJSON( self.getLumi( **kwargs ) )

    def showHelp(self) :

        # url = 'https://cms-conddb-dev.cern.ch'
        url = ''

        # We could use relative links as well, to avoid relying on
        # the service name; however, the links would be more confusing
        # to the users (e.g. "./?Runs..."), and therefore it was left as it is.

        helpMsg = """
        <p>
        <h3>Help for getting the right syntax:</h3>
        This web service is querying the <b>Lumi Service</b>,
        so it will find only runs in time interval which have a luminosity different from zero.
        </p>
        <ul class='main'>
        <li><a href="@URL@/getLumi/help">@URL@/getLumi/help</a> This help message.
        <li><a href="@URL@/getLumi/">@URL@/getLumi/</a> LumiInfo for the last 24 hours
        <li><a href="@URL@/getLumi/?startTime=16-Mar-11-14:00&endTime=18-Mar-11-14:00">@URL@/getLumi/?startTime=16-Mar-11-14:00&endTime=18-Mar-11-14:00</a> LumiInfo between start date and end date (end date is optional, corresponds to "now" if not given)
        <li><a href="@URL@/getLumi/?Runs=161297-161320,161331">@URL@/getLumi/?Runs=161297-161320,161331</a> or:
        <li><a href="@URL@/getLumi/?Runs=[161297-161320,161331]">@URL@/getLumi/?Runs=[61297-161320,161331]</a> LumiInfo for the given runs
        </ul>
""".replace('@URL@', url)

        ## <p>
        ## Optionally, if you specify "&lumiType=recorded" as an additional parameter you will get the recorded instead of the delivered lumi. Examples:
        ## </p>
        ## <ul>
        ## <li><a href="@URL@/getLumi/?Runs=160915&lumiType=recorded">@URL@/getLumi/?Runs=160915&lumiType=recorded</a>
        ## <li><a href="@URL@/getLumi/?startTime=12-Mar-11-14:00&endTime=18-Mar-11-14:00&&lumiType=recorded">@URL@/getLumi/?startTime=12-Mar-11-14:00&endTime=18-Mar-11-14:00&&lumiType=recorded</a>
        ## </ul>
        ##

        return helpMsg

    def getLumi(self, **kwargs):
        if len(kwargs) == 0:
            # return self.getLumiByRunNumbers( runList="160915,161224,167098",lumiType='delivered')
            # return info for last 24 hours
            startTime = time.strftime( "%d-%b-%y-%H:%M", time.localtime( time.time( ) - 86400 * 1 ) )
            endTime = time.strftime( "%d-%b-%y-%H:%M", time.localtime( ) )
            logging.debug("no kwargs given, checking runs in last 24 hours")
            return self.getLumiByRunNumbers( runList=self.getRunList(startTime, endTime),lumiType='delivered')
        else:
            lumiType = "delivered" # set the default
            if "lumiType" in kwargs and kwargs['lumiType'].lower() == 'recorded': lumiType = 'recorded'

            runList = []
            if "Runs"    in kwargs: runList = self.checkRunList( kwargs['Runs'] )

            startTime = None
            if "startTime" in kwargs:
                if self.checkTime( kwargs['startTime'] ): startTime = kwargs['startTime']
                else: raise cherrypy.HTTPError( 405, "getLumi> Illegal start time given: %s " % (kwargs['startTime'],) )
                logging.debug("found startTime: "+startTime)
            endTime = None
            if "endTime" in kwargs:
                if self.checkTime( kwargs['endTime'] ): endTime = kwargs['endTime']
                else: raise cherrypy.HTTPError( 405, "getLumi> Illegal end time given: %s " % (endTime,) )
                logging.debug("found endTime  : "+endTime)

            if not (runList or startTime or endTime) : # nothing given, use last 24 h
                startTime = time.strftime( "%d-%b-%y-%H:%M", time.localtime( time.time( ) - 86400 * 1 ) )
                endTime = time.strftime( "%d-%b-%y-%H:%M", time.localtime( ) )
                logging.debug("no args given, checking runs in last 24 hours")

            if startTime and not endTime: # use end time of "now"
                endTime = time.strftime( "%d-%b-%y-%H:%M", time.localtime( ) )
                logging.debug("startTime but no endTime given, endTime set to: "+endTime)

            if startTime:
                runs = self.getRunList(startTime, endTime)
                logging.debug('found %i runs from %s to %s : [%s]' % (len(runs), startTime, endTime, ','.join([str(x) for x in runs])))
                return self.getLumiByRunNumbers( runs, lumiType )
            elif runList:
                return self.getLumiByRunNumbers( runList, lumiType )
            else:
                raise cherrypy.HTTPError( 405, "This should never have happened ... :( " )

    def getRunList(self, startTime, endTime):

        if not self.checkTime(startTime):
            raise cherrypy.HTTPError( 405, "getRunList> Illegal start time given: %s " % (startTime,) )

        if not self.checkTime( endTime ) :
            raise cherrypy.HTTPError( 405, "getRunList> Illegal end time given: %s " % (endTime,) )

        runNumbers =   self.getRunNumbers(startTime= startTime, endTime=endTime)
        return runNumbers

    def checkTime(self, timeIn):

        if not timeIn:
            logging.info('checkTime> got None as input ...  ' )
            return True # allow None ...

        logging.info('checkTime> going to check %s ' % (timeIn,) )

        try:
            time.strptime(timeIn, "%d-%b-%y-%H:%M")
        except:
            logging.error('checkTime> found illegal time: %s ' % (timeIn,) )
            return False

        return True

    def checkRunList(self, runNumbers):

        allRuns = [ ]
        # handle request with string for run numbers:
        if type( runNumbers ) == type( "" ) or type( runNumbers ) == type( u"" ) :
            for runNrIn in runNumbers.replace('[','').replace(']','').split( ',' ) :
                if '-' in runNrIn :
                    rStart, rEnd = runNrIn.split( '-' )
                    try:
                        allRuns += range( int( rStart ), int( rEnd ) + 1 )
                    except Exception, e:
                        logging.error("  ...   got : %s " % str(e))
                        logging.error("illegal run number found for %s or %s -- ignoring" % (str(rStart), str(rEnd)) )
                else :
                    try:
                        allRuns.append( int( runNrIn ) )
                    except Exception, e:
                        logging.error("  ...   got : %s" % str(e))
                        logging.error("illegal run number found for %s -- ignoring" % (str(runNrIn),) )
        # handle requests with lists of run numbers
        elif type( runNumbers ) == type( [ ] ) :
            try:
                allRuns = [ int( x ) for x in runNumbers ]
            except Exception, e:
                logging.error("  ...   got : %s" % str(e))
                logging.error("illegal run number found for %s -- ignoring" % (str(x),) )

        else :
            raise cherrypy.HTTPError(405, "Unknown type for runNumbers found %s " % (type(runNumbers ),) )

        return allRuns

    def getLumiByRunNumbers(self, runList, lumiType) :

        lumisummaryOut = []
        for run in runList:
            csvFile = getCSVFileForRun(run)
            if csvFile == '':
                # No information for this run, continue
                continue

            # There is information for this run, read the CSV
            lumiResRdr = csv.reader(cStringIO.StringIO(csvFile))
            lumiResRdr.next()  # first line contains headers, ignore
            runFill, delLS, delUb, selLS, recUb = lumiResRdr.next()  # Run:Fill,DeliveredLS,Delivered(/ub),SelectedLS,Recorded(/ub)

            runNr, fillNr = [int(x) for x in runFill.split(':')]
            if lumiType == 'delivered':
                lumisummaryOut.append( { "Run" : runNr, lumiType.capitalize()+"Lumi" : float(delUb) } )
            elif lumiType == 'recorded':
                lumisummaryOut.append( { "Run" : runNr, lumiType.capitalize()+"Lumi" : float(recUb) } )

        return lumisummaryOut

    def normalizeRunNumbers(self, runNumbers):

        allRuns = [ ]

        # handle request with string for run numbers:
        if type( runNumbers ) == type( "" ) or type( runNumbers ) == type( u"" ) :
            for runNrIn in runNumbers.split( ',' ) :
                if '-' in runNrIn :
                    rStart, rEnd = runNrIn.split( '-' )
                    allRuns += range( int( rStart ), int( rEnd ) + 1 )
                else :
                    allRuns.append( int( runNrIn ) )
        # handle requests with lists of run numbers
        elif type( runNumbers ) == type( [ ] ) :
            allRuns = [ int( x ) for x in runNumbers ]
        else :
            logging.warning("++> Unknown type for runNumbers found: " + str(type(runNumbers)) )

        return sorted(allRuns)

    def getRunNumbers(self, startTime, endTime):

        authfile="./auth.xml"

        conn_string = service.getCxOracleConnectionString(service.secrets['connections']['pro'])

        conn = cx_Oracle.connect( conn_string )
        startTime = startTime + ":00.000000"
        endTime = endTime + ":00.000000"
        jobList = [ ]
        runNumb = [ ]

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
        try :
            curs = conn.cursor( )
            params = {"startTime" : startTime, "stopTime" : endTime}
            curs.prepare( sqlstr )
            curs.execute( sqlstr, params )

            for row in curs :
                runNumb.append( row[ 0 ] )
            jobList.append( {'runnumbers' : runNumb} )
        except cx_Oracle.DatabaseError, e :
            msg = "getRunNumber> Error from DB : " + str( e )
            logging.error( msg )
            logging.error( "query was: '" + sqlstr + "'" )
            # print "Unexpected error:", str( e ), sys.exc_info( )
            raise
        finally :
            conn.close( )

        return self.normalizeRunNumbers(runNumb)


def main():
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )
    service.start(LumiDB())


if __name__ == '__main__':
    main()

