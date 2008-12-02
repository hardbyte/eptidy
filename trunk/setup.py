#!/usr/bin/env python
# Installer for eptidy...
# Make a windows executable with: python setup.py bdist_wininst --install-script linking.py
from distutils.core import setup

setup(name = 'eptidy',
	  version = '0.1',
	  description = 'Tidy up all your tv episodes',
	  author = 'Og',
	  author_email = 'ogtifs@gmail.com',
	  license='GPL v3 :: GNU General Public License', 
	  classifiers=[ 'Development Status :: 3 - Alpha', 'Intended Audience :: End Users/Desktop', ], 
	  maintainer = 'Brian',
	  maintainer_email = 'hardbyte+eptidy@gmail.com',
	  url = 'http://code.google.com/p/eptidy/',
	  download_url = 'http://code.google.com/p/eptidy/downloads/list',
	  scripts=['linking.py'], 
	  py_modules = ['eptidy'],
	  )