"""
Lumidb backend application
Author: Antonio Pierro, antonio.pierro@cern.ch, Salvatore Di Guida, Aidas Tilmantas, Andreas Pfeiffer
"""

import re
import time

import logging

import cherrypy
import LumiDBNew_SQL as LumiDB_SQL

import service

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

    # root method
    @cherrypy.expose
    def index(self, **kwargs) :
        if 'help' in kwargs :
            return self.showHelp( )

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

            endTime = None
            if "endTime" in kwargs:
                if self.checkTime( kwargs['endTime'] ): endTime = kwargs['endTime']
                else: raise cherrypy.HTTPError( 405, "getLumi> Illegal end time given: %s " % (endTime,) )

            if not (runList or startTime or endTime) : # nothing given, use last 24 h
                startTime = time.strftime( "%d-%b-%y-%H:%M", time.localtime( time.time( ) - 86400 * 1 ) )
                endTime = time.strftime( "%d-%b-%y-%H:%M", time.localtime( ) )

            if startTime and not endTime: # use end time of "now"
                endTime = time.strftime( "%d-%b-%y-%H:%M", time.localtime( ) )

            if startTime:
                return self.getLumiByRunNumbers( self.getRunList(startTime, endTime), lumiType )
            elif runList:
                return self.getLumiByRunNumbers( runList, lumiType )
            else:
                raise cherrypy.HTTPError( 405, "This should never have happened ... :( " )

    def getRunList(self, startTime, endTime):

        if not self.checkTime(startTime):
            raise cherrypy.HTTPError( 405, "getRunList> Illegal start time given: %s " % (startTime,) )

        if not self.checkTime( endTime ) :
            raise cherrypy.HTTPError( 405, "getRunList> Illegal end time given: %s " % (endTime,) )

        LDB_SQL  = LumiDB_SQL.LumiDB_SQL()
        runNumbers =   LDB_SQL.getRunNumbers(startTime= startTime, endTime=endTime)
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

        runListOK = self.checkRunList( runList )
        if not  runListOK:
            logging.error('Checking runlist failed. ')
            return

        logging.info('Got request to show %s lumi for runs %s' % (lumiType, ','.join([str(x) for x in runListOK])) )

        if lumiType == 'delivered':
            return LumiDB_SQL.NewLumiDB().getDeliveredLumiSummaryByRun(runNumbers=runListOK)
        else:
            # return LumiDB_SQL.NewLumiDB( ).getRecordedLumiSummaryByRun( runNumbers=runListOK )
            raise cherrypy.HTTPError(405, 'recorded lumis not (yet?) supported ... ')

def main():
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )
    service.start(LumiDB())


if __name__ == '__main__':
    main()

