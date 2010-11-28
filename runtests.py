#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os, sys
from os import path
from django.core.management import call_command

def main():
    current_path = path.abspath(path.dirname(__file__))
    sys.path.insert(0, path.join(current_path, 'test_project'))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'
    call_command('test')

if __name__ == '__main__':
    main()
