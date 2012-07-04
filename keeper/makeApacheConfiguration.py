#!/usr/bin/env python2.6
'''Makes Apache configuration files for the frontend.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import sys
import socket
import optparse

import config


# Frontends
frontends = {
    # vocms147 = cms-conddb-dev = cms-conddb-int
    'vocms147': [
        'cms-conddb-dev', 'cms-conddb-int',
        'cmstags-dev', 'cmstags-int',
    ],

    # vocms{150,151} = cmsdbfe{1,2}
    'vocms150': ['cms-conddb-prod1'],
    'vocms151': ['cms-conddb-prod2'],

    'private': ['private'],
}

# Aliases
frontends['cms-conddb-dev'] = frontends['vocms147']
frontends['cms-conddb-int'] = frontends['vocms147']
frontends['cmsdbfe1'] = frontends['vocms150']
frontends['cmsdbfe2'] = frontends['vocms151']


# Virtual Hosts
#
# The 'backendHostnames' is a default for all the services of a virtual host.
# It can be overriden by the services if needed. See the description there.
virtualHosts = {
    'cms-conddb-dev': {
        'backendHostnames': ['vocms145'],
        'services': [
            # Keeper's services
            'admin',
            'docs', 'getLumi', 'gtList', 'payloadInspector', 'PdmV/valdb',
            'popcon', 'recordsProvider', 'regressionTest', 'shibbolethTest',

            # Other services
            'gtc-dev',
        ],
    },

    # From the old cmstags.conf
    'cmstags-prod1': {
        'backendHostnames': ['vocms131'],
        'services': ['tc'],
    },

    'cmstags-prod2': {
        'backendHostnames': ['vocms131'],
        'services': ['tc'],
    },

    'cmstags-int': {
        'backendHostnames': ['vocms129'],
        'services': ['tc'],
    },

    'cmstags-dev': {
        'backendHostnames': ['vocms130'],
        'services': ['tc'],
    },

    # From the old cmssdt.conf
    'cmssdt': {
        'services': ['SDT', 'dev', 'controllers', 'qa/perfmondb'],
    },

    # From the old cmscov.conf
    'cmscov': {
        'backendHostnames': ['lxbuild167'],
        'services': ['cmscov'],
    },

    # From the old cms-popularity.conf
    'cms-popularity': {
        'backendHostnames': ['cms-popularity-prod'],
        'services': ['cms-popularity'],
    },

    # From the old cms-popularity-dev.conf
    'cms-popularity-dev': {
        'backendHostnames': ['dashboard34'],
        'services': ['cms-popularity'],
    },
}

# private is a special virtual host which must be the same as -dev but
# with the 'backendHostnames' pointing to the localhost (but using
# the real hostname, not localhost nor 127.0.0.1, since the services only
# listen in the real IP)
virtualHosts['private'] = dict(virtualHosts['cms-conddb-dev'])
virtualHosts['private']['backendHostnames'] = [socket.gethostname()]

# cms-conddb-int must be exactly the same as -dev but with different
# 'backendHostnames' and the production gtc instead of gtc-dev
virtualHosts['cms-conddb-int'] = dict(virtualHosts['cms-conddb-dev'])
virtualHosts['cms-conddb-int']['backendHostnames'] = ['vocms146']
virtualHosts['cms-conddb-int']['services'] = list(virtualHosts['cms-conddb-int']['services'])
virtualHosts['cms-conddb-int']['services'].remove('gtc-dev')
virtualHosts['cms-conddb-int']['services'].append('gtc')

# cms-conddb-prod1 and -prod2 must be equal, and also the same as -int
# but with different 'backendHostnames'
virtualHosts['cms-conddb-prod1'] = dict(virtualHosts['cms-conddb-int'])
virtualHosts['cms-conddb-prod1']['backendHostnames'] = ['cmsdbbe1', 'cmsdbbe2']
virtualHosts['cms-conddb-prod2'] = dict(virtualHosts['cms-conddb-prod1'])


# Services
#
# 'url' is the prefix for the service. It defaults to the service's name.
# It should be only specified if you need to have services with the same URL
# in different virtual hosts that require different settings in each of them.
# (for instance this was used in gtc to have a -dev instance with Shibboleth
# and the old, production one in -int without Shibboleth; both in /gtc).
#
# If 'backendPort' is found, the service will be added in the addingSlashes,
# proxyPass and redirectToHttps sections. The 'backendHostnames', 'backendPort'
# and 'backendUrl' will be used in the proxyPass section.
#
#   If the 'backendHostnames' is not found, the default is the one
#   in the Virtual Hosts entry. How do you know whether to it here or
#   in the virtual host? Some guidelines:
#
#     If your service shares its virtual host with other services and
#     it uses the same backend as the others, use the default.
#     (e.g. keeper's services).
#
#     If your service shares its virtual host with other services but
#     each of them use different backends or you don't use the default one,
#     write the backend in the service.
#     (e.g. gtc, SDT).
#
#     If your service uses different virtual hosts to point to different
#     backends which behave the same way, create only one service and
#     write the backends in the virtual hosts.
#     (e.g. tc, cms-popularity).
#
#     If the service is only present in one virtual host for its own,
#     write the backends in the virtual host. This will allow in the future
#     to run another instance (e.g. -dev) without modifying the service.
#     (e.g. cmscov).
#
#     So, if possible, create as few services as possible and set
#     the backends in the virtual host. i.e. the ideal situation is
#     1 virtual host : default list of load balanced backends for all
#     its services; avoiding unrelated backends in the same virtual host.
#     Also, services should behave the same (i.e. backendPort, url, etc.)
#     regardless of the backendHostname.
#
#   If the 'backendHostnames' contains more than one, it will be load balanced
#   and the proxyPassLoadBalanced section will be used.
#
#   If 'backendUrl' is not found, the default is '/{url}'. This means that
#   by default a service in /service will be mapped to backend's /service,
#   like most of the services we are running. This allows to have consistent
#   behaviour when accessing the service directly to the backend or from
#   the frontend.
#
#   Note: if a service runs in / in both the frontend and the backend,
#   you only need to set 'url' == ''. In addition, in this case
#   you must not set redirectRoot.
#
# If 'shibbolethGroups' is found, the service will get a Shibboleth Location.
# The value is a list of the allowed groups. Moreover, if 'shibbolethMatch'
# is found, the service will get a Shibboleth LocationMatch. The value is
# the pattern to match. 'shibbolethGroups' is also used in this case.
#
# If 'redirectRoot' is found, the root of the frontend will be redirected
# to this service.
#
# If 'customHttp' is found, its value will be appended in the HTTP section.
# If 'customHttps' is found, its value will be appended in the HTTPS section.
services = {
    'weblibs': {
        #-mo FIXME: Set up weblibs: deploy.py/keeper.py need to set
        # up a server (httpd) in the backend machine to serve the files.
        # Otherwise, deploy.py could copy the files to the frontend and
        # serve them here.
    },

    'gtc': {
        'backendHostnames': ['gtc-prod'],
        'backendPort': 443,
    },

    'gtc-dev': {
        'url': 'gtc',
        'backendHostnames': ['gtc-dev'],
        'backendPort': 443,
        'shibbolethGroups': ['zh'],
    },

    # From the old cmstags.conf
    'tc': {
        'backendPort': 4443,
        'backendUrl': '',
        'redirectRoot': True,
        'shibbolethMatch': '^/tc/(?!ReleasesXML$|getCustomIBRequests$|ReleaseExternalsXML$|CategoriesPackagesJSON$|CategoriesManagersJSON$|CreateExternalList$|ReleaseTagsXML$|CreateTagList$|getReleasesInformation$|py_get)',
        'shibbolethGroups': ['zh'],
    },

    # From the old cmssdt.conf
    'SDT': {
        'backendHostnames': ['vocms12'],
        'backendPort': 443,
    },

    'dev': {
        'backendHostnames': ['vocms117'],
        'backendPort': 443,
        'shibbolethGroups': ['zh'],
    },

    'controllers': {
        'backendHostnames': ['cmsperfvm5'],
        'backendPort': 8085,
        'shibbolethGroups': ['zh'],
    },

    'qa/perfmondb': {
        'backendHostnames': ['cmsperfvm5'],
        'backendPort': 8085,
        'backendUrl': '',
        'shibbolethGroups': ['zh'],
    },

    # From the old cmscov.conf
    'cmscov': {
        'url': '',
        'backendPort': 8443,
    },

    # From the old cms-popularity.conf
    'cms-popularity': {
        'url': '',
        'backendPort': 443,
        'shibbolethGroups': ['cms-web-access', 'cms-cern-it-web-access'],
    },
}

# Add the services managed by the keeper
for service in config.servicesConfiguration:
    services[service] = {
        'backendPort': config.servicesConfiguration[service]['listeningPort'],
    }

# Redirect root to docs
services['docs']['redirectRoot'] = True

# Set the allowed groups for services behind Shibboleth
services['admin']['shibbolethGroups'] = ['cms-conddb-dev']
services['PdmV/valdb']['shibbolethGroups'] = ['cms-web-access']
services['shibbolethTest']['shibbolethGroups'] = ['zh']


# Templates
mainTemplate = '''
<VirtualHost {IP}:80>
   ServerName  {virtualHost}.cern.ch
   ServerAlias {virtualHost}

   {security}

   # redirect root
   {redirectRoot}

   # add slashes at the end of the URL if not present already
   {addingSlashes}

   # redirect to https
   {redirectToHttps}

   # more custom configuration
   {customHttp}
