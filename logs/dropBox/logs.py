'''Offline new dropBox's logs.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import datetime
import json

import cherrypy
import jinja2

import service
import html
import database
import shibboleth
import cache

import logPack
import Constants
import config


connection = database.Connection(config.connectionDictionary)


def getFiles():
    return connection.fetch('''
        select fileHash, state, backend, username, fileName, creationTimestamp, modificationTimestamp
        from files
        where creationTimestamp > sysdate - 7
    ''')


def getRunLogs():
    return connection.fetch('''
        select creationTimestamp, backend, statusCode, firstConditionSafeRun, hltRun, modificationTimestamp, nvl2(downloadLog, 1, 0), nvl2(globalLog, 1, 0)
        from runLog
        where creationTimestamp > sysdate - 7
    ''')


def getFileLogs():
    return connection.fetch('''
        select fileHash, statusCode, metadata, userText, runLogCreationTimestamp, creationTimestamp, modificationTimestamp, nvl2(log, 1, 0)
        from fileLog
        where creationTimestamp > sysdate - 7
    ''')


def getEmails():
    return connection.fetch('''
        select id, subject, fromAddress, toAddresses, ccAddresses, creationTimestamp, modificationTimestamp
        from emails
        where creationTimestamp > sysdate - 7
    ''')


def getFileLog(fileHash):
    return logPack.unpack(connection.fetch('''
        select log
        from fileLog
        where fileHash = :s
    ''', (fileHash, ))[0][0])


def getFileAcks():
    return connection.fetch('''
        select fileHash, username, rationale, creationTimestamp, modificationTimestamp
        from fileAcks
        where creationTimestamp > sysdate - 7
    ''')


def getRunDownloadLog(creationTimestamp, backend):
    return logPack.unpack(connection.fetch('''
        select downloadLog
        from runLog
        where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
            and backend = :s
    ''', (creationTimestamp, backend))[0][0])


def getRunGlobalLog(creationTimestamp, backend):
    return logPack.unpack(connection.fetch('''
        select globalLog
        from runLog
        where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
            and backend = :s
    ''', (creationTimestamp, backend))[0][0])


def _fillAcknowledgeColumn(data):
    # Give the correct value to the acknowledge column
    fileHashIndex = 0
    statusIndex = 4
    ackIndex = 5
    for row in data:
        if row[statusIndex] == Constants.PROCESSING_OK or row[statusIndex] == Constants.PCL_EXPORTING_OK_BUT_DUPLICATION_TO_HLTEXPRESS_FAILURE:
            # The file was correctly processed or it was a warning, so acknowledges do not apply
            row[ackIndex] = None
        else:
            ack = connection.fetch('''
                select username
                from fileAcks
                where fileHash = :s
            ''', (row[fileHashIndex], ))

            if len(ack) == 0:
                # The issue is not acknowledged
                row[ackIndex] = False
            else:
                # The issue was acknowledged, pass the username to the transform function
                row[ackIndex] = ack[0][0]

    return data


def getUserLogs():
    # The NULL gives us space for the acknowledge treatment below
    data = connection.fetch('''
        select fileHash, fileLog.modificationTimestamp, username, fileName, statusCode, NULL, metadata, userText, backend, nvl2(log, 1, 0)
        from files join fileLog using (fileHash)
        where files.creationTimestamp > sysdate - 7
    ''')

    return _fillAcknowledgeColumn(data)


def searchUserLog(beginDate, endDate, fileHash, username, fileName, statusCode, metadata, userText, backend):
    '''Returns a custom search of the userLog.

    Limited to a maximum of 100 rows in all cases.
    '''

    parameters = [beginDate, endDate]
    searchTerms = []

    for arg in ['fileHash', 'username', 'fileName', 'metadata', 'userText', 'backend']:
        value = locals()[arg]
        if value is not None:
            value = str(value).strip()
            if len(value) > 0:
                parameters.append(str(value).strip())
                searchTerms.append(arg)

    if statusCode == 'Success':
        searchStatusCode = 'and mod(statusCode, 100) = 99'
    elif statusCode == 'Warning':
        searchStatusCode = 'and mod(statusCode, 100) = 11'
    elif statusCode == 'Failure':
        searchStatusCode = 'and mod(statusCode, 100) in (10, 20)'
    else:
        searchStatusCode = ''

    # The NULL gives us space for the acknowledge treatment below
    data = connection.fetch('''
        select *
        from (
            select fileHash, fileLog.modificationTimestamp, username, fileName, statusCode, NULL, metadata, userText, backend, nvl2(log, 1, 0)
            from files join fileLog using (fileHash)
            where files.creationTimestamp >= to_timestamp(:s, 'YYYY-MM-DD')
                and files.creationTimestamp < to_timestamp(:s, 'YYYY-MM-DD') + 1
                %s
                %s
        ) where rownum <= 100
    ''' % (
        ' '.join(["and lower(%s) like lower('%%' || :s || '%%') escape '\\'" % x for x in searchTerms]),
        searchStatusCode,
    ), parameters)

    return _fillAcknowledgeColumn(data)


def getAcknowledgeRationale(fileHash):
    return connection.fetch('''
        select rationale
        from fileAcks
        where fileHash = :s
    ''', (fileHash, ))[0][0]


def getBackendsLatestRun():
    result = connection.fetch('''
        select backend, creationTimestamp, statusCode
        from runLog natural join (
            select backend, max(creationTimestamp) as creationTimestamp
            from runLog
            group by backend
        )
    ''')

    if len(result) == 0:
        return []

    return result


def getBackendsLatestNotEmptyRun():
    result = connection.fetch('''
        select backend, creationTimestamp, statusCode
        from runLog natural join (
            select backend, max(creationTimestamp) as creationTimestamp
            from runLog
            where statusCode <> 1999
            group by backend
        )
    ''')

    if len(result) == 0:
        return []

    return result


acknowledgeFileIssuePage = jinja2.Template('''
<!DOCTYPE HTML>
<html>
    <head>
            <title>Acknowledge file {{fileHash}}</title>
    </head>
    <body>
        <h1>Acknowledge file {{fileHash}}</h1>
        <form name="input" action="/dropBox/acknowledgeFileIssue" method="post">
            <input type="hidden" name="fileHash" value="{{fileHash}}">
            <p><textarea onKeyPress="return this.value.length < 4000;" name="rationale" rows="10" cols="80">Rationale: write here why it was acknowledged (4000 characters max).</textarea></p>
            <p><input type="submit" value="Acknowledge"></p>
        </form>
    </body>
