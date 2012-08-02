import subprocess
import service

subprocess.call('python src/manage.py syncdb', shell=True)
subprocess.call('python src/manage.py runserver 0.0.0.0:%s' % service.settings['listeningPort'], shell=True)