</VirtualHost>

<VirtualHost {IP}:443>
   ServerName  {virtualHost}.cern.ch
   ServerAlias {virtualHost}

   SSLEngine On
   SSLProtocol all -SSLv2
   SSLProxyEngine On

   #AB SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM:+LOW
   SSLCipherSuite HIGH:MEDIUM:-LOW:-SSLv2

   SSLCertificateFile    {hostcert}
   SSLCertificateKeyFile {hostkey}

   {security}

   # redirect root
   {redirectRoot}

   # add slashes at the end of the URL if not present already
   {addingSlashes}

   # ProxyPass
   {proxyPass}

   # Shibboleth
   {shibboleth}

   # more custom configuration
   {customHttps}
</VirtualHost>

'''

security = '''
   # This secures the server from being used as a third party proxy server
   ProxyRequests Off
   ProxyPreserveHost On
   ProxyVia On

   ### for Computer.Security @ CERN
   RewriteEngine on
   RewriteCond %{REQUEST_METHOD} ^(TRACE|TRACK)
   RewriteRule .* - [F]
   # Reject request when more than 5 ranges in the Range: header.
   # CVE-2011-3192
   RewriteEngine on
   RewriteCond %{HTTP:range} !(^bytes=[^,]+(,[^,]+){0,4}$|^$)
   RewriteRule .* - [F]
