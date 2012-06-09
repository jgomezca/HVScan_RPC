#
#Authors: Antonio Pierro & Salvatore Di Guida
#
import DLFCN,sys
sys.setdlopenflags(DLFCN.RTLD_GLOBAL+DLFCN.RTLD_LAZY)
from pluginCondDBPyInterface import *
from CondCore.Utilities import iovInspector as inspect
from Integration import Integration
import config

class CondDB_WebWrapper(object):
	def __init__(	self,
			dbName		=	config.ecalCondDB,
			authpath	=	'/afs/cern.ch/cms/DB/conddb'	
	):
		self.dbName	=	dbName
		self.authpath	=	authpath
		self.a 		= 	FWIncantation()
		self.rdbms      =       RDBMS(authpath)

	
	def get_list_tag(self):
		db 	= 	self.rdbms.getDB(self.dbName)
		db.startTransaction()
    		tags	=	db.allTags()
		db.commitTransaction()
		list_tags	=	[{'TAG_NAME': 'EcalADCToGeVConstant_2009runs_express'}, {'TAG_NAME':'EcalADCToGeVConstant_2009runs_hlt'}]
		return tags.split(" ") 
		return EcalCondTools.listTags

	def histo_json(self,list_histo=[['2','3','4'],[2,5,1]],title_text='HISTO',tag='EcalADCToGeVConstant_2009runs_express',RMS=0,ENTRIES=0,MEAN=0):
		X_VALUES	=	list_histo['y1'][0]
		Y_VALUES	=	list_histo['y1'][1]
		STEP_Y		=	len(Y_VALUES)*5.5
		STEP_X		=	len(X_VALUES)*5.5
		tag	=	"\nTAG:\t"+tag
		tag	+=	"\nENTRIES:\t"+str(list_histo['ENTRIES'])+"\nRMS:\t"+str(list_histo['RMS'])+'\nMEAN:\t'+str(list_histo['MEAN'])
		histo_json_output	=	"""{
    "bg_colour": "#FAFAFA",
    "title": {
        "text": " """+title_text+""" ",
        "style": "{font-size: 20px;}" 
    },
    "y_legend": {
        "text": "Occurency",
        "style": "{font-size: 12px; color:#736AFF;}" 
    },
    "y_axis": {
        "max": """+str(max(Y_VALUES))+""",
        "steps": """+str(STEP_Y)+""" 
    },
    "x_axis": {
        "steps": """+str(STEP_X)+""",
        "labels": {
            "rotate": -45,
            "labels": """+str(X_VALUES).replace("'","\"")+""" 
        } 
    },
    "elements": [
        {
            "type": "line",
            "tip": "#key#<br>Value: #val#, Date: #x_label#",
            "colour": "#8B008B",
            "text": " """+tag+""" ",
            "values" : """+str(Y_VALUES).replace("'","\"")+""" 
        } 
    ]
    };
		"""	
		return histo_json_output
	
	def histo(self, tag='EcalIntercalibConstantsMC_EBg50_EEnoB',since=1,till=4294967295,definition=30):
		#print "TILL: ",till
    		'''Make histograms. tag can be an xml file'''
		db 	= 	self.rdbms.getDB(self.dbName)
		db.startTransaction()
    		coeff_barl=[]
    		coeff_endc=[]
    		if  tag.find(".xml")< 0:
        		try:  
          			#exec('import '+db.moduleName(tag)+' as Plug')
				modName = str(db.payloadModules(tag)[0])
				Plug = __import__(modName)
          			what 	= 	{'how':'barrel'}
          			w 	= 	inspect.setWhat(Plug.What(),what)
          			ex 	= 	Plug.Extractor(w)
          			p	=	self.getObject(db,tag,since)
          			p.extract(ex)
          			coeff_barl = [i for i in ex.values()]


          			what = {'how':'endcap'}
          			w = inspect.setWhat(Plug.What(),what)
          			ex = Plug.Extractor(w)
          			p.extract(ex)
          			coeff_endc = [i for i in ex.values()]     

        		except Exception, er :
          			print er 

    		else :
        		coeff_barl,coeff_endc=EcalPyUtils.fromXML(tag)

		test = Integration(coeff_barl)
		db.commitTransaction()
		
		histo_obj		=	{}
		try:
			histo_obj['test']	=	dir(test)
			histo_obj['full']	=	test.result(definition)
			histo_obj['y1']		=	test.result(definition)[0]
			histo_obj['y2']		=	test.result(definition)[1]
			histo_obj['RMS'] 	=	test.rms()
			histo_obj['ENTRIES'] 	=	test.entries()
			histo_obj['MEAN'] 	=	test.mean()
			print histo_obj['y1']
	        except:
			histo_obj['test']	=       {}	
			histo_obj['full']	=	[]
			histo_obj['y1']		=	[["1","2"],["1","2"]]
			histo_obj['y2']		=	[["1","2"],["1","2"]]
			histo_obj['RMS']	=	0
			histo_obj['ENTRIES']	=	0
			histo_obj['MEAN']	=	0
			print "Object has no attribute result"
						

		return histo_obj['test']
		return test.result(definition)[0]
		return [(coeff_barl),(coeff_endc)]

	def getObject(self,db,tag,since):
    		''' Return payload object for a given iov, tag, db'''
    		found	=	0
    		try:
       			object = 0
			#exec('import '+db.moduleName(tag)+' as Plug')  
       			db.startTransaction()
			modName = str(db.payloadModules(tag)[0])
			Plug = __import__(modName)
			for elem in db.iov(tag).elements :       
           			if str(elem.since())==str(since):
               				found=1
               				object = Plug.Object(elem)
           		db.commitTransaction()
			return object
    		except Exception, er :
        		print er

    		if not found :
        		print "Could not retrieve payload for tag: " , tag, " since: ", since
        		sys.exit(0)

	
	def listIovs(self,tag='EcalIntercalibConstantsMC_EBg50_EEnoB'):
		db 		= 	self.rdbms.getDB(self.dbName)
		iov_list	=	[]
    		try :
       			#db.startTransaction()
			iov = inspect.Iov(db,tag)
       			iovlist = iov.list()
			#db.commitTransaction()
       			#print "Available iovs for tag: ",tag
       			for p in iovlist:
				iov_list.append([p[1],p[2]])
			iov	=	0
     
    		except Exception,er :
        		print er 
		db	=	0	
		return iov_list

