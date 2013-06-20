# coding=utf-8
import datetime
import json
import traceback
import urllib
from django.conf import  settings
import os
import subprocess
import re
import json_fetcher


import logging
from GlobalTagCollector.libs.exceptions import DataProviderNotImplemented, DataAccessException, DataFormatException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BaseDataProvider(object):

    def provide(self, *args, **kwargs):
        if hasattr(self, '_provide'):
            return self._provide(*args, **kwargs)
        else:
            raise DataProviderNotImplemented(self.__class__.__name__, self.__name__)

class DatabasesProvider(BaseDataProvider):

    def _provide(self, *args, **kwargs):
        json_data = json_fetcher.JsonFetcher.fetch(settings.DATABASES_LIST)
        return json_data


class SchemasProvider(BaseDataProvider):

    def _provide(self, database_name, *args, **kwargs):
        accounts_list = settings.SCHEMAS_DICT[database_name]["accounts"]
        return accounts_list


class AccountsProvider(BaseDataProvider):

    def __init__(self, *args, **kwargs):
     #   super(self, BaseDataProvider).__init__(*args, **kwargs)
        self.resource_url = settings.SERVICE_ACCOUNT_NAMES

    def _provide(self, *args, **kwargs):
        json_data = json_fetcher.JsonFetcher.fetch(self.resource_url)
        try:
            rez = []
            for account_data in json_data["connection names"]:
                if len(account_data) != 2:
                    #todo log
                    continue
                account_dict = {"account_type": account_data[0], "account_name": "CMS_COND_" + account_data[1]}
                rez.append(account_dict)
            return rez
        except (KeyError, IndexError) as e:
            raise DataFormatException(e)


class TagsProvider(BaseDataProvider):

    def __init__(self, *args, **kwargs):
        self.resource_url = settings.SERVICE_TAGS_FOR_ACCOUNT

    def _provide(self, account_connection_sting, **kwargs):
        logging.info("Providing tags for connection string %s" % account_connection_sting)
        request_url = self.resource_url + urllib.quote(account_connection_sting)
        json_data = json_fetcher.JsonFetcher.fetch(request_url)
        logging.info("tags provider got json data")
        logging.info(json_data)
        try:
            account_conn_str = json_data["Account"] # "oracle://cms_orcoff_prep/CMS_COND_TEMP"
            creation_time_str = json_data["CreationTime"] #27 Feb 2012 18:36 UTC
            tags_containers = json_data["TAGvsContainerName"] # [ [tag, container] ,[..]]
            creation_time = datetime.datetime.strptime(creation_time_str, "%d %b %Y %H:%M UTC")


            rez = []
            for tag_container in tags_containers:
                tag_name = tag_container[0]
                container_name = tag_container[1]
                tag_container_dictionary = {
                    "tag_name": tag_name,
                    "container_name": container_name,
                    "account_connection_string": account_conn_str,
                    "creation_time": creation_time
                }
                rez.append(tag_container_dictionary)
            return rez
        except (KeyError, IndexError, ValueError) as e:
            DataAccessException(e)


class SoftwareReleaseProvider(BaseDataProvider):

    def __init__(self):
        self.software_release_name_pattern = re.compile(settings.SOFTWARE_RELEASE_NAME_PATTERN)
        self.path_to_releases = settings.RELEASES_PATH


    def _provide(self, hardware_architecture_name):
        path = self.path_to_releases.format(hardware_architecture=hardware_architecture_name)
        full_directories_list = os.listdir(path)
        return filter(lambda x: self.software_release_name_pattern.match(x), full_directories_list)


class RecordProvider(BaseDataProvider):

    def _provide(self, architecture_name, release_name):
        params = urllib.urlencode({"hardware_architecture_name":architecture_name, "software_release_name":release_name})
        url = settings.SERVICE_FOR_RECORDS +"?%s" % params
        logger.info("Retriving data form %s" % url)
        json_data = json_fetcher.JsonFetcher.fetch(url)
        try:
            record_object_list = json_data['body']['record_container_map']
            record_object_map = {}
            for record_object_item in record_object_list:
                record_name = record_object_item['record_name']
                container_name = record_object_item['container']
                record_object_map[record_name] = container_name
            return record_object_map # {record_name: container_name, ...}
        except (KeyError, TypeError) as e:
            DataAccessException(e)



class GlobalTagListProvider(BaseDataProvider):

    def __init__(self):
        self.resource_url = settings.SERVICE_GLOBAL_TAG_LIST

    def _provide(self):
        try:
            remote_data = urllib.urlopen(self.resource_url).read()
            remote_data = remote_data.replace("'",'"')
            json_data = json.loads(remote_data)
            return json_data
        except IOError as e:
            raise DataAccessException(e)
        except ValueError as e:
            raise DataFormatException(e)


class GlobalTagProvider(BaseDataProvider):

    def __init__(self):
        self.resource_url = settings.SERVICE_GT_INFO
        self.cretion_time_format = "%d %B, %Y %H:%M:%S" #18 February, 2012 21:11:58
        self.entry_time_format = "%d %b %Y %H:%M" #"09 Jun 2009 10:05"

    def _get_remote_data(self, global_tag_name):
        request_url = self.resource_url + urllib.quote(global_tag_name)
        response = urllib.urlopen(request_url)
        if response.getcode() != 200: # if we got answer NOT OK
            response = urllib.urlopen(request_url)
            remote_data = response.read()
        else:
            remote_data = response.read()
            if remote_data == '[{}]': # if we got empty response
                response = urllib.urlopen(request_url)
                remote_data = response.read()
        json_data = json.loads(remote_data)
        return json_data

    def _provide(self, global_tag_name):
        try:
            json_data = self._get_remote_data(global_tag_name)
            header = json_data.pop("header")
            body = json_data.pop("body")
            rez = {"GlobalTagName": header["GlobalTagName"],
                   "creation_time": datetime.datetime.strptime(header["creation_time"], self.cretion_time_format),
                   "CMSSW_VERSION": header["CMSSW_VERSION"],
                   "global_tag_entries": body
            }
            for global_tag_entry in rez["global_tag_entries"]:
                pass
                #global_tag_entry["time"] = datetime.datetime.strptime(
                #    global_tag_entry["time"], self.entry_time_format)
            return rez
        except IOError as e: #thowed by urllib
            raise DataAccessException(e)
        except (ValueError, KeyError, IndexError) as e: #Not valid json, not valid json stucture
            raise DataFormatException(e)

class HardwareArchitecturesListProvider(BaseDataProvider):

    def __init__(self):
        self.resource_url = settings.HARDWARE_ARCHITECTURES_LIST

    def _provide(self):
        try:
            remote_data = urllib.urlopen(self.resource_url).read()
            architectures_list = json.loads(remote_data)
            return architectures_list
        except IOError as e:
            raise DataAccessException(e)
        except ValueError as e:
            raise DataFormatException(e)
