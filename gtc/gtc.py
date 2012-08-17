import json
import subprocess
import service

f = open("src/gtc/keeper_settings.json","wb")
json.dump(service.settings, f, indent=4)
f.close()

subprocess.call('python src/manage.py syncdb --noinput', shell=True)
subprocess.call('python src/manage.py runserver 0.0.0.0:%s' % service.settings['listeningPort'], shell=True)

