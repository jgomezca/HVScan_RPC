'''Common type matching code for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


class MatchError(Exception):
    def __init__(self, message):
        self.args = (message, )


def match(structure, data):
    '''Matches some data to some structure.
    '''

    #-mos TODO: Improve error messages for nested dictionaries/structures.
    #
    #-mos TODO: Since this was designed to match JSON, we could use tuple with
    #           a special meaning and other types like set will not be present
    #           in JSON either. However, if want to make this generic, we should
    #           add a class to match a possible set of matches (i.e. what
    #           the current tuple does), and then add support for iterating
    #           over sets/tuples/etc. in the "value" case (i.e. else) like
    #           it is done now for lists.
    #
    #           i.e. something like:
    #
    #               MatchSet(int, float) instead of (int, float)
    #
    #           so that we can for instance match for sets/tuples themselves:
    #
    #               MatchSet(set([int]), (int, float))

    if type(structure) == tuple:
        # If the type is a tuple, check whether the data matches any of the structures.
        # This can be used to match against several types, values, etc.
        # e.g. 'asdf', 123 and 1.3 matches (int, str, 1.3), but 1.2 does not.

        ok = False
        for item in structure:
            try:
                match(item, data)
                ok = True
                break
            except MatchError:
                pass

        if not ok:
            raise MatchError('%s does not match the expected structure.' % data)

    elif type(structure) == list:
        # If the type is a list, we match all elements in the data against
        # the element of the list.
        # i.e. we only allow here to match an entire list with one structure,
        # so it is not possible to match by position.
        # e.g. [int] means a list of ints so [1,2,3] would match.
        # e.g. [(int, float)] means a list of int or flots so [1,1.2] would match.
        for item in data:
            match(structure[0], item)

    elif type(structure) == dict:
        # If the type is a dictionary, the structure can contain two kinds of
        # keys: values or types. First, keys in data are matched with the values
        # i.e. fixed keys. If found, their value is a tuple (isRequiredKey, value).
        # Value is as usual the structure for the value in the data, and isRequiredKey
        # allows to specify whether this key must be in the data.
        # Then, if a key did not match any of the fixed keys, the key is matched
        # against the types.
        #
        # Example:
        #
        # {
        #     u'myRequiredKey': (True, str),
        #     u'myOptionalKey': (False, int),
        #     unicode: int,
        # }
        #
        # This structure tells that the data dictionary must contain a required
        # key with name myRequiredKey and that its value must be a string.
        # Then, the dictionary may contain myOptionalKey, which in that case
        # its value must be an integer.
        # Finally, other keys of type unicode are allowed, which their value
        # must be of type int.

        fixedKeys = set([x for x in structure.keys() if type(x) != type])
        typeKeys = set([x for x in structure.keys() if type(x) == type])

        requiredFixedKeys = set([x for x in fixedKeys if structure[x][0]])

        for key in data:
            # First try to match the key with the structure's fixed keys, if any.
            if key in fixedKeys:
                requiredFixedKeys.discard(key)
                match(structure[key][1], data[key])
                continue

            # If the key did not match a fixed one, let's try to match it
            # with one of the types, if any.
            if type(key) in typeKeys:
                match(structure[type(key)], data[key])
                continue

            raise MatchError('key %s does not match the expected structure.' % key)

        # Now check that all the required keys were found
        if len(requiredFixedKeys) != 0:
            raise MatchError('keys %s are required and were not found.' % list(requiredFixedKeys))

    elif type(structure) == type:
        # If the type is a type itself, e.g. we match against unicode, we check
        # whether the data is an instance of that type.
        if not isinstance(data, structure):
            raise MatchError('type %s is not and instance of %s.' % (type(data).__name__, structure.__name__))

    else:
        # If the type is not a tuple, dict or list and it is not a type itself,
        # we consider that this is a value so we compare it directly.
        # Note: This is a simple comparison that does not include type checking,
        # e.g. u'a' would match 'a' since u'a' == 'a'.
        if data != structure:
            raise MatchError('%s is not equal to %s.' % (data, structure))


def test():
    import unittest

    class TypeMatchTest(unittest.TestCase):

        def checkMatch(self, structure, good, bad):
            for data in good:
                match(structure, data)
            for data in bad:
                self.assertRaises(MatchError, match, structure, data)

        def test(self):

            self.checkMatch(
                None,
            [
                None,
            ], [
                1,
                1.1,
                'a',
                int,
            ])

            self.checkMatch(
                1,
            [
                1,
            ], [
                2,
                1.1,
                'a',
                int,
            ])

            self.checkMatch(
                'a',
            [
                'a',
                u'a', # since u'a' == 'a'
            ], [
                1,
                1.1,
                'b',
                u'b',
                int,
                None,
            ])

            self.checkMatch(
                u'a',
            [
                'a',
                u'a', # since u'a' == 'a'
            ], [
                1,
                1.1,
                'b',
                u'b',
                int,
                None,
            ])

            self.checkMatch(
                type(None),
            [
                None,
            ], [
                1,
                1.1,
                'a',
                int,
            ])

            self.checkMatch(
                int,
            [
                1,
            ], [
                'asd',
                1.2,
            ])

            self.checkMatch(
                str,
            [
                'a',
            ], [
                1,
                u'a',
            ])


            self.checkMatch(
                (int, float),
            [
                1,
                1.1,
            ], [
                'a',
                u'a',
            ])

            self.checkMatch(
                (int, float, 'a'),
            [
                1,
                1.1,
                'a',
                u'a', # since u'a' == 'a'
            ], [
                'b',
                u'b',
            ])

            self.checkMatch(
                [int],
            [
                [],
                [1, 2, 3],
            ], [
                [1.1],
                [1, 2.2, 3],
                [1, 'a', 3],
            ])

            self.checkMatch(
                [(int, unicode, 2.3)],
            [
                [],
                [1],
                [u'a'],
                [2.3],
                [1, u'a'],
                [1, 2.3],
                [2.3, u'a'],
                [1, u'a', 2.3],
                [u'a', 2.3, 1],
                [5, u'b', 4, u'a', 2.3, 1, 2.3],
            ], [
                [1, 2.2, 3],
                [1, 'a', 3],
                [1, u'a', 'a', 3],
                [1, u'a', u'a', 3, 2.3, float],
            ])

            self.checkMatch(
                {'required': (True, 1), 'optional': (False, str)},
            [
                {'required': 1},
                {'required': 1, 'optional': 'asd'},
                {'required': 1, 'optional': 'sdf'},
            ], [
                {},
                {'required': 'asd'},
                {'optional': 1},
                {'optional': 'asd'},
                {'asd': 'asd'},
                {'required': 1, 'asd': 'asd'},
            ])

            self.checkMatch(
                {'required': (True, float), 'optional': (False, (int, str)), unicode: 3},
            [
                {'required': 1.1},
                {'required': 1.1, 'optional': 1},
                {'required': 1.1, 'optional': 'sdf'},
                {'required': 1.1, u'a': 3},
                {'required': 1.1, 'optional': 1, u'a': 3},
                {'required': 1.1, 'optional': 'sdf', u'a': 3},
                {'required': 1.1, u'a': 3, u'b': 3},
                {'required': 1.1, 'optional': 1, u'a': 3, u'b': 3},
                {'required': 1.1, 'optional': 'sdf', u'a': 3, u'b': 3},
            ], [
                {},
                {'required': 'asd'},
                {'required': 1.1, 'optional': 1.1},
                {'required': 1.1, 'optional': u'asd'},
                {'asd': 3},
                {'required': 1.1, 'asd': 3},
                {'required': 1.1, 'optional': 1, 'asd': 3},
                {'required': 1.1, 'optional': 'sdf', 'asd': 3},
                {'required': 1.1, u'asd': 2},
                {'required': 1.1, 'optional': 1, u'asd': 2},
                {'required': 1.1, 'optional': 'sdf', u'asd': 2},
            ])

            self.checkMatch(
                {int: {unicode: float}},
            [
                {},
                {1: {}},
                {1: {u'a': 1.1}},
                {1: {u'a': 1.1}, 2: {u'b': 1.1, u'c': 3.4}},
            ], [
                {1.1: {}},
                {1: {'a': 1.1}},
                {1: {u'a': 1}},
                {1: {u'a': 1.1}, 2: {u'b': 1.1, u'c': 3.4, 1: 3}},
            ])

    return unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(TypeMatchTest)).wasSuccessful()


if __name__ == '__main__':
    test()

