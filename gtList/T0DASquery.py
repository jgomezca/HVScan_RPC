import sys, urllib2, json
import shlex, subprocess
import DBChecker

def unique(seq, keepstr=True):
    t = type(seq)
    if t in (unicode, str):
        t = (list, t('').join)[bool(keepstr)]
    try:
        remaining = set(seq)
        seen = set()
        return t(c for c in seq if (c in remaining and not remaining.remove(c)))
    except TypeError: # hashing didn't work, see if seq is sortable
        try:
            from itertools import groupby
            s = sorted(enumerate(seq),key=lambda (i,v):(v,i))
            return t(g.next() for k,g in groupby(s, lambda (i,v): v))
        except:  # not sortable, use brute force
            seen = []
            return t(c for c in seq if not (c in seen or seen.append(c)))

class Tier0GT(object):
    """ Class for retrieving a unique list of Global Tags from Tier0-DAS"""

    def queryTier0(self, src, proxy = None, out = 5):
        """
        queries Tier0-DAS
        src: Tier0-DAS URL
        proxy: proxy to be used when connecting (default None)
        out: timeout for HTTP request (default 5 seconds)
        @returns a dictionary, from which GT value must be extracted.
        """
        try:
            if proxy:
                opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.ProxyHandler({'http':proxy, 'https':proxy}))
            req = urllib2.Request(src)
            req.add_header("User-Agent","ConditionGlobalTagList/2.0 python/%d.%d.%d" % sys.version_info[:3])
            req.add_header("Accept","application/json")
            if proxy:
                jsonCall = opener.open(req, timeout = out)
            else:
                jsonCall = urllib2.urlopen(req, timeout = out)
            jsonText = jsonCall.read()
            data = json.loads(jsonText)
            return data
        except urllib2.HTTPError, h:
            errStr = """Cannot get connection to Tier0-DAS from URL \"%s\"""" %(src,)
            if proxy:
                errStr += """ using proxy \"%s\"""" %(str(self.proxy),)
            errStr += """ with timeout \"%d\" since \"%s\", code \"%d\"""" %(out, h.reason, h.code)
            raise TypeError(errStr)
        except urllib2.URLError, u:
            errStr = """Cannot get connection to Tier0-DAS from URL \"%s\"""" %(src,)
            if proxy:
                errStr += """ using proxy \"%s\"""" %(str(proxy),)
            errStr += """ with timeout \"%d\" since \"%s\"""" %(out, u.reason)
            raise TypeError(errStr)

    def __call__(self, src, proxy = None, out = 5):
        """
        @returns a unique list of GTs
        """
        try:
            data = self.queryTier0(src, proxy, out)
            gtnames = [str(di['global_tag']).replace("::All", "") for di in data]
            return unique(gtnames)
        except TypeError, t:
            errStr = """Cannot retrieve list of Global Tags used at Tier-0 from URL \"%s\"""" %(src,)
            if proxy:
                errStr += """ using proxy \"%s\"""" %(str(proxy),)
            errStr += """ with timeout \"%d\" since:
\t\"%s\"""" %(out, str(t))
            raise ValueError(errStr)

class HLTGT(object):

    def __call__(self
                ,dbName
                ,authPath
                ,tag):
        try:
            d = DBChecker.DBChecker(dbName,authPath)
            run = d.lastSince(tag)
            command_line = "edmConfigFromDB --orcoff --runNumber " + str(run)
            args = shlex.split(command_line)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = p.communicate()[0]
            resList = result.strip().split("\n")
            print "resList", resList
            resGT = [l.strip() for l in resList if l.find("globaltag") != -1]
            print "restgt", resGT
            globalTag = [l.strip().replace("::All","") for l in resGT[0].split("\"") if l.find("::All") != -1][0]
            return globalTag
        except ValueError, v:
            raise ValueError(str(v))
        except IndexError, i:
            raise ValueError("Configuration for run \"%d\" not found" %(run))
        except OSError, o:
            raise ValueError(str(o))
           

class GTValues(object):

    def __init__(self
                ,dbName
                ,authPath
                ,tag
                ,expressSrc = "https://cmsweb.cern.ch/tier0/express_config"
                ,promptSrc = "https://cmsweb.cern.ch/tier0/reco_config"
                ,proxy = None
                ,out = 5):
        self.hlt =  HLTGT()
        self.tier0 = Tier0GT()
        self.dbName = dbName
        self.authPath = authPath
        self.tag = tag
        self.expressSrc = expressSrc
        self.promptSrc = promptSrc
        self.proxy = proxy
        self.timeout = out

    def getHLTGT(self):
        try:
            globalTag = self.hlt(self.dbName,self.authPath,self.tag)
            return globalTag
        except ValueError, v:
            raise ValueError(str(v))

    def getExpressGT(self):
        try:
            gtList = self.tier0(self.expressSrc,self.proxy,self.timeout)
            return gtList[0]
        except IndexError, i:
            raise ValueError(str(i))
        except ValueError, v:
            raise ValueError(str(v))

    def getPromptGT(self):
        try:
            gtList = self.tier0(self.promptSrc,self.proxy,self.timeout)
            return gtList[0]
        except IndexError, i:
            raise ValueError(str(i))
        except ValueError, v:
            raise ValueError(str(v))

    def getGTDictionary(self):
        #try:
        #    return {'hlt':self.getHLTGT(), 'express':self.getExpressGT(), 'prompt':self.getPromptGT()}
        #except ValueError, v:
        #    raise ValueError(str(v))
        return {'hlt':self.getHLTGT(), 'express':self.getExpressGT(), 'prompt':self.getPromptGT()}

