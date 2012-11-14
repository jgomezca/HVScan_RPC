import json
import logging
import os
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from functools import wraps

import cherrypy
import GTServerSettings as Settings
import GTComparison
from GTLib import UploadGTLib

import api
import cache
import cPickle

logger = logging.getLogger(__name__)
PAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "pages"))

def get_gt_lib():
    return UploadGTLib(Settings.AUTHPATH, Settings.GLOBAL_TAG_SCHEMA, Settings.LOG_SCHEMA, Settings.CMSSW_VERSION)


def jsonify(func):
    '''JSON decorator for CherryPy'''
    #http://pythonwise.blogspot.com/2011/01/json-decorator-for-cherrypy.html
    #@wraps(func)
    def wrapper(*args, **kw):
        value = func(*args, **kw)
        cherrypy.response.headers["Content-Type"] = "application/json"
        return json.dumps(value)

    return wrapper


@api.generateServiceApi
class UploadGTServer(object):
    def __init__(self):     
        logger.info("Created UploadGTServer object")

    @cherrypy.expose
    @jsonify
    def getGTList(self):
        '''returns json of GT list'''
        return self._getGTList()

    def _getGTList(self):
        '''returns json of GT list'''
        rez = get_gt_lib().getGTList()
        return rez

    @cherrypy.expose
    def sendMail(self, messageText, emailSubject, **kwargs):
        print messageText, emailSubject
        msg = MIMEMultipart()
        msg['From'] = Settings.SEND_FROM
        send_to = Settings.MAILING_LIST
        msg['To'] = COMMASPACE.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = emailSubject
        try:
            msg.attach(MIMEText(messageText))
            smtpObj = smtplib.SMTP()
            smtpObj.connect()
            smtpObj.sendmail(Settings.SEND_FROM, send_to, msg.as_string())
            smtpObj.close()
        except Exception as e:
            print "Error: unable to send email", e.__class__
            return "Unable to send mail!Error - " + str(e)
        return "Mail was sent successfuly"

    @cherrypy.expose
    def GTdiff_html(self, **kwargs):
        if len(kwargs) == 2:
            if "GlobalTag" in kwargs and "GlobalTag2" in kwargs:
                gtList = self._getGTList()
                if kwargs["GlobalTag"] in gtList and kwargs["GlobalTag2"] in gtList:
                    return open(os.path.join(PAGES_DIR, 'GTdiff.html'), "rb").read()
                else:
                    raise cherrypy.HTTPError(405, "Error!!! There is no such Global Tag!!!")
            else:
                raise cherrypy.HTTPError(405, "Query has to have 2 parameters - GlobalTag and GlobalTag2 with values!!!")
        else:
            raise cherrypy.HTTPError(405, "Error!!! There has to be only 2 parameters: GlobalTag and GlobalTag2 with values!!!")


    @cherrypy.expose
    def index(self, *args, **kwargs):
        if len(args) == 0:
            if len(kwargs) == 3:
                if "GlobalTag" in kwargs and "GlobalTag2" in kwargs and "filter" in kwargs:
                    return open(os.path.join(PAGES_DIR, 'mainPage.html'), "rb").read()
                else:
                    raise cherrypy.HTTPError(405, "Error!!! Given 3 parameters should be: GlobalTag, GlobalTag2, filter with values (filter without or with value)!!!")
            elif len(kwargs) == 2:
                if "GlobalTag" in kwargs and "GlobalTag2" in kwargs:
                    return open(os.path.join(PAGES_DIR, 'mainPage.html'), "rb").read()
                else:
                    raise cherrypy.HTTPError(405, "Error!!! Given 2 parameters should be: GlobalTag, GlobalTag2  with values!!!")
            elif len(kwargs) == 0:
                return open(os.path.join(PAGES_DIR, 'mainPage.html'), "rb").read()
            else:
                raise cherrypy.HTTPError(405, "Error!!! Bad request should be 2 or 3 or 0 parameters!!!(?GloabalTag=...&GlobalTag2=... OR ?GlogabTag=...&GlobalTag2=...&filter=")

        elif len(kwargs) == 1:
            if "message-box.html" in args:
                if "msg_name" in kwargs:
                    if kwargs["msg_name"] == "Server Not Available":
                        cherrypy.response.headers['info'] = "server not available"
                    elif kwargs["msg_name"] == "Refreshing":
                        cherrypy.response.headers['info'] = "refreshing"
                    elif kwargs["msg_name"] == "missingRecordName":
                        cherrypy.response.headers['info'] = "missingrecordname"
                    else:
                        raise cherrypy.HTTPError(405, "Bad error message parameter value!!!")
                else:
                    raise cherrypy.HTTPError(405, "Missing parameter msg_name!!!")
                return open(os.path.join(PAGES_DIR, 'message-box.html'), "rb").read()
            else:
                raise cherrypy.HTTPError(405, "Bad error message query!!! Should be /message-box.html?msg_name=ERROR_NAME")
        else:
            raise cherrypy.HTTPError(405, "Error message request has to be with only one parameter msg_name!!!")

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getCMSSWVersion(self, *args, **kwargs):
        '''Returns tring with version'''
        return {'CMSSW_Version':get_gt_lib().cmssw_version}

