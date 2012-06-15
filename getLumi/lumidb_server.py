"""
Lumidb backend application
Author: Antonio Pierro, antonio.pierro@cern.ch, Salvatore Di Guida, Aidas Tilmantas
"""

import re
import time
import json

import cherrypy
import LumiDB_SQL

import service

class LumiDB:
    errorMessage =" Error!!! Incorect parameters! Possibilities:"\
                                  "    \n?Runs=xxx,xxx,xxx,....."\
                                  "    \n?Runs=xxx,xxx-xxx,....."\
                                  "    \n?Runs=xxx-xxx,..."\
                                  "    \n?Runs=[xxx,xxx-xxx,....]"\
                                  "    \nSame with the ?runList=....."\
                                  "    \nAvoid any whitespace!!"\
                                  "    \nxxx - ONLY NUMBERS!!!!"
    dateErrorMessage =" Error!!! Incorect date! Format is:    day-month-year-hours:minutes Example 01-Oct-10-00:00"
    
    def __init__(self):
        self.recent_activity_result = ''

    def checkParamsValidity(self, parameters):
        error = "ERROR"
        checkParamStatus = 0
        splitedParams = parameters.split(",")
        if len(splitedParams) == 1:
            p = re.compile('\[[0-9]*\]$'
                           '|[0-9]*$'
                           '|[0-9]+-[0-9]+$'
                           '|\[[0-9]+-[0-9]+\]$')
            m = p.match(splitedParams[0])
            if m:
                checkParamStatus = 1
                pass
            else:
                return error
        else:
            p = re.compile('\[[0-9]*$'
                           '|\[[0-9]+-[0-9]+$')
            p1 = re.compile('[0-9]*\]$'
                            '|[0-9]+-[0-9]+\]$')
            p2 = re.compile('[0-9]*$'
                            '|[0-9]+-[0-9]+$')
            if splitedParams[0] != "" and splitedParams[len(splitedParams)-1] != "":
                m = p.match(splitedParams[0])
                m1 = p1.match(splitedParams[len(splitedParams)-1])
                m2 = p2.match(splitedParams[0])
                m3 = p2.match(splitedParams[len(splitedParams)-1])
                if  m and m1 or m2 and m3:
                    checkParamStatus = 2
                    pass
                else:
                    return error
            else:
                return error
        p = re.compile('[0-9]*$'
                       '|[0-9]+-[0-9]+$')
        returnedValue = parameters
#Was written only one parameter value
        if checkParamStatus == 1:
            if returnedValue[0] == "[" and returnedValue[len(returnedValue)-1] == "]":
                returnedValue = returnedValue.replace('[', '')
                returnedValue = returnedValue.replace(']', '')
            if returnedValue != "":
                return returnedValue
            else:
                return error
