#!/usr/bin/env python

import sys
import netrc
from pprint import pprint

sys.path.append('.')
import modules.PyCurler as PyCurler

class LogDbReader(object):

    def __init__(self):

        self.c = PyCurler.Curler()
        self.baseUrl = 'https://mos-dev-slc6.cern.ch/dropBox/'

    def login(self) :
        nrc = netrc.netrc( )
        (login, account, password) = nrc.authenticators( 'newOffDb' )

        url = self.baseUrl + '/signIn'
        response = self.c.get( url, [ ('username', login), ('password', password) ] )

        msg = '\n'.join( response ).strip( )
        if msg :
            print( ' -- login returned: %s ' % (msg,) )
        else :
            print( ' -- login OK ' )

        return

    def getInfo(self):

        self.login()

        url = self.baseUrl + 'dumpDatabase'

        ret = self.c.get(url)

        print "got :"
        pprint( ret )

        return

def main():

    ldr = LogDbReader()
    ldr.getInfo()

if __name__ == '__main__':
    main()
