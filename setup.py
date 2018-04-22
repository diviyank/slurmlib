"""Setup the slurmlib package."""
# -*- coding: utf-8 -*-
# Copyright (C) 2016 Diviyan Kalainathan
# Licence: Apache 2.0
import os
from shutil import copy2

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages


def setup_package():
    setup(name='slurmlib',
          version='0.1',
          description='A useful tool to run jobs on SLURM',
          packages=find_packages(exclude=['examples', 'tests', 'tests.*']),
          # package_data={'': ['**/*.R']},
          # include_package_data=True,
          author='Diviyan Kalainathan',
          author_email='diviyan.kalainathan@lri.fr',
          license='Apache 2.0')
    print("Don't forget to configure the extra files in ~/.ssh/")


if __name__ == '__main__':
    copy2("./slurm_config.yml", os.environ['HOME'] + "/.ssh/")
    copy2("./default_ssh_config", os.environ['HOME'] + "/.ssh/")
    setup_package()
