import cStringIO
import json
import os
import sys
import time

import pycurl

class Tier0Error(Exception):
    '''Tier0 exception.
    '''

    def __init__(self, message):
        self.args = (message, )


def unique(seq, keepstr=True):
    t = type(seq)
    if t in (unicode, str):
        t = (list, t('').join)[bool(keepstr)]
    try:
        remaining = set(seq)
        seen = set()
        return t(c for c in seq if (c in remaining and not remaining.remove(c)))
    except TypeError: # hashing didn't work, see if seq is sortable
        try:
            from itertools import groupby
            s = sorted(enumerate(seq),key=lambda (i,v):(v,i))
            return t(g.next() for k,g in groupby(s, lambda (i,v): v))
        except:  # not sortable, use brute force
            seen = []
            return t(c for c in seq if not (c in seen or seen.append(c)))

class ResponseError( Tier0Error ):

    def __init__( self, curl, response, proxy ):
        super( ResponseError, self ).__init__( response )
        self.args += ( curl, proxy )

    def __str__( self ):
        errStr = """Wrong response for curl connection to Tier0DataSvc from URL \"%s\"""" %( self.args[1].getinfo( self.args[1].EFFECTIVE_URL ), )
        if self.args[ -1 ]:
            errStr += """ using proxy \"%s\"""" %( str( self.args[ -1 ] ), )
        errStr += """ with timeout \"%d\" with error code \"%d\".""" %( _timeOut, self.args[1].getinfo( self.args[1].RESPONSE_CODE) )
        if self.args[0].find( '<p>' ) != -1:
            errStr += """\nFull response: \"%s\".""" %( self.args[0].partition('<p>')[-1].rpartition('</p>')[0], )
        else:
            errStr += """\nFull response: \"%s\".""" %( self.args[0], )
        return errStr
#TODO: Add exceptions for each category of HTTP error codes

#TODO: check response code and raise corresponding exceptions
def _raise_http_error( curl, response, proxy ):
    raise ResponseError( curl, response, proxy )

class Tier0Handler( object ):

    def __init__( self, uri, timeOut, retries, retryPeriod, proxy, debug ):
        """
        Parameters:
        uri: Tier0DataSvc URI;
        timeOut: time out for Tier0DataSvc HTTPS calls;
        retries: maximum retries for Tier0DataSvc HTTPS calls;
        retryPeriod: sleep time between two Tier0DataSvc HTTPS calls;
        proxy: HTTP proxy for accessing Tier0DataSvc HTTPS calls;
        debug: if set to True, enables debug information.
        """
        self._uri = uri
        self._timeOut = timeOut
        self._retries = retries
        self._retryPeriod = retryPeriod
        self._proxy = proxy
        self._debug = debug

    def setDebug( self ):
        self._debug = True

    def unsetDebug( self ):
        self._debug = False

    def setProxy( self, proxy ):
        self._proxy = proxy

    def _queryTier0DataSvc( self, url ):
        """
        Queries Tier0DataSvc.
        url: Tier0DataSvc URL.
        @returns: dictionary, from whence the required information must be retrieved according to the API call.
        Raises if connection error, bad response, or timeout after retries occur.
        """
        cHandle = pycurl.Curl()
        cHandle.setopt( cHandle.SSL_VERIFYPEER, 0 )
        cHandle.setopt( cHandle.SSL_VERIFYHOST, 0 )
        cHandle.setopt( cHandle.URL, url )
        cHandle.setopt( cHandle.HTTPHEADER, [ "User-Agent: ConditionWebServices/1.0 python/%d.%d.%d PycURL/%s" %
                                              ( sys.version_info[ :3 ] + ( pycurl.version_info()[ 1 ], ) )
                                            , "Accept: application/json" ] )
        cHandle.setopt( cHandle.TIMEOUT, self._timeOut )
        if self._proxy:
            cHandle.setopt( cHandle.PROXY, self._proxy )
        if self._debug:
            cHandle.setopt( cHandle.VERBOSE, 1 )
        retry = 0
        while retry < self._retries:
            try:
                jsonCall = cStringIO.StringIO()
                cHandle.setopt( cHandle.WRITEFUNCTION, jsonCall.write )
                cHandle.perform()
                if cHandle.getinfo( cHandle.RESPONSE_CODE ) != 200:
                    _raise_http_error( cHandle, jsonCall.getvalue(), self._proxy )
                data = json.loads( jsonCall.getvalue() )
                return data
            except pycurl.error as pyCURLerror:
                errorCode, errorMessage = pyCURLerror
                if self._debug:
                    errStr = """Unable to establish connection to Tier0DataSvc from URL \"%s\"""" %( url, )
                    if self._proxy:
                        errStr += """ using proxy \"%s\"""" %( str( self._proxy ), )
                    errStr += """ with timeout \"%d\".\nThe reason is: \"%s\" (error code \"%d\").""" %( self._timeOut, errorMessage, errorCode )
                    print "pycurl.error:", errStr
                retry += 1
                if retry < self._retries: # no sleep in last iteration
                    time.sleep( self._retryPeriod )
            except ResponseError as r:
                if self._debug:
                    print "ResponseError:", r
                retry += 1
                if retry < self._retries: # no sleep in last iteration
                    time.sleep( self._retryPeriod )
            finally:
                jsonCall.close()
        errStr = """Unable to get Tier0DataSvc data from URL \"%s\"""" %( url, )
        if self._proxy:
            errStr += """ using proxy \"%s\"""" %( str( self._proxy ), )
        errStr += """ with timeout \"%d\" since maximum number of retries \"%d\" with retry period \"%d\" was reached.""" % ( self._timeOut, self._retries, self._retryPeriod )
        raise Tier0Error( errStr )

    def getFirstSafeRun( self, firstConditionSafeRunAPI ):
        """
        Queries Tier0DataSvc to get the first condition safe run.
        Parameters:
        firstConditionSafeRunAPI: the Tier0DataSvc API call for retrieving the first condition safe run.
        @returns: integer, the run number.
        Raises if connection error, bad response, timeout after retries occur, or if the run number is not available.
        """
        safeRun = self._queryTier0DataSvc( os.path.join( self._uri, firstConditionSafeRunAPI ) )[ 0 ][ 'run_id' ]
        if safeRun is None:
            errStr = """First condition safe run is not available in Tier0DataSvc from URL \"%s\"""" %( os.path.join( self._uri, firstConditionSafeRunAPI ), )
            if self._proxy:
                errStr += """ using proxy \"%s\".""" %( str( self._proxy ), )
            raise Tier0Error( errStr )
        return safeRun

    def getGlobalTag( self, config ):
        """
        Queries Tier0DataSvc to get the most recent Global Tag for a given workflow.
        Parameters:
        config: Tier0DataSvc API call for the workflow to be looked for;
        @returns: a string with the Global Tag name.
        Raises if connection error, bad response, timeout after retries occur, or if no Global Tags are available.
        """
        data = self._queryTier0DataSvc( os.path.join( self._uri, config ) )
        gtnames = unique( [ str( di[ 'global_tag' ] ).replace( "::All", "" ) for di in data if di[ 'global_tag' ] is not None ] )
        gtnames.sort()
        try:
            recentGT = gtnames[-1]
            return recentGT
        except IndexError:
            errStr = """No Global Tags for \"%s\" are available in Tier0DataSvc from URL \"%s\"""" %( config, os.path.join( self._uri, config ) )
            if self._proxy:
                errStr += """ using proxy \"%s\".""" %( str( self._proxy ), )
        raise Tier0Error( errStr )
