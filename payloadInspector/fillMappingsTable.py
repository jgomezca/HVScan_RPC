import sqlite3
import urllib2
import re
months=('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
con = sqlite3.connect('./NameMappings.db')
cur = con.cursor()
con1 = sqlite3.connect('Users.db')
cur1 = con1.cursor()
rez = cur1.execute('select distinct dbName from users').fetchall()
for db in rez:
    schemas = cur1.execute('select distinct dbSchema from users where dbName = \'%s\'' % db[0]).fetchall()
    for s in schemas:
        sp = s[0].split('_')
        alias = ''
        
        
        if len(sp) >= 5:
            if re.match(r'\d\d\d\d', sp[4]):
                year = int(sp[4][0:2])
                if year <= 10:
                    year = 2000 + year
                else:
                    year = 1900 + year
                year = str(year)
                month = int(sp[4][2:4])
                month = months[month - 1]
                alias = '%s for %s from %s %s' % (sp[3], sp[2], month, year)
            else:
                alias = '%s %s for %s' % (sp[3], sp[4].lower(), sp[2])
        elif len(sp) >= 4:
            alias = '%s for %s' % (sp[3], sp[2])
        elif len(sp) >= 3:
            alias = str(sp[2])
        else:
            alias = ''
        rez = raw_input('Alias for %s from db %s (default = %s): ' % (s[0], db[0], alias))
        if rez != '':
            alias = rez
        cur.execute('insert into schema_mappings values(\'%s\', \'%s\', \'%s\')' % (str(db[0]), str(s[0]), alias))
        
        
con.commit()
cur.close()
cur1.close()
