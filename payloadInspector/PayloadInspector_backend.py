 # -*- coding: utf-8 -*-
"""
CondDB Payload Inspector
Author: Antonio Pierro, Salvatore Di Guida, Aidas Tilmantas
"""
import re
import os
import sys
import json

import cherrypy

from CondDB_WebWrapper import *
import CondDB_Utils, EcalCondDB
import payloadUserDB
import lastIOVSince
#import bugReveal
#from backend_utils import *
#import StripPlot
import SubdetectorFactory
from optparse import OptionParser
import DBDataMasker as dm

import traceback
import ArgumentValidator as av
import tempfile
import tarfile
import cmpPNG
import datetime
#from XMLdiff import diff_match_patch
#from diff_match_patch import diff_match_patch

import config
import re

import service
import api

#from PIL import Image, ImageChops
from readXML import *

PAGES_DIR = "pages"


def getFrontierConnectionString(account, level, short = False):
        '''Returns a connection string from the secrets given its account name
        and the production level.
        '''

        return service.getFrontierConnectionString({
            'account': account,
            'frontier_name': service.secrets['connections'][level]['frontier_name'],
        }, short = short)


@api.generateServiceApi
class CondDBPayloadInspector:
    ''' Sample request handler class. '''
    def __init__(self):
        self.Records		=	[]
        self.__ecalCondDB = EcalCondDB.EcalCondDB()
        self.__condDB_Utils = CondDB_Utils.CondDB_Utils()
        self.__payloadUserDB = payloadUserDB.payloadUserDB(db_file=config.db_data.users_db_conn_str)
        self.tablePath = config.folders.table_dir
        self.iovTablePath = config.folders.iov_table_dir
        self.masker = dm.Masker()
        self.iov_table_name = config.folders.iov_table_name
        self.tag_table_name = config.folders.tag_table_name
        self.__plotsdir = config.folders.plots_dir
        self.__trendplotsdir = config.folders.trend_plots_dir
        self.__histodir = config.folders.histo_dir
        self.__xmldir = config.folders.xml_dir
        self.__tmpdir = config.folders.tmp_dir

    @cherrypy.expose
    def index(self, *args, **kwargs):
        if len(args) == 1:
            if "get_summaries.html" in args:
                cherrypy.response.headers['Content-Type'] = 'text/html'
                return open(os.path.join(PAGES_DIR, 'get_summaries.html'), "rb").read()
            elif "get_plot_list.html" in args:
                cherrypy.response.headers['Content-Type'] = 'text/html'
                return open(os.path.join(PAGES_DIR, 'get_plot_list.html'), "rb").read()
            elif "get_xml.html" in args:
                cherrypy.response.headers['Content-Type'] = 'text/html'
                return open(os.path.join(PAGES_DIR, 'get_xml.html'), "rb").read()
            elif "get_trend_plot.html" in args:
                cherrypy.response.headers['Content-Type'] = 'text/html'
                return open(os.path.join(PAGES_DIR, 'get_trend_plot.html'), "rb").read()
            elif "get_plot_cmp.html" in args:
                cherrypy.response.headers['Content-Type'] = 'text/html'                
                return open(os.path.join(PAGES_DIR, 'get_plot_cmp.html'), "rb").read()
            elif "get_histo.html" in args:
                cherrypy.response.headers['Content-Type'] = 'text/html'
                return open(os.path.join(PAGES_DIR, 'get_histo.html'), "rb").read()
        else:
            return open(os.path.join(PAGES_DIR, 'mainPage.html'), "rb").read()
  
    #seems to be useless since only tags for ecal are shown
    @cherrypy.expose
    def get_list_tags(self):
        tags = self.__ecalCondDB.listTags()
        return self.__condDB_Utils.createJSON('tags', tags)

    @cherrypy.expose
    def get_tagsVScontainer(self,dbName=config.rpcCondDB):
        #accountName =   re.split('(\W+)', dbName)[-1]
	accountName =   dbName.replace("/","@")
        try:
	    print "@@@@@@@@: ",config.folders.json_dir+"/"+accountName+".json"
            tagsVScontainerContents =   open(config.folders.json_dir+"/"+accountName+".json").read()
        except IOError:
            tagsVScontainerContents =   "{'key':'value'}"
        return json.dumps(eval(tagsVScontainerContents))
    
    #don't expose this, since big number of requests for timestamp conversion might overload the server
    #@cherrypy.expose
    def get_human_date(self, timestamp = None, lumiid = None, format = None):
        if not format:
            format = config.general.date_format
        try:
            if timestamp != None:
                return datetime.datetime.fromtimestamp(int(timestamp) >> 32).strftime(format)
            elif lumiid != None:
                return 'RUNNMBR: %d, LUMISECTION: %d' % (int(lumiid) >> 32, int(lumiid) & 0XFFFFFFFF)
        except:
            return ''
    
    @cherrypy.expose
    def get_timetype(self, dbName = '', acc='', tag = ''):
        self.check_dbName_acc(dbName, acc, '1');
        try:
            c = readXML()
            db      =       str(c.dbMap_reverse[dbName]+"/CMS_COND_"+acc)
            vtag    =       str(tag)
            iov = lastIOVSince.LastIOVSince(dbName = db)
            return str(iov.iovSequence(tag = vtag).timetype())
        except:
            return ''

    def check_dbName_acc(self, dbName, acc, since):
        if dbName in service.secrets['connections']:
            if acc in service.secrets['connections'][dbName]['accounts']:
                splitedSince = since.split(";");
                p = re.compile('[0-9]*$')
                for i in splitedSince:
                    m = p.match(i)
                    if m:
                        pass
                    else:
                        raise cherrypy.HTTPError(405, "Bad Since Value !!!!!")
                return "OK"
            else:
                raise cherrypy.HTTPError(405, "Bad Account Name !!!!!")
        else:
            raise cherrypy.HTTPError(405, "Bad DB Name !!!!!")    
        
    def get_decorated_since(self, db, acc, tag, since):
        self.check_dbName_acc(db, acc, since);  
        #raise Exception(str(self.get_timetype(dbName = db, acc = acc, tag = tag)).lower())
        if str(self.get_timetype(dbName = db, acc = acc, tag = tag)).lower() == 'timestamp':
            return self.get_human_date(timestamp = since)
        elif str(self.get_timetype(dbName = db, acc = acc, tag = tag)).lower() == 'lumiid':
            return self.get_human_date(lumiid = since)
        return since
    
    @cherrypy.expose
    def get_tag_table(self, dbName, acc):
        self.check_dbName_acc(dbName, acc, '1');
        tmpdb = self.masker.unmask_dbname(dbName)
        tmpacc = self.masker.unmask_schema(tmpdb, acc)
        db = av.get_validated_dbname(value = tmpdb, acc = tmpacc)
        f = open(os.path.join(SubdetectorFactory.getDirectory(dbName = db, 
                                basedir = self.iovTablePath, default = True), self.tag_table_name), 'r')
        data = f.read()
        f.close()
        return data
        
    #NOT WORKING, tag is not initialised. tag probably has to be passed as argument
    #@cherrypy.expose
    def getTrendForTag(self, what):
        #these tags were used to reveal problems
        tag1 = 'EcalADCToGeVConstant_2009runs_express'
        tag2 = 'EcalIntercalibConstantsMC_EBg50_EEnoB'
        trend = self.__ecalCondDB.getTrendForTag(tag, what)
        return str(trend)
    
    @cherrypy.expose
    def getWhatForTag(self, tag="EcalADCToGeVConstant_2009runs_express"):
        return str(self.__ecalCondDB.getWhatForTag(tag))
    
    @cherrypy.expose
    def listIovs(self,tag='EcalIntercalibConstantsMC_EBg50_EEnoB'):
        from itertools import izip
        tok		=	('since','till')
        val		=	CondDB_WebWrapper().listIovs(tag)
        listIovs_json 	= 	map(lambda pair: dict(izip(tok,pair)), val)
        return str(listIovs_json)
 
    #NOT WORKING
    #@cherrypy.expose
    def histo(self,tag='EcalIntercalibConstantsMC_EBg50_EEnoB',since=1,till=4294967295,definition=50):
        definition	=	int(definition)
        title_text	=	"HISTO"
        #return str(CondDB_WebWrapper().histo(tag,since,till,definition))
        histo_test	=	[['0.394739896059', '0.47954299897', '0.56434610188', '0.649149204791', '0.733952307701', '0.818755410612', '0.903558513522', '0.988361616433', '1.07316471934', '1.15796782225', '1.24277092516', '1.32757402807', '1.41237713099', '1.4971802339', '1.58198333681', '1.66678643972', '1.75158954263', '1.83639264554', '1.92119574845', '2.00599885136'], [1, 0, 12, 175, 2078, 9975, 17279, 16719, 9121, 4674, 1024, 113, 16, 2, 3, 2, 2, 2, 1, 1]]
        histo_test	=	CondDB_WebWrapper().histo(tag,since,till,definition)
        return CondDB_WebWrapper().histo_json(histo_test,title_text,tag)
    
    @cherrypy.expose
    def get_dbs(self):
	return json.dumps([{'DBID': x, 'DB': x} for x in service.secrets['connections'].keys()])

    @cherrypy.expose
    def getDBs(self):
        dbs = self.__payloadUserDB.getDBs()
        dbs = [{x[x.keys()[0]]:self.masker.mask_dbname(x[x.keys()[0]])} for x in dbs]
        return self.__condDB_Utils.createJSON('dbs', dbs)

    @cherrypy.expose
    def get_cmsswReleas(self):
        try:
                return  os.environ['CMSSW_RELEASE']
        except KeyError:
                raise ImportError('CMSSW not set correctly')
        except:
                raise ImportError('????')
        return "I am ListTags backend!"
    
    #hardcoded values, probably should be replaced with environment information
    #@cherrypy.expose
    def getReleases(self):
        releases = [{'release' : 'CMSSW_3_3_1'}, {'release' : 'CMSSW_3_3_2'}]
        return self.__condDB_Utils.createJSON('releases', releases)

    #is not needed, if exposed accounts have to be masked
    #(now masked as schemas, if different mask is needed another methods have to be inplemented)
    #@cherrypy.expose
    def getAccounts(self, db=""):
        self.check_dbName_acc(db, "31X_ECAL", '1'); 
        dbname = self.masker.unmask_dbname(db = db)
        dbname = av.get_validated_dbname(value = dbname)
        accounts = self.__payloadUserDB.getUsers(dbNameSearch=dbname)
        accounts = [{x[x.keys()[0]]:self.masker.mask_schema(db = dbname, schema = x[x.keys()[0]])} for x in accounts]
        #return str(accounts)
        return self.__condDB_Utils.createJSON('accounts', accounts)

    @cherrypy.expose
    def get_schemas(self, db = ""):
        return json.dumps([{'Account': x} for x in service.secrets['connections'][db]['accounts']])

    @cherrypy.expose
    #def getSchemas(self, db=""):
    def getSchemas(self, db="",rn=""):
        self.check_dbName_acc(db, "31X_ECAL", '1');
        dbname = self.masker.unmask_dbname(db = db)
        dbname = av.get_validated_dbname(value = dbname)
        schemas = self.__payloadUserDB.getSchemas(dbNameSearch=dbname) 
        if rn=="vs":
            return self.__condDB_Utils.createJSON('schemas', schemas)
        schemas = [{x[x.keys()[0]]:self.masker.mask_schema(db = dbname, schema = x[x.keys()[0]])} for x in schemas]
        #return str(schemas)
        return self.__condDB_Utils.createJSON('schemas', schemas)

    #Useless method, leaving it for now, but it is better to remove it later
    @cherrypy.expose
    def getSummary(self, dbName='', acc='', tag = '', since=''):
        self.check_dbName_acc(dbName, acc, since); 
        '''Return payload summary'''
        # temporary:
        return self.get_summary(dbName, acc, tag, since)

    #Exposing method that generates something isn't very secure
    #@cherrypy.expose 
    def buildLastIOVTable(self, dbName='', acc=''):
        self.check_dbName_acc(dbName, acc, '1');
        #db = self.masker.unmask_dbname(db = dbName)
        #db = av.get_validated_dbname(value = db, acc = self.masker.unmask_schema(db, acc))
	c = readXML()
	db	=	str(c.dbMap_reverse[dbName]+"/CMS_COND_"+acc)
        lastIOV = lastIOVSince.LastIOVSince(dbName=db)
        lastIOV.writeTable()
        return "done"

    @cherrypy.expose
    def get_lastIovTable(self, dbName='Offline Production', acc='31X_ECAL'):
        self.check_dbName_acc(dbName, acc, '1');
        fileName = 'frontier_%s_%s.html' % (service.secrets['connections'][dbName]['frontier_name'], acc)
        return open(os.path.join(self.tablePath, fileName), "r").read()

    @cherrypy.expose
    def get_iovContent(self, dbName='Offline production', acc='ECAL LAS for 311X',tagname='EcalLaserAPDPNRatios_v5_online'):
        self.check_dbName_acc(dbName, acc, '1');
        fileName = 'frontier_%s_%s_%s.html' % (service.secrets['connections'][dbName]['frontier_name'], acc, tagname)
        return open(os.path.join(self.tablePath, fileName), "r").read()
    
    #return JSON instead of string when frontend is able to understand JSON
    @cherrypy.expose
    def get_plot_list(self, dbName='', acc='', tag='', since='', fileType='png', test=None):
        self.check_dbName_acc(dbName, acc, since);
        if fileType != "png":
            cherrypy.HTTPError(405, "Bad file type !!!!!")
        #try:
        #ArgumentValidator.validateArgs(dbName = dbName, tag = tag, since = since, onesince = False)
        #db = self.masker.unmask_dbname(dbName)
        #db = av.get_validated_dbname(value = db, acc = self.masker.unmask_schema(db, acc))
        #vtag = av.get_validated_tag(dbName = db, value = tag)
        connectionString = getFrontierConnectionString(acc, dbName)
        shortConnectionString = getFrontierConnectionString(acc, dbName, short = True)
	#c = readXML()
	#db	=	str(c.dbMap_reverse[dbName]+"/CMS_COND_"+acc)
	vtag	=	str(tag)
        #sinces = av.get_validated_since(value = since, db = db, tag = vtag).split(';')
        sinces = av.get_validated_since(value = since.strip(), db = connectionString, tag = vtag).split(';')
        dict = {}
	print self.__plotsdir
        for i in sinces:
            if i != '' or i != None:
                plot = SubdetectorFactory.getPlotInstance(dbName = connectionString, tag = vtag, since = i, 
                                                          fileType = fileType, directory = self.__plotsdir,
                                                          shortName = shortConnectionString)
                dict[i] = plot.get_names()            
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        #start returning json when frontend is able do decode it
        #return json.dumps(dict)
        #outer for-comprehension calls inner for-c for every key in dictionary
        #inner for-c creates a list of strings that llok like 1:a
        #{1:[a,b], 2:[b,c]} -> 1:a;1:b;2:b;2:c
        return ';'.join([';'.join(['%s:%s' % (i, x) for x in dict[i]]) for i in dict.keys()])
        '''except ValueError, e:
            return 'Wrong parameter value. ERROR returned: %s' % str(e)
        except TypeError, e:
            return 'Wrong parameter type. ERROR returned: %s' % str(e)  
        except RuntimeError,e:
            return 'Error connecting to DB. ERROR returned: %s' % str(e)
        except:
            return ''
        '''
        #return lastIOVSince.LastIOVSince(dbName = dbName).iovSequence(tag))


    @cherrypy.expose
    def get_connectionName(self,dbFilter=""):
	c = readXML()
	return json.dumps(c.get_connectionNameMasked(dbFilter=dbFilter))
   
    @cherrypy.expose
    def get_trend_plot(self, dbName = '', acc = '', tag = '', since = '', fileType = 'png'):
        self.check_dbName_acc(dbName, acc, since);
        if fileType != "png" :
            cherrypy.HTTPError(405, "Bad file type !!!!!")
	c = readXML()
	db	=	str(c.dbMap_reverse[dbName]+"/CMS_COND_"+acc)
	vtag	=	str(tag)
        return "ciao"
        vsince = av.get_validated_since(value = since.strip(), db = db, tag = vtag, onlyone = False)
        plot = SubdetectorFactory.getTrendPlotInstance(dbName = db, tag = vtag, since = vsince, 
                                                fileType = fileType, directory = self.__trendplotsdir)
        data = plot.get()
        cherrypy.response.headers['Content-Type'] = 'image/' + fileType
        return data
     
    @cherrypy.expose
    def get_plot(self, dbName='', acc='',tag='', since='1', fileType='png', png='',test=None):
        self.check_dbName_acc(dbName, acc, since);
        if fileType != "png" :
            cherrypy.HTTPError(405, "Bad file type !!!!!")
        '''Returns plot image (changes response header content-type)
        All arguments in get_plot method have default value equal to '' just
        for avoiding exception if some parameter is missing.

        For testing:
        http://HOSTNAME:PORT/get_plot?dbName=oracle://cms_orcoff_prod/CMS_COND_31X_ECAL&tag=EcalIntercalibConstants_EBg50_EEnoB&since=1&fileType=root
        '''
        #try:
        #ArgumentValidator.validateArgs(dbName = dbName, tag = tag, since = since, onesince = True)
	#c = readXML()
	#db	=	str(c.dbMap_reverse[dbName]+"/CMS_COND_"+acc)
        connectionString = getFrontierConnectionString(acc, dbName)
        shortConnectionString = getFrontierConnectionString(acc, dbName, short = True)
	vtag	=	str(tag)
        vsince = av.get_validated_since(value = since.strip(), db = connectionString, tag = vtag, onlyone = True)
        plot = SubdetectorFactory.getPlotInstance(dbName = connectionString, tag = vtag, since = vsince, 
                                                fileType = fileType, directory = self.__plotsdir, image = png,
                                                shortName = shortConnectionString)
        plotData = plot.get()
            #return plotData
        '''except ValueError, e:
            return 'Wrong parameter value. ERROR returned: %s' % str(e)
        except TypeError, e:
            return 'Wrong parameter type. ERROR returned: %s' % str(e)       
        except IOError, e:
            return 'Could not access file %s. ERROR returned: %s' % (self.__plotsdir, e)
        except AttributeError, e:
            return 'Couldn\t generate plot instance. ERROR returned: %s' % str(e)
        except RuntimeError,e:
            return 'Error connecting to DB. ERROR returned: %s' % str(e)   
        except Exception, e:
            return 'Plot is not implemented for this tag. ERROR returned: %s ' % str(e)
        else:
            if (fileType == 'root'):
                cherrypy.response.headers['Content-Disposition'] = \
                'attachment;filename=' + plot.get_name()
                cherrypy.response.headers['Content-Type'] = 'text/plain'
            else:'''
        cherrypy.response.headers['Content-Type'] = 'image/' + fileType
        return plotData
        
    
        
    @cherrypy.expose
    def get_plot_cmp(self, dbName1 = '', acc1='',tag1 = '', since1 = '1', fileType1 = 'png', png1 = '',
                    dbName2 = '', acc2='',tag2 = '', since2 = '1', fileType2 = 'png', png2 = '', type='3', istkmap = '1'):
        self.check_dbName_acc(dbName1, acc1, since1);
        self.check_dbName_acc(dbName2, acc2, since2);
        if fileType1 != "png" and fileType2 != "png":
            cherrypy.HTTPError(405, "Bad file type !!!!!")
        tmpdb = self.masker.unmask_dbname(dbName1)
        db = av.get_validated_dbname(value = tmpdb, acc = self.masker.unmask_schema(tmpdb, acc1))
        vtag = av.get_validated_tag(dbName = db, value = tag1)
        vsince = av.get_validated_since(value = since1.strip(), db = db, tag = vtag, onlyone = True)
        plot = SubdetectorFactory.getPlotInstance(dbName = db, tag = vtag, since = vsince, 
                                                fileType = fileType1, directory = self.__plotsdir, image = png1)
        img1 = plot.get(get_fname = True)
        tmpdb = self.masker.unmask_dbname(dbName2)
        db = av.get_validated_dbname(value = tmpdb, acc = self.masker.unmask_schema(tmpdb, acc2))
        vtag = av.get_validated_tag(dbName = db, value = tag2)
        vsince = av.get_validated_since(value = since2.strip(), db = db, tag = vtag, onlyone = True)
        plot = SubdetectorFactory.getPlotInstance(dbName = db, tag = vtag, since = vsince, 
                                                fileType = fileType2, directory = self.__plotsdir, image = png2)
        img2 = plot.get(get_fname = True)
        #raise Exception('asdasd'+img2)
        '''if type == '1':
            img3 = ImageChops.subtract(img1, img2, scale=1, offset=128)
        elif type == '2':
            img3 = ImageChops.subtract(img2, img1, scale=1, offset=128)
        elif type == '3':
            img3 =  ImageChops.difference(img1, img2)
        elif type == '4':
            img3 = ImageChops.subtract(img1, img2, scale=1, offset=0)
        else:
            img3 = ImageChops.subtract(img2, img1, scale=1, offset=0)
        '''
        if not os.path.isdir(self.__tmpdir):
            os.makedirs(self.__tmpdir)
        temp = tempfile.TemporaryFile(dir = self.__tmpdir)
        plotTxt = ""
        if re.search('strip', vtag.lower()):
            plotTxt = 'ABSOLUTE DIFFERENCE  (The more lighter colors, the higher the difference.)'
        cmpPNG.CmpTrackerDiff(fileName1 = img1, fileName2 = img2, result = temp,
                   txt = plotTxt,
                   debug = False)
        #img3.save(temp, 'png')
        temp.seek(0)
        cherrypy.response.headers['Content-Type'] = 'image/' + fileType1
        data = temp.read()
        temp.close()
        return data

        #img3.save(tmp, 'png')
        #cherrypy.response.headers['Content-Type'] = 'image/' + fileType1
        #return tmp.read()
        #img3.save('lol.png')
        #return open('lol.png').read()
        #if type(img1) == type(''):
        #    return 'Unable to get first image'
        #img1 = Image.frombuffer("RGBA", len(img1), img1)
        #return img1
        #img2 = self.get_plot(dbName = dbName2, tag = tag2, since = since2, fileType = fileType2, png = png2)
        #if type(img2) == type(''):
        #    return 'Unable to get second image'


    @cherrypy.expose
    def get_histo(self, dbName='', acc='',tag='', since=''):
        self.check_dbName_acc(dbName, acc, since);
        '''Returns histo. 
        All arguments in get_histo method have default value equal to '' just
        for avoiding exception if some parameter is missing.

        For testing:
        http://HOSTNAME:PORT/get_histo?dbName=oracle://cms_orcoff_prod/CMS_COND_31X_ECAL&tag=EcalIntercalibConstants_EBg50_EEnoB&since=1
        '''
        
        try:
            tmpdb = self.masker.unmask_dbname(dbName)
            db = av.get_validated_dbname(value = tmpdb, acc = self.masker.unmask_schema(tmpdb, acc))
            vtag = av.get_validated_tag(dbName = db, value = tag)
            vsince = av.get_validated_since(value = since.strip(), db = db, tag = vtag, onlyone = True)
            directory = self.__histodir
            histo = SubdetectorFactory.getHistoInstance(dbName = db, tag = vtag, 
                                                    since = vsince, fileType = 'png', directory = directory)
            histoData = histo.get()
        except:
            return 'Tag doesn\'t exist'
        else:
            cherrypy.response.headers['Content-Type'] = 'image/png'
            return histoData



    @cherrypy.expose
    def get_xml(self, dbName='', acc='',tag='', since=''):
        self.check_dbName_acc(dbName, acc, since);
        '''Returns gzipped XML payload. 
        All arguments in get_xml method have default value equal to '' just
        for avoiding exception if some parameter is missing.

        For testing:
	http://webcondvm2:8083/get_xml?dbName=oracle://cms_orcoff_prod/CMS_COND_31X_ECAL&tag=EcalIntercalibConstants_EBg50_EEnoB&since=1;
        '''
        #try:
	#c = readXML()
	#db	=	str(c.dbMap_reverse[dbName]+"/CMS_COND_"+acc)
        connectionString = getFrontierConnectionString(acc, dbName)
        shortConnectionString = getFrontierConnectionString(acc, dbName, short = True)
	vtag	=	str(tag)
        vsince = av.get_validated_since(value = since, db = connectionString, tag = vtag, onlyone = False)
        
        if len(vsince.split(';')) == 1:
            xml = SubdetectorFactory.getXMLInstance(dbName = connectionString, tag = vtag, 
                                    since = vsince, fileType = 'tar.gz', directory = self.__xmldir, shortName = shortConnectionString)
            data = xml.get()
        else:
            temp = tempfile.TemporaryFile(dir = self.__tmpdir)
            tar = tarfile.open(mode = "w|gz", fileobj = temp)
            for i in vsince.split(';'):
                xml = SubdetectorFactory.getXMLInstance(dbName = connectionString, tag = vtag, 
                                        since = i, fileType = 'xml', directory = self.__xmldir, shortName = shortConnectionString)
                name = xml.dump()
                tar.add(name, arcname = os.path.basename(name), recursive = False)

            tar.close()
            temp.seek(0)
            data = temp.read()
        
        cherrypy.response.headers['Content-Disposition'] = \
                'attachment;filename=' + '_'.join([vtag, vsince.replace(';', '_'), '.tar.gz'])
        #cherrypy.response.headers['Content-Type'] = 'application/x-gzip'
        cherrypy.response.headers['Content-Encoding'] = 'gzip'
        return data
        #except Exception, er:
        #    return 'Tag doesn\'t exist'
        #else:
        #cherrypy.response.headers['Content-Disposition'] = \
        #    'attachment;filename=' + xml.get_name()
        #cherrypy.response.headers['Content-Type'] = 'text/xml'
        #cherrypy.response.headers['Content-Encoding'] = 'xml'
        #return xmlData
    
    @cherrypy.expose
    def get_xml_diff(self, dbName1='', acc1='', tag1='', since1='', dbName2='', acc2='', tag2='', since2=''):
        self.check_dbName_acc(dbName1, acc1, since1);
        self.check_dbName_acc(dbName2, acc2, since2);
	#see the file 
	# http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/UserCode/Pierro/WebGUI/CondDBPayloadInspector/backend/CondDBPayloadInspector_backend.py?view=markup
        return ""

    @cherrypy.expose
    def get_summary(self, dbName='Offline Production', acc='31X_ECAL',tag='EcalIntercalibConstants_EBg50_EEnoB', since='1'):
        self.check_dbName_acc(dbName, acc, since);
        '''Return payload summary.
        For testing:
        http://HOSTNAME:PORT/get_summary?dbName=oracle://cms_orcoff_prod/CMS_COND_31X_ECAL&tag=EcalIntercalibConstants_EBg50_EEnoB&since=1
        '''
	#c = readXML()
	#db	=	str(c.dbMap_reverse[dbName]+"/CMS_COND_"+acc)
        connectionString = getFrontierConnectionString(acc, dbName)
	vtag	=	str(tag)
        sinces = av.get_validated_since(value = since, db = connectionString, tag = vtag).split(';')
        rez = []
        for i in sinces:
            inst = SubdetectorFactory.getSummaryInstance(dbName = connectionString, tag = vtag, since = str(i))
            rez.append({self.get_decorated_since(db = dbName, acc = acc, tag = tag, since = i):inst.summary()})
        return json.dumps({'summary':rez})
            #return SubdetectorFactory.getSummaryInstance().summary()
        #except:
        #    return 'Tag doesn\'t exist'


def main():
	service.start(CondDBPayloadInspector())


if __name__ == '__main__':
	main()

