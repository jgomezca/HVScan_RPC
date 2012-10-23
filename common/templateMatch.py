'''Common template matching code for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import re


class MatchError(Exception):
    def __init__(self, message):
        self.args = (message, )


def match(template, text):
    '''Matches a template with a text.

    The template specifies placholders with %s (which match the same as re's \S+,
    i.e. strings of at least one caracter without whitespace in them).

    This makes easier to write simple templates/regexes to match logs in tests
    without having to manually write/escape regexes.
    '''

    if not re.match('^%s$' % '\S+'.join([re.escape(x) for x in template.split('%s')]), text):
        raise MatchError('Text %s does not match template %s.' % (repr(text), repr(template)))


def test():
    import unittest

    class TemplateMatchTest(unittest.TestCase):

        def checkMatch(self, template, good, bad):
            for data in good:
                match(template, data)
            for data in bad:
                self.assertRaises(MatchError, match, template, data)

        def test(self):

            self.checkMatch(
                'test',
            [
                'test',
            ], [
                '',
                'tes',
                'testt',
                'text',
            ])

            self.checkMatch(
                'test %s',
            [
                'test a',
                'test 1',
                'test aa',
                'test a1',
            ], [
                '',
                'tes',
                'text',
                'test ',
                'test a ',
                'test a a',
            ])

            self.checkMatch(
                '%s',
            [
                'a',
                'aa',
                'aaa',
            ], [
                '',
            ])

            self.checkMatch(
                '%s%s',
            [
                'aa',
                'aaa',
            ], [
                '',
                'a',
            ])

    return unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(TemplateMatchTest)).wasSuccessful()


if __name__ == '__main__':
    test()

