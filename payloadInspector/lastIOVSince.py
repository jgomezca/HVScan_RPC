#!usr/bin/env python
import os, sys, DLFCN
import re
sys.setdlopenflags(DLFCN.RTLD_GLOBAL+DLFCN.RTLD_LAZY)
import pluginCondDBPyInterface as CondDB
import payloadUserDB
import datetime

import config

class LastIOVSince(object):
    def __init__(self
                 , authPath = None
                 , dbName = config.stripCondDB
                 #, dbName = "oracle://cms_orcoff_prod/CMS_COND_30X_ECAL"
                 , tablePath = None):
        if not tablePath:
            tablePath = config.folders.table_dir
        if not authPath:
            authPath = config.db_data.auth_path
        self.authPath = authPath
        self.dbName = dbName
        self.a = CondDB.FWIncantation()
        self.initDB()
        self.tablePath = tablePath
        self.dateformat = config.general.date_format

    def initDB(self, authPath = None, dbName = None):
        if(authPath == None):
            authPath = self.authPath
        if(dbName == None):
            dbName = self.dbName
        else:
            self.dbName = dbName
        if dbName.startswith('frontier'):
            self.rdbms = CondDB.RDBMS('')
            self.db = self.rdbms.getReadOnlyDB(str(dbName))
        else:
            self.rdbms = CondDB.RDBMS(authPath)
            self.db = self.rdbms.getDB(dbName)

    def getTags(self):
        listTags    =   []
        self.db.startReadOnlyTransaction()
        tags = self.db.allTags()
        self.db.commitTransaction()
        for tag in tags.split():
            listTags.append(tag)
        return listTags

    def iovSequence(self, tag):
        try:
            self.db.startReadOnlyTransaction()
            iov =  self.db.iov(tag)
            self.db.commitTransaction()
            return iov
        except:
            raise

    def __call__(self, tag):
        iov = self.iovSequence(tag)
        iov.tail(1)
        for elem in iov.elements:
            lastSince = elem.since()
        return lastSince

    def writeTable(self, silent = False, dbName = None):
        if dbName is None:
            dbName = self.dbName

        if silent:
            try:
                table = self.buildTable(dbName)
            except Exception as e:
		print e
                table = "No data"
                pass
        else:
            table = self.buildTable(dbName)
        
        #try:
        fileName = re.sub(r'(://|/)', '_', dbName) + '.html'
        f = open(os.path.join(self.tablePath, fileName), "w")
        f.write(table)
        f.close()
        #except Exception as e:
        #    return "error: " + e#self.dbName
        return "written: " + os.path.join(self.tablePath, fileName)

    def formatted_iovList(self,iovlist,record_, timetype):
        #Commented out, because person of SiStripDetVOff asked to show whole list
        #Uncommented, since some html are too huge, Beamspot html was 20mb!!
        #if(iovlist.__len__()>5):
        #    iovlist =   iovlist[:1]+iovlist[-4:]
        with open('good.txt') as f:
            goodTags = f.read().split('\n')

	iovlist_formatted	=""
        #iovlist_formatted   +=  "<div class='tableContainer'>"
        #iovlist_formatted   +=  "<table class='myTable01'>"
        formhead1 = formhead2 = ''
        if str(timetype) == 'timestamp': 
            iovlist_formatted   +=  "<thead><tr><th>since ; run number ; lumi</th><th>till ; run number ; lumi</th></tr></thead>"
        elif str(timetype) == 'lumiid': 
            iovlist_formatted   +=  "<thead><tr><th>since ; run number ; lumi</th><th>till ; run number ; lumi</th></tr></thead>"
	else:
            iovlist_formatted   +=  "<thead><tr><th>since</th><th>till</th></tr></thead>"

        #iovlist_formatted   +=  "<thead><tr>"+formhead1+"<th>since</th>"+formhead2+"<th>till</th></tr></thead>"
        iovlist_formatted   +=  "<tbody>"
        realsince = realtill = ''
        for i,j in iovlist:
            date_i=str(i)
            date_j=str(j)
            if str(timetype) == 'timestamp':
                #realsince = "<td>%s</td>" % str(i)
                #realtill = "<td>%s</td>" % str(j)
                realsince =  str(i)
                realtill = str(j)
                try:
                    date_i=";"+datetime.datetime.utcfromtimestamp(i >> 32).strftime(self.dateformat)
                except:
                    date_i=";Infinity"
                try:
                    date_j=";"+datetime.datetime.utcfromtimestamp(i >> 32).strftime(self.dateformat)
                except:
                    date_j=";Infinity"
            elif str(timetype) == 'lumiid':
                realsince = str(i)
                realtill = str(j)
                try:
                    #date_i='RUNNMBR: %d, LUMISECTION: %d' % (int(i) >> 32, int(i) & 0XFFFFFFFF)
                    date_i=';%d;%d' % (int(i) >> 32, int(i) & 0XFFFFFFFF)
                except:
                    date_i=";Infinity"
                try:
                    #date_j='RUNNMBR: %d, LUMISECTION: %d' % (int(j) >> 32, int(j) & 0XFFFFFFFF)
                    date_j=';%d;%d' % (int(j) >> 32, int(j) & 0XFFFFFFFF)
                except:
                    date_j="Infinity"
            iovlist_formatted   +=  "@"+realsince+date_i+"_"+realtill+date_j+"#"
            #iovlist_formatted   +=  "<tr>"+realsince+"<td>"+date_i+"</td>"+realtill+"<td>"+date_j+"</td></tr>"
	    #iovlist_formatted   +=  "<tr>"+realsince+"<td>"+date_i+"</td>"+realtill+"<td>"+date_j+"</td><td><input type='checkbox'></td></tr>"
        #iovlist_formatted   +=  "</tbody>"

        return iovlist_formatted

    def writeBigIOV(self,iovSince=1,tag_name="",iovBigContent="", dbName = None):
        if dbName is None:
            dbName = self.dbName
        fileName = re.sub(r'(://|/)', '_', dbName) +'_'+tag_name+'.html'
        f = open(os.path.join(self.tablePath, fileName), "w")
	#print os.path.join(self.tablePath, fileName)
        f.write(iovBigContent)
        f.close()
	return "written iovBigSize:" + os.path.join(self.tablePath, fileName)

    def buildTable(self, dbName):
        import time
        listTags    =   []
        self.db.startReadOnlyTransaction()
        tags = self.db.allTags()
        result = '<div id="dataCreation">'+str(datetime.datetime.utcnow().strftime("%d %h, %Y %H:%M"))+'</div><table class="display" id="example">'
	result_js ="\n<script>"
        result += '\n<thead><tr><th>ID</th><th>Tagname</th><th>Last update time</th><th>IOV size</th></tr></thead>'
        result += '\n<tbody>'
        id = 1
        for tag in tags.split():
            if tag in config.skippedTags:
                print 'Skipped %s' % tag
                continue

            iov = self.db.iov(tag)
            log = self.db.lastLogEntry(tag).getState()
            listTags.append(tag)

            #result += "<tr><td>" + str(id) + "</td><td>" + tag.strip() + "</td><td>" + str(datetime.datetime.fromtimestamp(int(iov.timestamp()) >> 32).strftime(self.dateformat)) + "</td><td> " + \
            timeVal     =   str(datetime.datetime.utcfromtimestamp(int(iov.timestamp()) >> 32).strftime(self.dateformat))
            timeValjs   =   time.strftime("%d %b %Y %H:%M",time.strptime(timeVal, "%d/%m/%y %H:%M:%S"))
            result += "<tr><td>" + str(id) + "</td><td>" + tag.strip() + "</td><td>" + timeValjs + "</td><td> " + \
            str(iov.size()) + "</td>"
            id += 1

            iovlist = []
            
	    current_since	=	0
            for elem in iov.elements:
		current_since	=	elem.since()
                iovlist.append((current_since, elem.till()))
                #iov_table  += "<tr><td>" +  str(elem.since()) +"</td><td>" + str(elem.till())  +"</td></tr>" 
            if(iovlist.__len__()<10):
        	#iovlist_formatted   =   "iovList_array['"+record_+"']=\""
            	result_js += "iovList_array['"+tag.strip()+"']=\""+self.formatted_iovList(iovlist,tag.strip(), iov.timetype())+"\";"
	    else:
		iovBigContent	=	self.formatted_iovList(iovlist,tag.strip(), iov.timetype())
		#print "\niovContent:"+
		self.writeBigIOV(iovSince=current_since,tag_name=tag.strip(),iovBigContent=iovBigContent, dbName = dbName) #(iovContent=,)
            result += "</tr>\n"
        result += '</tbody>'
        result += '</table>'
	result += result_js+"</script>"
        self.db.commitTransaction()
        return result 

