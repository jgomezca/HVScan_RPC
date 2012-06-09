'''
Created on 2009.07.06
'''

from xml.sax.handler import ContentHandler
from xml.sax import make_parser, SAXException
import re 

'''
Import con handler
'''
from XMLConHandler import conHandler
from payloadUserDB import payloadUserDB
    
def extract(searchTerm, authfile='./authentication.xml'):
    '''
    Obtains DB connection string from xml file

    @var searchTerm1: DB name for which connection string is constructed
    @var authfile: xml file name where stored connection data
    
    @return: tuple ('connectionString', 'user', 'schema')
    '''
    
    parser = make_parser()
    handler = conHandler(searchTerm)
    parser.setContentHandler(handler)
    try:
        parser.parse(authfile)
    except Exception, e:
        if 'password' in handler.conDict:
            connectionString = str(handler.conDict['user']+'/'+handler.conDict['password']+'@'+handler.conDict['dbName'])           
            connectionDict = {'connectionstring': connectionString, 'user':str(handler.conDict['user']), 'schema': str(handler.conDict['schema'])}
            return connectionDict
        else:
            raise Exception('Can\'t extract connection string from ' + authfile + '\n\tError code: ' + str(e))
    
    return None

       
def storeUsers(authfile='./authentication.xml'):
    '''
    Stores all users from xml file to DB, skips duplicates

    @var authfile: xml file name where stored connection data
    
    @return: none
    '''
    
    parser = make_parser()
    handler = conHandler("",1)
    parser.setContentHandler(handler)
    try:
        parser.parse(authfile)
        udb = payloadUserDB()
        udb.createUserDB()
        udb.storeUsers(handler.conList)
    except Exception, e:
        #print handler.conList
        print e
        if 'password' in handler.conDict:
            connectionString = str(handler.conDict['user']+'/'+handler.conDict['password']+'@'+handler.conDict['dbName'])           
            connectionDict = {'connectionstring': connectionString, 'user':str(handler.conDict['user']), 'schema': str(handler.conDict['schema'])}
            return connectionDict
        else:
            raise Exception('Can\'t extract connection string from ' + authfile + '\n\tError code: ' + str(e))
    
    return None

if __name__ == '__main__':
    ret = storeUsers()
