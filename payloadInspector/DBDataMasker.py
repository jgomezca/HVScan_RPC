import sqlite3

class Masker:
    
    def __init__(self, mask_db = './NameMappings.db'):
        '''Constructor. Initializes objects and selects all mappings from database into memory to increase speed'''
        self.__db = mask_db
        self.__con = None
        self.__db_cache = {}
        self.__db_mask_cache = {}
        self.__schema_cache = {}
        self.__schema_mask_cache = {}
        cur = self.__get_cursor()
        cur.execute("select dbname, mask from db_mappings")
        i = cur.fetchone()
        while i:
            self.__db_mask_cache[str(i[1])] = str(i[0])
            self.__db_cache[str(i[0])] = str(i[1])
            i = cur.fetchone()
            
        for j in self.__db_cache.keys():  
            cur.execute("select schema, mask from schema_mappings where dbname = ? and schema not like '%30X%'", (j, ))
            i = cur.fetchone()
            tmp1 = {}
            tmp2 = {}
            while i:
                tmp1[str(i[0])] = str(i[1])
                tmp2[str(i[1])] = str(i[0])
                i = cur.fetchone()
            self.__schema_cache[j] = tmp1
            self.__schema_mask_cache[j] = tmp2
            
        
    def __get_cursor(self):
        if self.__con == None:
            self.__con = sqlite3.connect(self.__db)
        return self.__con.cursor()
        
    def mask_dbname(self, db):
        #cur = self.__get_cursor()
        #cur.execute("select mask from db_mappings where dbname = ?", (str(db),))
        #return str(cur.fetchone()[0])
        return self.__db_cache.get(db, '')
        
    def unmask_dbname(self, db):
        #cur = self.__get_cursor()
        #cur.execute("select dbname from db_mappings where mask = ?", (str(db),))
        #return str(cur.fetchone()[0])
        return self.__db_mask_cache.get(db, '')
        
    def mask_schema(self, db, schema):
        #cur = self.__get_cursor()
        #cur.execute("select mask from schema_mappings where schema = ? and dbname = ?", (str(schema), str(db)))
        #return str(cur.fetchone()[0])
        return self.__schema_cache[db].get(schema, '')
        
    def unmask_schema(self, db, schema):
        #cur = self.__get_cursor()
        #cur.execute("select schema from schema_mappings where mask = ? and dbname = ?", (str(schema), str(db)))
        #return str(cur.fetchone()[0])
        return self.__schema_mask_cache[db].get(schema, '')
