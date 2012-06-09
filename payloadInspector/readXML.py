 # -*- coding: utf-8 -*-
'''
Created on 2011.05.20

@author: Antonio Pierro
'''

from xml.dom.minidom import parseString
import json, re
import config

class readXML():
    def __init__(self):
	self.authfile	=	[
                #"/afs/cern.ch/cms/DB/conddb/readOnlyArch.xml",
                "/afs/cern.ch/cms/DB/conddb/readOnlyProd.xml",
                "/afs/cern.ch/cms/DB/conddb/readWritePrep.xml"
        ]
	self.dbMap	=	{
		config.baseDBUrl: "Offline Production",
		#"oracle://cms_orcon_prod":"Online Production",
		#"oracle://cms_orcon_prep":"Online Preparation",
		"oracle://cms_orcoff_prep":"Offline Preparation",
		#"oracle://cmsarc_lb":"Archive"
	}
	self.dbMap_reverse	=	dict((v,k) for k, v in self.dbMap.iteritems())

    def get_connectionName(self):
	fContener	=	""
	for fName in self.authfile:
		fContener	+=	open(fName,'r').read()
	fContener	=	'<?xml version="1.0"?><connections>'+fContener+'</connections>'
	document 	= 	parseString(fContener.encode("utf-8"))
	names 		= 	[]
	for connection in document.getElementsByTagName('connection'):
		connectionName	=	connection.getAttribute('name')	
		if connectionName.find("cms_orcon_adg") == -1 and connectionName.find("cms_orcon_") != -1: continue
		if connectionName.find("devdb10/CMS_COND_STRIP") != -1: continue
		if connectionName.find("CMS_COND_WEB") != -1: continue
		if connectionName.find("POPCONLOG") != -1: continue
		if connectionName.find("FRONTIER") != -1: continue
		if connectionName.find("_30X_") != -1: continue
		if connectionName.find("_20X_") != -1: continue
		if connectionName.find("_21X_") != -1: continue
		if connectionName.find("_18X_") != -1: continue
		if connectionName.find("_CSA07_") != -1: continue
		if connectionName.find("CMS_COND_RPC") != -1: continue
		#if connectionName.find("CMS_COND_GEOMETRY") != -1: continue
		names.append(connectionName)
	return names

    def get_connectionNameMasked(self, dbFilter=""):
	fContener	=	""
	for fName in self.authfile:
		fContener	+=	open(fName,'r').read()
	fContener	=	"<?xml version=\"1.0\" encoding=\"UTF-8\" ?><connections>" + str(fContener) + "</connections>"
	document 	= 	parseString(fContener)
	names 		= 	{'connection names': []}
	for connection in document.getElementsByTagName('connection'):
		connectionName	=	connection.getAttribute('name')	
		if (connectionName.find('_FRONTIER')!=-1 or connectionName.find('_21X_')!=-1 or connectionName.find('_18X_')!=-1 or connectionName.find('_20X_')!=-1 or connectionName.find('_30X_')!=-1 or connectionName.find('_CSA07_')!=-1):
			continue
		connectionName	=	self.get_dbVsAccount(connectionMasked=connectionName)
		try:
			connectionName	=	[self.get_dbMask(connectionName[0]),connectionName[1]]
		except:
			print "ERROR: get_connectionNameMasked except",connectionName
		if dbFilter != "" and connectionName[0] == dbFilter:
 			names['connection names'].append(connectionName)
		if dbFilter == "":
			names['connection names'].append(connectionName)
	return names
   
    def get_fileName(self, dbName='Offline Production', acc='31X_ECAL'):
	fileName	=	self.dbMap_reverse[dbName]+"_CMS_COND_"+acc
	fileName	=	re.sub(r'(://|/)', '_', fileName) + '.html'
	return	fileName

    def get_fileNameIov(self, dbName='Offline Production', acc='31X_ECAL', tagname='EcalLaserAPDPNRatios_v5_online'):
	fileName	=	self.dbMap_reverse[dbName]+"_CMS_COND_"+acc+'_'+tagname
	fileName	=	re.sub(r'(://|/)', '_', fileName) + '.html'
	return	fileName


    def get_dbs(self):
	dbs	= [{"DBID":self.dbMap[x],"DB":self.dbMap[x]} for x in self.dbMap]
	return dbs

    def get_dbVsAccount(self,connectionMasked=config.baseDBUrl + "/CMS_COND_43X_ECAL"):
	return connectionMasked.split("/CMS_COND_")

    def get_dbMask(self,dbName=config.baseDBUrl + "/"):
	for dbN	in self.dbMap:
		if dbN==dbName:
			return self.dbMap[dbN] 
	return dbName

if __name__ == "__main__":
	c = readXML()
	print c.get_dbVsAccount()
	#print c.get_dbs()
	#print json.dumps(c.get_connectionNameMasked(dbFilter="Offline Production"))
	#print c.get_fileName()
	print c.get_connectionName()
    
