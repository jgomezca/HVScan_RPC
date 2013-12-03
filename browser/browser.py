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
import glob

import cherrypy
import mako.template

import service
import database
import shibboleth


limit = 100


def _high(n):
    return int(n) >> 32


def _low(n):
    return int(n) & 0xffffffff


def _render_sinces(time_type, data):
    if time_type == 'Time':
        for row in data:
            # datetime does not support nanosecond precision: format ourselves
            row[0] = '%s (UTC: %s,%s)' % (row[0], datetime.datetime.utcfromtimestamp(_high(row[0])), str(_low(row[0])).zfill(9))

    elif time_type == 'Lumi':
        for row in data:
            row[0] = '%s (Run: %s Lumi: %s)' % (row[0], _high(row[0]), _low(row[0]))

    return data


def render_template(filename):
    with open(filename, 'rb') as f:
        return mako.template.Template(f.read())


class Browser(object):
    '''Browser server.
    '''

    def __init__(self):
        self.templates = dict(
            (filename.split('templates/')[1].rsplit('.html')[0], render_template(filename))
            for filename
            in glob.glob('templates/*.html')
        )

        self.connections = dict(
            (name, database.Connection(conn))
            for name,conn
            in service.secrets['connections'].items()
        )

    @cherrypy.expose
    def index(self):
        return self.templates['index'].render(
            username = shibboleth.getUsername(),
        )


    @cherrypy.expose
    def news(self):
        # TODO: Render from an Atom/RSS feed
        return self.templates['news'].render(
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
            time_type = self.connections[database].fetch('''
                select time_type
                from tag
                where name = :s
            ''', (item, ))[0][0]

            return json.dumps({
                'headers': ['Since', 'Insertion Time', 'Payload'],
                'data': _render_sinces(time_type, self.connections[database].fetch('''
                        select *
                        from (
                            select since, insertion_time, payload_hash
                            from iov
                            where tag_name = :s
                            order by since desc, insertion_time desc
                        )
                        where rownum <= :s
                    ''', (item, limit))),
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
                    ''', (item, )),
            })

        raise Exception('Wrong type requested for listing.')


    @cherrypy.expose
    def diff(self, database, type_, first, second):
        return json.dumps([])


    @cherrypy.expose
    def upload(self, file_content, source_tag, destination_tags, comment):
        return '%s' % {
            'file_content': file_content[0:50] + ' (...)',
            'source_tag': source_tag,
            'destination_tags': json.loads(destination_tags),
            'comment': comment,
        }


def main():
    service.start(Browser())


if __name__ == '__main__':
    main()

