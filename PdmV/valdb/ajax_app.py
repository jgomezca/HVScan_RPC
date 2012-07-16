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

import service


#-mo FIXME: The old code used the production DB in -int and -pro. However,
#           as at the moment -int is the new -dev, for the moment always use
#           the development DB.
connectionDictionary = service.secrets['connections']['dev']["writer"]
engine = create_engine(service.getSqlAlchemyConnectionString(connectionDictionary), echo=False)
Session = sessionmaker(bind=engine)


def loadPage(page):
    if service.settings['productionLevel'] == 'private':
        username = pwd.getpwuid(os.getuid())[0]
    else:
        username = service.getUsername()
    return open('pages/%s.html' % page, 'rb').read().replace('%USERNAME', username)


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

    MAILING_LIST = ["anorkus@cern.ch"]
    VALIDATION_STATUS = "VALIDATION_STATUS"
    COMMENTS = "COMMENTS"
    LINKS = "LINKS"
    USER_NAME = "USER_NAME"
    MESSAGE_ID = 'MESSAGE_ID'
    EMAIL_SUBJECT = 'EMAIL_SUBJECT'
    data = { "link" : "index" }
    
    @cherrypy.expose
    def logoutUser(self, *args, **kwargs):
        cherrypy.session['username'] = None
        cherrypy.session['fullname'] = None
        cherrypy.session['userstatus'] = None
        cherrypy.session.regenerate()
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(self.data)

    @cherrypy.expose
    def index(self, *args, **kwargs):
        cherrypy.session.regenerate()
        cherrypy.session['redirectionLink'] = ""

        # If in a private VM, take the username of the machine
        if service.settings['productionLevel'] == 'private':
            cherrypy.session['username'] = pwd.getpwuid(os.getuid())[0]
            cherrypy.session['fullname'] = pwd.getpwuid(os.getuid())[0]
        else:
            cherrypy.session['username'] = service.getUsername()
            cherrypy.session['fullname'] = service.getFullName()

        cherrypy.session['userstatus'] = "Success"
        
        if not self.is_user_in_group(cherrypy.session.get('username')):
            cherrypy.response.headers['Content-Type'] = 'application/json'
            info = "You are not in cms-CERN-users group so you cannot see this page."
            return simplejson.dumps([info])

        cookie = cherrypy.response.cookie
        cookie['redirectionLink'] = cherrypy.session['redirectionLink']
        cookie['redirectionLink'] ['max-age'] = 3600
        cherrypy.session['redirectionLink'] = ""

        if checkAdmin(cherrypy.session.get('username'), Session):
            return loadPage('indexAdmin')
        elif checkValidator(cherrypy.session.get('username'), Session):
            return loadPage('indexValidator')
        else:
            return loadPage('indexUser')
    
    @cherrypy.expose
    def cookieErrorMessage(self):
        return """ <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
               "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
               <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
               <head>
                   <title>Coockie error</title>
                   <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
               </head>
               <body>
               <body style="background-color: #ADD8E6">
               <p style="text-align:center; font-family:verdana"><font color="red"> Please enable cookies to view this site! </font></p>
               </head>
               </html>"""

    def checkUserAndSession(self):
        try:
            cookieString = cherrypy.request.headers.get('cookie')
            sesid = cookieString[cookieString.find("session_id=") + len("session_id="):]
            if sesid != cherrypy.session.id:
                return False
            else:
                if cherrypy.session.get('userstatus') == None:
                    return False
                else:
                    return True
        except Exception as e:
            raise cherrypy.InternalRedirect('/cookieErrorMessage')

    def is_user_in_group(self, username):
        # If in a private VM, bypass
        if service.settings['productionLevel'] == 'private':
            return True

        return 'cms-zh' in service.getGroups() or 'cms-CERN-users' in service.getGroups()
    
    @cherrypy.expose
    def getLogedUserName (self, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps([cherrypy.session.get('fullname')])
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(self.data)

    @cherrypy.expose
    def checkValidatorsRights (self, cat, subCategory, statusKind, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps([checkValidatorRights(cat, subCategory,  statusKind, cherrypy.session.get('username'), Session)])
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(self.data)

    @cherrypy.expose
    def submit(self, releaseName, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return search(releaseName, Session)
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(self.data)

    @cherrypy.expose
    def getDetailInformation(self, catSubCat, relName, state, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            cat = None
            subCat = None
            configuration = self.configuration
            cat, subCat = configuration.get(catSubCat, (None,None))
            return getReleaseDetails(cat, subCat, relName, state, Session)
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(self.data)

    @cherrypy.expose
    def addNewRelease(self, sendMail, categ, subCat, relName, statusNames, statusValues, statComments, statAuthors, statLinks, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            if len(statusNames) == len(statusValues)  and len(statusNames) == len(statComments) and len(statusNames) == len(statAuthors) and len(statusNames) == len(statLinks):
                cherrypy.response.headers['Content-Type'] = 'text/html'
                dictionaryFull = {}
                returnedInformation = {}
                mime_MSG_id = email.utils.make_msgid()
                msgSubject = "New release " + relName + " was added"
                for index in range(len(statusNames)):
                    tmpDictionary = {}
                    tmpDictionary[VALIDATION_STATUS] = statusValues[index]
                    tmpDictionary[COMMENTS] = statComments[index]
                    tmpDictionary[LINKS] = statLinks[index]
                    tmpDictionary[USER_NAME] = statAuthors[index]
                    tmpDictionary[MESSAGE_ID] = mime_MSG_id
                    tmpDictionary['EMAIL_SUBJECT'] = msgSubject
                    dictionaryFull[statusNames[index]] = tmpDictionary
                returnedInformation = newRelease(categ, subCat, relName, simplejson.dumps(dictionaryFull), Session)
                if returnedInformation == "True":
                    msgText = """ New release: %s In category: %s In subcategory: %s Was added. Check it!
                    """ % (relName.upper(), categ.upper(), subCat.upper())
                    self.sendMailOnChanges(msgText, msgSubject, None, mime_MSG_id)
                    info = "New release added successfuly"
                    cherrypy.response.headers['Content-Type'] = 'application/json'
                    return simplejson.dumps([info])
                else:
                    cherrypy.response.headers['Content-Type'] = 'application/json'
                    info = 'Error. In parameters settings'
                    return simplejson.dumps([returnedInformation])
            else:
                cherrypy.response.headers['Content-Type'] = 'application/json'
                info = "Error. Information is damaged"
                return simplejson.dumps([info])
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(self.data)

    @cherrypy.expose
    def updateReleaseInfo(self, comentAuthor, stateValue, relName, newComment, newLinks, catSubCat, statusKind, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            cat = None
            subCat = None
            returnedInformation = None
            configuration = self.configuration
            cat, subCat = configuration.get(catSubCat, (None,None))
            returnedStatusValueOld = getStatus(cat, subCat, relName, statusKind, Session)
            #returnedStatusValueOld - tuple: 0 is old status, 1 is old messageID
            #make new messageID
            new_message_ID = email.utils.make_msgid()
            msgSubject = "Re: "+returnedStatusValueOld[2]+""
            returnedInformation = changeStatus(cat, subCat, relName, statusKind, stateValue, newComment, comentAuthor, newLinks, Session, new_message_ID, msgSubject)
            if returnedInformation == "True":
                msgText = """Release: %s In category: %s In subcategory: %s In column: %s Has Changed: From status: %s To status: %s By: %s Comment: %s
                    """ % (relName.upper(), cat.upper(), subCat.upper(), statusKind.upper(), returnedStatusValueOld[0].upper(), stateValue.upper(), comentAuthor.upper(), newComment)
                self.sendMailOnChanges(msgText, msgSubject, returnedStatusValueOld[1], new_message_ID)
                info = "Release information updated successfuly"
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return simplejson.dumps([info])
            else:
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return simplejson.dumps([returnedInformation])
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(self.data)

    @cherrypy.expose
    def addNewUser (self, user_Name, userTypeValue, usrRDataStatList, usrRFastStatList, usrRFullStatList, usrHDataStatList, usrHFastStatList, usrHFullStatList, usrPDataStatList, usrPFastStatList, usrPFullStatList, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            if userTypeValue == "------":
                info = "User with status ------ cannot be added"
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return simplejson.dumps([info])
            elif userTypeValue == "Validator":
                removeUser(user_Name, Session)
                check1 = addUser(user_Name, None, Session)
                check2 = grantValidatorRights(user_Name, Session)
                check3 = grantValidatorRightsForStatusKindList(user_Name, usrRDataStatList, usrRFastStatList, usrRFullStatList, usrHDataStatList, usrHFastStatList, usrHFullStatList, usrPDataStatList, usrPFastStatList, usrPFullStatList, Session)
                if check1 and check2 and check3:
                    info = "User " + user_Name + " as VALIDATOR was added successfuly"
                    cherrypy.response.headers['Content-Type'] = 'application/json'    
                    return simplejson.dumps([info])
                else:
                    info = "User " + user_Name + " was not added. Problems with database"
                    cherrypy.response.headers['Content-Type'] = 'application/json'
                    return simplejson.dumps([info]) 
            elif userTypeValue == "Admin":
                removeUser(user_Name, Session)
                check1 = addUser(user_Name, None, Session)
                check2 = grantAdminRights(user_Name, Session)
                if check1 and check2:
                    info = "User " + user_Name + " as ADMIN was added successfuly"
                    cherrypy.response.headers['Content-Type'] = 'application/json'
                    return simplejson.dumps([info])
                else:
                    info = "User " + user_Name + " was not added. Problems with database"
                    cherrypy.response.headers['Content-Type'] = 'application/json'
                    return simplejson.dumps([info])
            else:
                info = "Something happend wrong with User Type"
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return simplejson.dumps([info])
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(self.data)

    @cherrypy.expose
    def removeUser (self, user_Name, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            returnInformation = removeUser(user_Name, Session)
            if returnInformation == "True":
                info = "User " + user_Name + " was removed successfuly"
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return simplejson.dumps([info])
            else:
                info = "User " + user_Name + " was not removed because - " + returnInformation
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return simplejson.dumps([info])
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(self.data)
    
    @cherrypy.expose
    def showUsers (self, userName, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            template = Template(open('pages/userRightsTemplate.html', "rb").read())
            title = 'PdmV Users List'
            header = 'Selected Users:'
            users = getAllUsersInfo(userName, Session)
            users = simplejson.loads(users)
            try:
                return template.render(title=title, header=header, users=users['validators'], admins=users['admins'])
            except Exception as e:
                return str(e)
        else:
            cherrypy.InternalRedirect('/index')

    @cherrypy.expose
    def showAllHistory (self, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            template = Template(open('pages/historyTemplate.html', "rb").read())
            title = 'PdmV history'
            header = 'Selected history:'
            history = getAllHistory(Session)
            history = simplejson.loads(history)
            try:
                return template.render(title=title, header=header, history=history)
            except Exception as e:
                return str(e)
        else:
            cherrypy.InternalRedirect('/index')
    
    @cherrypy.expose
    def showHistory (self, subCatList, recoStatsChecked, hltStatsChecked, pagsStatsChecked, releaseList, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            template = Template(open('pages/historyTemplate.html', "rb").read())
            title = 'PdmV history'
            header = 'Selected history:'
            history = getHistory(releaseList, subCatList, recoStatsChecked, hltStatsChecked, pagsStatsChecked, Session)
            history = simplejson.loads(history)
            try:
                return template.render(title=title, header=header, history=history)
            except Exception as e:
                return str(e)
        else:
            cherrypy.InternalRedirect('/index')

    def sendMailOnChanges(self, messageText, emailSubject, org_message_ID, new_message_ID, **kwargs):
        msg = MIMEMultipart()
        if org_message_ID != None:
            msg['In-Reply-To'] = org_message_ID
            msg['References'] = org_message_ID
            
        send_from = "PdmV.ValDb@cern.ch"
        msg['From'] = send_from
        send_to = self.MAILING_LIST
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
            print "Error: unable to send email", e.__class__

    @cherrypy.expose
    def mainInformation(self, catSubCat, relName, **kwargs):
        returned_val = self.checkUserAndSession()
        if returned_val:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            cat = None
            subCat = None
            configuration = self.configuration
            cat, subCat = configuration.get(catSubCat, (None,None))
            return getReleaseShortInfo(cat, subCat, relName, Session)
        else:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return simplejson.dumps(self.data)


def main():
	service.start(AjaxApp())


if __name__ == '__main__':
	main()

