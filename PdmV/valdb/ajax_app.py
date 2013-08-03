import cherrypy
import os
import pwd
import smtplib
import email
import json as simplejson
import sys
from database_access import *
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from jinja2 import Template
from sqlalchemy import create_engine
import urllib
import logging
import service


#-mo FIXME: The old code used the production DB in -int and -pro. However,
#           as at the moment -int is the new -dev, for the moment always use
#           the development DB.
connectionDictionary = service.secrets['connections']['dev']["writer"]
engine = create_engine(service.getSqlAlchemyConnectionString(connectionDictionary), echo=False)
Session = sessionmaker(bind=engine)

class API(object):
    def __init__(self, param):
        self.parent_obj = param ##inherit parent object -> to be albe use all methods of DB access
        
    @cherrypy.expose
    def index(self): ##take info from defined methods docstrings
        return self.parent_obj.loadPage('API')
    
    def get_CatSubCat_details(self, catSubCat, release_name):
        data = self.parent_obj.mainInformation(catSubCat, release_name)
        tmp = json.loads(data)
        detailedinfo = {}
        tmp_arr = []  #an array to save all the status
        for elem in tmp:
            if elem == 'RelMon':  ##in case the RelMon -> save it as a string of URL
                #detailedinfo[elem] = tmp[elem]
                tmp_arr.append({elem: tmp[elem]})
            else:  ##for all the different load as a JSON object
                json_obj = json.loads(self.parent_obj.getDetailInformation(catSubCat, release_name, elem))
                tmp_arr.append({elem : json_obj})
        #return detailedinfo
        return tmp_arr

    @cherrypy.expose
    def release_info(self,release_name):
        
        detailedinfo = {}
        ### GET Reconstruction info
        detailedinfo['RData']= self.get_CatSubCat_details('RData', release_name)
        detailedinfo['RFast']= self.get_CatSubCat_details('RFast', release_name)
        detailedinfo['RFull']= self.get_CatSubCat_details('RFull', release_name)
        
        #GET HLT info
        detailedinfo['HData']= self.get_CatSubCat_details('HData', release_name)
        detailedinfo['HFast']= self.get_CatSubCat_details('HFast', release_name)
        detailedinfo['HFull']= self.get_CatSubCat_details('HFull', release_name)
        
        ###GET PAGs info
        detailedinfo['PData']= self.get_CatSubCat_details('PData', release_name)
        detailedinfo['PFast']= self.get_CatSubCat_details('PFast', release_name)
        detailedinfo['PFull']= self.get_CatSubCat_details('PFull', release_name)
        
        return json.dumps(detailedinfo)
        
    @cherrypy.expose
    def all_releases(self):
        data = self.parent_obj.submit('*')
        return data
        
    @cherrypy.expose
    def add_release(self, release_name, catSubCat, relmon_url=False):
        catSubCatList = catSubCat.split(',')
        if not relmon_url:
            relmon_url = ""
        defaultKeys = []
        mailId = self.parent_obj.getMsgId()
        for cat in catSubCatList: #in case user specified a comma separated list for releases CatSubCats
            if cat[0].upper() == 'R': #get subCategory collumn list
                defaultKeys = ["CSC", "TAU", "TRACKING", "BTAG", "JET", "ECAL", "RPC", "PHOTON", "MUON", "MET", "ELECTRON", "TK", "HCAL", "DT", "SUMMARY"]
            elif cat[0].upper() == 'H':
                defaultKeys = ["TAU", "JET", "HIGGS", "TOP", "MUON", "PHOTON", "MET", "ELECTRON", "EXOTICA", "SUSY", "SMP", "FWD", "BTAG", "TRACKING", "B", "SUMMARY"]
            elif cat[0].upper() == 'P':
                defaultKeys = ["B2G","B", "HIGGS", "FWD", "TOP", "SMP", "EXOTICA", "SUSY", "SUMMARY"]
            subCat = self.parent_obj.configuration[cat]
            StatList = []
            StatValList = []
            StatComments = []
            StatAuthor = []
            StatLinks = []
            for key in defaultKeys:
                StatList.append(key)
                StatValList.append("NOT YET DONE")
                StatComments.append("")
                StatAuthor.append("")
                StatLinks.append("")
            #(self, sendMail, categ, subCat, relName, statusNames, statusValues, statComments, statAuthors, statLinks, mailID, relMonURL, **kwargs):
            returninfo =  json.loads(self.parent_obj.addNewRelease(self, subCat[0], subCat[1], release_name, StatList, StatValList, StatComments, StatAuthor, StatLinks, mailId, relmon_url))
            if returninfo[0] == "New release added successfuly":
                added = True
            else:
                added = False
                return "Failure in adding: %s" %(returninfo[0])
        if added:
            msgSubject = "New release "+release_name+" added"
            msgText = "New release: "+release_name +" was added by "+self.parent_obj.get_username()+". Please check it!"
          ##sendMail(self, messageText, emailSubject, org_message_ID, new_message_ID, username=False, **kwargs):
            self.parent_obj.sendMail(msgText, msgSubject, "", mailId, "vlimant") ##send emails from Jean-Roch as for now (its Robot uses api)
            logging.info("API: added release %s successfuly by", release_name, self.get_fullname())
            return "Added successfuly"
        else:
            logging.error("API: error adding release %s by %s", release_name, self.get_fullname())
            return returninfo[0] #Failure in adding -> return DB interface output

