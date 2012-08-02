import logging

logger = logging.getLogger(__name__)

class ResourceNotAvailable(Exception):
    pass

class JsonResourceNotAvailable(Exception):

    def __init__(self, url, reason, extra_information):
        super(JsonResourceNotAvailable, self).__init__()
        self._url = url
        self._reason = reason
        self._extra_information = extra_information

    def __str__(self):
        if self._extra_information:
            return "Json resource not available at url '%s'. Reason: %s. Extra information %s" % \
                   (self._url, str(self._reason), str(self._extra_information))
        else:
            return "Json resource not available at url '%s'. Reason: %s." % (self._url, str(self._reason))

class JsonResourceNotReachable(JsonResourceNotAvailable):
    pass

class JsonResourceDataFormatError(JsonResourceNotAvailable):
    pass




#-------------
class DataProviderNotImplemented(Exception):
    """Raised when data provider metod not implemented (probaly "provide")"""

    def __init__(self, class_name, method_name, *args, **kwargs):
        super(DataProviderNotImplemented, self).__init__(*args, **kwargs)
        self.method_name = method_name
        self.class_name = class_name

    def __str__(self):
        return "Data provider {class_name} method {method_name} not "\
               "implemented".format(class_name=self.class_name,
            method_name=self.method_name)


class DataAccessException(Exception):

    def __init__(self, exception, *args, **kwargs):
        super(DataAccessException, self).__init__(*args, **kwargs)
        self.exception = exception
        self.traceback = ''

    def __str__(self):
        return "DataAccessException. Real exception: \n{exception}\nOriginal "\
               "taceback: \n{traceback}".format(traceback=self.traceback,
            exception=self.exception)


class DataFormatException(Exception):

    def __init__(self, exception, *args, **kwargs):
        super(DataFormatException, self).__init__(*args, **kwargs)
        self.exception = exception
        self.traceback = ''

    def __str__(self):
        return "DataAccessException. Real exception: \n{exception}\nOriginal "\
               "taceback: \n{traceback}".format(traceback=self.traceback,
            exception=self.exception)

#--------
class TagNotDetectedException(Exception):

    def __init__(self, tag_name, account_type_obj, account_name, base_exception
                 , *args, **kwargs):
        super(TagNotDetectedException, self).__init__(*args, **kwargs)
        self.tag_name = tag_name
        self.account_type_obj = account_type_obj
        self.account_name = account_name
        self.e = base_exception

    def __str__(self):
        return "Tag could not be detected with name %s for account type '%s' " \
               "and account name '%s. Base exception %s" % (
                str(self.tag_name), str(self.account_type_obj),
                str(self.account_name), str(self.e) )

#        if self.tag_name is None: #todo del
#            return "Exception: tag detection failed"
#        return "Exception: tag  %s detection failed" % str(self.tag_name)


class TagDetectionCanceled(Exception):
    def __init__(self, account_type, tag_name, *args, **kwargs):
        super(TagDetectionCanceled, self).__init__(*args, **kwargs)
        self.account_type = account_type
        self.tag_name = tag_name

    def __str__(self):
        return "Exception. Tag detection canceled. Reason: Account type in " \
               "ignore list. Tag name: %s, Account type: %s" % (self.tag_name, self.account_type)

class RecordNotDetectedException(Exception):
        def __init__(self, tag, record_name, *args, **kwargs):
            super(RecordNotDetectedException, self).__init__(*args, **kwargs)
            self.tag = tag
            self.record_name = record_name
        def __str__(self):
            return "Exception. Could not detect record with name %s which " \
                   "belongs to tag %s" % (self.record_name, str(self.tag))


class GTEntryCreationFromRemoteCanceled(Exception):
    def __init__(self, remote_gt_entry, *args, **kwargs):
        super(GTEntryCreationFromRemoteCanceled, self).__init__(*args,
                                                                **kwargs)
        self.remote_gt_entry = remote_gt_entry
        logger.warn("GTEntry from remote gt_entry '%s'could not be created. \
                    It is in ignore list" % str(remote_gt_entry))

    def __str__(self):
        return "Exception: tag  %s detection failed" % str(self.tag_name)



class ZeroImportableChildrenException(Exception):
    def __init__(self, gt_name=None, *args, **kwargs):
        super(ZeroImportableChildrenException, self).__init__(*args, **kwargs)
        self.gt_name = gt_name

    def __str__(self):
        return "Exception: Zero importable children in GT named %s " % \
               str(self.gt_name)


#--------------------------------------------
class UnknownSoftwareReleaseNamePattern(Exception):

    def __init__(self, software_release_name, *args, **kwargs):
        super(UnknownSoftwareReleaseNamePattern, self).__init__(*args,
            **kwargs)
        self.software_release_name = software_release_name

    def __str__(self):
        return "Software release name was not recognised with known patterns. Name: %s" % str(self.software_release_name)


class AccountTypeNotFoundedForPFNBase(Exception):

    def __init__(self, pfn_base, *args, **kwargs):
        super(AccountTypeNotFoundedForPFNBase, self).__init__(*args, **kwargs)
        self.pfn_base = pfn_base

    def __str__(self):
        return "Account type could not be detected by using pfn base: %s" % str(self.pfn_base)


class AccountNotFoundedException(Exception):

    def __init__(self, account_type_obj, account_name):
        self.account_type_obj = account_type_obj
        self.account_name = account_name

    def __str__(self):
        return "Account with name %s could not be detected in account type %s" % (self.account_type_obj, self.account_name)


class AccountNotFoundedException(Exception):

    def __init__(self, account_type_obj, account_name):
        self.account_type_obj = account_type_obj
        self.account_name = account_name

    def __str__(self):
        return "Account with name %s could not be detected in account type %s" % (self.account_name, self.account_type_obj)


class RawGTEntryIgnoredException(Exception):
    def __init__(self, reason, raw_data=None):
        self.reason = reason
        self.raw_data = raw_data

    def __str__(self):
        return self.reason
