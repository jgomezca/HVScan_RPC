import sys
import urllib2

from testData import lumiTestList as testList

try:
    serverName = sys.argv[1]
except Exception as e:
    print "Wrong parameters !!!"
    print "USE - python2.6 testLumi.py serverName"
    print "serverName  - your server name, with port if needed"
    raise SystemExit
f = open(serverName+".out", 'w')
i = 0
for test in testList:
    i+=1
    url = "http://" + serverName + test
    try:
        request = urllib2.Request(url)
        response = urllib2.urlopen(request, None, 10).read()
    except Exception as e:
        # raise SystemExit, "Could not reach requested page at:"+url
        print "ERROR from server for ", url, str(e)
        response = str(e)
    f.write("\n---------------------------------------------------------------------------Test: " + test + " -----------------------------------------------------------------\n")
    f.write(str(response))
    print "Test number " + str(i) + " with parameters " + test + " completed! Written to file - " + serverName + ".out"
f.close()
