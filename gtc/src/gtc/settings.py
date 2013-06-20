# Django settings for gtc project.
from os.path import abspath, dirname, join
import socket
import sys
import json

import secrets

SETTINGS_ROOT = abspath(join(dirname(__file__)))
SOURCE_ROOT = abspath(join(dirname(__file__), ".."))
SERVICE_ROOT = abspath(join(dirname(__file__), "..", ".."))

settings_from_keeper_file = abspath(join(SETTINGS_ROOT, "keeper_settings.json"))
f = open(settings_from_keeper_file,"rb")
SETTINGS_FROM_KEEPER = json.load(f)
f.close()

PRODUCTION_LEVEL = SETTINGS_FROM_KEEPER["productionLevel"]

DEBUG = True #TODO set debug mode according settings from keeper
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

if PRODUCTION_LEVEL == "private":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': abspath(join(SERVICE_ROOT, "var", "db", "test.db")),
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        }
    }
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
elif PRODUCTION_LEVEL == "dev" :
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.oracle',
            'NAME': secrets.secrets["gtc"]["connections"]["dev"]["owner"]["db_name"],
            'USER': secrets.secrets["gtc"]["connections"]["dev"]["owner"]["user"],
            'PASSWORD': secrets.secrets["gtc"]["connections"]["dev"]["owner"]["password"],
            'HOST': '',
            'PORT': '',
        }
    }
elif (PRODUCTION_LEVEL == "int") or (PRODUCTION_LEVEL == "pro"):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.oracle',
            'NAME': secrets.secrets["gtc"]["connections"]["pro"]["owner"]["db_name"],
            'USER': secrets.secrets["gtc"]["connections"]["pro"]["owner"]["user"],
            'PASSWORD': secrets.secrets["gtc"]["connections"]["pro"]["owner"]["password"],
            'HOST': '',
            'PORT': '',
            }
    }
else:
    raise Exception("Correct settings could not be detected")

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Zurich'# 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/gtc/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 's5hsm*ghd@fnsudj8t8hrjgi5u=ex6p1a00t8e#%-0*m-s3rxi'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'gtc.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'gtc.wsgi.application'

AUTHENTICATION_BACKENDS = (
    'GlobalTagCollector.views.ShibbolethBackend', #custom
    'django.contrib.auth.backends.ModelBackend', #default
    )

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'GlobalTagCollector',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django.contrib.flatpages',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose',
            'strm': sys.stdout,
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends':{
            'level': 'DEBUG',
            'handlers': [],
            'propagate': False,
        },
        '':{
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}
#custom
TEMPLATE_CONTEXT_PROCESSORS = (
 "django.contrib.auth.context_processors.auth",
 "django.core.context_processors.debug",
 "django.core.context_processors.i18n",
 "django.core.context_processors.media",
 "django.core.context_processors.static",
 "django.core.context_processors.tz",
 "django.contrib.messages.context_processors.messages",
 #from here manually added. Before -default
 'django.core.context_processors.request',

)
#=======================================================================================================================
#SERVICE_ACCOUNT_NAMES = 'http://webcondvm2:8083/get_connectionName'
##SERVICE_TAGS_FOR_ACCOUNT = 'http://cms-conddb.cern.ch/payload_inspector_1.1/?getTAGvsContainer='
#SERVICE_TAGS_FOR_ACCOUNT = 'https://cms-conddb-dev.cern.ch/payloadInspector/get_tagsVScontainer?dbName='
#SERVICE_FOR_RECORDS = 'https://kostas-conddev5.cern.ch:8088/recordsProvider/record_container_map'#?hardware_architecture_name=slc5_amd64_gcc323&software_release_name=CMSSW_5_1_0
#SERVICE_GLOBAL_TAG_LIST = 'http://webcondvm2.cern.ch:8081/get_list_GT'
#SERVICE_GT_INFO = 'http://webcondvm2.cern.ch:8081/getGTinfo?GT_name='
##SERVICE_GT_INFO = 'https://kostas-conddev5.cern.ch/gtList/getGTinfo?GT_name='
#SERVICE_GT_INFO_UPDATE = 'http://webcondvm2.cern.ch:8081/uploadGT?tag='
#RELEASES_PATH = "/afs/cern.ch/cms/{hardware_architecture}/cms/cmssw"
#SOFTWARE_RELEASE_NAME_PATTERN = "^CMSSW_(\d+)_(\d+)_(\d+)(?:_pre(\d+))?$"
#DATABASES_LIST = "https://cms-conddb-dev.cern.ch/payloadInspector/get_dbs"
#SCHEMAS_LIST = "https://cms-conddb-dev.cern.ch/payloadInspector/get_schemas?"


def getHostname():
    '''Returns the 'official' hostname where services are run.
    In private deployments, this is the current hostname. However,
    in official ones, could be, for instance, a DNS alias.
    e.g. cms-conddb-dev.cern.ch
    '''
    hostnameByLevel = {
        'pro': 'cms-conddb-prod.cern.ch',
        'int': 'cms-conddb-int.cern.ch',
        'dev': 'cms-conddb-dev.cern.ch',
        'private': socket.getfqdn(),
        }

    return hostnameByLevel[PRODUCTION_LEVEL]

HOSTNAME = getHostname()

SERVICE_ACCOUNT_NAMES = 'https://%s/payloadInspector/get_connectionName' % HOSTNAME
SERVICE_TAGS_FOR_ACCOUNT = 'https://%s/payloadInspector/get_tagsVScontainer?dbName=' % HOSTNAME
SERVICE_FOR_RECORDS = 'https://%s/recordsProvider/record_container_map' % HOSTNAME#?hardware_architecture_name=slc5_amd64_gcc323&software_release_name=CMSSW_5_1_0
SERVICE_GLOBAL_TAG_LIST = 'https://%s/gtList/getGTList' % HOSTNAME
SERVICE_GT_INFO = 'https://%s/gtList/getGTInfo?GT_name=' % HOSTNAME
RELEASES_PATH = "/afs/cern.ch/cms/{hardware_architecture}/cms/cmssw"
SOFTWARE_RELEASE_NAME_PATTERN = "^CMSSW_(\d+)_(\d+)_(\d+)(?:_pre(\d+))?$"
DATABASES_LIST = "https://%s/payloadInspector/get_dbs" % HOSTNAME
SCHEMAS_DICT = secrets.secrets["payloadInspector"]["connections"]
HARDWARE_ARCHITECTURES_LIST = 'https://cmstags.cern.ch/tc/public/py_getActiveArchitectures'

ADMIN_GROUP_NAME = 'global-tag-administrators'

#custom
#SECURE_PROXY_SSL_HEADER  = ('HTTP_X_FORWARDED_PROTOCOL', 'https')

LOGIN_URL = '/gtc/accounts/login/'

EMAIL_HOST_USER = secrets.secrets["gtc"]["email"]["sender"]
EMAIL_HOST_PASSWORD = secrets.secrets["gtc"]["email"]["password"]
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.cern.ch"