class AjaxApp(object):
    def __init__(self):
        self.configuration = {
            'RData' : ('Reconstruction', 'Data'),
            'RFull' : ('Reconstruction', 'FullSim'),
            'RFast' : ('Reconstruction', 'FastSim'),
            'HData' : ('HLT', 'Data'),
            'HFull' : ('HLT', 'FullSim'),
            'HFast' : ('HLT', 'FastSim'),
            'PData' : ('PAGs', 'Data'),
            'PFull' : ('PAGs', 'FullSim'),
            'PFast' : ('PAGs', 'FastSim'),
        }
        
        self.api = API(self)

    MAILING_LIST = ["hn-cms-relval@cern.ch","hn-cms-trigger-performance@cern.ch","hn-cms-muon-object-validation@cern.ch"]
    #MAILING_LIST = ["anorkus@cern.ch","vlimant@cern.ch","franzoni@cern.ch"]#, "hn-cms-hnTest@cern.ch"] #testing mailing list
    VALIDATION_STATUS = "VALIDATION_STATUS"
    COMMENTS = "COMMENTS"
    LINKS = "LINKS"
    USER_NAME = "USER_NAME"
    MESSAGE_ID = 'MESSAGE_ID'
    EMAIL_SUBJECT = 'EMAIL_SUBJECT'
    data = { "link" : "index" }


    def loadPage(self, page):
        username = self.get_username()
        fullname = self.get_fullname() 
        return open('pages/%s.html' % page, 'rb').read().replace('%USERNAME', username)
        
    @cherrypy.expose
    def logoutUser(self, *args, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(self.data)

    @cherrypy.expose
    def index(self, *args, **kwargs):
        username = self.get_username()
        fullname = self.get_fullname()  

        if not self.is_user_in_group(username):
            cherrypy.response.headers['Content-Type'] = 'application/json'
            info = "You are not in cms-CERN-users group so you cannot see this page."
            return simplejson.dumps([info])

        if checkAdmin(username, Session):
            return self.loadPage('indexAdmin')
        elif checkValidator(username, Session):
            return self.loadPage('indexValidator')
        else:
            return self.loadPage('indexUser')
           
    @cherrypy.expose
    def permissionErrorMessage(self):
        return """ <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
               "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
               <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
               <head>
                   <title>Permission error</title>
                   <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
               </head>
               <body>
               <body style="background-color: #ADD8E6">
               <p style="text-align:center; font-family:verdana"><font color="red"> You don't have privileges to use this method! </font></p>
               </head>
               </html>"""
               
    def is_user_in_group(self, username):
        # If in a private VM, bypass
        if service.settings['productionLevel'] == 'private':
            return True
        return 'cms-zh' in service.getGroups() or 'cms-CERN-users' in service.getGroups()

    @cherrypy.expose
    def getLogedUserName (self, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        info = []
        info.append(self.get_username())
        info.append(self.get_fullname())
        return simplejson.dumps(info)

    @cherrypy.expose
    def checkValidatorsRights (self):
        if not self.check_validator():
            raise cherrypy.InternalRedirect('/permissionErrorMessage')
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        request = json.loads(rawbody)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps([checkValidatorRights(request["cat"], request["subCategory"],  request["statusKind"], self.get_username(), Session)])

    @cherrypy.expose
    def submit(self):
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        request = json.loads(rawbody)
        releaseName = request["releaseName"]
        cherrypy.response.headers['Content-Type'] = 'application/json'
        logging.info("%s searching form: %s",self.get_fullname(), releaseName)
        return search(releaseName, Session)
        
    @cherrypy.expose
    def testSQL(self):
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        request = json.loads(rawbody)
        releaseName = request["releaseName"]
        cherrypy.response.headers['Content-Type'] = 'application/json'
        logging.info("%s searching details for: %s",self.get_fullname(), releaseName)
        return testFullReleaseInfo(releaseName, Session)

    @cherrypy.expose
    def FullDetails(self):
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        request = json.loads(rawbody)
        catSubCat = request["category"][0]+request["subCategory"][:4]
        logging.info("%s searching for details. release: %s column: %s",self.get_fullname(), request["release"], request["column"])
        return self.getDetailInformation(catSubCat, request["release"], request["column"])

    def getDetailInformation(self, catSubCat, relName, state, **kwargs):
       cherrypy.response.headers['Content-Type'] = 'application/json'
       cat = None
       subCat = None
       configuration = self.configuration
       cat, subCat = configuration.get(catSubCat, (None,None))
       return getReleaseFullDetails(cat, subCat, relName, state, Session)

    def addNewRelease(self, sendMail, categ, subCat, relName, statusNames, statusValues, statComments, statAuthors, statLinks, mailID, relMonURL, **kwargs):
        if not (self.check_admin() or self.check_validator()):
            raise cherrypy.InternalRedirect('/permissionErrorMessage')
        if len(statusNames) == len(statusValues)  and len(statusNames) == len(statComments) and len(statusNames) == len(statAuthors) and len(statusNames) == len(statLinks):
            cherrypy.response.headers['Content-Type'] = 'text/html'
            dictionaryFull = {}
            returnedInformation = {}
            mime_MSG_id = mailID
            #mime_MSG_id = email.utils.make_msgid()
            msgSubject = "New release "+relName+" added"
            for index in range(len(statusNames)):
                tmpDictionary = {}
                tmpDictionary[VALIDATION_STATUS] = statusValues[index]
                tmpDictionary[COMMENTS] = statComments[index]
                tmpDictionary[LINKS] = statLinks[index]
                tmpDictionary[USER_NAME] = statAuthors[index]
                if categ == "Reconstruction":
                    if statusNames[index].upper() == "MUON" :
                        tmpDictionary[MESSAGE_ID] = mime_MSG_id #if colum in RECO/MUON -> make messages for 2 HyperNews
                    else:
                        tmpDictionary[MESSAGE_ID] = mime_MSG_id.split(',')[0] #else make the messageId only for RelVals
                elif categ == "HLT":
                    tmpDictionary[MESSAGE_ID] = mime_MSG_id # for HLT all messageIds are 2: RelVals and Trigger
                else:
                    tmpDictionary[MESSAGE_ID] = mime_MSG_id.split(',')[0] #by default make only 1 messageID for RelVal HyperNews
                    
                tmpDictionary['EMAIL_SUBJECT'] = msgSubject
                tmpDictionary['RELMON_URL'] = relMonURL
                dictionaryFull[statusNames[index]] = tmpDictionary
            returnedInformation = newRelease(categ, subCat, relName, simplejson.dumps(dictionaryFull), Session)
            if returnedInformation == "True":
                msgText = """ New release: %s In category: %s In subcategory: %s Was added. Check it!
                """ % (relName.upper(), categ.upper(), subCat.upper())
               # self.sendMailOnChanges(msgText, msgSubject, None, mime_MSG_id)
                info = "New release added successfuly"
                cherrypy.response.headers['Content-Type'] = 'application/json'
                logging.info("%s",info)
                return simplejson.dumps([info])
            else:
                cherrypy.response.headers['Content-Type'] = 'application/json'
                info = 'Error. In parameters settings'
                logging.error("Error adding new release. %s", info)
                return simplejson.dumps([returnedInformation])
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            info = "Error. Information is damaged"
            logging.error("Error adding new release. %s", info)
            return simplejson.dumps([info])

    @cherrypy.expose
    def addNewReleaseUpdated(self):
        if not (self.check_admin()):
            raise cherrypy.InternalRedirect('/permissionErrorMessage')
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        request = json.loads(rawbody)
        releaseName = request["release_name"]
        relmon_url = request["relmon_url"]
        categories = request["categories"]
        subcategories = request["subcats"]
        msgIDs = self.getMultipleMsgId()
        messageID_to_inform = ["","",""]
        reco_default_keys = ["CSC", "TAU", "TRACKING", "BTAG", "JET", "ECAL", "RPC", "PHOTON", "MUON", "MET", "ELECTRON", "TK", "HCAL", "DT", "SUMMARY"]
        hlt_default_keys = ["TAU", "JET", "HIGGS", "TOP", "MUON", "PHOTON", "MET", "ELECTRON", "EXOTICA", "SUSY", "SMP", "FWD", "BTAG", "TRACKING", "B", "SUMMARY"]
        pags_default_keys = ["B2G", "B", "HIGGS", "FWD", "TOP", "SMP", "EXOTICA", "SUSY", "SUMMARY"]
        msgSubject = "New release %s added" %(releaseName)
        success = []
        for cat in categories:
            if cat.upper() == "PAGS":
                default_keys = pags_default_keys
                mime_MSG_id = msgIDs[0]
                messageID_to_inform[0] = msgIDs[0]
            elif cat.upper() == "HLT":
                default_keys = hlt_default_keys
                mime_MSG_id = msgIDs[0] + "," +msgIDs[1]
                messageID_to_inform[0] = msgIDs[0]
                messageID_to_inform[1] = msgIDs[1]
            elif  cat.upper() == "RECONSTRUCTION":
                default_keys = reco_default_keys
                mime_MSG_id = msgIDs[0] + "," +msgIDs[2]
                messageID_to_inform[0] = msgIDs[0]
                messageID_to_inform[2] = msgIDs[2]
            else:
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return simplejson.dumps(["Problems while processing default columns"])

            for subCat in subcategories:
                tmp_dict = {}
                for column in default_keys:
                    tmp_dict[column]={}
                    tmp_dict[column]["VALIDATION_STATUS"] = "NOT YET DONE"
                    tmp_dict[column]["COMMENTS"] = ""
                    tmp_dict[column]["LINKS"] = ""
                    tmp_dict[column]["USER_NAME"] = ""
                    if cat.upper() == "RECONSTRUCTION":
                        if column.upper() == "MUON" :
                            tmp_dict[column][MESSAGE_ID] = mime_MSG_id #if column in RECO/MUON -> make messages for 2 HyperNews
                        else:
                            tmp_dict[column][MESSAGE_ID] = mime_MSG_id.split(',')[0] #else make the messageId only for RelVals
                    elif cat.upper() == "HLT": 
                        tmp_dict[column][MESSAGE_ID] = mime_MSG_id # for HLT all messageIds are 2: RelVals and Trigger
                    else:
                        tmp_dict[column][MESSAGE_ID] = mime_MSG_id.split(',')[0] #by default make only 1 messageID for RelVal HyperNews
                    tmp_dict[column]['EMAIL_SUBJECT'] = msgSubject.encode('ascii','ignore')
                    tmp_dict[column]['RELMON_URL'] = relmon_url.encode('ascii','ignore')
                returnedInformation = newRelease(cat, subCat, releaseName, simplejson.dumps(tmp_dict), Session)
                if returnedInformation == "True":
                  success.append("%s and %s success" %(cat,subCat))
                else:
                  cherrypy.response.headers['Content-Type'] = 'application/json'
                  info = 'Error. While adding new release in %s and %s' %(cat,subCat)
                  logging.error("%s. %s",self.get_fullname(), info)
                  return simplejson.dumps(returnedInformation)
        msgText = "New release: %s was added by %s. Please check it!"%(releaseName, self.get_fullname())
        messageID_to_inform = filter(lambda x:x!='',messageID_to_inform)
        self.sendMail(msgText, msgSubject, "", ','.join(messageID_to_inform), self.get_username())
        logging.info("%s", msgText)
        return json.dumps({"results": True, "data":"New release %s  was added"%(releaseName)})

    @cherrypy.expose
    def updateReleaseInfo(self):
        if not (self.check_admin() or self.check_validator()):
            raise cherrypy.InternalRedirect('/permissionErrorMessage')
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        request = json.loads(rawbody)
        comentAuthor = request["comentAuthor"]
        stateValue = request["stateValue"]
        relName = request["relName"]
        newComment = request["newComment"]
        newLinks = request["newLinks"]
        catSubCat = request["catSubCat"]
        statusKind = request["statusKind"]
        userName = request["userName"]
        cat = None
        subCat = None
        returnedInformation = None
        configuration = self.configuration
        cat, subCat = configuration.get(catSubCat, (None,None))
        returnedStatusValueOld = getStatus(cat, subCat, relName, statusKind, Session)
        #returnedStatusValueOld - tuple: 0 is old status, 1 is old messageID, 2 is releaseName
        #make new messageID
        newIDs = []
        for i in range(len(returnedStatusValueOld[1].split(","))):
           newIDs.append(email.utils.make_msgid())  
        #new_message_ID = email.utils.make_msgid()
        if cat == "Reconstruction":
            emailCat = "RECO"
        else:
            emailCat = cat
        if statusKind == "TK":
            msgSubject = ">TRACKER "+ emailCat + " " + subCat + "< " + returnedStatusValueOld[2]  ##make a message subject with statuskin/subcat mentioned in case of Tracker subCat
        else:
            msgSubject = ">"+statusKind + " " + emailCat + " " + subCat + "< " + returnedStatusValueOld[2]  ##make a message subject with statuskin/subcat mentioned in case of other subCats
        returnedInformation = changeStatus(cat, subCat, relName, statusKind,
                                          stateValue, newComment, comentAuthor, 
                                          newLinks,Session, ",".join(newIDs), returnedStatusValueOld[2])
        if returnedInformation == "True":
            if statusKind.upper() == "SUMMARY":
                return simplejson.dumps(["INFO column won't be announced over emails"])
            msgText = """Release: %s
In category: %s
In subcategory: %s 
validation for: %s
Has Changed: From status: %s 
             To status: %s
By: %s
Comment: %s
Links: %s
""" % (relName.upper(), cat.upper(), subCat.upper(), statusKind.upper(), returnedStatusValueOld[0].upper(), stateValue.upper(), comentAuthor.upper(), newComment, newLinks)
            
            if (cat.upper() == 'HLT'): #if the category is HLT  -> send email to trigger hn and a reply to orginal with text to diff hn
                hlt_msg_id = email.utils.make_msgid()
                hn_address = 'hn-cms-trigger-performance@cern.ch'
                hn_address = 'hn-cms-hnTest@cern.ch'
                #hn_address = 'vlimant@cern.ch'  # Testing adresses
                if len(returnedStatusValueOld[1].split(",")) == 1:
                    self.sendMailOnChanges(msgText, msgSubject, None, hlt_msg_id, userName, hn_address) #send message to other HN adress without threading
                else:
                    self.sendMailOnChanges(msgText, msgSubject, returnedStatusValueOld[1].split(",")[1], newIDs[1], userName, hn_address) #send message to other HN adress with threading
                newText = """Release: %s
In category: %s
In subcategory: %s 
validation for: %s
Has Changed: From status: %s 
             To status: %s
By: %s

The full details was sent to %s find it there""" %(relName.upper(), cat.upper(), subCat.upper(), statusKind.upper(), returnedStatusValueOld[0].upper(), stateValue.upper(), comentAuthor.upper(),"https://hypernews.cern.ch/HyperNews/CMS/get/trigger-performance.html") #new text for RelVal HN
                self.sendMailOnChanges(newText, msgSubject, returnedStatusValueOld[1].split(",")[0], newIDs[0], userName) #send a threaded message to RelVal HN
                
            elif (cat.upper() == 'RECONSTRUCTION') and (statusKind.upper() == 'MUON'): #same for Reco Muon as for all HLT
                reco_msg_id = email.utils.make_msgid()
                hn_address = 'hn-cms-muon-object-validation@cern.ch'
                #hn_address = 'hn-cms-hnTest@cern.ch'  # Testing adresses
                #hn_address = 'franzoni@cern.ch'
                if len(returnedStatusValueOld[1].split(",")) == 1:
                    self.sendMailOnChanges(msgText, msgSubject, None, reco_msg_id, userName, hn_address) #mail to Muon HN without threading
                else:
                    self.sendMailOnChanges(msgText, msgSubject, returnedStatusValueOld[1].split(",")[1], newIDs[1], userName, hn_address) #mail to Muon HN with threading
                newText = """Release: %s
In category: %s
In subcategory: %s 
validation for: %s
Has Changed: From status: %s 
             To status: %s
By: %s

The full details was sent to %s find it there""" %(relName.upper(), cat.upper(), subCat.upper(), statusKind.upper(), returnedStatusValueOld[0].upper(), stateValue.upper(), comentAuthor.upper(),"https://hypernews.cern.ch/HyperNews/CMS/get/muon-object-validation.html") #new text for RelVal HN
                self.sendMailOnChanges(newText, msgSubject, returnedStatusValueOld[1].split(",")[0], newIDs[0], userName) #send a threaded message to RelVal HN
                
            else:  #by default send to relval
                self.sendMailOnChanges(msgText, msgSubject, returnedStatusValueOld[1], newIDs[0], userName) 
            info = "Release information updated successfuly"
            cherrypy.response.headers['Content-Type'] = 'application/json'
            logging.info("%s %s %s", self.get_fullname(), relName, info)
            return simplejson.dumps([info])
        else:
            logging.error("%s %s %s", self.get_fullname(), relName, returnedInformation)
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps([returnedInformation])

    @cherrypy.expose
    def addNewUser (self):
        if not self.check_admin():
            raise cherrypy.InternalRedirect('/permissionErrorMessage')
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        request = json.loads(rawbody)
        user_Name = request["user_Name"]
        userTypeValue = request["userTypeValue"]
        userEmail = request["userEmail"]
        usrRDataStatList = request["usrRDataStatList"]
        usrRFastStatList = request["usrRFastStatList"]
        usrRFullStatList = request["usrRFullStatList"]
        usrHDataStatList = request["usrHDataStatList"]
        usrHFastStatList = request["usrHFastStatList"]
        usrHFullStatList = request["usrHFullStatList"]
        usrPDataStatList = request["usrPDataStatList"]
        usrPFastStatList = request["usrPFastStatList"]
        usrPFullStatList = request["usrPFullStatList"]
        if userTypeValue == "------":
            info = "User with status ------ cannot be added"
            cherrypy.response.headers['Content-Type'] = 'application/json'
            logging.error("%s %s", self.get_fullname(), info)
            return simplejson.dumps([info])
        elif userTypeValue == "Validator":
            removeUser(user_Name, Session)
            check1 = addUser(user_Name, Session, userEmail)
            check2 = grantValidatorRights(user_Name, Session)
            check3 = grantValidatorRightsForStatusKindList(user_Name, usrRDataStatList, usrRFastStatList, usrRFullStatList, usrHDataStatList, usrHFastStatList, usrHFullStatList, usrPDataStatList, usrPFastStatList, usrPFullStatList, Session)
            if check1 and check2 and check3:
                info = "User " + user_Name + " as VALIDATOR was added successfuly"
                cherrypy.response.headers['Content-Type'] = 'application/json'
                logging.error("%s %s", self.get_fullname(), info)
                return simplejson.dumps([info])
            else:
                info = "User " + user_Name + " was not added. Problems with database"
                cherrypy.response.headers['Content-Type'] = 'application/json'
                logging.error("%s %s", self.get_fullname(), info)
                return simplejson.dumps([info]) 
        elif userTypeValue == "Admin":
            removeUser(user_Name, Session)
            check1 = addUser(user_Name, Session, userEmail)
            check2 = grantAdminRights(user_Name, Session)
            if check1 and check2:
                info = "User " + user_Name + " as ADMIN was added successfuly"
                cherrypy.response.headers['Content-Type'] = 'application/json'
                logging.error("%s %s", self.get_fullname(), info)
                return simplejson.dumps([info])
            else:
                info = "User " + user_Name + " was not added. Problems with database"
                cherrypy.response.headers['Content-Type'] = 'application/json'
                logging.error("%s %s", self.get_fullname(), info)
                return simplejson.dumps([info])
        else:
            info = "Something happend wrong with User Type"
            cherrypy.response.headers['Content-Type'] = 'application/json'
            logging.error("%s %s", self.get_fullname(), info)
            return simplejson.dumps([info])

    @cherrypy.expose
    def removeUser (self):
        if not self.check_admin():
            raise cherrypy.InternalRedirect('/permissionErrorMessage')
        cherrypy.response.headers['Content-Type'] = 'application/json'
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        request = json.loads(rawbody)
        user_Name = request["user_Name"]
        returnInformation = removeUser(user_Name, Session)
        if returnInformation == "True":
            info = "User " + user_Name + " was removed successfuly"
            cherrypy.response.headers['Content-Type'] = 'application/json'
            logging.info("%s %s", self.get_fullname(), info)
            return simplejson.dumps([info])
        else:
            info = "User " + user_Name + " was not removed because - " + returnInformation
            cherrypy.response.headers['Content-Type'] = 'application/json'
            logging.error("%s %s", self.get_fullname(), info)
            return simplejson.dumps([info])

    @cherrypy.expose
    def showUsers (self, userName, **kwargs):
        template = Template(open('pages/userRightsTemplate.html', "rb").read())
        title = 'PdmV Users List'
        header = 'Selected Users:'
        users = getAllUsersInfo(userName, Session)
        users = simplejson.loads(users)
        logging.error("%s searching for user: %s", self.get_fullname(), userName)
        try:
            return template.render(title=title, header=header, users=users['validators'], admins=users['admins'], validators_email=users["validator_mail"])
        except Exception as e:
            logging.error("%s %s", self.get_fullname(), str(e))
            return str(e)

    def sendMailOnChanges(self, messageText, emailSubject, org_message_ID, new_message_ID, username=False, diff_HN_adress=None, **kwargs):
        msg = MIMEMultipart()
        reply_to = []
        send_to = []
        if org_message_ID != None:
            msg['In-Reply-To'] = org_message_ID
            msg['References'] = org_message_ID

        #send_from = "PdmV.ValDb@cern.ch"
        send_from = getUserEmail(username, Session)
        msg['From'] = send_from
        if diff_HN_adress == None:
            send_to += [self.MAILING_LIST[0]]
        else:
            send_to += [diff_HN_adress]
        #if username != False:   #send email copy to the sender himself
        #    email = getUserEmail(username, Session)
        #    send_to.append(email)
        reply_to.append(send_from) #make a reply header to sender+receivers of the email.
        reply_to.append("hn-cms-relval@cern.ch")
        msg['reply-to'] = COMMASPACE.join(reply_to)
        msg['To'] = COMMASPACE.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = emailSubject
        msg['Message-ID'] = new_message_ID

        try:
            msg.attach(MIMEText(messageText))
            smtpObj = smtplib.SMTP()
            smtpObj.connect()
            smtpObj.sendmail(send_from, send_to, msg.as_string())
            smtpObj.close()         
        except Exception as e:
            logging.error("Error: unable to send email: %s", str(e))

    @cherrypy.expose
    def mainInformation(self, catSubCat, relName, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        cat = None
        subCat = None
        configuration = self.configuration
        response = {}
        cat, subCat = configuration.get(catSubCat, (None,None))
        return getReleaseShortInfo(cat, subCat, relName, Session)


    def check_admin(self):
        if checkAdmin(self.get_username(), Session) == False:
            return False
        else:
            return True;
        
    def check_validator(self):        
        if checkValidator(self.get_username(), Session) == False:
           return False
        else:
           return True

    def get_username(self):
        if service.settings['productionLevel'] == 'private':
            username = pwd.getpwuid(os.getuid())[0]
        else:
            username = service.getUsername()
        return username

    def get_fullname(self):
        if service.settings['productionLevel'] == 'private':
            fullname = pwd.getpwuid(os.getuid())[0]
        else:
            fullname = service.getFullName()
        return fullname


###UPDATED FUNCTIONALITIES as of 2012-09-07###

    ##method to generate and get email messageID for first email sending.
    @cherrypy.expose
    def getMsgId(self, *args, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        messageID = email.utils.make_msgid()
        return json.dumps(messageID)

    def getMultipleMsgId(self, *args, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        info = []
        for i in range(3):
            info.append(email.utils.make_msgid()) #3 msgIDs -> RelVal,HLT,MUON hypernews
        #messageID = email.utils.make_msgid()
        return info
    ######

    def sendMail(self, messageText, emailSubject, org_message_ID, new_message_ID, username=False, **kwargs):
        for index,elem in enumerate(new_message_ID.split(',')):
            msg = MIMEMultipart()
            if org_message_ID != None:
                msg['In-Reply-To'] = org_message_ID
                msg['References'] = org_message_ID

            # send_from = "PdmV.ValDb@cern.ch"
            if username != False:
                send_from = getUserEmail(username, Session)
            else:
                send_from = "anorkus@cern.ch"
            msg['From'] = send_from
        
            send_to = [self.MAILING_LIST[index]]
            #send_to.append(self.MAILING_LIST[index])
            #if username != False:
             #   send_to.append(send_from)  ##send a copy to user himself
            msg['To'] = COMMASPACE.join(send_to)
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = emailSubject
            msg['Message-ID'] = elem

            try:
                msg.attach(MIMEText(messageText))
                smtpObj = smtplib.SMTP()
                smtpObj.connect()
                smtpObj.sendmail(send_from, send_to, msg.as_string())
                smtpObj.close()         
            except Exception as e:
                logging.error("Error: unable to send email: %s", str(e))
        return json.dumps('New release added. Email was sent.')

def main():
    service.start(AjaxApp())

if __name__ == '__main__':
    main()
