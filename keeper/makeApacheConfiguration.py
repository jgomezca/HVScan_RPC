#!/usr/bin/env python2.6
'''Makes Apache and Shibboleth configuration files for the frontends.
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
import logging

import config


def getHostname():
    '''Returns the current hostname without '.cern.ch'
    '''

    hostname = socket.gethostname()

    if hostname.endswith('.cern.ch'):
        return hostname[:-len('.cern.ch')]

    return hostname


# Frontends
frontends = {
    # vocms147 = cms-conddb-dev = cms-conddb-int
    'vocms147': [
        'cms-conddb-dev', 'cms-conddb-int',
        'cmstags-dev', 'cmstags-int',
    ],

    # vocms{150,151} = cmsdbfe{1,2}
    'vocms150': [
        'cms-conddb-prod', 'cms-conddb-prod1',
        'cmstags-prod', 'cmstags-prod1',
        'cmssdt-prod', 'cmssdt-prod1',
        'cmscov-prod', 'cmscov-prod1',
        'cms-pop-prod', 'cms-pop-prod1',
    ],
    'vocms151': [
        'cms-conddb-prod', 'cms-conddb-prod2',
        'cmstags-prod', 'cmstags-prod2',
        'cmssdt-prod', 'cmssdt-prod2',
        'cmscov-prod', 'cmscov-prod2',
        'cms-pop-prod', 'cms-pop-prod2',
    ],

    'private': ['private'],
}

# Aliases
frontends['cms-conddb-dev'] = frontends['cms-conddb-int'] = frontends['vocms147']
frontends['cms-conddb-prod1'] = frontends['cmsdbfe1'] = frontends['vocms150']
frontends['cms-conddb-prod2'] = frontends['cmsdbfe2'] = frontends['vocms151']


# Virtual Hosts
#
# The 'backendHostnames' is a default for all the services of a virtual host.
# It can be overriden by the services if needed. See the description there.
virtualHosts = {
    'cms-conddb-dev': {
        'backendHostnames': ['vocms145'],
        'services': [],
    },

    # From the old cmstags.conf
    'cmstags-prod': {
        'backendHostnames': ['vocms131'],
        'services': ['tc'],
    },

    # From the old cmssdt.conf
    'cmssdt-prod': {
        'services': ['SDT', 'dev', 'controllers', 'qa/perfmondb'],
    },

    # From the old cmscov.conf
    'cmscov-prod': {
        'backendHostnames': ['lxbuild167'],
        'services': ['cmscov'],
    },

    # From the old cms-popularity.conf
    'cms-pop-prod': {
        'backendHostnames': ['cms-popularity-prod'],
        'services': ['cms-popularity'],
    },
}

# Add the services managed by the keeper to the cms-conddb-dev virtual host
for service in sorted(config.servicesConfiguration, key = str.lower):
    virtualHosts['cms-conddb-dev']['services'].append(service)

# private is a special virtual host which must be the same as -dev but
# with the 'backendHostnames' pointing to the localhost (but using
# the real hostname, not localhost nor 127.0.0.1, since the services only
# listen in the real IP)
virtualHosts['private'] = dict(virtualHosts['cms-conddb-dev'])
virtualHosts['private']['backendHostnames'] = [getHostname()]

# cms-conddb-int must be exactly the same as -dev but with different
# 'backendHostnames'
virtualHosts['cms-conddb-int'] = dict(virtualHosts['cms-conddb-dev'])
virtualHosts['cms-conddb-int']['backendHostnames'] = ['vocms146']

# cms-conddb-prod{,1,2} must be equal, and also the same as -int
# but with different 'backendHostnames'.
virtualHosts['cms-conddb-prod'] = dict(virtualHosts['cms-conddb-int'])
virtualHosts['cms-conddb-prod']['backendHostnames'] = ['cmsdbbe1', 'cmsdbbe2']
virtualHosts['cms-conddb-prod1'] = dict(virtualHosts['cms-conddb-prod'])
virtualHosts['cms-conddb-prod2'] = dict(virtualHosts['cms-conddb-prod'])

# cmstags-prod has also its -prod{1,2} counterparts, as well as -dev and -int
virtualHosts['cmstags-prod1'] = dict(virtualHosts['cmstags-prod'])
virtualHosts['cmstags-prod2'] = dict(virtualHosts['cmstags-prod'])

virtualHosts['cmstags-dev'] = dict(virtualHosts['cmstags-prod'])
virtualHosts['cmstags-dev']['backendHostnames'] = ['vocms130']

virtualHosts['cmstags-int'] = dict(virtualHosts['cmstags-prod'])
virtualHosts['cmstags-int']['backendHostnames'] = ['vocms129']

# cmssdt-prod, cmscov-prod and cms-pop-prod have also
# their -prod{1,2} counterparts
virtualHosts['cmssdt-prod1'] = dict(virtualHosts['cmssdt-prod'])
virtualHosts['cmssdt-prod2'] = dict(virtualHosts['cmssdt-prod'])

virtualHosts['cmscov-prod1'] = dict(virtualHosts['cmscov-prod'])
virtualHosts['cmscov-prod2'] = dict(virtualHosts['cmscov-prod'])

virtualHosts['cms-pop-prod1'] = dict(virtualHosts['cms-pop-prod'])
virtualHosts['cms-pop-prod2'] = dict(virtualHosts['cms-pop-prod'])


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
        'redirectRoot': True,
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
services['admin']['shibbolethGroups'] = ['cms-cond-dev']
services['dropBox']['shibbolethGroups'] = ['cms-cond-dropbox']
services['dropBox']['shibbolethMatch'] = '^/dropBox/signInSSO$'
services['gtc']['shibbolethGroups'] = ['zh']
services['logs']['shibbolethGroups'] = ['zh']
services['PdmV/valdb']['shibbolethGroups'] = ['cms-web-access']
services['shibbolethTest']['shibbolethGroups'] = ['zh']

# FIXME: gtc still uses HTTP
services['gtc']['protocol'] = 'http'

# Templates
httpdTemplate = '''
# August29, patch
# Reject request when more than 5 ranges in the Range: header.
# CVE-2011-3192
RewriteEngine on
RewriteCond %{{HTTP:range}} !(^bytes=[^,]+(,[^,]+){{0,4}}$|^$)
RewriteRule .* - [F]

