#!/usr/bin/env python2.6
'''Check_MK (OMD) manage/deploy/backup/restore script.

As per [1] and the other message in the thread, there is no simple way
to restore/backup a full OMD/Check_MK installation. There are several aspects
of backing up/restoring:

  1. Check_MK configuration (i.e. local Nagios one): check_mk --restore/--backup.
  2. WATO configuration: WATO Backup/Restore web interface.
  3. RRD databases: architecture dependant.

One can move the full installation to another machine with the same
architecture making a tar of the full /omd/site/mysite folder and extracting
it in the new machine, see [2]. However, this does not fit our needs.

This script does not deal with the RRD databases, but allows to:

  * Automatically download, install and configure OMD in a new SLC6 machine.
  * Request a new snapshot to WATO. Also, it can extract it afterwards,
    useful to put the contents into a git repository.
  * Request to restore a snapshot to WATO (at the moment just copies
    the file to WATO's path but does not do the 3 required requests in WATO
    to actually activate it). Also, it can compress from the files
    back to the original snapshot. Useful to fetch changes from git and create
    a valid tarball for WATO.

This script enables us to keep an independent Git repo in AFS with
our WATO configuration extracted, and deploy it in a new machine easily.

Note that the WATO configuration includes the OMD passwords (i.e. htpasswd)
and user's settings. Therefore, *the git repository MUST be stored in a safe
location, readable only by the admins*.

It does not try to be a replacement for a (missing) feature in OMD/Check_MK,
but just to be an script to re-do what we needed to setup our monitoring, which
serves as documentation as well.

Some bits are yet out, like setting the iptables.

Other OMD/Check_MK notes:

  * After a reboot to update from SLC 6.3 to SLC 6.4, and running 'omd restart',
    we got several errors relating a missing

        /omd/sites/prod/tmp/nagios/nagios.cfg

    It turns out that OMD's binary

        /opt/omd/versions/0.56/bin/omd

    tries to run

        mount -i /omd/sites/prod/tmp

    but mount complains about that entry not existing in /etc/fstab. However,
    the entry is there; but /omd is a symlink to /opt/omd and mount tries
    to look for the resolved path in /etc/fstab instead of the symlink one
    (see the strace). The error message is confusing because it contains
    the original (symlink) path instead of the resolved one, and it does not
    warn about that it tried to find the resolved one either.

    Manually editing the /etc/fstab with the resolved path

        /opt/omd/sites/prod/tmp

    solves this issue, and with it, all the other as well.
    'omd restart' works again.

    SLC 6.3's util-linux-ng's 'mount -i' [3] with symlinks works fine
    but it should not, is a security bug! SLC 6.4's one [4] does not,
    unless you are root. See CVE-2013-0157 and [5] for more details about
    the security issue and changes in the Red Hat package (patch
    util-linux-ng-2.17-mount-canonicalize.patch). The link does not explicitly
    mention this (they talk about mount/umount exposing information,
    which is caused by the same bug).

[1] http://lists.mathias-kettner.de/pipermail/omd-users/2010-December/000008.html
[2] http://lists.mathias-kettner.de/pipermail/omd-users/2010-December/000009.html
[3] http://linuxsoft.cern.ch/cern/slc63/updates/SRPMS/util-linux-ng-2.17.2-12.7.el6.src.rpm
[4] http://linuxsoft.cern.ch/cern/slc64/updates/SRPMS/util-linux-ng-2.17.2-12.9.el6.src.rpm
[5] https://bugzilla.redhat.com/show_bug.cgi?id=892330
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import sys
import optparse
import logging
import subprocess
import socket
import re
import getpass
import tempfile


siteName = 'prod'

omdApacheConfPath = '/etc/httpd/conf.d/zzz_omd.conf'
siteConfPath = '/omd/sites/%s/etc/omd/site.conf' % siteName
snapshotsPath = '/omd/sites/%s/var/check_mk/wato/snapshots' % siteName


OMDUsername = None
OMDPassword = None


def check_output(*popenargs, **kwargs):
    '''Port from Python 2.7.
    '''

    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd)
    return output


def run(command):
    logging.debug('Running: %s', command)
    return check_output(command, shell = True)


def sudo(command):
    return run('sudo %s' % command)


def ask(question, default = None):
    answer = raw_input('%s %s' % (question, '[%s] ' % default if default else '')).strip()

    if answer:
        return answer

    return default


def queryCheckMK(url):
    global OMDUsername
    if OMDUsername is None:
        OMDUsername = raw_input('OMD Username: ')

    global OMDPassword
    if OMDPassword is None:
        OMDPassword = raw_input('OMD Password: ')

    baseUrl = 'https://%s/%s/check_mk/' % (socket.getfqdn(), siteName)
    finalUrl = '%s%s' % (baseUrl, url)

    logging.debug('Querying WATO: %s', finalUrl)

    # Avoid passing the username/password in the command line to curl.
    # pycurl would do fine as well, this avoids the dependency.
    with tempfile.NamedTemporaryFile() as f:
        f.write('%s:%s' % (OMDUsername, OMDPassword))
        f.flush()
        return run('''echo `echo -n 'user = "'; cat %s; echo -n '"'` | curl -k -K - '%s' ''' % (f.name, finalUrl))


def getCheckMKFinalURL(url, regexp):
    '''Used to retrieve the URLs which contain the required _transid that can
    be used to perform the real action.
    '''

    page = queryCheckMK(url)
    match = re.search(regexp, page)
    if not match:
        raise Exception('Something went wrong.')
    return match.group(1)


def getLatestSnapshot():
    return sudo('ls -t %s | head -1' % snapshotsPath).strip()


def copyLatestSnapshot(snapshotFile):
    user = getpass.getuser()
    sudo("cp '%s' '%s'" % (os.path.join(snapshotsPath, getLatestSnapshot()), snapshotFile))
    sudo("chown %s '%s'" % (user, snapshotFile))


def download():
    '''Download supported OMD (0.56) to the current folder.
    '''

    url = 'http://omdistro.org/attachments/download/201/omd-0.56-rh60-29.x86_64.rpm'
    outputFile = 'omd-0.56-rh60-29.x86_64.rpm'

    logging.info('Downloading OMD from %s into %s...', url, outputFile)

    run("curl -o '%s' '%s'" % (outputFile, url))


def deploy(package):
    '''See [1].

    [1] http://omdistro.org/wiki/omd/Quickstart_redhat
    '''

    logging.info('Deploying OMD from RPM %s...', package)

    # We don't run sudo('yum install epel-release')
    # since it conflicts with sl-release.

    # This downloaded 22 MB, and installed 315 MB. Installs mainly parts of
    # Perl, PHP, MySQL and graphviz.
    logging.info('Installing OMD...')
    try:
        sudo("yum list 'omd-*'")
    except subprocess.CalledProcessError as e:
        sudo('yum install --nogpgcheck %s' % package)
    else:
        logging.warn('Looks like the OMD package is already installed (see above). Continue (without installing)?')
        if ask('Continue?', 'y').lower() != 'y':
            raise Exception('Aborted by user.')

    logging.info('Cleaning up some created Apache conf files...')

    # Disable fcgid.conf and php.conf from the normal Apache (i.e. the system
    # one, not those used by OMD which are independent and run in /opt).
    # These files get installed by OMD's dependencies, but they are not needed
    # in the normal Apache and, if the keeper/other services are installed,
    # we are already using custom Apache configuration, which does not load
    # all the standard modules (e.g. for AddHandler), so it would not work.
    try:
        sudo('mv /etc/httpd/conf.d/fcgid.conf{,.original}')
    except subprocess.CalledProcessError as e:
        logging.info('fcgid.conf could not be moved, probably OMD was already installed in this machine in the past.')

    try:
        sudo('mv /etc/httpd/conf.d/php.conf{,.original}')
    except subprocess.CalledProcessError as e:
        logging.info('php.conf could not be moved, probably OMD was already installed in this machine in the past.')

    # The OMD's Apache configuration use the env module for SetEnv et al.,
    # so enable it just for those configuration files before including them.
    # Note that this deletes the symbolic link and creates a real file with
    # the modification.
    line = 'LoadModule env_module modules/mod_env.so'
    with open(omdApacheConfPath, 'rb') as f:
        addLine = line not in f.read()
    if addLine:
        sudo("sed -i '2i%s' '%s'" % (line, omdApacheConfPath))
    else:
        logging.info('The LoadModule directive was already in the Apache configuration, probably OMD was already installed in this machine in the past.')

    # Create site
    logging.info('Creating OMD site %s...', siteName)
    sudo('omd create %s' % siteName)

    # Configure site (it is usually done manually navigating the menus
    # in sudo omd config prod, this automates the only change required for us)
    logging.info('Configuring OMD site %s...', siteName)
    sudo('''sed -i 's/CONFIG_DEFAULT_GUI='"'"'welcome'"'"'/CONFIG_DEFAULT_GUI='"'"'check_mk'"'"'/g' %s''' % siteConfPath)

    # Start site
    logging.info('Starting OMD site %s...', siteName)
    sudo('omd start %s' % siteName)


def backup(snapshotFile):
    logging.info('Backing up into %s...', snapshotFile)

    previousLatestSnapshotFile = getLatestSnapshot()
    logging.info('Latest WATO snapshot: %s', previousLatestSnapshotFile)

    url = getCheckMKFinalURL('wato.py?mode=snapshot', 'href="(wato.py\?mode=snapshot&_create_snapshot=Yes.*?)"')
    logging.info('Requesting snapshot to WATO via %s ...', url)
    queryCheckMK(url)

    latestSnapshotFile = getLatestSnapshot()
    logging.info('Latest WATO snapshot (should be the new one): %s', latestSnapshotFile)

    if previousLatestSnapshotFile is not None and latestSnapshotFile == previousLatestSnapshotFile:
        raise Exception('Making the snapshot through WATO failed.')

    copyLatestSnapshot(snapshotFile)


def restore(snapshotFile):
    logging.info('Restoring from %s...', snapshotFile)

    sudo("cp '%s' '%s'" % (snapshotFile, os.path.join(snapshotsPath, snapshotFile)))
    sudo("chown %s:%s '%s'" % (siteName, siteName, os.path.join(snapshotsPath, snapshotFile)))

    # To fully automate we would need to do:
    #
    # url = getCheckMKFinalURL('wato.py?mode=snapshot', 'href="(wato.py\?mode=snapshot&_restore_snapshot=%s.*?)"' % snapshotFile)
    # logging.info('Requesting snapshot to WATO via %s ...', url)
    # queryCheckMK(url)
    #
    # Then confirm (POST request)
    # Then activate the changes (wato.py?folder=&mode=changelog&_action=activate...)
    #
    # Since we will not use it, we leave it as a TODO.


def extract(snapshotFile, path):
    if snapshotFile == '-':
        snapshotFile = '/tmp/wato-snapshot-latest.tar.gz'
        copyLatestSnapshot(snapshotFile)

    logging.info('Extracting from %s into %s...', snapshotFile, path)

    # Not pretty, but does the trick: extracts the main tar file, then creates
    # a folder for each sub .tar and extract them in their folder.
    run("tar -xf %s -C %s" % (snapshotFile, path))
    run("cd %s && ls --color=never *.tar | sed 's/\.tar//g' | xargs -n1 -IFILE sh -c 'mkdir -p FILE && tar -xf FILE.tar -C FILE && rm FILE.tar'" % path)


def compress(snapshotFile, path):
    logging.info('Compressing %s into %s...', path, snapshotFile)

    # Again, not pretty, see extract() above.
    run("cd %s && ls --color=never | xargs -n1 -IFILE tar -cvf FILE.tar -C FILE ." % path)
    run("tar -cvzf %s -C %s `cd %s && ls --color=never *.tar`" % (snapshotFile, path, path))

    # Clean up temporary .tar files
    run("rm %s/*.tar" % path)

    # How to test: Given a snapshot test1.tar.gz created with backup(), do:
    # rm -rf t1 t2 && mkdir t1 t2 && python manageCheckMK.py extract test1.tar.gz t1 && python manageCheckMK.py compress test2.tar.gz t1 && python manageCheckMK.py extract test2.tar.gz t2 && diff -rqu t1 t2


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage = '''Usage:
  %prog download                                     Downloads the supported OMD RPM.
  %prog deploy    <OMD package path (.rpm)>          Installs and configures OMD from scratch.
  %prog backup    <snapshot file (.tar.gz)>          Backs up WATO into a snapshot.
  %prog restore   <snapshot file (.tar.gz)>          Restores a WATO snapshot (only copies the snapshot to WATO's folder).
  %prog extract   <snapshot file (.tar.gz)>  <path>  Fully extracts a WATO snapshot (if the snapshot is -, picks the latest from WATO).
  %prog compress  <snapshot file (.tar.gz)>  <path>  Compresses a extracted WATO snapshot.
''')

    (options, arguments) = parser.parse_args(sys.argv[1:])

    if len(arguments) < 1:
        parser.print_help()
        return -2

    if arguments[0] == 'download':
        if len(arguments) != 1:
            parser.print_help()
            return -2

        download()

    elif arguments[0] == 'deploy':
        if len(arguments) != 2:
            parser.print_help()
            return -2

        deploy(arguments[1])

    elif arguments[0] == 'backup':
        if len(arguments) != 2:
            parser.print_help()
            return -2

        backup(arguments[1])

    elif arguments[0] == 'restore':
        if len(arguments) != 2:
            parser.print_help()
            return -2

        restore(arguments[1])

    elif arguments[0] == 'extract':
        if len(arguments) != 3:
            parser.print_help()
            return -2

        extract(arguments[1], arguments[2])

    elif arguments[0] == 'compress':
        if len(arguments) != 3:
            parser.print_help()
            return -2

        compress(arguments[1], arguments[2])

    else:
        parser.print_help()
        return -2


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

