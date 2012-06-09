from xml.sax.handler import ContentHandler
from xml.sax import make_parser, SAXException
import re 
import copy

class conHandler(ContentHandler):
    '''        
    Overriden SAX ContentHandler for parser
    '''
    
    def __init__(self, searchTerm, useConList=0):
        self.searchTerm = searchTerm
        self.state = 0 # 0 - searching; 1 - DB name obtained; 2 - username obtained
        self.conDict = {}
        
        self.useConList = useConList
        self.conList = [] # Connection list - for retrieving full user list
        
    def startElement(self, name, attrs):
        # getting password
        if self.state == 2:
            self.conDict['password'] = attrs.getValue("value")
            
            if(self.useConList == 1):
                self.conList.append(copy.copy(self.conDict))
                self.state = 0
            else:
                raise SAXException() # stop parsing
        # getting username
        if self.state == 1:
            self.conDict['user'] = attrs.getValue("value")
            self.state = 2
        # getting DB name & schema
        if name == "connection" and (attrs.getValue("name") == self.searchTerm or self.useConList == 1):
            splitedDBConList = re.split(r'//', attrs.getValue("name"))
            splitedDBConList = re.split(r'/', splitedDBConList[1])
            self.conDict['dbName'] = splitedDBConList[0]
            if len(splitedDBConList) == 1 or splitedDBConList[1] == '':   # Checking for schema presence
                self.conDict['schema'] = ''
            else:
                self.conDict['schema'] = splitedDBConList[1]
                
            self.conDict['connStr'] = attrs.getValue("name")
            self.state = 1