#Was written more thn one parameter values
        elif checkParamStatus == 2:
            if returnedValue[0] == "[" and returnedValue[len(returnedValue)-1] == "]":
                returnedValue = returnedValue.replace('[', '')
                returnedValue = returnedValue.replace(']', '')
            splitedParams = returnedValue.split(',')
            for param in splitedParams:
                if param != "":
                    m = p.match(param)
                    if param == "":
                        return error
                    if  m:
                        pass
                    else:
                        return error
                else:
                    return error
            return returnedValue
    
    def checkParamsNames(self, params, function, *args):
        if len(args) != 0:
            if type(params).__name__!='list' and type(args[0]).__name__!='list':
                if params == "" and args[0] == "":
                    raise cherrypy.HTTPError(405, "Missing parameter values!!!!!")
                else:
                    return function(params, args[0])
            else:
                return function(params[0], args[0][0])
        else:
            if type(params).__name__!='list':
                if params == "":
                    raise cherrypy.HTTPError(405, "Missing parameter values!!!!!")
                else:
                    return function(params)
            else:
                return function(params[0])

    def getLumi(self, **kwargs):
        if len(kwargs) == 0:
            return self.getDeliveredLumiByRunNumbers()       
        else:
            if "Runs" in kwargs:
                if "lumiType" in kwargs:
                    if "startTime" in kwargs or "endTime" in kwargs:
                        return self.checkParamsNames(kwargs["startTime"], self.getDeliveredLumiFromDate, kwargs["endTime"])
                    return self.checkParamsNames(kwargs["Runs"], self.getDeliveredLumiByRunNumbers)
                else:
                    return self.checkParamsNames(kwargs["Runs"], self.getLumiInfoByRunNumbers)
            elif "startTime" in kwargs or "endTime" in kwargs:
                if "lumiType" in kwargs:
                    return self.checkParamsNames(kwargs["startTime"], self.getDeliveredLumiFromDate, kwargs["endTime"])
                else:
                    return self.checkParamsNames(kwargs["startTime"], self.getLumiInfoFromDate, kwargs["endTime"])
            else:
                return self.getDeliveredLumiByRunNumbers()
                
    # root method
    @cherrypy.expose
    def index(self, **kwargs):
        return self.getLumi(**kwargs)

    def getRunInfoFromDate(self,
            startTime   =   time.strftime("%d-%b-%y %H:%M", time.localtime(time.time()-86400)), 
            endTime     =   time.strftime("%d-%b-%y %H:%M", time.localtime()), *args, **kwargs
        ):
        try:
            time.strptime(startTime, "%d-%b-%y-%H:%M")
            time.strptime(endTime, "%d-%b-%y-%H:%M")
        except Exception as e:
            raise cherrypy.HTTPError(405, "[startTime " + startTime + "] "  + " [endTime " + endTime + "] " + "    " + self.dateErrorMessage)
        LDB_SQL  = LumiDB_SQL.LumiDB_SQL()
        runNumbList         =   LDB_SQL.getRunNumber(authfile="./auth.xml", startTime= startTime, endTime=endTime)
#         runNumbersString    =   LDB_SQL.getRunNumberString(runNumbList=runNumbList)
#         runNumbersString    =   LDB_SQL.getMaxMinString(StringNumber=runNumbersString)
# 	print "runNumbersString:",runNumbersString
#         runNumbersString    =   LDB_SQL.getRunNumberWhereClause(runNumbRance=runNumbersString)
        items =  LDB_SQL.getRunNumberExtendedInfo(runNumbers=runNumbList)
        return json.dumps(items)


    def getLumiInfoFromDate(self,
            startTime   =   time.strftime("%d-%b-%y %H:%M", time.localtime(time.time()-86400)), 
            endTime     =   time.strftime("%d-%b-%y %H:%M", time.localtime()), *args, **kwargs
        ):
        try:
            time.strptime(startTime, "%d-%b-%y-%H:%M")
            time.strptime(endTime, "%d-%b-%y-%H:%M")
        except Exception as e:
            raise cherrypy.HTTPError(405, "[startTime " + startTime + "] "  + " [endTime " + endTime + "] " + "    " + self.dateErrorMessage)
        LDB_SQL  = LumiDB_SQL.LumiDB_SQL()
        runNumbList         =   LDB_SQL.getRunNumber(authfile="./auth.xml", startTime= startTime, endTime=endTime)
#         runNumbersString    =   LDB_SQL.getRunNumberString(runNumbList=runNumbList)
#         runNumbersString    =   LDB_SQL.getMaxMinString(StringNumber=runNumbersString)
#         runNumbersString    =   LDB_SQL.getRunNumberWhereClause(runNumbRance=runNumbersString,column_name='runnum')
        items =  LumiDB_SQL.LumiDB_SQL().getLumiByRun(runNumbers=runNumbList)
        return json.dumps(items)
        #runNumbList         =   LumiDB_SQL.LumiDB_SQL().getRunNumber(authfile="./auth.xml", startTime= startTime, endTime=endTime)
        #runNumbersString    =   LumiDB_SQL.LumiDB_SQL().getRunNumberString(runNumbList=runNumbList)

    def getRunInfoByRunNumbers(self,
            runList="160614 , 160650-160659, 160789", *args, **kwargs
        ):
        paramsValidationStatus = self.checkParamsValidity(runList)
        if paramsValidationStatus != "ERROR":
            runList = paramsValidationStatus
        else:
            raise cherrypy.HTTPError(405, "[You typed:     " + str(runList) + "] " + "     " +  self.errorMessage)
