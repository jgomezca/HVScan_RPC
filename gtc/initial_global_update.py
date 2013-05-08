import sys
import subprocess
import service
import logging

def main():
    if service.isAnotherInstanceRunning():
        logging.info('Another instance is running, exiting...')
        return

    if service.settings['productionLevel'] != 'private':
        logging.info('This script is only meant for private deployments.')
        return

    subprocess.call('python src/manage.py initial_global_update', shell=True)


if __name__ == '__main__':
    sys.exit(main())

