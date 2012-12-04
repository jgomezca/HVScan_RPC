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

import jinja2

import html
import database

import logPack
import Constants
import config


connection = database.Connection(config.connections['dropBox'])


def getFiles():
    return connection.fetch('''
        select fileHash, state, backend, username, fileName, creationTimestamp, modificationTimestamp
        from files
    ''')


def getRunLogs():
    return connection.fetch('''
        select creationTimestamp, backend, statusCode, firstConditionSafeRun, hltRun, modificationTimestamp, nvl2(downloadLog, 1, 0), nvl2(globalLog, 1, 0)
        from runLog
    ''')


def getFileLogs():
    return connection.fetch('''
        select fileHash, statusCode, metadata, userText, runLogCreationTimestamp, creationTimestamp, modificationTimestamp, nvl2(log, 1, 0)
        from fileLog
    ''')


def getEmails():
    return connection.fetch('''
        select id, subject, fromAddress, toAddresses, ccAddresses, creationTimestamp, modificationTimestamp
        from emails
    ''')


def getFileLog(fileHash):
    return logPack.unpack(connection.fetch('''
        select log
        from fileLog
        where fileHash = :s
    ''', (fileHash, ))[0][0])


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


def getUserLogs():
    return connection.fetch('''
        select fileHash, fileLog.modificationTimestamp, username, fileName, statusCode, metadata, userText, backend, nvl2(log, 1, 0)
        from files join fileLog using (fileHash)
    ''')


mainTemplate = jinja2.Template('''
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
    $('#{{name}}Table').dataTable({
        "bJQueryUI": true,
        "sPaginationType": "full_numbers",
        "iDisplayLength": 25,
        {{dataTablesInit}}
    });
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
        return 'class="statusFinishedFailed"'

    # Finished: OK -> Green
    elif statusCodeEnding == 99:
        return 'class="statusFinishedOK"'

    # Any other is probably "In progress" -> No color
    return 'class="statusInProgress"'


def getStatusCodeHumanString(statusCode, row):
    try:
        return (getStatusCodeColor(statusCode), '%s (%s)' % (statusCode, Constants.inverseMapping[int(statusCode)]))
    except KeyError:
        return statusCode


def getStatusCodeHumanStringUser(statusCode, row):
    try:
        return (getStatusCodeColor(statusCode), Constants.inverseMapping[int(statusCode)].replace('_', ' '))
    except KeyError:
        return statusCode


def getShortHash(fileHash, row):
    return getShortText(fileHash, row, 8)


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


def renderLogs():
    sortedTabs = ['userLog', 'runLog', 'fileLog', 'files', 'emails']

    tabs = {
        'userLog': {
            'title': 'Log with the most useful information for users',
            'headers': [
                'Hash', 'Last update', 'User', 'File', 'Status', 'Metadata', 'User Text', 'Backend', 'Log',
            ],
            'dataTablesInit': '''
                "aaSorting": [[1, 'desc']]
            ''',
            'transform': {
                'Hash': getShortHash,
                'Status': getStatusCodeHumanStringUser,
                'Metadata': getShortText,
                'User Text': getShortText,
                'Log': getFileLogLink,
            },
            'table': getUserLogs(),
        },

        'runLog': {
            'title': 'Logs of each run of the dropBox',
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
            'title': 'Logs of each file (request) processed by the dropBox',
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

        'files': {
            'title': 'All files (requests) of the dropBox',
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
            'title': 'Queue of emails to be sent by the dropBox',
            'headers': [
                'id', 'subject', 'fromAddress', 'toAddresses', 'ccAddresses', 'creationTimestamp', 'modificationTimestamp'
            ],
            'table': getEmails(),
        },
    }

    renderedTabs = {}
    for tab in tabs:
        renderedTabs[tab] = renderTable(tab, tabs[tab])

    return mainTemplate.render(sortedTabs = sortedTabs, tabs = renderedTabs)

