__author__="jonathan"
__date__ ="$Jul 4, 2011 2:46:44 AM$"

from setuptools import setup,find_packages

setup (
  name = 'Mist',
  version = '0.1',
  packages = find_packages(),

  install_requires=['mutagen', 'sqlalchemy'],

  author = 'jonathan',
  author_email = 'jallen01@mit.edu',

  summary = 'Manage music files accross multiple directories',
  url = '',
  license = '',
  long_description= '',

)