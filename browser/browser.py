'''CMS DB Web browser server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2013, CERN CMS'
__credits__ = ['Giacomo Govi', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import datetime
import json

import cherrypy
import mako.template

import service
import database


limit = 100


class Browser(object):
    '''Browser server.
    '''

    def __init__(self):
        with open('index.html', 'rb') as f:
            self.indexTemplate = mako.template.Template(f.read())

        self.connections = dict(map(
            lambda x: (x, database.Connection(service.secrets['connections'][x])),
            ['Development', 'Integration', 'Archive', 'Production']
        ))

    @cherrypy.expose
    def index(self):
        '''Status page.
        '''

        return self.indexTemplate.render(
            title = 'CMS Conditions DB Browser'
        )

    @cherrypy.expose
    def search(self, database, string):
        string = '%%%s%%' % string.lower()

        tags = self.connections[database].fetch('''
            select *
            from (
                select name, time_type, object_type, synchronization, insertion_time, description
                from tag
                where
                       lower(name)        like :s
                    or lower(object_type) like :s
                    or lower(description) like :s
                order by insertion_time desc
            )
            where rownum <= :s
        ''', (string, string, string, limit))

        payloads = self.connections[database].fetch('''
            select *
            from (
                select hash, object_type, version, insertion_time
                from payload
                where
                       lower(hash)        like :s
                    or lower(object_type) like :s
                order by insertion_time desc
            )
            where rownum <= :s
        ''', (string, string, limit))

        gts = self.connections[database].fetch('''
            select *
            from (
                select name, release, insertion_time, description
                from global_tag
                where
                       lower(name)        like :s
                    or lower(release)     like :s
                    or lower(description) like :s
                order by insertion_time desc
            )
            where rownum <= :s
        ''', (string, string, string, limit))

        service.setResponseJSON()
        return json.dumps({
            'tags': {
                'headers': ['Tag', 'Time Type', 'Object Type', 'Synchronization', 'Insertion Time', 'Description'],
                'data': tags,
            },
            'payloads': {
                'headers': ['Payload', 'Object Type', 'Version', 'Insertion Time'],
                'data': payloads,
            },
            'gts': {
                'headers': ['Global Tag', 'Release', 'Insertion Time', 'Description'],
                'data': gts,
            },
        }, default = lambda obj:
            obj.strftime('%Y-%m-%d %H:%M:%S,%f') if isinstance(obj, datetime.datetime) else None
        )


    @cherrypy.expose
    def list_(self, database, type_, item):
        service.setResponseJSON()

        if type_ == 'tags':
            return json.dumps({
                'headers': ['Since', 'Insertion Time', 'Payload'],
                'data': self.connections[database].fetch('''
                        select *
                        from (
                            select *
                            from (
                                select since, insertion_time, payload_hash
                                from iov
                                where tag_name = :s
                                order by since desc, insertion_time desc
                            )
                            where rownum <= :s
                        )
                        order by since, insertion_time
                    ''', (item, limit)),
            }, default = lambda obj:
                obj.strftime('%Y-%m-%d %H:%M:%S,%f') if isinstance(obj, datetime.datetime) else None
            )

        if type_ == 'gts':
            return json.dumps({
                'headers': ['Record', 'Label', 'Tag'],
                'data': self.connections[database].fetch('''
                        select record, label, tag_name
                        from global_tag_map
                        where global_tag_name = :s
                        order by record, label
                    ''', (item, )),
            })

        raise Exception('Wrong type requested for listing.')


    @cherrypy.expose
    def diff(self, database, type_, first, second):
        return json.dumps([])


def main():
    service.start(Browser())


if __name__ == '__main__':
    main()

