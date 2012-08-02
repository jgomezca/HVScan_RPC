import json
import logging
import urllib2
from exceptions import JsonResourceNotReachable, JsonResourceDataFormatError

logger = logging.getLogger(__name__)

class JsonFetcher(object):

    @classmethod
    def fetch(cls, url):
        """Returns json structure or raises JsonResourceNotAvailable"""
        logging.info("Fetching url: %s" % url)
        try:
            web_resource = urllib2.urlopen(url)
            if web_resource.code != 200:
                raise JsonResourceNotReachable(url, reason="Bad status code", extra_information=web_resource.code)
            url_data = web_resource.read()
        except urllib2.URLError as e:
            logging.error("Failed to fetch url: %s\n%s" % (url, str(e)))
            raise JsonResourceNotReachable(url=url, reason=str(e))
        except Exception as e:
            logger.critical(e)

        try:
            logging.debug("Parsing json structure from url: %s\n" % url)
            json_data = json.loads(url_data)
            return json_data
        except ValueError as e:
            logging.error("Json could not be parsed. Source url: %s\n%s" % (url, str(e)))
            raise JsonResourceDataFormatError(url=url, reason=e.reason, extra_information=url_data)