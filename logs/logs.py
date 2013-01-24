'''CMS DB Web Logs server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import cherrypy
import jinja2

import service

import dropBox.logs


mainTemplate = jinja2.Template('''
<!DOCTYPE HTML>
<html>
    <head>
            <title>CMS DB Web Services' Logs</title>
            <meta http-equiv='refresh' content='600'>
            <link rel="stylesheet" type="text/css" href="/libs/jquery-ui/1.8.20/css/smoothness/jquery-ui-1.8.20.custom.css" />
            <link rel="stylesheet" type="text/css" href="/libs/datatables/1.9.4/media/css/jquery.dataTables_themeroller.css" />
            <link rel="stylesheet" type="text/css" href="/libs/bootstrap/2.2.1/css/bootstrap.min.css" />
            <style type="text/css">
                html, body, div, span, applet, object, iframe,h1, h2, h3, h4, h5, h6, p, blockquote, pre,a, abbr, acronym, address, big, cite, code,del, dfn, em, font, img, ins, kbd, q, s, samp, small, strike, strong, sub, sup, tt, var,b, u, i, center,dl, dt, dd, fieldset, ol, ul, li, form, label, legend,table, caption, tbody, tfoot, thead, tr, th, td {
                    margin: 0;
                    padding: 0;
                    border: 0;
                    outline: 0;
                    font-size: 13px;
                    line-height: 15px;
                    vertical-align: baseline;
                    background: transparent;
                }
                .ui-tabs .ui-tabs-panel {
                    padding: 10px;
                }
                .navbar-inner {
                    min-height: 30px;
                }
                body {
                    padding-top: 40px;
                }
                h2 {
                    font-size: 15px;
                    margin-bottom: 10px;
                }
                .page {
                    padding: 10px;
                }
                .fg-toolbar select, .fg-toolbar input {
                    margin: 0px;
                    padding: 0px;
                }
                .clickable {
                    cursor: pointer;
                }
                .expandCellButton {
                    float: right;
                    vertical-align: middle;
                }
                .hidden {
                    display: none;
                }
                .status {
                    margin-bottom: 10px;
                }
                .status td, .status th {
                    padding: 5px;
                }
                .statusInProgress {
                    background-color: #99FFFF !important;
                }
                .statusFinishedFailed {
                    background-color: #FF9999 !important;
                }
                .statusFinishedWarning {
                    background-color: #FFCC80 !important;
                }
                .statusFinishedOK {
                    background-color: #99FF99 !important;
                }
                .statusOld {
                    background-color: #DD99FF !important;
                }
            </style>
            <script src="/libs/jquery-1.7.2.min.js"></script>
            <script src="/libs/jquery-ui/1.8.20/js/jquery-ui-1.8.20.custom.min.js"></script>
            <script src="/libs/datatables/1.9.4/media/js/jquery.dataTables.min.js"></script>
    </head>
    <body>
        <div class="navbar navbar-inverse navbar-fixed-top">
            <div class="navbar-inner">
                <div class="container">
                    <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                    </a>
                    <a class="brand" href="/logs">CMS DB Web Services' Logs</a>
                    <div class="nav-collapse collapse">
                        <ul class="nav">
                            {% for service in services %}
                                {% if services[service] == None %}
                                    <li><a href="/logs/{{service}}">{{service}}</a></li>
                                {% endif %}
                            {% endfor %}
                        </ul>
                    </div><!--/.nav-collapse -->
                </div>
            </div>
        </div>

        <div class="page">{{body}}</div>
    </body>
</html>
''')


def renderPage(body):
    return mainTemplate.render(body = body, services = {
        'dropBox': None,
    })


class DropBoxLogs(object):
    '''dropBox logs.
    '''

    @cherrypy.expose
    def index(self):
        return renderPage(dropBox.logs.renderLogs())


    @cherrypy.expose
    def getRunDownloadLog(self, creationTimestamp, backend):
        return service.setResponsePlainText(dropBox.logs.getRunDownloadLog(creationTimestamp, backend))


    @cherrypy.expose
    def getRunGlobalLog(self, creationTimestamp, backend):
        return service.setResponsePlainText(dropBox.logs.getRunGlobalLog(creationTimestamp, backend))


    @cherrypy.expose
    def getFileLog(self, fileHash):
        return service.setResponsePlainText(dropBox.logs.getFileLog(fileHash))


class Logs(object):
    '''Logs server.
    '''

    dropBox = DropBoxLogs()

    @cherrypy.expose
    def index(self):
        return renderPage("<p>Use the menu above to browse the services' logs.</p>")


def main():
    service.start(Logs())


if __name__ == '__main__':
    main()

