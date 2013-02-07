import dateutil.parser

class PopConUtils(object):

    def __init__(self):
        self.__weekDays = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        self.__months = ['dec', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov']
   
    def logToTimeStamps(self, logTail):
        timeStamps = []
        logList = logTail.strip().split('\n')
        timeList = [logList[i] for i in range(len(logList)) if i % 2 != 0]
        timeStamps = [dateutil.parser.parse(tStamp) for tStamp in timeList]
        return timeStamps
        
# for testing:
if __name__ == '__main__':
    short_tail="""
----- new cronjob started for BeamSpot at -----\nMon Feb 22 11:30:01 CET 2010\n----- new cronjob started for BeamSpot at -----\nMon Feb 22 11:40:04 CET 2010\n----- new cronjob started for BeamSpot at -----\nMon Feb 22 11:50:04 CET 2010\n----- new cronjob started for BeamSpot at -----\nMon Feb 22 12:00:02 CET 2010\n----- new cronjob started for BeamSpot at -----\nMon Feb 22 12:10:01 CET 2010
    """
    popConUtils = PopConUtils()
    timeStamps = popConUtils.logToTimeStamps(logString = short_tail)
    for t in timeStamps:
        print t
    
