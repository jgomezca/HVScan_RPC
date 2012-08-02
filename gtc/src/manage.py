#!/usr/bin/env python
import os
import sys

from os import listdir
from os.path import abspath, dirname, join

def abs_path_join(path, new_path):
    return abspath(join(path,new_path))

def list_abs_dirs(path):
    dir_list = listdir(path)
    rez = []
    for dir_name in dir_list:
        rez.append(abs_path_join(path,dir_name))
    return rez

MANAGE_FILE_DIR = abspath(dirname(__file__))
SERVICE_ROOT = abspath(join(dirname(__file__), ".."))
LIB_DIR_EXTERNAL =  os.path.abspath(os.path.join(SERVICE_ROOT, "lib", "external"))
LIB_DIR_LOCAL = os.path.abspath(os.path.join(SERVICE_ROOT, "lib", "local"))
sys.path.extend(list_abs_dirs(LIB_DIR_EXTERNAL))
sys.path.extend(list_abs_dirs(LIB_DIR_LOCAL))
sys.path.append(os.path.abspath(os.path.join(SERVICE_ROOT, "lib", "external", "dateutil")))
sys.path.append('/afs/cern.ch/cms/DB/utilities/python-packages/django-1.4.1/lib/python2.6/site-packages/')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gtc.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