'''

redirectRoot = '''
   RewriteRule ^/+$ /{url}  [NE,L,R]
'''

addingSlashes = '''
   RewriteRule ^/{url}$ /{url}/ [NE,L,R]
'''

redirectToHttps = '''
   RewriteCond %{{HTTPS}} !=on
   RewriteRule ^/{url} https://%{{SERVER_NAME}}%{{REQUEST_URI}} [NE,L,R]
'''

proxyPass = '''
   ProxyPass        /{url} https://{backendHostname}.cern.ch:{backendPort}{backendUrl}
   ProxyPassReverse /{url} https://{backendHostname}.cern.ch:{backendPort}{backendUrl}
'''

proxyPassLoadBalanced = '''
   <Proxy balancer://{balancerName}>
      {balancerMembers}
      ProxySet stickysession=ROUTEID
   </Proxy>
   <Location /{url}>
      Header add Set-Cookie "ROUTEID=.%{{BALANCER_WORKER_ROUTE}}e; path=/{url}" env=BALANCER_ROUTE_CHANGED
      ProxyPass        balancer://{balancerName}
      ProxyPassReverse balancer://{balancerName}
   </Location>
'''

balancerMember = '''
      BalancerMember https://{backendHostname}.cern.ch:{backendPort}{backendUrl} route={route}
'''

shibbolethTemplate = '''
   <{location} {parameter}>
      SSLRequireSSL   # The modules only work using HTTPS

      AuthType shibboleth
      ShibRequestSetting requireSession 1
      ShibRequireSession On

      ShibRequireAll On
      ShibExportAssertion Off

      ShibUseHeaders On
      ### Uncomment above line if you want shibboleth to
      ### use also old-style request headers
      ### may be required for use with Tomcat, or to
      ### allow easy migration of older applications.
      ### It is strongly recommended not to use above
      ### option in order to improve security.

      Require valid-user
      Require ADFS_GROUP {{shibbolethGroupsText}}
 
   </{location}>