#         runNumbersString = LumiDB_SQL.LumiDB_SQL().getRunNumberWhereClause(runNumbRance=runList)
        #items =  LumiDB_SQL.LumiDB_SQL().getRunNumberInfo(runNumbers=runNumbersString)
        items =  LumiDB_SQL.LumiDB_SQL().getRunNumberExtendedInfo(runNumbers=runList)
        return json.dumps(items)
    
    def getLumiInfoByRunNumbers(self,
            runList="161222,161223,161224", *args, **kwargs
        ):
        paramsValidationStatus = self.checkParamsValidity(runList)
        if paramsValidationStatus != "ERROR":
            runList = paramsValidationStatus
        else:
            raise cherrypy.HTTPError(405, "[You typed:     " + str(runList) + "] " + "     " +  self.errorMessage)
        items =  LumiDB_SQL.LumiDB_SQL().getLumiByRun(runNumbers=runList)
        return json.dumps(items)


    def getDeliveredLumiFromDate(self,
	    startTime   =   time.strftime("%d-%b-%y %H:%M", time.localtime(time.time()-86400*7)),
            endTime     =   time.strftime("%d-%b-%y %H:%M", time.localtime()), *args, **kwargs
        ):
        try:
            time.strptime(startTime, "%d-%b-%y-%H:%M")
            time.strptime(endTime, "%d-%b-%y-%H:%M")
        except Exception as e:
            raise cherrypy.HTTPError(405, "[startTime " + startTime + "] "  + " [endTime " + endTime + "] " + "    " + self.dateErrorMessage)
        LDB_SQL  = LumiDB_SQL.LumiDB_SQL()
        runNumbList         =   LDB_SQL.getRunNumber(authfile="./auth.xml", startTime= startTime, endTime=endTime)
#         runNumbersString    =   LDB_SQL.getRunNumberString(runNumbList=runNumbList)
#         runNumbersString    =   LDB_SQL.getMaxMinString(StringNumber=runNumbersString)
#         runNumbersString    =   LDB_SQL.getRunNumberWhereClause(runNumbRance=runNumbersString,column_name='runnum')
        items =  LumiDB_SQL.LumiDB_SQL().getDeliveredLumiForRun(runNumbers=runNumbList)
        return json.dumps(items)
        #pass

    def getDeliveredLumiByRunNumbers(self,
            runList="161222,161223,161224", *args, **kwargs
        ):
        paramsValidationStatus = self.checkParamsValidity(runList)
        if paramsValidationStatus != "ERROR":
            runList = paramsValidationStatus
        else:
            raise cherrypy.HTTPError(405, "[You typed:     " + str(runList) + "] " + "     " +  self.errorMessage)
#         runNumbersString = LumiDB_SQL.LumiDB_SQL().getRunNumberWhereClause(runNumbRance=runList,column_name='runnum')
        items =  LumiDB_SQL.LumiDB_SQL().getDeliveredLumiForRun(runNumbers=runList)
        return json.dumps(items)
    
    def getLumiDB(self, *args, **kwargs):
        CTF = LumiDB_SQL.LumiDB_SQL().test()
        items = {'items' : [CTF]}
        #items = {'run' : 'x'}
        return json.dumps(items)


def main():
	service.start(LumiDB())


if __name__ == '__main__':
	main()

