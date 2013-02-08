#!/usr/bin/env python
'''CherryPy REST server example.

See: http://docs.cherrypy.org/dev/progguide/REST.html
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import cherrypy
import re


class Resource(object):

    def __init__(self, content):
        self.content = content

    exposed = True

    def GET(self):
        html_item = lambda (name,value): '<div>{name}:{value}</div>'.format(**vars())
        items = map(html_item, self.content.items())
        items = ''.join(items)
        return '<html>{items}</html>'.format(**vars())

    def PUT(self):
        data = cherrypy.request.body.read()
        pattern = re.compile(r'\<div\>(?P<name>.*?)\:(?P<value>.*?)\</div\>')
        items = [match.groups() for match in pattern.finditer(data)]
        self.content = dict(items)


class Collection(object):

    def __init__(self):
        self.members = []

    exposed = True

    def GET(self):
        html_item = lambda (name): '<div><a href="{name}">{name}</a></div>'.format(**vars())
        items = map(html_item, self.members)
        items = ''.join(items)
        return '<html>{items}</html>'.format(**vars())


def main():
    root = Collection()
    root.sidewinder = Resource({'color': 'red', 'weight': 176, 'type': 'stable'})
    root.teebird = Resource({'color': 'green', 'weight': 173, 'type': 'overstable'})
    root.blowfly = Resource({'color': 'purple', 'weight': 169, 'type': 'putter'})
    root.members = ['sidewinder', 'teebird', 'blowfly']

    cherrypy.quickstart(root, '/', {
        'global': {
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 8099,
        },
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        }
    })

if __name__ == '__main__':
    main()

