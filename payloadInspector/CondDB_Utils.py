import json

class CondDB_Utils:
	def __init__(self):
		pass
	
	def __createJSONTags(self, data):
		return json.dumps(data)
	
	def __createJSONReleases(self, data):
		jsonOut = []
		for release in data:
			jsonOut.append({"releaseId" : release['release'], "release" : release['release']})
		return json.dumps(jsonOut)
	
	def __createJSONAccounts(self, data):
		jsonOut = []
		for acc in data:
			jsonOut.append({'DBserviceId' : acc.values()[0], 'DBservice' : acc.values()[0]})
		return json.dumps(jsonOut)
	
	def __createJSONSchemas(self, data):
		jsonOut = []
		for schema in data:
			jsonOut.append({'AccountID' : schema.values()[0], 'Account' : schema.values()[0]})
		return json.dumps(jsonOut)
	
	def __createJSONDBs(self, data):
		jsonOut = []
		for db in data:
			jsonOut.append({'DBID' : db.values()[0], 'DB' : db.values()[0]})
		return json.dumps(jsonOut)
		
	def createJSON(self, tag, data):
		if tag == 'tags':
			return self.__createJSONTags(data)
		elif tag == 'releases':
			return self.__createJSONReleases(data)
		elif tag == 'accounts':
			return self.__createJSONAccounts(data)
		elif tag == 'schemas':
			return self.__createJSONSchemas(data)
		elif tag =='dbs':
		    return self.__createJSONDBs(data)
	