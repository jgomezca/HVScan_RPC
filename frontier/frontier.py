'''CMS DB Web frontier server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import cherrypy
import jinja2

import http

import service


mainTemplate = jinja2.Template('''
<!DOCTYPE HTML>
<html>
    <head>
            <title>CMS DB Web Frontier</title>
            <meta http-equiv='refresh' content='600'>
    </head>
    <body>
        <h1>CMS DB Web Frontier</h1>
        <p>The blue line is the traffic received from upstream. The green is the traffic sent downstream.</p>
        <table>
        {% for (name, title, description) in images %}
            <tr>
                <td><img src="getImage?name={{name}}"></td>
                <td><h2>{{title}}</h2><p>{{description}}</p></td>
            </tr>
        {% endfor %}
        </table>
    </body>
</html>
''')


images = [
    ('frontier1_proxy-hit-day.png',        'Frontier 1 - network activity - Daily report',  'Bytes per minute transmitted'),
    ('frontier1_proxy-hit-week.png',       'Frontier 1 - network activity - Weekly report', 'Bytes per minute transmitted'),
    ('frontier1_proxy-srvkbinout-day.png', 'Frontier 1 - network activity - Daily report',  'Bytes per second transmitted'),
    ('frontier2_proxy-hit-day.png',        'Frontier 2 - network activity - Daily report',  'Bytes per minute transmitted'),
    ('frontier2_proxy-hit-week.png',       'Frontier 2 - network activity - Weekly report', 'Bytes per minute transmitted'),
    ('frontier2_proxy-srvkbinout-day.png', 'Frontier 2 - network activity - Daily report',  'Bytes per second transmitted'),
]


# It is a static page; but this way we keep the images as a Python list
# which can be looked up in getImage()
renderedMainTemplate = mainTemplate.render(images = images)


class Frontier(object):
    '''Frontier server.
    '''


    @cherrypy.expose
    def index(self):
        return renderedMainTemplate


    @cherrypy.expose
    def getImage(self, name):
        if name not in zip(*images)[0]:
            raise cherrypy.NotFound()

        cherrypy.response.headers['Content-Type'] = "image/png"
        return http.HTTP().query('http://popcon2vm:8081/snapshot/%s' % name)


def main():
    service.start(Frontier())


if __name__ == '__main__':
    main()

