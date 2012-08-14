import sys
import subprocess
import service
import logging

def main():
    if service.isAnotherInstanceRunning():
        logging.info('Another instance is running, exiting...')
        return

    subprocess.call('python src/manage.py global_update', shell=True)


if __name__ == '__main__':
    sys.exit(main())