ServerTokens ProductOnly
ServerRoot "/etc/httpd"
PidFile run/httpd.pid
Timeout 120
KeepAlive Off
MaxKeepAliveRequests 100
KeepAliveTimeout 15

<IfModule prefork.c>
StartServers       8
MinSpareServers    5
MaxSpareServers   20
ServerLimit      256
MaxClients       256
MaxRequestsPerChild  4000
</IfModule>

<IfModule worker.c>
StartServers         2
MaxClients         150
MinSpareThreads     25
MaxSpareThreads     75 
ThreadsPerChild     25
MaxRequestsPerChild  0
</IfModule>

Listen 80

# Enable name-based virtual hosts for the following IP:port pairs
NameVirtualHost {IP}:80
NameVirtualHost {IP}:443

# Empty default virtual hosts: prevents wrongly matching the other ones.
# (Apache matches the first virtual host if the others do not match).
<VirtualHost {IP}:80>
    ServerName x.ch

    {security}
</VirtualHost>

# We need to set up the SSLEngine in the default HTTPS virtual host
# because SSL connections are fully encrypted, therefore the Host header
# is hidden for Apache until the SSL connection is finished, thus Apache
# can't decide the name-based virtual host to use at that moment,
# using the default one.
<VirtualHost {IP}:443>
    ServerName x.ch

    SSLEngine On
    SSLProtocol all -SSLv2

    #AB SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM:+LOW
    SSLCipherSuite HIGH:MEDIUM:-LOW:-SSLv2

    SSLCertificateFile    {hostcert}
    SSLCertificateKeyFile {hostkey}

    {security}
</VirtualHost>