</html>
''')

def getAcknowledgeFileIssuePage(fileHash):
    return acknowledgeFileIssuePage.render(fileHash = fileHash)


@cache.logs.cacheCall('dropBox_getStatus', 60)
def getStatus():
    '''Returns a the list of failed processed files in the latest hour.

    For check_mk agent dropBox.check_mk.py.

    Cached to prevent abuse/bugs loading the database.
    '''

    return service.getPrettifiedJSON(connection.fetch('''
        select fileHash, statusCode, creationTimestamp
        from fileLog
        where mod(statusCode, 100) in (10, 20)
            and creationTimestamp > sysdate - (1/24)
            and not exists (
                select fileHash
                from fileAcks
                where fileAcks.fileHash = fileLog.fileHash
            )
        order by creationTimestamp
    '''))


mainTemplate = jinja2.Template('''
<table>
    <tr>
    <td>
    <table class="status">
        <tr>
            <th></th>
            {% for backend in backends %}
                <th>{{backend}}</th>
            {% endfor %}
        </tr>
        <tr>
            <td>Backends' latest runs</td>
            {% for backend in backends %}
                {% if backend in backendsLatestRun %}
                    <td class="{{backendsLatestRun[backend][1]}}">{{backendsLatestRun[backend][0]}}</td>
                {% else %}
                    <td>-</td>
                {% endif %}
            {% endfor %}
        </tr>
        <tr>
            <td>Backends' latest non-empty runs</td>
            {% for backend in backends %}
                {% if backend in backendsLatestNotEmptyRun %}
                    <td class="{{backendsLatestNotEmptyRun[backend][1]}}">{{backendsLatestNotEmptyRun[backend][0]}}</td>
                {% else %}
                    <td>-</td>
                {% endif %}
            {% endfor %}
        </tr>
    </table>
    </td>
    <td>
    <form id="userLogSearch" name="userLogSearch" action="searchUserLog" method="get">
    <table class="status">
        <tr>
            <td><label for="beginDate">Time range (start)</label></td>
            <td><input type="text" name="beginDate" id="beginDate" placeholder="e.g. 2013-01-01" value="{{searchFields['beginDate']}}" required></td>
            <td><label for="fileName">File</label></td>
            <td><input type="text" name="fileName" id="fileName" value="{{searchFields['fileName']}}"></td>
        </tr>
        <tr>
            <td><label for="endDate">Time range (end)</label></td>
            <td><input type="search" name="endDate" id="endDate" placeholder="e.g. 2013-01-01" value="{{searchFields['endDate']}}" required></td>
            <td><label for="metadata">Metadata</label></td>
            <td><input type="search" name="metadata" id="metadata" value="{{searchFields['metadata']}}"></td>
        </tr>
        <tr>
            <td><label for="fileHash">Hash</td>
            <td><input type="search" name="fileHash" id="fileHash" value="{{searchFields['fileHash']}}"></td>
            <td><label for="userText">User Text</label></td>
            <td><input type="search" name="userText" id="userText" value="{{searchFields['userText']}}"></td>
        </tr>
        <tr>
            <td><label for="username">User</label></td>
            <td><input type="search" name="username" id="username" value="{{searchFields['username']}}"></td>
            <td><label for="backend">Backend</label></td>
            <td><input type="search" name="backend" id="backend" value="{{searchFields['backend']}}"></td>
        </tr>
        <tr>
            <td><label for="statusCode">Status</label></td>
            <td>
                <select name="statusCode">
                    {% for option in ['Any', 'Success', 'Warning', 'Failure'] %}
                        <option {{'selected' if searchFields['statusCode'] == option else ''}} value="{{option}}">{{option}}</option>
                    {% endfor %}
                </select>
            </td>
            <td></td>
            <td><input type="submit" value="Search userLog"></td>
        </tr>
    </table>
    </form>
    </td>
    </tr>