'''

shibboleth = shibbolethTemplate.format(
    location = 'Location',
    parameter = '/{url}/',
)

shibbolethMatch = shibbolethTemplate.format(
    location = 'LocationMatch',
    parameter = '{shibbolethMatch}',
)


class NotRegisteredError(Exception):
    pass


def makeApacheConfiguration(virtualHost):
    '''Returns an Apache configuration file for the given virtualHost
    '''

    if virtualHost not in virtualHosts:
        raise NotRegisteredError('Error: %s is not in the registered virtual hosts.' % virtualHost)

    infoMap = virtualHosts[virtualHost]
    if virtualHost == 'private':
        infoMap['virtualHost'] = socket.gethostname()
        infoMap['hostcert'] = config.hostCertificateFiles['private']['crt']
        infoMap['hostkey'] = config.hostCertificateFiles['private']['key']
    else:
        infoMap['virtualHost'] = virtualHost
        infoMap['hostcert'] = config.hostCertificateFiles['devintpro']['crt']
        infoMap['hostkey'] = config.hostCertificateFiles['devintpro']['key']
    infoMap['IP'] = socket.gethostbyname(infoMap['virtualHost'])
    infoMap['security'] = security
    infoMap['redirectRoot'] = ''
    infoMap['addingSlashes'] = ''
    infoMap['redirectToHttps'] = ''
    infoMap['proxyPass'] = ''
    infoMap['shibboleth'] = ''
    infoMap['customHttp'] = ''
    infoMap['customHttps'] = ''
    
    # Documentation: Read the description in the 'services' dictionary.
    for service in infoMap['services']:
        if 'url' not in services[service]:
            services[service]['url'] = service

        if 'backendHostnames' in services[service]:
            backendHostnames = services[service]['backendHostnames']
        else:
            backendHostnames = virtualHosts[virtualHost]['backendHostnames']

        if 'redirectRoot' in services[service]:
            if infoMap['redirectRoot'] != '':
                raise Exception('Tried to redirectRoot to more than one service.')

            infoMap['redirectRoot'] += redirectRoot.format(**services[service])

        if 'backendPort' in services[service]:
            if services[service]['url'] != '':
                infoMap['addingSlashes'] += addingSlashes.format(**services[service])

            infoMap['redirectToHttps'] += redirectToHttps.format(**services[service])

            if 'backendUrl' not in services[service]:
                services[service]['backendUrl'] = '/' + services[service]['url']

            if len(backendHostnames) == 1:
                infoMap['proxyPass'] += proxyPass.format(backendHostname = backendHostnames[0], **services[service])
            else:
                balancerMembers = ''
                route = 0
                for backendHostname in backendHostnames:
                    route += 1
                    dictCopy = dict(services[service])
                    dictCopy.update(backendHostname = backendHostname)
                    balancerMembers += balancerMember.format(route = route, **dictCopy)
                infoMap['proxyPass'] += proxyPassLoadBalanced.format(
                    balancerMembers = balancerMembers,
                    # We can't use the url as the balancerName
                    # if the 'url' contains slashes, e.g. PdmV/valdb.
                    balancerName = services[service]['url'].replace('/', '_'),
                    **services[service]
                )

        if 'shibbolethGroups' in services[service] and virtualHost != 'private':
            services[service]['shibbolethGroupsText'] = ' '.join(['"%s"' % x for x in services[service]['shibbolethGroups']])

            if 'shibbolethMatch' in services[service]:
                infoMap['shibboleth'] += shibbolethMatch.format(**services[service])
            else:
                infoMap['shibboleth'] += shibboleth.format(**services[service])

        if 'customHttp' in services[service]:
            infoMap['customHttp'] += services[service]['customHttp']

        if 'customHttps' in services[service]:
            infoMap['customHttps'] += services[service]['customHttps']

    return mainTemplate.format(**infoMap)


def buildApacheConfiguration(frontend):
    '''Builds all the Apache configuration files for a given frontend.
    '''

    if frontend not in frontends:
        raise NotRegisteredError('Error: %s is not in the registered frontends.' % frontend)

    for virtualHost in frontends[frontend]:
        with open('%s.conf' % virtualHost, 'w') as f:
            f.write(makeApacheConfiguration(virtualHost))


def main():
    '''Prints an Apache configuration file for a given virtualHost
    or regenerates all the configuration files for a frontend
    or for the current one (if no arguments are passed).
    '''

    scriptName = os.path.basename(__file__)

    parser = optparse.OptionParser(usage =
        'Usage: %s -v <virtualHost>\n'
        '  where <virtualHost> can be one of:\n'
        '  %s\n'
        '\n'
        'or: %s -f <frontend>\n'
        '  where <frontend> can be one of:\n'
        '  %s\n'
        '\n'
        'or: %s\n'
        '  (uses current hostname as frontend)\n'
        % (
            scriptName, ', '.join(virtualHosts),
            scriptName, ', '.join(frontends),
            scriptName,
        )
    )

    parser.add_option('-v', '--virtualHost',
        dest = 'virtualHost',
        default = None,
        help = 'The virtual host for which the .conf file will be printed to stdout.'
    )

    parser.add_option('-f', '--frontend',
        dest = 'frontend',
        default = None,
        help = 'The frontend for which all its virtual host .conf files will be written.'
    )

    (options, arguments) = parser.parse_args()

    try:
        if options.virtualHost:
            print makeApacheConfiguration(options.virtualHost),
            return

        if options.frontend:
            buildApacheConfiguration(options.frontend)
            return

        if len(arguments) == 0:
            buildApacheConfiguration(socket.gethostname().rstrip('.cern.ch'))
            return
    except NotRegisteredError as e:
        print str(e)
        print
        parser.print_help()
        sys.exit(-1)

    parser.print_help()
    sys.exit(-2)


if __name__ == '__main__':
    main()

