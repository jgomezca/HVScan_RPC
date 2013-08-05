'''Fabfile used to automate deployment of frontends and backends.

Usage examples:

  * Full deployment on production of v1.0:

    $ fab deploy:level=pro,tag=v1.0

    You must warn one day before running this, and avoid doing in on Fridays.


  * Frontends-only deployment on production of v1.0, including changes
    in Shibboleth's configuration.

    $ deployFrontends:level=pro,tag=v1.0,shib=yes

    This includes Shibboleth reconfiguration and restart, which implies
    that users will see an automatic re-signIn. Even being automatic,
    non-idempotent requests like POST could be lost as per CERN IT,
    and therefore, this is non-transparent and the same rules as a full
    deployment apply, read above.

    Shibboleth requires reconfiguration if, for instance, a new domain
    was added. If you only modify Apache's configuration, use the next one,
    since it is much less invasive.


  * Frontends-only deployment on production of v1.0,
    without reconfiguring/restarting Shibboleth (default):

    $ fab deployFrontends:level=pro,tag=v1.0

    This will only regenerate Apache's configuration and gracefully
    restart it, which should be transparent for users. Use this when,
    for instance, you just add a new proxy/service/rewrite rule in Apache.

    This is the default since it is the safest option and in most deployments
    the frontend's configuration does not change (or the only changes are
    to Apache and not Shibboleth). If the deployer really needed to restart
    Shibboleth and forgot to specify shib=yes, he can anyway do it later after
    a full deployment.


  * Redeploy/Bootstrap a backend/frontend (in a new machine, e.g. after
    reinstallation of a machine or migration to another SLC):

    $ fab redeployFrontend:frontend=cmsdbfe2,level=pro,tag=v1.0,shib=yes

    Typically you will need shib=yes. The default is 'no' to be consistent
    with the other functions, but you will get a warning if so as a reminder.
'''

import os
import config
from fabric.api import run, sudo, cd, task, execute, env

env.use_ssh_config = True


configuration = {
    'pro': {
        'frontends': ['cmsdbfe1', 'cmsdbfe2'],
        'backends': ['cmsdbbe1', 'cmsdbbe2'],
    },

    'int': {
        'frontends': ['cms-conddb-dev'],
        'backends': ['vocms146'],
    },

    'dev': {
        'frontends': ['cms-conddb-dev'],
        'backends': ['vocms145'],
    }
}


servicesRepository = '/tmp/services'
keeperPath = os.path.join(servicesRepository, 'keeper')


# Utility functions
def setup(tag):
    '''Clones the cmsDbWebServices.git repository and checks out the given tag.
    '''

    sudo('rm -rf %s' % servicesRepository)
    run('git clone -q %s %s' % (config.servicesRepository, servicesRepository))
    with cd(servicesRepository):
        run('git checkout -q %s' % tag)


# Commands that actually deploy a frontend or a backend, independent of hostname
def deployFrontend(tag, shib = 'no'):
    setup(tag)

    if shib == 'yes':
        sudo('%s shib' % (os.path.join(keeperPath, 'makeApacheConfiguration.py')))

    sudo('%s httpd' % (os.path.join(keeperPath, 'makeApacheConfiguration.py')))
    sudo('%s vhosts' % (os.path.join(keeperPath, 'makeApacheConfiguration.py')))

    # Set required SELinux policies
    sudo('/usr/sbin/setsebool -P httpd_can_network_connect on')

    if shib == 'yes':
        sudo('/etc/init.d/shibd restart')

    sudo('/etc/init.d/httpd graceful')

def deployBackend(level, tag):
    if level == 'pro':
        disableBackend(level, tag, env.host_string)

    setup(tag)
    sudo('%s' % (os.path.join(keeperPath, 'makeRedisConfiguration.py')))
    sudo('/etc/init.d/redis restart')
    sudo('%s --force --update --nosendEmail -s %s %s' % (os.path.join(keeperPath, 'deploy.py'), config.servicesRepository, tag))

    if level == 'pro':
        enableBackend(level, tag, env.host_string)

def manageBackend(tag, backendHostname, action):
    setup(tag)
    run('%s %s %s' % (os.path.join(keeperPath, 'manageApacheWorkers.py'), action, backendHostname))


# Tasks that redeploy an explicit backend or frontend (typically used for
# bootstrapping after a reinstallation of a machine/migration to another SLC)
def redeployChecks(kind, hostname, level, shib):
    if hostname not in configuration[level][kind]:
        raise Exception("%s is not in %s level's %s: %s" % (hostname, level, kind, configuration[level]['frontends']))
    if shib != 'yes':
        print 'Warning: If you are redeploying/bootstrapping, you probably want shib == yes.'
        if 'y' != raw_input('Continue? [n]: '):
            raise Exception('Aborted by the user.')

@task
def redeployFrontend(frontend, level, tag, shib = 'no'):
    redeployChecks('frontends', frontend, level, shib)
    env.hosts = [frontend]
    execute(deployFrontend, tag, shib)

@task
def redeployBackend(backend, level, tag, shib = 'no'):
    redeployChecks('backends', backend, level, shib)
    env.hosts = [backend]
    execute(deployBackend, tag, shib)


# Tasks that enable/disable a backend in the load balancer of all frontends
# of a given production level
@task
def enableBackend(level, tag, backendHostname):
    env.hosts = configuration[level]['frontends']
    execute(manageBackend, tag, backendHostname, 'enable')

@task
def disableBackend(level, tag, backendHostname):
    env.hosts = configuration[level]['frontends']
    execute(manageBackend, tag, backendHostname, 'disable')


# Tasks that know where to deploy the frontends or backends for a given
# production level
@task
def deployFrontends(level, tag, shib = 'no'):
    env.hosts = configuration[level]['frontends']
    execute(deployFrontend, tag, shib)

@task
def deployBackends(level, tag):
    env.hosts = configuration[level]['backends']
    execute(deployBackend, level, tag)


# Task that deploy both frontends and backends for a given production level
@task
def deploy(level, tag, shib = 'no'):
    deployBackends(level, tag)
    deployFrontends(level, tag, shib)