</table>
<div id="dropBoxTabs">
    <ul>
        {% for tabName in sortedTabs %}
            <li><a href="#{{tabName}}">{{tabName}}</a></li>
        {% endfor %}
    </ul>
    {% for tabName in sortedTabs %}
        <div id="{{tabName}}">{{tabs[tabName]}}</div>
    {% endfor %}
</div>
<script>
    $('#dropBoxTabs').tabs();

    var dates = $("#beginDate, #endDate").datepicker({
	    changeMonth: true,
	    changeYear: true,
	    numberOfMonths: 1,
	    minDate: new Date(2012, 11, 20), // the first rows in the DB were inserted on 2012-11-21
	    maxDate: new Date(), // can't be later than today
	    dateFormat: "yy-mm-dd",
	    onSelect: function(selectedDate) {
		    var option = this.id == "beginDate" ? "minDate" : "maxDate";
		    var instance = jQuery(this).data("datepicker");
		    var date = jQuery.datepicker.parseDate(instance.settings.dateFormat || jQuery.datepicker._defaults.dateFormat, selectedDate, instance.settings);
		    dates.not(this).datepicker("option", option, date);
	    }
    });

    // Only set if there is no default value yet
    if ($("#beginDate")[0].value == '')
        $("#beginDate").datepicker("setDate", new Date());
    if ($("#endDate")[0].value == '')
        $("#endDate").datepicker("setDate", new Date());

</script>
''')


tableTemplate = jinja2.Template('''
<h2>{{title}}</h2>
<table id="{{name}}Table">
    <thead>
        <tr>
            {% for header in headers %}
                <th>{{header}}</th>
            {% endfor %}
        </tr>
    </thead>
    <tbody>
    {% for row in table %}
        <tr>
            {% for (attributes, value) in row %}
                <td {{attributes}}>{{value}}</td>
            {% endfor %}
        </tr>
    {% endfor %}
    </tbody>
</table>
<script>
    function escapeHTML(text) {
        return $('<i></i>').text(text).html();
    }

    function expandableCell_expand(cell) {
        cell.html(escapeHTML(cell.attr('data-expanded')) + '<img class="expandCellButton unexpandCell clickable" height="15" width="15" src="/libs/datatables/1.9.4/examples/examples_support/details_close.png" />');
    }

    function expandableCell_unexpand(cell) {
        cell.html(escapeHTML(cell.attr('data-unexpanded')) + '...<img class="expandCellButton expandCell clickable" height="15" width="15" src="/libs/datatables/1.9.4/examples/examples_support/details_open.png" /><span class="hidden">' + escapeHTML(cell.attr('data-expanded')) + '</span>');
    }

    $('#{{name}}Table .expandCell').live('click', function() {
        expandableCell_expand($(this).parent());
    });

    $('#{{name}}Table .unexpandCell').live('click', function() {
        expandableCell_unexpand($(this).parent());
    });

    // Before the dataTable is created, for expand-able cells, put the full text
    // inside the <td> (but hidden) to allow searches on it, add the expand
    // "plus" button and some style
    $('#{{name}}Table td.expandableCell').each(function() {
        expandableCell_unexpand($(this));
    });

    // Create the dataTable
    var table = $('#{{name}}Table').dataTable({
        "bJQueryUI": true,
        "sPaginationType": "full_numbers",
        "iDisplayLength": 25,
        {{dataTablesInit}}
    });

    // If there is no records to display, remove the search field
    if (table.fnSettings().fnRecordsDisplay() == 0) {
        $("#{{name}}Table_filter input").val('');
        table.fnFilter('');
    }
