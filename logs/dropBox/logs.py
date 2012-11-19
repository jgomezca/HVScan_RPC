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
        select creationTimestamp, statusCode, firstConditionSafeRun, hltRun, modificationTimestamp, nvl2(downloadLog, 1, 0), nvl2(globalLog, 1, 0)
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


def getRunDownloadLog(creationTimestamp):
    return logPack.unpack(connection.fetch('''
        select downloadLog
        from runLog
        where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
    ''', (creationTimestamp, ))[0][0])


def getRunGlobalLog(creationTimestamp):
    return logPack.unpack(connection.fetch('''
        select globalLog
        from runLog
        where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
    ''', (creationTimestamp, ))[0][0])


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
            {% for value in row[0] %}
                <td>{{value}}</td>
            {% endfor %}
            {% for link in row[1] %}
                {% if link %}
                    <td><a target="_blank" href="{{link[0]}}{{row[0][0]}}">{{link[1]}}</a></td>
                {% else %}
                    <td>-</td>
                {% endif %}
            {% endfor %}
        </tr>
    {% endfor %}
    </tbody>
</table>
<script>
    $('#{{name}}Table').dataTable({
        "bJQueryUI": true,
        "sPaginationType": "full_numbers",
        "aaSorting": [{{sortOn}}]
    });
</script>
''')


def transformData(table, headers, transformFunctions):
    newTable = []

    for row in table:
        newRow = []
        for (index, value) in enumerate(row):
            if headers[index] in transformFunctions:
                value = transformFunctions[headers[index]](value)
            elif isinstance(value, datetime.datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
            elif value is None:
                value = '-'
            newRow.append(html.escape(value))
        newTable.append(newRow)

    return newTable


def renderTable(name, table):
    table['table'] = transformData(table['table'], table['headers'], table['transform'])

    newTable = []
    for row in table['table']:
        links = []
        for (index, link) in enumerate(table['links']):
            if row[-len(table['links'])+index]:
                links.append(link)
            else:
                links.append(None)
        if len(links) == 0:
            newTable.append([row, []])
        else:
            newTable.append([row[:-len(table['links'])], links])

    if table['sortOn'] is None:
        table['sortOn'] = "[0, 'desc']"

    return tableTemplate.render(
        name = name,
        title = table['title'],
        headers = table['headers'],
        sortOn = table['sortOn'],
        table = newTable,
    )


def getStatusCodeHumanString(statusCode):
    try:
        return '%s (%s)' % (statusCode, Constants.inverseMapping[int(statusCode)])
    except KeyError:
        return statusCode


def renderLogs():
    sortedTabs = ['runLog', 'fileLog', 'files', 'emails']

    tabs = {
        'runLog': {
            'title': 'Logs of each run of the dropBox',
            'headers': [
                'creationTimestamp', 'statusCode', 'fcsRun', 'hltRun',
                'modificationTimestamp', 'downloadLog', 'globalLog',
            ],
            'sortOn': None,
            'transform': {
                'statusCode': getStatusCodeHumanString
            },
            'table': getRunLogs(),
            'links': [
                ('getRunDownloadLog?creationTimestamp=', 'Read log'),
                ('getRunGlobalLog?creationTimestamp=', 'Read log'),
            ],
        },

        'fileLog': {
            'title': 'Logs of each file (request) processed by the dropBox',
            'headers': [
                'fileHash', 'statusCode', 'metadata', 'userText', 'runLogCreationTimestamp',
                'creationTimestamp', 'modificationTimestamp', 'log',
            ],
            'sortOn': "[5, 'desc']",
            'transform': {
                'statusCode': getStatusCodeHumanString
            },
            'table': getFileLogs(),
            'links': [
                ('getFileLog?fileHash=', 'Read log'),
            ],
        },

        'files': {
            'title': 'All files (requests) of the dropBox',
            'headers': [
                'fileHash', 'state', 'backend', 'username', 'fileName',
                'creationTimestamp', 'modificationTimestamp'
            ],
            'sortOn': "[4, 'desc']",
            'transform': {},
            'table': getFiles(),
            'links': [
            ],
        },

        'emails': {
            'title': 'Queue of emails to be sent by the dropBox',
            'headers': [
                'id', 'subject', 'fromAddress', 'toAddresses', 'ccAddresses', 'creationTimestamp', 'modificationTimestamp'
            ],
            'sortOn': None,
            'transform': {},
            'table': getEmails(),
            'links': [
            ],
        },
    }

    renderedTabs = {}
    for tab in tabs:
        renderedTabs[tab] = renderTable(tab, tabs[tab])

    return mainTemplate.render(sortedTabs = sortedTabs, tabs = renderedTabs)

