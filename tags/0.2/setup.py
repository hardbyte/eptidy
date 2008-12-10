#!/usr/bin/env python
# Installer for eptidy...
# Make a windows executable with: python setup.py bdist_wininst --install-script linking.py
# Make a debian or rpm in a similar way.

from distutils.core import setup

setup(name = 'eptidy',
	  version = '0.2',
	  description = 'Tidy up all your tv episodes',
	  author = 'Og and the Tait Slackers :-p',
	  author_email = 'ogtifs+eptidy@gmail.com',
	  license='GPL v3 :: GNU General Public License', 
	  classifiers=[ 'Development Status :: 3 - Alpha/Beta', 'Intended Audience :: End Users/Desktop', ], 
	  maintainer = 'Brian',
	  maintainer_email = 'hardbyte+eptidy@gmail.com',
	  url = 'http://code.google.com/p/eptidy/',
	  download_url = 'http://code.google.com/p/eptidy/downloads/list',
	  scripts=['linking.py'], 
	  py_modules = ['eptidy'],
	  )