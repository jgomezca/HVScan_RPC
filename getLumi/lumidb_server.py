"""
Lumidb backend application
Author: Antonio Pierro, antonio.pierro@cern.ch, Salvatore Di Guida, Aidas Tilmantas, Andreas Pfeiffer
"""


import datetime
import logging

import dateutil.parser
import cherrypy

import service

import lumi


# FIXME: If this is not enough, we will need to query before hand
#        the list of runs to the database to know actually how many
#        contain data.
maxRuns = 3000
maxDays = 30


def merge(ranges):
    '''Merges ranges, including contiguous ones.
    '''

    if len(ranges) == 0:
        return []

    result = []

    sortedRanges = sorted([sorted(x) for x in ranges])
    begin, end = sortedRanges[0]
    for nextBegin, nextEnd in sortedRanges:
        if nextBegin - 1 <= end:
            end = max(end, nextEnd)
        else:
            result.append((begin, end))
            begin, end = nextBegin, nextEnd
    result.append((begin, end))

    return result


class LumiDB(object):

    @cherrypy.expose
    def help(self):
        # We could use relative links as well, to avoid relying on
        # the service name; however, the links would be more confusing
        # to the users (e.g. "./?Runs..."), and therefore it was left as it is.

        return '''
            <!DOCTYPE html>
            <html>
                <head>
                    <title>CMS ConditionDB GetLumi Help</title>
                </head>
                <body>
                    <h3>Help for getting the right syntax:</h3>
                    <p>This web service is querying the <b>Lumi Service</b>, so it will find only runs in time interval which have a luminosity different from zero.</p>
                    <ul>
                        <li><a href="/getLumi/help">/getLumi/help</a> This help message.</li>
                        <li><a href="/getLumi/">/getLumi/</a> LumiInfo for the last 24 hours</li>
                        <li><a href="/getLumi/?startTime=16-Mar-11-14:00&endTime=18-Mar-11-14:00">/getLumi/?startTime=16-Mar-11-14:00&endTime=18-Mar-11-14:00</a> LumiInfo between start date and end date (end date is optional, corresponds to "now" if not given)</li>
                        <li><a href="/getLumi/?Runs=161297-161320,161331">/getLumi/?Runs=161297-161320,161331</a> or:</li>
                        <li><a href="/getLumi/?Runs=[161297-161320,161331]">/getLumi/?Runs=[161297-161320,161331]</a> LumiInfo for the given runs</li>
                    </ul>
                </body>
            </html>
        '''

    @cherrypy.expose
    def up(self):
        return service.setResponseJSON( [] )

    # root method
    @cherrypy.expose
    def index(self, **kwargs) :
        if 'help' in kwargs :
            return self.help( )
        if 'up' in kwargs :
            return self.up( )

        return service.setResponseJSON( self.getLumi( **kwargs ) )


    def format(self, lumiDictionary, lumiType):
        '''Formats a dictionary from the lumi module into the expected
        format by the users.
        '''

        lumiTypeKey = '%sLumi' % lumiType.capitalize()

        output = []
        for run in sorted(lumiDictionary):
            output.append({
                'Run': run,
                lumiTypeKey: lumiDictionary[run],
            })

        return output


    def getLumi(self, **kwargs):
        '''Parses the arguments and builds the corresponding queries
        to the lumi module.
        '''

        # If lumiType was given, check and set it. Otherwise use default.
        lumiType = 'delivered'
        if 'lumiType' in kwargs:
            if kwargs['lumiType'].lower() == 'recorded':
                lumiType = 'recorded'
            else:
                raise cherrypy.HTTPError(405, 'Invalid lumiType.')

        # If Runs was given, this is a run-based query
        if 'Runs' in kwargs:
            if 'startTime' in kwargs or 'endTime' in kwargs:
                raise cherrypy.HTTPError(405, 'Runs was specified, so startTime and endTime cannot be specified at the same time.')

            runsString = kwargs['Runs']

            if len(runsString) > 1000:
                raise cherrypy.HTTPError(405, 'Query string too long.')

            # Remove optional [] characters
            runsString = runsString.replace('[', '').replace(']', '')

            # Parse the string into several queries
            ranges = []
            queries = runsString.split(',')

            for query in queries:
                try:
                    # Individual run
                    begin = end = int(query)
                except ValueError:
                    # If not, has to be a range
                    begin, end = [int(x) for x in query.split('-')]

                if begin < 0 or end < 0:
                    raise cherrypy.HTTPError(405, 'Negative run numbers.')

                if begin > end:
                    raise cherrypy.HTTPError(405, 'The begin run number is greater than the end run number.')

                ranges.append((begin, end))

            # Merge the ranges to reduce the number of queries
            ranges = merge(ranges)

            # See how many runs we are asking to check in total
            total = 0
            for (begin, end) in ranges:
                total += end - begin + 1
            if total > maxRuns:
                raise cherrypy.HTTPError(405, 'The query requested too many (> %s) run numbers to check.' % maxRuns)

            # Now we have the final ranges, run a query for each
            output = {}
            for (begin, end) in ranges:
                output.update(lumi.query(begin, end, lumiType))

            return self.format(output, lumiType)

        # If startTime was given, this is a time-based query
        if 'startTime' in kwargs:
            begin = dateutil.parser.parse(kwargs['startTime'])

            # If endTime is not specified, take now
            if 'endTime' in kwargs:
                end = dateutil.parser.parse(kwargs['endTime'])
            else:
                end = datetime.datetime.now()

            if begin > end:
                raise cherrypy.HTTPError(405, 'The begin time is greater than the end time.')

            if (end - begin).days > maxDays:
                raise cherrypy.HTTPError(405, 'The query requested a too long time (> %s days) to check.' % maxDays)

            return self.format(lumi.query(begin, end, lumiType), lumiType)

        # If endTime was given but startTime was not, complain
        if 'endTime' in kwargs:
            raise cherrypy.HTTPError(405, 'startTime is required for all time-based queries.')

        # If nothing was specified, return the latest 24 hours
        if len(kwargs) == 0:
            begin = datetime.datetime.now()
            end = begin - datetime.timedelta(days = 1)

            return self.format(lumi.query(begin, end, lumiType), lumiType)

        # In any other case, complain
        raise cherrypy.HTTPError(405, 'Invalid parameters. See /getLumi/help for syntax.')


def main():
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )
    service.start(LumiDB())


if __name__ == '__main__':
    main()