</script>
''')


def renderTable(name, table):
    table.setdefault('transform', {})
    table.setdefault('dataTablesInit', '''
        "aaSorting": [[0, 'desc']]
    ''')

    newTable = []
    for row in table['table']:
        newRow = []
        for (index, value) in enumerate(row):
            # If there is a transformation function, use it
            # The function is responsible for escaping properly
            if table['headers'][index] in table['transform']:
                value = table['transform'][table['headers'][index]](value, row)

            # If it is a datetime, render it up to seconds
            elif isinstance(value, datetime.datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')

            # If it is None, use '-' as a placeholder
            elif value is None:
                value = '-'

            # If it is anything else, stringify it and escape it
            else:
                value = html.escape(str(value))

            # If the result is not already the (attributes, value) tuple
            # for the <td> element, wrap it
            if type(value) is not tuple:
                value = ('', value)

            newRow.append(value)
        newTable.append(newRow)

    return tableTemplate.render(
        name = name,
        title = table['title'],
        headers = table['headers'],
        dataTablesInit = table['dataTablesInit'],
        table = newTable,
    )


def getStatusCodeColor(statusCode):
    statusCodeEnding = int(statusCode) % 100

    # Finished: Failed -> Red
    if statusCodeEnding == 10:
        return 'statusFinishedFailed'

    # Finished: Warning -> Orange
    elif statusCodeEnding == 11:
        return 'statusFinishedWarning'

    # Finished: OK -> Green
    elif statusCodeEnding == 99:
        return 'statusFinishedOK'

    # Any other is probably "In progress" -> No color
    return 'statusInProgress'


def getStatusCodeHumanString(statusCode, row):
    try:
        return ('class="%s"' % getStatusCodeColor(statusCode), '%s (%s)' % (statusCode, Constants.inverseMapping[int(statusCode)]))
    except KeyError:
        return statusCode


def getStatusCodeHumanStringUser(statusCode, row):
    try:
        if statusCode == Constants.PCL_EXPORTING_OK_BUT_DUPLICATION_TO_HLTEXPRESS_FAILURE:
            humanString = 'PCL EXPORTING OK BUT DUPLICATION TO HLT/EXPRESS FAILURE'
        else:
            humanString = Constants.inverseMapping[int(statusCode)].replace('_', ' ')
        return ('class="%s"' % getStatusCodeColor(statusCode), humanString)
    except KeyError:
        return statusCode


def getAcknowledged(acknowledged, row):
    '''Three possibilities:

      * acknowledge is None: Means there was no error for this file.
                             A dash is displayed.

      * acknowledge is str:  Means there was an error and it was acknowledged.
                             'Yes' is displayed, with a link to display the rationale.

      * otherwise:           Means there was an error but it was not acknowledged.
                             A link to acknowledge is displayed.
    '''

    if acknowledged is None:
        return '-'
    elif isinstance(acknowledged, str):
        return buildLink('getAcknowledgeRationale?fileHash=%s' % row[0], 'Yes, by %s, read why' % acknowledged)
    else:
        return buildLink('getAcknowledgeFileIssuePage?fileHash=%s' % row[0], 'No, acknowledge it')


def getShortHash(fileHash, row):
    return getShortText(fileHash, row, 8)


def getShortFile(fileName, row):
    return getShortText(fileName, row, 20)


def getShortText(text, row, lengthLimit = 40):
    if len(text) <= lengthLimit:
        return html.escape(text)

    return ("class='expandableCell' data-expanded='%s' data-unexpanded='%s'" % (html.escape(text), html.escape(text[:lengthLimit])), '')


def buildLink(target, title):
    return '<a target="_blank" href="%s">%s</a>' % (target, html.escape(title))


def getFileLogLink(isThereLog, row):
    if not isThereLog:
        return '-'

    return buildLink('getFileLog?fileHash=%s' % row[0], 'Read')


def getRunDownloadLogLink(isThereLog, row):
    if not isThereLog:
        return '-'

    return buildLink('getRunDownloadLog?creationTimestamp=%s&backend=%s' % (row[0].strftime('%Y-%m-%d %H:%M:%S,%f')[:-3], row[1]), 'Read')


def getRunGlobalLogLink(isThereLog, row):
    if not isThereLog:
        return '-'

    return buildLink('getRunGlobalLog?creationTimestamp=%s&backend=%s' % (row[0].strftime('%Y-%m-%d %H:%M:%S,%f')[:-3], row[1]), 'Read')


def getRunStatus(backend, creationTimestamp, statusCode, checkTooOld):
    timeString = creationTimestamp.strftime('%Y-%m-%d %H:%M:%S')
    timeDelta = datetime.datetime.now() - creationTimestamp
    timeDelta = timeDelta.days * 24 * 60 * 60 + timeDelta.seconds

    if checkTooOld and timeDelta > config.getBackendOldThreshold(backend):
        return ('%s (%s seconds too old!)' % (timeString, timeDelta - config.getBackendOldThreshold(backend)), 'statusOld')

    return (timeString, getStatusCodeColor(statusCode))


def getSearchUserLogTabs(beginDate, endDate, fileHash, username, fileName, statusCode, metadata, userText, backend):
    sortedTabs = ['userLogSearchResult']
    tabs = {
        'userLogSearchResult': {
            'title': 'Result of the search in the userLog',
            'headers': [
                'Hash', 'Last update', 'User', 'File', 'Status', 'Acknowledged', 'Metadata', 'User Text', 'Backend', 'Log',
            ],
            'dataTablesInit': '''
                "aaSorting": [[1, 'desc']]
            ''',
            'transform': {
                'Hash': getShortHash,
                'File': getShortFile,
                'Status': getStatusCodeHumanStringUser,
                'Acknowledged': getAcknowledged,
                'Metadata': getShortText,
                'User Text': getShortText,
                'Log': getFileLogLink,
            },
            'table': searchUserLog(beginDate, endDate, fileHash, username, fileName, statusCode, metadata, userText, backend),
        },
    }

    return (sortedTabs, tabs)


def getDefaultTabs():
    # In the userLog:
    #   If the user receives all the notifications, by default show all the entries.
    #   If not, by default show only those for him.
    defaultUserLogSearch = ''
    if 'cms-cond-dropbox-notifications' not in shibboleth.getGroups():
        defaultUserLogSearch = shibboleth.getUsername()

    sortedTabs = ['userLog', 'runLog', 'fileLog', 'fileAcks', 'files', 'emails']
    tabs = {
        'userLog': {
            'title': 'Log with the most useful information for users (last week)',
            'headers': [
                'Hash', 'Last update', 'User', 'File', 'Status', 'Acknowledged', 'Metadata', 'User Text', 'Backend', 'Log',
            ],
            'dataTablesInit': '''
                "aaSorting": [[1, 'desc']],
                "oSearch": {
                    "sSearch": "%s"
                }
            ''' % defaultUserLogSearch,
            'transform': {
                'Hash': getShortHash,
                'File': getShortFile,
                'Status': getStatusCodeHumanStringUser,
                'Acknowledged': getAcknowledged,
                'Metadata': getShortText,
                'User Text': getShortText,
                'Log': getFileLogLink,
            },
            'table': getUserLogs(),
        },

        'runLog': {
            'title': 'Logs of each run of the dropBox (last week)',
            'headers': [
                'creationTimestamp', 'backend', 'statusCode', 'fcsRun', 'hltRun',
                'modificationTimestamp', 'downloadLog', 'globalLog',
            ],
            'transform': {
                'statusCode': getStatusCodeHumanString,
                'downloadLog': getRunDownloadLogLink,
                'globalLog': getRunGlobalLogLink,
            },
            'table': getRunLogs(),
        },

        'fileLog': {
            'title': 'Logs of each file (request) processed by the dropBox (last week)',
            'headers': [
                'fileHash', 'statusCode', 'metadata', 'userText', 'runLogCreationTimestamp',
                'creationTimestamp', 'modificationTimestamp', 'log',
            ],
            'dataTablesInit': '''
                "aaSorting": [[5, 'desc']]
            ''',
            'transform': {
                'statusCode': getStatusCodeHumanString,
                'log': getFileLogLink,
            },
            'table': getFileLogs(),
        },

        'fileAcks': {
            'title': 'Logs of acknowledges for issues in files (requests) processed by the dropBox (last week)',
            'headers': [
                'fileHash', 'username', 'rationale', 'creationTimestamp', 'modificationTimestamp'
            ],
            'dataTablesInit': '''
                "aaSorting": [[3, 'desc']]
            ''',
            'table': getFileAcks(),
        },

        'files': {
            'title': 'All files (requests) of the dropBox (last week)',
            'headers': [
                'fileHash', 'state', 'backend', 'username', 'fileName',
                'creationTimestamp', 'modificationTimestamp'
            ],
            'dataTablesInit': '''
                "aaSorting": [[5, 'desc']]
            ''',
            'table': getFiles(),
        },

        'emails': {
            'title': 'Queue of emails to be sent by the dropBox (last week)',
            'headers': [
                'id', 'subject', 'fromAddress', 'toAddresses', 'ccAddresses', 'creationTimestamp', 'modificationTimestamp'
            ],
            'table': getEmails(),
        },
    }

    return (sortedTabs, tabs)


def renderTabs(sortedTabs, tabs, searchFields = {}):
    _backendsLatestRun = getBackendsLatestRun()
    backendsLatestRun = {}
    for backend, creationTimestamp, statusCode in _backendsLatestRun:
        backendsLatestRun[backend] = getRunStatus(backend, creationTimestamp, statusCode, True)

    _backendsLatestNotEmptyRun = getBackendsLatestNotEmptyRun()
    backendsLatestNotEmptyRun = {}
    for backend, creationTimestamp, statusCode in _backendsLatestNotEmptyRun:
        backendsLatestNotEmptyRun[backend] = getRunStatus(backend, creationTimestamp, statusCode, False)

    backends = sorted(set(backendsLatestRun) | set(backendsLatestNotEmptyRun))

    renderedTabs = {}
    for tab in tabs:
        renderedTabs[tab] = renderTable(tab, tabs[tab])

    for key in ['beginDate', 'endDate', 'fileHash', 'username', 'fileName', 'metadata', 'userText', 'backend']:
        searchFields[key] = searchFields.setdefault(key, '')

    return mainTemplate.render(sortedTabs = sortedTabs, tabs = renderedTabs, backendsLatestRun = backendsLatestRun, backendsLatestNotEmptyRun = backendsLatestNotEmptyRun, backends = backends, searchFields = searchFields)


class DropBoxLogs(object):
    '''dropBox logs.
    '''

    def __init__(self, renderPage):
        self.renderPage = renderPage


    @cherrypy.expose
    def index(self):
        tabs = getDefaultTabs()
        return self.renderPage(renderTabs(*tabs))


    @cherrypy.expose
    def searchUserLog(self, beginDate, endDate, fileHash, username, fileName, statusCode, metadata, userText, backend):
        tabs = getSearchUserLogTabs(beginDate, endDate, fileHash, username, fileName, statusCode, metadata, userText, backend)
        return self.renderPage(renderTabs(*tabs, searchFields = {
            'beginDate': beginDate,
            'endDate': endDate,
            'fileHash': fileHash,
            'username': username,
            'fileName': fileName,
            'statusCode': statusCode,
            'metadata': metadata,
            'userText': userText,
            'backend': backend,
        }))


    @cherrypy.expose
    def getRunDownloadLog(self, creationTimestamp, backend):
        return service.setResponsePlainText(getRunDownloadLog(creationTimestamp, backend))


    @cherrypy.expose
    def getRunGlobalLog(self, creationTimestamp, backend):
        return service.setResponsePlainText(getRunGlobalLog(creationTimestamp, backend))


    @cherrypy.expose
    def getFileLog(self, fileHash):
        return service.setResponsePlainText(getFileLog(fileHash))


    @cherrypy.expose
    def getAcknowledgeRationale(self, fileHash):
        return service.setResponsePlainText(getAcknowledgeRationale(fileHash))


    @cherrypy.expose
    def getAcknowledgeFileIssuePage(self, fileHash):
        return getAcknowledgeFileIssuePage(fileHash)


    @cherrypy.expose
    def getStatus(self):
        return service.setResponsePlainText(getStatus())

