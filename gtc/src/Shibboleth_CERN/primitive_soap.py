import urllib
from django.conf import settings
from django.utils import html
import logging
import re


def is_user_in_admin_group(username):
   # return True
    try:
        SOAP_SERVICE_LOGIN = settings.SOAP_SERVICE_LOGIN
        SOAP_SERVICE_PASSWD = settings.SOAP_SERVICE_PASSWD
        ADMIN_GROUP_NAME = settings.ADMIN_GROUP_NAME
        search_string = '<string>'+ADMIN_GROUP_NAME +'</string>'
        auth_info = SOAP_SERVICE_LOGIN + ':' + SOAP_SERVICE_PASSWD + "@"
        base_url_address = "winservices-soap.web.cern.ch/winservices-soap/Generic/Authentication.asmx/GetGroupsForUser?UserName="
        #TODO USE HTTPS
        request_url = "http://" + auth_info + base_url_address + html.escape(username)
        logging.debug(request_url)
        print request_url
        remote_data = urllib.urlopen(request_url).read()
        logging.debug(remote_data)
        return search_string in  remote_data
    except Exception as e:
        logging.error(str(e))
        return False


def list_administrator_emails():
   # return True
    try:
        SOAP_SERVICE_LOGIN = settings.SOAP_SERVICE_LOGIN
        SOAP_SERVICE_PASSWD = settings.SOAP_SERVICE_PASSWD
        ADMIN_GROUP_NAME = settings.ADMIN_GROUP_NAME


   #     search_string = '<string>'+ADMIN_GROUP_NAME +'</string>'
        auth_info = SOAP_SERVICE_LOGIN + ':' + SOAP_SERVICE_PASSWD + "@"
        base_url_address = "winservices-soap.web.cern.ch/winservices-soap/Generic/Authentication.asmx/GetListMembers?ListName="
        #TODO USE HTTPS
        print "still works"
        request_url = "http://" + auth_info + base_url_address + html.escape(ADMIN_GROUP_NAME)
        logging.debug(request_url)
        print request_url
        remote_data = urllib.urlopen(request_url).read()
        logging.debug(remote_data)
        return re.findall('<string>(.*)</string>', remote_data) #return search_string in  remote_data
    except Exception as e:
        logging.error(str(e))
        return []

