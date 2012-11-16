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

import database

import logPack
import config


connection = database.Connection(config.connections['dropBox'])


def getFiles():
    return connection.fetch('''
        select fileHash, state, backend, username, creationTimestamp, modificationTimestamp
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
<div class="tabs">
    <ul>
        {% for tabName in tabs %}
            <li><a href="#{{tabName}}">{{tabName}}</a></li>
        {% endfor %}
    </ul>
    {% for tabName in tabs %}
        <div id="{{tabName}}">{{tabs[tabName]}}</div>
    {% endfor %}
</div>
<script>
    $('.tabs').tabs();
    $('.dataTable').dataTable({
        "bJQueryUI": true,
        "sPaginationType": "full_numbers"
    });
</script>
''')


tableTemplate = jinja2.Template('''
<h2>{{title}}</h2>
<table class="dataTable">
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
                    <td>No log</td>
                {% endif %}
            {% endfor %}
        </tr>
    {% endfor %}
    </tbody>
</table>
''')


def convertDatetimes(table):
    newTable = []

    for row in table:
        newRow = []
        for value in row:
            if isinstance(value, datetime.datetime):
                newRow.append(value.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3])
            else:
                newRow.append(value)
        newTable.append(newRow)

    return newTable


def renderTable(table):
    table['table'] = convertDatetimes(table['table'])

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

    return tableTemplate.render(
        title = table['title'],
        headers = table['headers'],
        table = newTable,
    )


def renderLogs():
    tabs = {
        'runLog': {
            'title': 'Logs of each run of the dropBox',
            'headers': [
                'creationTimestamp', 'statusCode', 'firstConditionSafeRun', 'hltRun',
                'modificationTimestamp', 'downloadLog', 'globalLog',
            ],
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
            'table': getFileLogs(),
            'links': [
                ('getFileLog?fileHash=', 'Read log'),
            ],
        },

        'files': {
            'title': 'All files (requests) of the dropBox',
            'headers': [
                'fileHash', 'state', 'backend', 'username',
                'creationTimestamp', 'modificationTimestamp'
            ],
            'table': getFiles(),
            'links': [
            ],
        },

        'emails': {
            'title': 'Queue of emails to be sent by the dropBox',
            'headers': [
                'id', 'subject', 'fromAddress', 'toAddresses', 'ccAddresses', 'creationTimestamp', 'modificationTimestamp'
            ],
            'table': getEmails(),
            'links': [
            ],
        },
    }

    renderedTabs = {}
    for tab in tabs:
        renderedTabs[tab] = renderTable(tabs[tab])

    return mainTemplate.render(tabs = renderedTabs)