# Required for Shibboleth
LoadModule authz_host_module modules/mod_authz_host.so

# Required for logging
LoadModule log_config_module modules/mod_log_config.so

# Required for the rewrite rules
LoadModule rewrite_module modules/mod_rewrite.so

# Required for proxy, balancer and session stickyness
LoadModule headers_module modules/mod_headers.so
LoadModule setenvif_module modules/mod_setenvif.so
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_balancer_module modules/mod_proxy_balancer.so
LoadModule proxy_http_module modules/mod_proxy_http.so

Include conf.d/*.conf

User apache
Group apache

ServerAdmin root@localhost
UseCanonicalName Off
DocumentRoot /var/www/html

# For everywhere in the filesystem
<Directory />
    # Do not enable any feature
    Options None

    # Forbid access to filesystem
    Order Deny,Allow
    Deny from all

    # Ignore all .htaccess files
    AllowOverride None
</Directory>

# Hide the backend's server name/version: on non-successful requests, Apache
# will fill it with its signature, even if "unset" is specified. Therefore,
# in succesful requests, we set it to the same. We could unset for succesful
# requests, but that would reveal that Apache is probably not serving the page.
Header set Server Apache

DefaultType text/plain

HostnameLookups Off

# Logging
ErrorLog logs/error_log
LogLevel warn
LogFormat "%v %h %l %u %t \\"%r\\" %>s %b \\"%{{Referer}}i\\" \\"%{{User-Agent}}i\\"" combinedwithvhost
CustomLog logs/access_log combinedwithvhost

ServerSignature Off

AddDefaultCharset UTF-8

# The following directives modify normal HTTP response behavior to
# handle known problems with browser implementations.
BrowserMatch "Mozilla/2" nokeepalive
BrowserMatch "MSIE 4\.0b2;" nokeepalive downgrade-1.0 force-response-1.0
BrowserMatch "RealPlayer 4\.0" force-response-1.0
BrowserMatch "Java/1\.0" force-response-1.0
BrowserMatch "JDK/1\.0" force-response-1.0

# The following directive disables redirects on non-GET requests for
# a directory that does not include the trailing slash.  This fixes a 
# problem with Microsoft WebFolders which does not appropriately handle 
# redirects for folders with DAV methods.
# Same deal with Apple's DAV filesystem and Gnome VFS support for DAV.
BrowserMatch "Microsoft Data Access Internet Publishing Provider" redirect-carefully
BrowserMatch "MS FrontPage" redirect-carefully
BrowserMatch "^WebDrive" redirect-carefully
BrowserMatch "^WebDAVFS/1.[0123]" redirect-carefully
BrowserMatch "^gnome-vfs/1.0" redirect-carefully
BrowserMatch "^XML Spy" redirect-carefully
BrowserMatch "^Dreamweaver-WebDAV-SCM1" redirect-carefully
'''

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

    # Allow this URL for Shibboleth
    <Location /Shibboleth.sso/ADFS>
        Order Allow,Deny
        Allow from all
    </Location>

    {balancerManager}

    # more custom configuration
    {customHttps}

</VirtualHost>
'''

security = '''
    # This secures the server from being used as a forward (third party) proxy server
    ProxyRequests Off

    ProxyPreserveHost On
    ProxyVia Block

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
    ProxyPass        /{url} {protocol}://{backendHostname}.cern.ch:{backendPort}{backendUrl} retry=0
    ProxyPassReverse /{url} {protocol}://{backendHostname}.cern.ch:{backendPort}{backendUrl}
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
        BalancerMember {protocol}://{backendHostname}.cern.ch:{backendPort}{backendUrl} route={route} retry=0
'''

balancerManager = '''
    # Allow access the balancer manager only from this host
    <Location /balancer-manager>
        SetHandler balancer-manager

        Order Deny,Allow
        Deny from all
        Allow from {IP}
    </Location>
'''

shibbolethTemplate = '''
    <{location} {parameter}>
        SSLRequireSSL

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
    parameter = '/{url}',
)

shibbolethMatch = shibbolethTemplate.format(
    location = 'LocationMatch',
    parameter = '{shibbolethMatch}',
)


shibbolethXMLHostName = '''
            <Host name="{virtualHost}.cern.ch" applicationId="{virtualHost}" />
'''

shibbolethXMLAudience = '''
        <saml:Audience>https://{virtualHost}.cern.ch/Shibboleth.sso/ADFS</saml:Audience>
'''

shibbolethXMLApplicationOverride = '''
        <ApplicationOverride id="{virtualHost}" entityID="https://{virtualHost}.cern.ch/Shibboleth.sso/ADFS"/>
'''

shibbolethXMLTemplate = '''
<SPConfig xmlns="urn:mace:shibboleth:2.0:native:sp:config"
    xmlns:conf="urn:mace:shibboleth:2.0:native:sp:config"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="urn:mace:shibboleth:2.0:native:sp:config /usr/share/xml/shibboleth/shibboleth-2.0-native-sp-config.xsd"
    logger="/etc/shibboleth/syslog.logger" clockSkew="180">

    <!-- The OutOfProcess section contains properties affecting the shibd daemon. -->
    <OutOfProcess logger="/etc/shibboleth/shibd.logger">
        <Extensions>
            <Library path="adfs.so" fatal="true"/>
        </Extensions>
    </OutOfProcess>

    <!-- The InProcess section conrains settings affecting web server modules/filters. -->
    <InProcess logger="/etc/shibboleth/native.logger">
        <Extensions>
            <Library path="adfs-lite.so" fatal="true"/>
        </Extensions>
        <ISAPI normalizeRequest="true">
            <!--
            Maps IIS Instance ID values to the host scheme/name/port/sslport. The name is
            required so that the proper <Host> in the request map above is found without
            having to cover every possible DNS/IP combination the user might enter.
            The port and scheme can    usually be omitted, so the HTTP request's port and
            scheme will be used.
            -->
            <Site id="1" name="{defaultVirtualHost}.cern.ch"/>
        </ISAPI>
    </InProcess>

    <!-- Only one listener can be defined, to connect in process modules to shibd. -->
    <!-- <UnixListener address="/var/run/shibboleth/shibd.sock"/> -->
    <TCPListener address="127.0.0.1" port="1600" acl="127.0.0.1"/>

    <!-- This set of components stores sessions and other persistent data in daemon memory. -->
    <StorageService type="Memory" id="mem" cleanupInterval="900"/>
    <SessionCache type="StorageService" StorageService="mem" cacheTimeout="30000" inprocTimeout="900" cleanupInterval="900"/>
    <ReplayCache StorageService="mem"/>
    <ArtifactMap artifactTTL="180"/>

    <!-- To customize behavior, map hostnames and path components to applicationId and other settings. -->
    <RequestMapper type="Native">
        <RequestMap applicationId="default">
            <!--
            The example requires a session for documents in /secure on the containing host with http and
            https on the default ports. Note that the name and port in the <Host> elements MUST match
            Apache's ServerName and Port directives or the IIS Site name in the <ISAPI> element
            below.
            -->
            {hostNames}
        </RequestMap>
    </RequestMapper>

    <!--
    The ApplicationDefaults element is where most of Shibboleth's SAML bits are defined.
    Resource requests are mapped by the RequestMapper to an applicationId that
    points into to this section.
    -->
    <ApplicationDefaults id="default" policyId="default"
        entityID="https://{defaultVirtualHost}.cern.ch"
        homeURL="https://{defaultVirtualHost}.cern.ch"
        REMOTE_USER="user"
        signing="false" encryption="false"
        >

        <!--
        Controls session lifetimes, address checks, cookie handling, and the protocol handlers.
        You MUST supply an effectively unique handlerURL value for each of your applications.
        The value can be a relative path, a URL with no hostname (https:///path) or a full URL.
        The system can compute a relative value based on the virtual host. Using handlerSSL="true"
        will force the protocol to be https. You should also add a cookieProps setting of "; path=/; secure"
        in that case. Note that while we default checkAddress to "false", this has a negative
        impact on the security of the SP. Stealing cookies/sessions is much easier with this disabled.
        -->
        <Sessions lifetime="30000" timeout="15000" checkAddress="false"
            handlerURL="/Shibboleth.sso" handlerSSL="true"
            cookieName="{cookieName}"
            exportLocation="http://localhost/Shibboleth.sso/GetAssertion"
            idpHistory="true" idpHistoryDays="7">

            <!--
            SessionInitiators handle session requests and relay them to a Discovery page,
            or to an IdP if possible. Automatic session setup will use the default or first
            element (or requireSessionWith can specify a specific id to use).
            -->

            <!-- CERN ADFS SessionInitiator -->
            <SessionInitiator type="ADFS" Location="/" id="adfs" isDefault="true"
                relayState="cookie" entityID="https://cern.ch/login" /> 

            <!--
            md:AssertionConsumerService locations handle specific SSO protocol bindings,
            such as SAML 2.0 POST or SAML 1.1 Artifact. The isDefault and index attributes
            are used when sessions are initiated to determine how to tell the IdP where and
            how to return the response.
            -->
            <md:AssertionConsumerService Location="/ADFS" isDefault="true" index="1"
                Binding="http://schemas.xmlsoap.org/ws/2003/07/secext" ResponseLocation="/shibboleth-sp/wsignout.gif"/>

            <!-- LogoutInitiators enable SP-initiated local or global/single logout of sessions. -->
            <LogoutInitiator type="Chaining" Location="/Logout" relayState="cookie">
                <LogoutInitiator type="SAML2" template="/etc/shibboleth/bindingTemplate.html"/>
                <LogoutInitiator type="ADFS"/>
                <LogoutInitiator type="Local"/>
            </LogoutInitiator>

            <!-- md:SingleLogoutService locations handle single logout (SLO) protocol messages. -->
            <md:SingleLogoutService Location="/SLO/SOAP"
                Binding="urn:oasis:names:tc:SAML:2.0:bindings:SOAP"/>
            <md:SingleLogoutService Location="/SLO/Redirect" conf:template="/etc/shibboleth/bindingTemplate.html"
                Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"/>
            <md:SingleLogoutService Location="/SLO/POST" conf:template="/etc/shibboleth/bindingTemplate.html"
                Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"/>
            <md:SingleLogoutService Location="/SLO/Artifact" conf:template="/etc/shibboleth/bindingTemplate.html"
                Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact"/>

            <!-- md:ManageNameIDService locations handle NameID management (NIM) protocol messages. -->
            <md:ManageNameIDService Location="/NIM/SOAP"
                Binding="urn:oasis:names:tc:SAML:2.0:bindings:SOAP"/>
            <md:ManageNameIDService Location="/NIM/Redirect" conf:template="/etc/shibboleth/bindingTemplate.html"
                Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"/>
            <md:ManageNameIDService Location="/NIM/POST" conf:template="/etc/shibboleth/bindingTemplate.html"
                Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"/>
            <md:ManageNameIDService Location="/NIM/Artifact" conf:template="/etc/shibboleth/bindingTemplate.html"
                Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact"/>

            <!--
            md:ArtifactResolutionService locations resolve artifacts issued when using the
            SAML 2.0 HTTP-Artifact binding on outgoing messages, generally uses SOAP.
            -->
            <md:ArtifactResolutionService Location="/Artifact/SOAP" index="1"
                Binding="urn:oasis:names:tc:SAML:2.0:bindings:SOAP"/>

            <!-- Extension service that generates "approximate" metadata based on SP configuration. -->
            <Handler type="MetadataGenerator" Location="/Metadata" signing="false"/>

            <!-- Status reporting service. -->
            <Handler type="Status" Location="/Status" acl="127.0.0.1"/>

            <!-- Session diagnostic service. -->
            <Handler type="Session" Location="/Session"/>

        </Sessions>

        <!--
        You should customize these pages! You can add attributes with values that can be plugged
        into your templates. You can remove the access attribute to cause the module to return a
        standard 403 Forbidden error code if authorization fails, and then customize that condition
        using your web server.
        -->
        <Errors session="/etc/shibboleth/sessionError.html"
            metadata="/etc/shibboleth/metadataError.html"
            access="/etc/shibboleth/accessError.html"
            ssl="/etc/shibboleth/sslError.html"
            localLogout="/etc/shibboleth/localLogout.html"
            globalLogout="/etc/shibboleth/globalLogout.html"
            supportContact="somebody@cern.ch"
            logoLocation="/shibboleth-sp/logo.jpg"
            styleSheet="/shibboleth-sp/main.css"/>

        <!-- Uncomment and modify to tweak settings for specific IdPs or groups. -->
        <!-- <RelyingParty Name="SpecialFederation" keyName="SpecialKey"/> -->

        {audiences}

        <!-- CERN ADFS Metadata -->
        <MetadataProvider type="XML" uri="https://login.cern.ch/adfs/XML/ADFS-metadata.xml"
            backingFilePath="/etc/shibboleth/ADFS-metadata.xml" reloadInterval="7200" />

        <!-- Chains together all your metadata sources. -->
        <!--
        <MetadataProvider type="Chaining">
            <MetadataProvider type="XML" uri="https://espace.cern.ch/authentication/Images%20and%20documents/ADFS-metadata.xml"
                 backingFilePath="/etc/shibboleth/ADFS-metadata.xml" reloadInterval="7200">
               <SignatureMetadataFilter certificate="/etc/shibboleth/fedsigner.pem"/>
            </MetadataProvider>
            <MetadataProvider type="XML" file="/etc/shibboleth/partner-metadata.xml"/>
        </MetadataProvider>
        -->

        <!-- Chain the two built-in trust engines together. -->
        <TrustEngine type="Chaining">
            <TrustEngine type="ExplicitKey"/>
            <TrustEngine type="PKIX"/>
        </TrustEngine>

        <!-- Map to extract attributes from SAML assertions. -->
        <AttributeExtractor type="XML" path="/etc/shibboleth/attribute-map.xml"/>

        <!-- Use a SAML query if no attributes are supplied during SSO. -->
        <AttributeResolver type="Query"/>

        <!-- Default filtering policy for recognized attributes, lets other data pass. -->
        <!-- <AttributeFilter type="XML" path="/etc/shibboleth/attribute-policy.xml"/> -->

        <!-- Simple file-based resolver for using a single keypair. -->
        <CredentialResolver type="File">
            <!--
            <Key>
                <Path>/etc/shibboleth/sp-example.key</Path>
            </Key>
            <Certificate>
                <Path>/etc/shibboleth/sp-example.crt</Path>
            </Certificate>
            -->
        </CredentialResolver>

        {applicationOverrides}

    </ApplicationDefaults>

    <!-- Each policy defines a set of rules to use to secure messages. -->
    <SecurityPolicies>
        <!-- The predefined policy enforces replay/freshness and permits signing and client TLS. -->
        <Policy id="default" validate="false">
            <Rule type="MessageFlow" checkReplay="true" expires="60"/>
            <Rule type="ClientCertAuth" errorFatal="true"/>
            <Rule type="XMLSigning" errorFatal="true"/>
            <Rule type="SimpleSigning" errorFatal="true"/>
        </Policy>
    </SecurityPolicies>

</SPConfig>
'''


attributeMap = '''<Attributes xmlns="urn:mace:shibboleth:2.0:attribute-map"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="urn:mace:shibboleth:2.0:attribute-map /usr/share/xml/shibboleth/shibboleth-2.0-attribute-map.xsd">

<Attribute name="Group" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_GROUP" />
<Attribute name="http://schemas.xmlsoap.org/claims/UPN" id="user"/>
<Attribute name="EmailAddress" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_EMAIL"/>
<Attribute name="CommonName" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_LOGIN"/>
<Attribute name="DisplayName" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_FULLNAME"/>
<Attribute name="PhoneNumber" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_PHONENUMBER"/>
<Attribute name="FaxNumber" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_FAXNUMBER"/>
<Attribute name="MobileNumber" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_MOBILENUMBER"/>
<Attribute name="Building" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_BUILDING"/>
<Attribute name="Firstname" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_FIRSTNAME"/>
<Attribute name="Lastname" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_LASTNAME"/>
<Attribute name="Department" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_DEPARTMENT"/>
<Attribute name="HomeInstitute" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_HOMEINSTITUTE"/>
<Attribute name="HomeDir" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_HOMEDIR"/>
<Attribute name="PersonID" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_PERSONID"/>
<Attribute name="PreferredLanguage" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_PREFERREDLANGUAGE"/>
<Attribute name="role" nameFormat="http://schemas.microsoft.com/ws/2008/06/identity/claims" id="ADFS_ROLE"/>
<Attribute name="IdentityClass" nameFormat="http://schemas.xmlsoap.org/claims" id="ADFS_IDENTITYCLASS"/>

</Attributes>

'''


class NotRegisteredError(Exception):
    pass


def getVirtualHost(virtualHost):
    '''Returns virtualHost, unless is 'private': in this case, return
    the current hostname.
    '''

    if virtualHost == 'private':
        return getHostname()

    return virtualHost


def getBasicInfoMap(frontend):
    '''Returns a basic info map used in both the main HTTP configuration
    and in the virtual hosts.
    '''

    infoMap = {}
    infoMap['security'] = security

    # Get the IP of the current hostname if generating the HTTP configuration in a private machine
    if frontend == 'private':
        infoMap['IP'] = socket.gethostbyname(getHostname())
    else:
        infoMap['IP'] = socket.gethostbyname(frontend)

    if frontend == 'private':
        infoMap['hostcert'] = config.hostCertificateFiles['private']['crt']
        infoMap['hostkey'] = config.hostCertificateFiles['private']['key']
    else:
        infoMap['hostcert'] = config.hostCertificateFiles['devintpro']['crt']
        infoMap['hostkey'] = config.hostCertificateFiles['devintpro']['key']

    return infoMap


def makeHttpdConfiguration(frontend):
    '''Returns the main Apache configuration file (httpd.conf) for the given frontend.
    '''

    if frontend not in frontends:
        raise NotRegisteredError('Error: %s is not in the registered frontends.' % frontend)

    return httpdTemplate.format(**getBasicInfoMap(frontend))


def makeApacheConfiguration(frontend, virtualHost):
    '''Returns an Apache configuration file for the given frontend and virtualHost.
    The frontend is required to get its IP instead of using the virtual host name,
    which could be a load balanced DNS alias (i.e. same virtual host used in
    several frontends).
    '''

    if virtualHost not in virtualHosts:
        raise NotRegisteredError('Error: %s is not in the registered virtual hosts.' % virtualHost)

    infoMap = getBasicInfoMap(frontend)
    infoMap.update(virtualHosts[virtualHost])
    infoMap['virtualHost'] = getVirtualHost(virtualHost)
    infoMap['redirectRoot'] = ''
    infoMap['addingSlashes'] = ''
    infoMap['redirectToHttps'] = ''
    infoMap['proxyPass'] = ''
    infoMap['balancerManager'] = ''
    useBalancerManager = False
    infoMap['shibboleth'] = ''
    infoMap['customHttp'] = ''
    infoMap['customHttps'] = ''
    
    # Documentation: Read the description in the 'services' dictionary.
    for service in infoMap['services']:
        if 'url' not in services[service]:
            services[service]['url'] = service

        if 'protocol' not in services[service]:
            services[service]['protocol'] = 'https'

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
                useBalancerManager = True
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

    if useBalancerManager:
        infoMap['balancerManager'] = balancerManager.format(**infoMap)

    return mainTemplate.format(**infoMap)


def makeShibbolethConfiguration(frontend):
    '''Returns the main Shibboleth configuration file (shibboleth2.xml) for the given frontend.
    '''

    if frontend not in frontends:
        raise NotRegisteredError('Error: %s is not in the registered frontends.' % frontend)

    infoMap = {}
    infoMap['defaultVirtualHost'] = frontends[frontend][0]
    infoMap['hostNames'] = ''
    infoMap['audiences'] = ''
    infoMap['applicationOverrides'] = ''
    infoMap['cookieName'] = frontend

    for virtualHost in frontends[frontend]:
        infoMap['hostNames'] += shibbolethXMLHostName.format(virtualHost = virtualHost)
        infoMap['audiences'] += shibbolethXMLAudience.format(virtualHost = virtualHost)
        infoMap['applicationOverrides'] += shibbolethXMLApplicationOverride.format(virtualHost = virtualHost)

    return shibbolethXMLTemplate.format(**infoMap)


def httpd(arguments):
    '''Generates the main Apache configuration file (httpd.conf) for the given frontend.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog httpd [options]'
    )

    parser.add_option('-f', '--frontend',
        dest = 'frontend',
        default = getHostname(),
        help = 'The frontend for which the file will be generated. Default: %default'
    )

    parser.add_option('-o', '--outputFile',
        dest = 'outputFile',
        default = '/etc/httpd/conf/httpd.conf',
        help = 'The output file. Default: %default'
    )

    (options, arguments) = parser.parse_args(arguments)

    output = makeHttpdConfiguration(options.frontend)
    with open(options.outputFile, 'w') as f:
        logging.info('Generating: %s', options.outputFile)
        f.write(output)


def vhosts(arguments):
    '''Generates all the virtual host Apache configuration files for the given frontend.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog vhosts [options]'
    )

    parser.add_option('-f', '--frontend',
        dest = 'frontend',
        default = getHostname(),
        help = 'The frontend for which the files will be generated. Default: %default'
    )

    parser.add_option('-o', '--outputPath',
        dest = 'outputPath',
        default = '/etc/httpd/conf.d/',
        help = 'The output path. Default: %default'
    )

    (options, arguments) = parser.parse_args(arguments)

    for virtualHost in frontends[options.frontend]:
        output = makeApacheConfiguration(options.frontend, virtualHost)
        outputFile = os.path.join(options.outputPath, '%s.conf' % virtualHost)
        with open(outputFile, 'w') as f:
            logging.info('Generating: %s', outputFile)
            f.write(output)


def shib(arguments):
    '''Generates the main Shibboleth configuration file (shibboleth2.xml)
    and related files (attribute-map.xml) for the given frontend.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog shib [options]'
    )

    parser.add_option('-f', '--frontend',
        dest = 'frontend',
        default = getHostname(),
        help = 'The frontend for which the file will be generated. Default: %default'
    )

    parser.add_option('-o', '--outputPath',
        dest = 'outputPath',
        default = '/etc/shibboleth',
        help = 'The output path. Default: %default'
    )

    (options, arguments) = parser.parse_args(arguments)

    output = makeShibbolethConfiguration(options.frontend)
    outputFile = os.path.join(options.outputPath, 'shibboleth2.xml')
    with open(outputFile, 'w') as f:
        logging.info('Generating: %s', outputFile)
        f.write(output)

    outputFile = os.path.join(options.outputPath, 'attribute-map.xml')
    with open(outputFile, 'w') as f:
        logging.info('Generating: %s', outputFile)
        f.write(attributeMap)


def runAll(arguments):
    '''Runs all commands to update a frontend.
    Typically run without arguments to deploy a frontend.
    '''

    httpd(arguments)
    vhosts(arguments)
    shib(arguments)


def main():
    '''Entry point.
    '''

    commands = {
        'all': runAll,
        'httpd': httpd,
        'vhosts': vhosts,
        'shib': shib,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print 'Usage: %s <command> [arguments].' % os.path.basename(__file__)
        print 'Where <command> can be one of: %s' % ', '.join(commands)
        return -2

    try:
        return commands[sys.argv[1]](sys.argv[2:])
    except Exception as e:
        logging.error(e)
        return -1


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

