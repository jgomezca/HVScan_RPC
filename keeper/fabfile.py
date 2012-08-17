'''Fabfile used to automate deployment of frontends and backends.

Usage example: $ fab deploy:level=pro,tag=v1.0
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

    run('rm -rf %s' % servicesRepository)
    run('git clone -q %s %s' % (config.servicesRepository, servicesRepository))
    with cd(servicesRepository):
        run('git checkout -q %s' % tag)


# Commands that actually deploy a frontend or a backend, independent of hostname
def deployFrontend(tag):
    setup(tag)
    sudo('%s all' % (os.path.join(keeperPath, 'makeApacheConfiguration.py')))
    sudo('/etc/init.d/shibd restart')
    sudo('/etc/init.d/httpd graceful')

def deployBackend(level, tag):
    if level == 'pro':
        disableBackend(level, tag, env.host_string)

    setup(tag)
    run('%s --force --update --nosendEmail -s %s %s' % (os.path.join(keeperPath, 'deploy.py'), config.servicesRepository, tag))

    if level == 'pro':
        enableBackend(level, tag, env.host_string)

def manageBackend(tag, backendHostname, action):
    setup(tag)
    run('%s %s %s' % (os.path.join(keeperPath, 'manageApacheWorkers.py'), action, backendHostname))


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
def deployFrontends(level, tag):
    env.hosts = configuration[level]['frontends']
    execute(deployFrontend, tag)

@task
def deployBackends(level, tag):
    env.hosts = configuration[level]['backends']
    execute(deployBackend, level, tag)


# Task that deploy both frontends and backends for a given production level
@task
def deploy(level, tag):
    deployBackends(level, tag)
    deployFrontends(level, tag)

