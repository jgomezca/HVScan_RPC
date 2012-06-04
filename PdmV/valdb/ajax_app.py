import cherrypy
import os
import smtplib
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
#-mo FIXME: Put methods in common/ for building connection strings of all kinds
#           for all services.
connectionDictionary = service.getSecrets()['connections']['dev']
connectionString = 'oracle://' + connectionDictionary['user'] + ':' + connectionDictionary['password'] + '@' + connectionDictionary['db_name']
engine = create_engine(connectionString, echo=False)
Session = sessionmaker(bind=engine)


def getWinServicesConnectionString():
    winservices = service.getSecrets()['winservices']
    return 'https://%s:%s@winservices-soap.web.cern.ch/winservices-soap/Generic/Authentication.asmx/' % (winservices['user'], winservices['password'])


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

    MAILING_LIST = ["danilo.piparo@cern.ch", "jean-roch.vlimant@cern.ch", "a.tilmantas@gmail.com"]
    VALIDATION_STATUS = "VALIDATION_STATUS"
    COMMENTS = "COMMENTS"
    LINKS = "LINKS"
    USER_NAME = "USER_NAME"
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
        returned_val = self.checkUserAndSession()
        if returned_val:
            cookie = cherrypy.response.cookie
            cookie['redirectionLink'] = cherrypy.session['redirectionLink']
            cookie['redirectionLink'] ['max-age'] = 3600
            cherrypy.session['redirectionLink'] = ""  
            if self.is_user_in_group(cherrypy.session.get('username')):
                if checkAdmin(cherrypy.session.get('username'), Session):
                    return open('pages/indexAdmin.html', "rb").read()
                elif checkValidator(cherrypy.session.get('username'), Session):
                    return open('pages/indexValidator.html', "rb").read()
                else:
                    return open('pages/indexUser.html', "rb").read()
            else:
                return open('pages/indexLogin.html', "rb").read()
        else:
            return open('pages/indexLogin.html', "rb").read()
    
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

    @cherrypy.expose
    def redirection(self, username, psw, adress, **kwargs):
        try:
            cherrypy.session.regenerate()
            User_Status = self.user_status(username, psw)
            User_Name, User_Full_Name = self.get_user_full_name_username(username, psw)
            cherrypy.session['username'] = User_Name
            cherrypy.session['fullname'] = User_Full_Name
            cherrypy.session['userstatus'] = User_Status
            if cherrypy.session.get('userstatus') == "Success":
                if self.is_user_in_group(cherrypy.session.get('username')):
		    cherrypy.session['redirectionLink'] = adress
                    return simplejson.dumps(self.data)
                else:
                    cherrypy.response.headers['Content-Type'] = 'application/json'
                    info = "You are not in cms-CERN-users group so you cannot see this page."
                    return simplejson.dumps([info])
            else:
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return simplejson.dumps([str(cherrypy.session.get('userstatus'))])
        except Exception as e:
            print "redirection> ERROR :", e
            print "Unknown error"

    def is_user_in_group(self, username):
        # return True
        try:
            request_url = getWinServicesConnectionString() + 'GetGroupsForUser?UserName=' + username
            remote_data = urllib.urlopen(request_url).read()
            search_cms_zh = '<string>'+ 'cms-zh' +'</string>'
            search_cms_u = '<string>'+ 'cms-CERN-users' +'</string>'
            if search_cms_u or search_cms_zh in remote_data:
                return True
        except Exception as e:
            print "is_user_in_group> ERROR from soap auth:", e
            return False

    def user_status(self, username, psw):
        dict = {"0" : "Account disabled or activation pending or expired", \
            "1" : "Invalid password", \
            "2" : "Incorrect login or E-mail", \
            "3" : "Success", \
        }
        try:
            request_url = getWinServicesConnectionString() + 'GetUserInfo?UserName=' + username + '&Password=' + psw
            remote_data = urllib.urlopen(request_url).read()
            search_string = '</auth>'
            return dict[remote_data[remote_data.find(search_string) - 1]]
        except Exception as e:
            print "Error in getting information about user, errno=", remote_data[remote_data.find(search_string)-1]
            print e
            return None

    def get_user_full_name_username(self, username, psw):
        try:
            request_url = getWinServicesConnectionString() + 'GetUserInfo?UserName=' + username + '&Password=' + psw
            remote_data = urllib.urlopen(request_url).read()
            user_name = remote_data[remote_data.find('<login>') + len('<login>'):remote_data.find('</login>')]
            full_name = remote_data[remote_data.find('<name>') + len('<name>'):remote_data.find('</name>')]
            return user_name, full_name
        except Exception as e:
            print "Error in getting information about user"
            print e
            return None, None
    
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
                for index in range(len(statusNames)):
                    tmpDictionary = {}
                    tmpDictionary[VALIDATION_STATUS] = statusValues[index]
                    tmpDictionary[COMMENTS] = statComments[index]
                    tmpDictionary[LINKS] = statLinks[index]
                    tmpDictionary[USER_NAME] = statAuthors[index]
                    dictionaryFull[statusNames[index]] = tmpDictionary
                returnedInformation = newRelease(categ, subCat, relName, simplejson.dumps(dictionaryFull), Session)
                if returnedInformation == "True":
                    msgText = """ New release: %s In category: %s In subcategory: %s Was added. Check it!
                    """ % (relName.upper(), categ.upper(), subCat.upper())
                    msgSubject = "New release was added"
                    self.sendMailOnChanges(msgText, msgSubject)
                    info = "New release added successfuly"
                    cherrypy.response.headers['Content-Type'] = 'application/json'
                    return simplejson.dumps([info])
                else:
                    cherrypy.response.headers['Content-Type'] = 'application/json'
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
            returnedInformation = changeStatus(cat, subCat, relName, statusKind, stateValue, newComment, comentAuthor, newLinks, Session)
            if returnedInformation == "True":
                msgText = """Release: %s In category: %s In subcategory: %s In column: %s Has Changed: From status: %s To status: %s By: %s Comment: %s
                    """ % (relName.upper(), cat.upper(), subCat.upper(), statusKind.upper(), returnedStatusValueOld.upper(), stateValue.upper(), comentAuthor.upper(), newComment)
                msgSubject = "Release information was updated"
                self.sendMailOnChanges(msgText, msgSubject)
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

    def sendMailOnChanges(self, messageText, emailSubject, **kwargs):
        msg = MIMEMultipart()
        send_from = "PdmV.ValDb@cern.ch"
        msg['From'] = send_from
        send_to = self.MAILING_LIST
        msg['To'] = COMMASPACE.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = emailSubject
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

