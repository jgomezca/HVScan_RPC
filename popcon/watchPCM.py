#!/usr/bin/env python

import os, sys, time, re
import pwd

from subprocess import *

class WatchDog():

    def __init__(self):

        self.user = pwd.getpwuid(os.getuid())[0]

        self.cmdMap = { 'popconBackend.py' : 'PCM_start' }

    def doCmd(self, cmd, dryRun=False, verbose=False):

        if dryRun:
            self.log( "dryRun requested, would execute "+cmd)
            return 0,[],[]
        
        if verbose: self.log('going to execute '+cmd)
        
        p = Popen(cmd, shell=True, bufsize=1, # line-buffered
                        stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

        (child_stdin,
         child_stdout,
         child_stderr) = (p.stdin, p.stdout, p.stderr)

        ret = p.wait()

        errLines = child_stderr.readlines()
        outLines = child_stdout.readlines()
    
        return ret, outLines, errLines

    def check(self):
    
        cmd = 'ps xu -U '+self.user
        ret, outLines, errLines = self.doCmd(cmd)

        if ret != 0:
            self.log( "ERROR from command: return code = " + str(ret) )
    
        if errLines:
            self.log( "ERROR from command: stderr = " + "".join(errLines))
    
        if not outLines:
            self.log( "ERROR: no output from ps command !?!?!? cmd=" + cmd)
            return False
    
        # condbpro 22875  0.6  1.5 702280 31216 ?        Sl   15:08   0:01 python2.6 /home/condbpro/PopConMonitoring/popconBackend.py
        
        haveCmd0 = False
        haveCmd1 = False
        procRe = re.compile('\w*\s*(\d+)\s*.*\s(\w.*)$')
        for line in outLines:
            for cmd0,cmd1 in self.cmdMap.items():
                if cmd0 in line:
                    haveCmd0 = True
                    pid0, cmdFound0 = procRe.match(line).groups()
                if cmd1 in line:
                    haveCmd1 = True
                    pid1, cmdFound1 = procRe.match(line).groups()
    
        if not haveCmd0 and     haveCmd1:
            self.log("likely restarting ... ")
            return True # likely restarting

        if not haveCmd0 and not haveCmd1:
            self.log("process needs restart ... ")
            self.log(''.join(outLines))
            return False

        if haveCmd0:
            self.log( "running OK, cmd1 is "+str(haveCmd1)+' pid0: '+str(pid0) )

        return True

    def log(self, msg):
        now = time.asctime()
        print now+"> "+msg
        sys.stdout.flush()
        
    def restart(self):

        cmd = 'cd /home/condbpro/PayloadInspector ; /bin/sh '+self.cmdMap['popconBackend.py']+'.sh '
        ret, outLInes, errLInes = self.doCmd(cmd, verbose=True)
        if ret != 0:
            self.log( "ERROR restarting returned: " + str(ret))
            self.log( "      stderr : " + ''.join(errLines))
            self.log( "      stdout : " + ''.join(outLines))

wd = WatchDog()
found = wd.check()
while (True):
    found = wd.check()
    if not found: wd.restart()
    time.sleep(30)
