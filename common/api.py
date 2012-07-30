'''Code for generating the api() and apih() methods for CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Kostas Tamosiunas']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import inspect
import cherrypy
import jinja2
import service


def generateServiceApi(cherrypyClass):
    '''CherryPy class decorator for generating the api() and apih() methods for CMS DB Web services.
    '''

    # Get the methods' details
    methods = {}
    for (name, method) in inspect.getmembers(cherrypyClass, predicate = inspect.ismethod):
        if hasattr(method, 'exposed') and method.exposed == True:
            argspec = inspect.getargspec(method)
            methods[name] = {
                'short_spec': str(argspec),
                'doc': inspect.getdoc(method),
                'args': argspec[0][1:],
                'varargs': argspec[1],
                'keywords': argspec[2],
                'defaults': argspec[3],
            }

    template = '''
        <!DOCTYPE html>
        <html>
            <head>
                <style type="text/css">
                    table {
                        border-collapse: collapse;
                    }
                    td, th {
                        border: 1px solid #7A7A7A;
                        padding: 3px;
                        vertical-align: middle;
                    }
                    th {
                        background-color: #CACACA;
                        text-align: center;
                    }
                    pre {
                        margin: 0;
                    }
                    span {
                        color: blue;
                        font-weight: bold;
                    }
                </style>
                <title>Exposed methods</title>
            </head>
            <body>
                <h1>Exposed methods</h1>
                <table>
                    <tr>
                        <th>Method</th>
                        <th>Documentation</th>
                    </tr>
                    {% for method in methods %}
                        <tr>
                            <td>
                                <span>{{method}}</span> {{methods[method]['short_spec']}}
                            </td>
                            <td>
                                <pre>{{methods[method]['doc']}}</pre>
                            </td>
                        </tr>
                    {% endfor %}
                </table>
            </body>
        </html>
    '''

    # Pregenerate the JSON and HTML, so that it is done only once
    jsonApi = service.getPrettifiedJSON(methods)
    humanApi = jinja2.Template(template).render(methods = methods)

    # Generate the api() and apih() methods
    @cherrypy.expose
    def api(self):
        '''Returns the API of the class in JSON.
        '''

        return service.setResponseJSON(jsonApi, encode = False)

    @cherrypy.expose
    def apih(self):
        '''Returns the API of the class in HTML (i.e. for humans).
        '''

        return humanApi

    # Add the methods to the class
    cherrypyClass.api = api
    cherrypyClass.apih = apih

    return cherrypyClass