#    @cherrypy.expose
#    @cherrypy.tools.json_out()
#    def getCurrentGT(self):
#        '''Globalt tags used by T0. Returns Json list'''
#        return get_gt_lib().getCurrentGT()

    @cherrypy.expose
    @jsonify
    def getGTInfo(self, GT_name, truncated="True"): #format json erased, because now no other formath exist
        return self._getGTInfo(GT_name, truncated)

    def _getGTInfo(self, GT_name, truncated="True"): #format json erased, because now no other formath exist
        '''Information about GT. Possible Json/Html
           GT_name - Name of global tag
           truncated - Should list of iov given tuncated or full. Default
           truncated(true)(optional)
        '''

        def truncate(info):
            for body_entry in info["body"]:
                iov_list = body_entry['iov_list']
                iov_list = iov_list[-Settings.GT_IOV_LIST_TRUNCATED_COUNT:]
                body_entry['iov_list'] = iov_list
            return info
        truncated = (truncated != "False")
        GT_name =str(GT_name)
        info = cache.gts.get(GT_name+"_truncated_"+str(truncated))
        if info is not None:
            return cPickle.loads(info)
        gt_lib = get_gt_lib()
        info = gt_lib.getGTInfo(GT_name)
        cache.gts.put(GT_name+"_truncated_False", cPickle.dumps(info), Settings.GT_INFO_MAX_AGE)
        info_truncated = truncate(info)
        cache.gts.put(GT_name+"_truncated_True", cPickle.dumps(info_truncated), Settings.GT_INFO_MAX_AGE) #could be delayed
        if truncated:
            return info_truncated
        else:
            return info

    @cherrypy.expose
    @jsonify
    def getGTDiff(self, gt1_name, gt2_name, *args, **kwargs):
        '''Comparing GT. Returns json'''
        
        gtnames = [gt_name for gt_name in kwargs.values()]
        gtnames.insert(0, gt2_name)
        gtnames.insert(0, gt1_name)
        gtnames = [str(gtname) for gtname in gtnames]
        if not set(gtnames).issubset(set(self._getGTList())):
            raise cherrypy.HTTPError(404,'One of GT names not found.')
        gtlist = [self._getGTInfo(gt_name) for gt_name in gtnames]
        #gtlist = [get_gt_lib().getGTInfo(gt_name) for gt_name in gtnames]

        comp_response = GTComparison.compare_gt(*gtlist)
        for key, value in comp_response['body'].items():
            new_key = "#".join(key)
            comp_response['body'][new_key] = value
            del comp_response['body'][key]

        return comp_response



    @cherrypy.expose()
    @jsonify
    def getProductionGTs(self):
        try:
            data = get_gt_lib().getProductionGTs()
        except ValueError as e :
            print str(e)
            data = Settings.PRODUCTION_GTS
        return data

