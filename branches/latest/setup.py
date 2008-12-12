#!/usr/bin/env python
# Installer and installer maker for eptidy...
# Make a windows executable with: 
# python setup.py bdist_wininst --bitmap tv_icon.bmp --install-script linking.py
# Make a standalone windows exe with: python setup.py py2exe
# Make a debian or rpm in a similar way.

from distutils.core import setup
import py2exe

manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="x86"
    name=""
    type="win32"
/>
<description>Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''

setup(name = 'eptidy',
	  version = '0.3',
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
	  options = {
		  	"py2exe": {
		  		"compressed": 1, 
		  		"optimize": 2, 
		  		"ascii": 1, 
		  		"bundle_files": 1,
		  		},
	  		},
	  zipfile = None,
	  windows = ["eptidy.py"],
	  	#'icon_resources':[(0,'tvi.ico')],
	  	#'other_resources':[(24, 1, manifest_template)],

	  	#},
	  #data_files = [('',['tvi.ico'])],
	  )
	  