if __name__ == "__main__":
    l = LastIOVSince()
    #last = l("runinfo_start_31X_hlt")
    #print last
    connection_list =['CMS_COND_31X_ALIGNMENT','CMS_COND_31X_RUN_INFO','CMS_COND_34X_ECAL','CMS_COND_34X_DQM']#,'CMS_COND_30X_STRIP','CMS_COND_30X_HCAL','CMS_COND_30X_BTAU']
    connection_list =['CMS_COND_34X_ECAL']#,'CMS_COND_30X_STRIP','CMS_COND_30X_HCAL','CMS_COND_30X_BTAU']
    #connection_list = ['CMS_COND_31X_RUN_INFO']
    #connection_list = ['CMS_COND_31X_ECAL']
    __payloadUserDB = payloadUserDB.payloadUserDB(db_file='sqlite:///Users.db')
    db_list = __payloadUserDB.getDBs()
    for db in db_list:
        db = str(db.values()[0])
        schema = __payloadUserDB.getSchemas(dbNameSearch=db)
        for schema_val in schema:
            print schema_val
    for connection in connection_list:
        connection_string = 'oracle://cms_orcoff_prep/'+connection
        print connection_string
        l.initDB(dbName = connection_string)
        #print l.buildTable()
        print l.writeTable()
    #last = l("EcalPedestals_v5_online")
    #print last
