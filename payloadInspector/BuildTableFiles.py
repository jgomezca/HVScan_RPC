from xml.sax.handler import ContentHandler
from xml.sax import make_parser, SAXException
import re, datetime
'''
Import con handler
'''
from XMLConHandler import conHandler
from payloadUserDB import payloadUserDB
import ConStrParser
from lastIOVSince import LastIOVSince
from EcalCondDB import EcalCondDB


class BuildTableFiles():
    
    def __init__(self,authfile="/afs/cern.ch/cms/DB/conddb/authentication.xml"):
        """parser = make_parser()
        handler = conHandler("",1)
        parser.setContentHandler(handler)
        try:
            parser.parse(authfile)
            self.list = handler.conList
        except Exception, e:
            raise Exception('Can\'t extract connection string from ' + authfile + '\n\tError code: ' + str(e))"""
        #ConStrParser.storeUsers()
        
    def createUsersDB(self):
        ConStrParser.storeUsers()
        
    def buildFiles(self,filter=[],black_list=[]):
        udb = payloadUserDB()
        list = udb.get_distinctConnStr() # udb.getDistinctConnStr deprecated
	print "zzzzzzz:",list
        l = LastIOVSince()
        #TEST: list    = ['oracle://cms_orcoff_prod/CMS_COND_31X_RUN_INFO','oracle://cms_orcoff_prod/CMS_COND_31X_ECAL','oracle://cms_orcoff_prod/CMS_COND_31X_HLT']
        for record in list:
            filterOk = 1
		
            if (filter):
		filterOk	=	0
                for f in filter:
                    if (re.search(f, record)):
                        filterOk = 1

            if (black_list):
                for f in black_list:
                    if (re.search(f, record)):
                        filterOk = 0

            if(filterOk):
                print "\n################ ",record," #############"
		localStartTime 	= 	datetime.datetime.now()
		print "\nstarttime: ",localStartTime
                l.initDB(dbName = str(record))
                print l.writeTable(1)
		localEndTime	=	datetime.datetime.now()	
		print "\nendtime: ",localEndTime
		if ((localEndTime-localStartTime).seconds>5):
			print "@@@@@@@@@@@@@@@@ ",record,"takes about ", (localEndTime-localStartTime).seconds," seconds @@@@@@@@@@@@@@@@@@@@"
                print "\nwriting json: ",record
		print "\nstarttime: ",datetime.datetime.now()
                condDB = EcalCondDB(dbName = str(record))
                #condDB = EcalCondDB(dbName = "oracle://cms_orcoff_prod/CMS_COND_31X_ALIGNMENT")
                containers  = condDB.listContainers()
                print condDB.listContainers_json_writer(content=containers)
		print "endtime: ",datetime.datetime.now(),"\n\n"
    
if __name__ == '__main__':
    #udb = payloadUserDB()
    #print  udb.get_distinctConnStr() 
    btf = BuildTableFiles()
    btf.buildFiles()
    #btf.buildFiles(["CMS_COND_31X_STRIP"])