if __name__=="__main__":
	C 	= 	CondDB_WebWrapper()
	#print	C.get_list_tag()
	print C.listIovs(tag='EcalIntercalibConstantsMC_EBg50_EEnoB')
	# EcalTimeCalibConstants_mc, EcalIntercalibConstantsMC_EBg50_EEnoB
	histo_obj	=	C.histo(tag='EcalChannelStatus_AllCruzet_online', since=1,till=4294)
	print histo_obj 
	#histo_obj	=	C.histo(tag='EcalIntercalibConstantsMC_EBg50_EEnoB', since=1,till=4294)
	#print C.histo_json(list_histo=C.histo(since=1,till=4294))
	#histo_test	=	[['0.394739896059', '0.47954299897', '0.56434610188', '0.649149204791', '0.733952307701', '0.818755410612', '0.903558513522', '0.988361616433', '1.07316471934', '1.15796782225', '1.24277092516', '1.32757402807', '1.41237713099', '1.4971802339', '1.58198333681', '1.66678643972', '1.75158954263', '1.83639264554', '1.92119574845', '2.00599885136'], [1, 0, 12, 175, 2078, 9975, 17279, 16719, 9121, 4674, 1024, 113, 16, 2, 3, 2, 2, 2, 1, 1]]
	#print C.histo_json(list_histo=histo_obj)



