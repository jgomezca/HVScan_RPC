import gzip,re
from time import gmtime, strftime
import DLFCN,sys, os, coral
sys.setdlopenflags(DLFCN.RTLD_GLOBAL+DLFCN.RTLD_LAZY)
from pluginCondDBPyInterface import *
from pluginEcalPyUtils import *
from CondCore.Utilities import iovInspector as inspect
from ROOT import TCanvas,TH1F, TH2F, gStyle, TChain, TTree, TLegend, TFile
import EcalPyUtils
import config
from math import sqrt

class EcalCondDB(object):
  
  def __init__(self, dbName = config.ecalCondDB,
              authPath = "/afs/cern.ch/cms/DB/conddb"):
    self.dbName =  dbName
    self.authPath = authPath
    self.inf="4294967295"	
    FWIncantation()
    if dbName.startswith('frontier'):
        self.rdbms = RDBMS('')
        self.db = self.rdbms.getReadOnlyDB(str(dbName))
    else:
        self.rdbms = RDBMS(self.authPath)
        self.db = self.rdbms.getDB(self.dbName)
  
  def __fromXML(filename):
    barrel=barrelfromXML(filename)
    endcap=endcapfromXML(filename)
    return barrel,endcap

  def get_db(self):
      """Return the DB cursor of EcalConDB initialized DB"""
      return self.db

  def get_token(self, tag, since):
      """Return token"""
      try:
	#self.db.startTransaction()
        iov = inspect.Iov(self.db, tag)
	#self.db.commitTransaction()
        iovlist = iov.list()
        tok = ''
        check = False
        for p in iovlist:
            tmpsince=p[1]
            if str(tmpsince) == str(since) :
                tok = p[0]
                check = True
                break
        return tok
        if not check:
            print "Could not retrieve token for tag: " , tag, " since: ", since
            sys.exit(0)
         
      except Exception, er:
        print er

  def get_payload(self, tag='runinfo_35X_mc', since=1268139421):
      """Return payload information"""
      #try:
      #self.db.startTransaction()
      iov = inspect.Iov(self.db, tag)
      #self.db.commitTransaction()
      token = self.get_token(tag, since)       
      #payload=inspect.PayLoad(self.db, token)
      payload = iov.payLoad(int(since))
      #except Exception, er:
      #  print er
      #  payload = 0
      return payload

  def resetDB(self, dbName = config.ecalCondDB,
            authPath = "/afs/cern.ch/cms/DB/conddb"):
    '''Re-initialize the database, given the database name and the authPath '''
   
    FWIncantation()
    self.rdbms = RDBMS(self.authPath)
    self.db = self.rdbms.getDB(self.dbName)
  
  def listTags(self):
    '''List all available tags for a given db '''
    try:
	self.db.startReadOnlyTransaction()
        tags = self.db.allTags()
	self.db.commitTransaction() 
    except:
        return ""
    return tags.split()

  def listContainers(self):
    '''List all containers for a given db '''
    tags    =   self.listTags()
    containers  =   []
    self.db.startReadOnlyTransaction()
    for tag in tags:
        if tag in config.skippedTags:
            print 'Skipped %s' % tag
            continue

        containers.append([str(tag),str(iter(self.db.iov(tag).payloadClasses()).next())])
	L = self.db.iov(tag).payloadClasses();
	#i = iter(L)
	#print "ss: ",i.next()
	#print ".payloadClasses..", str(iter(self.db.iov(tag).payloadClasses()).next())
        #containers.append([str(tag),str(tag)]); 
    self.db.commitTransaction() 
    return containers #tags

  def listContainers_json_writer(self,content=[['tag1', 'ContainerName1'],['tag2', 'ContainerName2']], dbName = None):
    '''Write Json File contaning List of all containers for a given account'''
    if dbName is None:
        dbName = self.dbName
    #accountName =   re.split('(\W+)', self.dbName)
    accountName =   dbName.replace("/","@")
    fileName    =   config.folders.json_dir+"/"+accountName+".json"
    #if os.path.exists(fileName):
	#return "file not written because it exists \n"+fileName
    f=open(fileName, 'w')
    jsonContainer   =   {}
    jsonContainer["CreationTime"]       =   strftime("%d %b %Y %H:%M UTC", gmtime())
    jsonContainer["TAGvsContainerName"] =   content
    jsonContainer["Account"]            =   dbName
    #print jsonContainer
    f.write(str(jsonContainer))
    f.close()
    return "file written in \n"+fileName
  
  def listIovs(self, tag):
    '''List all available iovs for a given tag'''
    
    try :
       #self.db.startTransaction()
       iov = inspect.Iov(self.db,tag)
       #self.db.commitTransaction()
       iovlist = iov.list()
       #print "Available iovs for tag: ",tag
       for p in iovlist:
           #print "  Since " , p[1], " Till " , p[2]
           yield p[1]
     

       # for testing purpose:
    except Exception,er :
        print er
  
  def dumpGzippedXML(self, tag='EcalIntercalibConstants_mc', since=1, fileName='dump.xml.gz'):
    '''Dump record in XML format for a given tag '''  
    
    try :
       #self.db.startTransaction()
       iov = inspect.Iov(self.db,tag)
       token = self.getToken(tag,since)       
       #payload=inspect.PayLoad(self.db,token)
       payload=inspect.PayLoad(self.db,tag, token)
       f = gzip.open(fileName, 'w')
       f.write(str(payload))
       f.close()
       
    except Exception, er:
        raise Exception('Can\'t create XML file: ' + str(er))
  
  def makedist(self, coeff_barl, coeff_endc):

     ebmap = TH2F("EB","EB",360,1,261,171, -85,86)
     eePmap = TH2F("EE","EE",100, 1,101,100,1,101)
     eeMmap = TH2F("EEminus","EEminus",100,1,101,100,1,101)
     ebdist = TH1F("EBdist","EBdist",100,-2,2)
     ebBorderdist = TH1F("EBBorderdist","EBBorderdist",100,-2,2)

     ebeta = TH2F("ebeta","ebeta",171,-85,86,100,-2,2)
     ebphi = TH2F("ebphi","ebphi",360,1,361,100,-2,2)

     eePL = TH2F("EEPL","EEPlus Left",50,10,55,100,-2,2)
     eePR = TH2F("EEPR","EEPlus Right",50,10,55,100,-2,2)
     eeML = TH2F("EEML","EEMinus Left",50,10,55,100,-2,2)
     eeMR = TH2F("EEMR","EEMinus Right",50,10,55,100,-2,2)
     
     for i,c in enumerate(coeff_barl):
         ieta,iphi = EcalPyUtils.unhashEBIndex(i)
         ebmap.Fill(iphi,ieta,c)
         ebdist.Fill(c)
         ebeta.Fill(ieta,c)
         ebphi.Fill(iphi,c)

         if (abs(ieta)==85 or abs(ieta)==65 or abs(ieta)==64 or abs(ieta)==45 or abs(ieta)==44 or abs(ieta)==25 or abs(ieta)==24 or abs(ieta)==1 or iphi%20==1 or iphi%20==0):
             ebBorderdist.Fill(c)


     for i,c in enumerate(coeff_endc):
         ix,iy,iz = EcalPyUtils.unhashEEIndex(i)
         R = sqrt((ix-50)*(ix-50)+(iy-50)*(iy-50))

         if  iz>0:
             eePmap.Fill(ix,iy,c)
             if ix<50:
                 eePL.Fill(R,c,1)
             if ix>50:
                 eePR.Fill(R,c,1)

         if iz<0:
             eeMmap.Fill(ix,iy,c)
             if ix<50:
                 eeML.Fill(R,c,1)
             if ix>50:
                 eeMR.Fill(R,c,1)

     prof_eePL = eePL.ProfileX()
     prof_eePR = eePR.ProfileX()
     prof_eeML = eeML.ProfileX()
     prof_eeMR = eeMR.ProfileX()
     
     return ebmap, ebeta, ebphi, eePmap, ebdist, eeMmap, prof_eePL, prof_eePR, prof_eeML, prof_eeMR, ebBorderdist


  def histo(self, tag, since, filename='histo.root'):
    coeff_barl=[]
    coeff_endc=[]

    if  tag.find(".xml")< 0:
      # try:
         exec('import '+self.db.moduleName(tag)+' as Plug')

         what = {'how':'barrel'}
         w = inspect.setWhat(Plug.What(),what)
         ex = Plug.Extractor(w)
         p=getObject(self.db,tag,since)
	 p.extract(ex)
         coeff_barl = [i for i in ex.values()]


         what = {'how':'endcap'}
         w = inspect.setWhat(Plug.What(),what)
         ex = Plug.Extractor(w)
         p.extract(ex)
         coeff_endc = [i for i in ex.values()]

       #except Exception, er :
         #print er

    else :
       coeff_barl,coeff_endc=EcalPyUtils.fromXML(tag)


    c =  TCanvas("CC distribution")
    c.Divide(2)
    eb = TH1F("EB","EB",100, -2,4)
    ee = TH1F("EE","EE",100, -2,4)

    for cb,ce in zip(coeff_barl,coeff_endc):
       eb.Fill(cb)
       ee.Fill(ce)

    c.cd(1)
    eb.Draw()
    c.cd(2)
    ee.Draw()

    c.SaveAs(filename)
  def plot(self, tag, since, fileName = 'plot.root'):
      '''Invoke the plot function from the wrapper and save to the specified \
       file. The file format will reflect the extension given.'''
      print "\n##### fileName ######:",fileName
    #try:
      #self.db.startTransaction()
      #iov = inspect.Iov(self.db, tag)
      #iovList = iov.list()
      token = self.getToken(tag, since)
      self.db.startReadOnlyTransaction()
      iov = self.db.iov(tag)
      listOfIovElem= [iovElem for iovElem in iov.elements]
      payload = inspect.PayLoad(self.db, tag, listOfIovElem[0])
      #self.db.commitTransaction()
      payload.plot(str(fileName), "", [], [])
    #except Exception, er:
    #  print er
    
  def trend_plot(self, tag, since, fileName = 'plot.root', optional_str = "", array_int = () , array_float = (), array_str = () ):
      '''Invoke the plot function from the wrapper and save to the specified \
       file. The file format will reflect the extension given.'''
      print "\n##### fileName ######:",fileName
      #self.db.startTransaction()
      iov = inspect.Iov(self.db, tag)
      iovList = iov.list()
      token = self.getToken(tag, since)
      payload = inspect.PayLoad(self.db, token)
      #self.db.commitTransaction()
      f=open('gg1', 'w+')
      f.write(str([fileName, optional_str, array_int, array_float, array_str]))
      f.close()
      return payload.trend_plot(fileName, optional_str, array_int, array_float, array_str)

      
  def compare(self, tag1, since1, tag2, since2): 
    '''Produce comparison plots for two records. '''
    coeff_1_b=[]
    coeff_2_b=[]

    coeff_1_e=[]
    coeff_2_e=[]   
    
    if tag1.find(".xml") < 0:
      try:
        modName = str(db.payloadModules(tag1)[0])
	Plug = __import__(modName)
	#exec 'import ' + self.db.moduleName(tag1) + ' as Plug'
        what = {'how':'barrel'}
        w = inspect.setWhat(Plug.What(), what)
        ex = Plug.Extractor(w)
        p = self.getObject(tag1, since1)
        p.extract(ex)
        coeff_1_b = [i for i in ex.values()]# first set of coefficients
        what = {'how':'endcap'}
        w = inspect.setWhat(Plug.What(),what)
        ex = Plug.Extractor(w)
        p.extract(ex)
        coeff_1_e = [i for i in ex.values()]# first set of coefficients
      except Exception, er :
        print er
    else:
      coeff_1_b,coeff_1_e = __fromXML(tag1)
    
    if tag2.find(".xml") < 0:
      try:
        modName = str(db.payloadModules(tag2)[0])
	Plug = __import__(modName)
	#exec 'import ' + self.db.moduleName(tag2) + ' as Plug'
        what = {'how':'barrel'}
        w = inspect.setWhat(Plug.What(), what)
        ex = Plug.Extractor(w)
        p = self.getObject(tag2, since2)
        p.extract(ex)
        coeff_2_b = [i for i in ex.values()]# 2nd set of coefficients
        what = {'how':'endcap'}
        w = inspect.setWhat(Plug.What(), what)
        ex = Plug.Extractor(w)
        p.extract(ex)
        coeff_2_e = [i for i in ex.values()]# first set of coefficients
      except Exception, er :
        print er
    else:
      coeff_2_b,coeff_2_e = __fromXML(tag2)    
    return coeff_1_b, coeff_1_e, coeff_2_b, coeff_2_e
    
  def getToken(self, tag, since):
    ''' Return payload token for a given tag'''
    try:
      #self.db.startTransaction()
      iov = inspect.Iov(self.db, tag)
      #self.db.commitTransaction()
      iovlist = iov.list()
      for p in iovlist:
        tmpsince=p[1]
        if str(tmpsince) == str(since) :
          print str(tmpsince) + '=' + str(since)
          return p[0]
        else:
          continue
      print "Could not retrieve token for tag: " , tag, " since: ", since
      #@TODO: change sys.exit!
      #sys.exit(0)
        
    except Exception, er:
      print er

  def getWhatForTag(self,tag):
        what = inspect.extractorWhat(self.db,tag)
        return what
  
  def getTrendForTag(self, tag = 'EcalADCToGeVConstant_2009runs_express', what={'how':'barrel'}):
        #self.db.startTransaction()
	iov = inspect.Iov(self.db, tag)
        what = inspect.extractorWhat(self.db,tag)
	#self.db.commitTransaction()
        #return str(what)
	#what={}
	#what = {'how':'barrel'}
        #if (what == {}):
        #    what = {}
        #else:
        #    what = {'how': what['how'][1][1]}
        #return what
        return iov.trend(what)
      
  def getObject(self, tag, since):
  	''' Return payload object for a given iov, tag, db'''
    	found=0
    	object = 0
    	try:
 		modName = str(db.payloadModules(tag)[0])
		Plug = __import__(modName)
		#exec 'import ' + self.db.moduleName(tag) + ' as Plug'
      		self.db.startTransaction()
		object = Plug.Object(db)  
      		for elem in self.db.iov(tag).elements:       
        		if str(elem.since())==str(since):
          			found=1
	  			object.load(elem)
		self.db.commitTransaction()
      		return object
 	except Exception, er:
		print er

	if not found:
		print "Could not retrieve payload for tag: " , tag, " since: ", since
		sys.exit(0)

  def trendPlotAdv(self,
                      own_tag,
                      own_since,
                      own_pngName,
                      own_authPath,
                      target_dbName,
                      target_tag,
                      target_since,
                      target_until,
                      target_authPath = "/afs/cern.ch/cms/DB/conddb",
                      opt_string = "test"):
                      #array_int = [],
                      #array_float = [],
                      #array_str = []):
    """for getting objects which can be in other database(!) from since to till"""
    target_condDB = EcalCondDB(dbName =target_dbName)
    target_since = int(target_since)
    target_until = int(target_until)
    iovs = target_condDB.listIovs(target_tag)
    array_str = [target_dbName, target_authPath]
    array_float = []
    array_int = []
    for i in iovs:
      if (( i >= target_since) and (i <= target_until)):
        array_float.append(i)
        array_str.append(target_condDB.get_token(target_tag, i))
    return self.trend_plot(own_tag, own_since, own_pngName, opt_string, array_int, array_float, array_str)

  def trendPlot(self, tag,
                  since,
                  until,
                  pngName):
    """for getting multiple objects from since to till"""
    
    return self.trendPlotAdv(
                      own_tag = tag,
                      own_since = since,
                      own_pngName = pngName,
                      own_authPath = self.authPath,
                      target_dbName = self.dbName,
                      target_tag = tag,
                      target_since = since,
                      target_until = until,
                      target_authPath = self.authPath
                      )


if __name__ == "__main__":
    condDB = EcalCondDB(dbName = config.ecalCondDB)
    containers  = condDB.listContainers()
    print condDB.listContainers_json_writer(content=containers)
    
    #tag = 'EcalIntercalibConstantsRcd'
    #tag = 'EcalIntercalibConstantsMC_EBg50_EEwithB'
    #since = "1"

    #condDB.histo(tag, since, 'test_1_histo.png')
    #condDB.plot(tag, since, 'test_1_plot.png')
    #condDB = EcalCondDB(dbName = "oracle://cms_orcoff_prod/CMS_COND_34X_ECAL")
    #condDB.dumpGzippedXML(tag='EcalPedestals_mc', since=1, fileName='dump.xml.gz')

