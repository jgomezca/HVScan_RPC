import sqlite3
import re
import lastIOVSince
import os.path


def validateIOV(dbName, tag, iovn):
    iov = lastIOVSince.LastIOVSince(dbName = dbName)
    elems = iov.iovSequence(tag = tag).elements 
    for el in elems:
        n = int(iovn)
        if n >= el.since() and n <= el.till():
            return el.since()
    return el.since()

def validateType(param, types):
    return type(param) in types
    
def validateDirectory(dir):
    if not validateType(param = dir, types = (type(''),)):
        return False
    if not os.path.isdir(dir):
        return False
    if not os.access(dir, os.R_OK | os.W_OK):
        return False
    return True
        
def validateSince(value, onlyone = True):
    if not validateType(value, (type(''), type(1), type(1l))):
        return False
    if value.find(';') != -1  and onlyone:
        return False
    since = value.strip().split(';')    
    for i in since:
        if re.match('\d+', i) == None:
            return False
    return True

def get_validated_dbname(value, acc=None):
    if acc == None:
        val = str(value)
    else:
        val = 'oracle://%s/%s' % (str(value), str(acc))
    con = sqlite3.Connection('Users.db')
    cur = con.cursor()
    if acc == None:
        cur.execute('select distinct dbName from users')
    else:
        cur.execute('select distinct connStr from users')
    i = cur.fetchone()
    while i:
        if str(i[0]) == val:
            return val
        i = cur.fetchone()
    raise ValueError('Parameter "dbName" doesn\'t have valid value. Value=%s' % val)
    
#def get_validated_acc(value):
#    val = str(value)
#    con = sqlite3.Connection('Users.db')
#    cur = con.cursor()
#    cur.execute('select distinct connStr from users')
#    i = cur.fetchone()
#    while i:
#        if i[0] == val:
#            return val
#        i = cur.fetchone()
#    raise ValueError('Parameter "acc" doesn\'t have valid value.')
    
def get_validated_tag(dbName, value):
    val = str(value)
    iov = lastIOVSince.LastIOVSince(dbName = dbName)
    if value in iov.getTags():
        return val
    raise ValueError("Parameter \"tag\" doesn't have valid value")
    
def get_validated_since(value, db, tag, onlyone = False):
    if type(value) == type(''):
        #print "%s is a string" %(value,)
	sinces = value.strip().split(';')
    elif type(value) == type(u''):
	#print "value is unicode"
	valStr = str(value)
	sinces = valStr.strip().split(';')
    elif type(value) in (type(1), type(1l)):
        #print "value is an integer or a long"
	sinces = [str(value), ]
    else:
	print "type(value): ",type(value)
    rez = []
    iov = lastIOVSince.LastIOVSince(dbName = db)    
    for i in sinces:
        if not validateSince(i, onlyone = True):
            continue
        #for el in iov.iovSequence(tag = tag).elements:
        #    n = int(i)
        #    if n >= el.since() and n <= el.till():
        #        rez.append(str(el.since()))
        #        break
        rez.append(str(validateIOV(dbName = db, tag = tag, iovn = i)))
        if onlyone:
            break
    return ';'.join(rez)
    
    
def validateTag(self, dbName, tag):
    if type(tag) != type(''):
        raise TypeError('tag has to be string')
    if type(dbName) != type(''):
        raise TypeError('dbName has to be string')
    if len(tag.strip()) == 0:
        raise ValueError('tag value can not be empty.')
    iov = lastIOVSince.LastIOVSince(dbName = dbName)
    tags = iov.getTags()
    rez = False
    for t in tags:
        if tag == t:
            rez = True
            break
    if not rez:
        raise ValueError('no such tag exist for given DB.')
        
def validateArgs(dbName, tag, since, onesince = True):
    if not validateSince(value = since, onlyone = onesince):
        raise ValueError('wrong "since" value')
        
    
