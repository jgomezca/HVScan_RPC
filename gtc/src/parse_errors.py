import json
json_dict = json.load(open('all_errors.txt',"rb"))
import pprint


not_matching_containers = set()
missing_records = set()
for error_dict in json_dict:

    if error_dict['record_containers'] and error_dict['tag_container']:
        tag_container = error_dict['tag_container']['main']
        record_container = error_dict['record_containers'][0]['main']
        not_matching_containers.add((tag_container, record_container))

    if error_dict['tag_container'] and error_dict['record_containers'] is None:
        tag_container = error_dict['tag_container']['main']
        record_name = error_dict['data']['record']
        missing_records.add((tag_container, record_name))
print "Not matching containers:"
pprint.pprint(not_matching_containers)

print "missing records:"
pprint.pprint(missing_records)