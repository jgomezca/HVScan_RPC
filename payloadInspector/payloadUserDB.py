import sqlalchemy
import json
from datetime import datetime,date,time
from readXML import readXML

class payloadUserDB():
    
    def __init__(self,db_file='sqlite:///Users.db'):
        self.__engine = sqlalchemy.create_engine(db_file) 
        self.__datetime = datetime.now()
    
    def createUserDB(self):
        print "Creating DB"
        metadata = sqlalchemy.MetaData()
        user = sqlalchemy.Table('users', metadata,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key = True),
            sqlalchemy.Column('user', sqlalchemy.String(20)),
            sqlalchemy.Column('dbName', sqlalchemy.String(60)),
            sqlalchemy.Column('dbSchema', sqlalchemy.String(60)),
            sqlalchemy.Column('connStr', sqlalchemy.String(120)),
            sqlalchemy.Column('updateDate', sqlalchemy.DateTime),
            sqlalchemy.UniqueConstraint('user', 'dbName', 'dbSchema')
        )
        metadata.create_all(self.__engine)
    
    def storeUsers(self, list):
        print "Inserting users"
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("users", metadata, autoload=True, autoload_with=self.__engine)
        connection = self.__engine.connect()
        
        for record in list:
            try:
                ins = table.insert().values(user = record['user'], dbName = record['dbName'], dbSchema = record['schema'], connStr = str(record['connStr']), updateDate=self.__datetime)
                connection.execute(ins)
            except:
                try:
                    upd = table.update().where(table.c.user == record['user']).where(table.c.dbName == record['dbName']).where(table.c.dbSchema == record['schema']).values(connStr = str(record['connStr']), updateDate=self.__datetime)
                    connection.execute(upd)
                except Exception as e:
                    #print e
                    print "Error updating date for: "+record['dbName']+'-'+record['schema']
                #print "Duplicate. Ignoring: "+record['dbName']+'-'+record['schema']
        try:
            ''' Delete rows that weren't updated (means they are not in the auth file '''
            dele = table.delete().where(table.c.updateDate!=self.__datetime)
            connection.execute(dele)
        except Exception as e:
            #print e
            print "Error deleting old schemas"
        
        connection.close()
    
    def getUsersByDB(self, dbNameSearch=""):
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("users", metadata, autoload=True, autoload_with=self.__engine)
        connection = self.__engine.connect()
        
        select = table.select()
        if(dbNameSearch != ""):
            select = select.where(table.c.dbName==dbNameSearch)
        rows = connection.execute(select)
        connection.close()
        
        return rows
        
    
    def getUsers(self, dbNameSearch=""):
        rows = self.getUsersByDB(dbNameSearch)
        d = []
        for row in rows:
            d.append({row.id: row.user})
        return d
    
    def getDBs(self):
	##### deprecated method, for full definition see 
	#### http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/UserCode/Pierro/WebGUI/CondDBPayloadInspector/backend/
        return ""
        
    def get_distinctConnStr(self):
	Connections	=	"""
 [u'oracle://cms_orcoff_int/CMS_COND_16X_ALIGNMENT', u'oracle://cms_orcoff_int/CMS_COND_16X_BTAU', u'oracle://cms_orcoff_int/CMS_COND_16X_CSC', u'oracle://cms_orcoff_int/CMS_COND_16X_DT']
	"""
	c	=	readXML()
	return	c.get_connectionName()
    
    def getDistinctConnStr(self):
	### Deprecate method
	### see http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/UserCode/Pierro/WebGUI/CondDBPayloadInspector/backend/
        return ""
        
    def getSchemas(self, dbNameSearch=""):
        rows = self.getUsersByDB(dbNameSearch)
        d = []
        for row in rows:
            d.append({row.id: row.dbSchema})
        return d
        
        # Build dict
        d = []
        i=0
        for row in rows:
            i+=1
            d.append({"db"+str(i): row[0]})
        return d
        
    def getConnStr(self, dbNameSearch, dbSchemaSearch):
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("users", metadata, autoload=True, autoload_with=self.__engine)
        connection = self.__engine.connect()
        
        select = table.select()
        select = select.where(table.c.dbName==dbNameSearch).where(table.c.dbSchema==dbSchemaSearch).limit(1)
        rows = connection.execute(select)
        connection.close()
        
        # Build dict
        d = []
        row = rows.fetchone()
        d.append({"connStr": row['connStr']})
        return d

if __name__ == '__main__':
    udb = payloadUserDB()
    rows = udb.getUsersByDB("cms_orcoff_prep")
           
    '''for row in rows:
        print 'User: '+row.user+'(#'+str(row.id)+', connStr:'+row.connStr+')'
    '''
    print json.dumps(udb.getUsers("cms_orcoff_prep"))
    #print json.dumps(udb.getDBs())
    #print json.dumps(udb.getSchemas("cms_orcoff_prep"))
    #print json.dumps(udb.getConnStr("cms_orcoff_prep", "CMS_COND_DQM"))
