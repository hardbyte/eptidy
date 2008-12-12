#!/usr/bin/python
"""see: http://docs.python.org/distutils/builtdist.html
this script gets run after the module has been installed.
Anything printed gets output to the gui installer.
It makes the shortcuts currently just for windows
"""

import sys, os

def install():
	if sys.platform == 'win32':
		print "Adding shortcuts to >>Start>Programs>eptidy" 
		progsFolder= get_special_folder_path("CSIDL_COMMON_PROGRAMS") 
		sitePackages = os.path.join(sys.prefix , 'lib','site-packages')

		#Create Eptidy Programs folder 
		eptidyShortcuts = os.path.join(progsFolder, 'eptidy') 
		if not os.path.isdir(eptidyShortcuts): 
			os.mkdir(eptidyShortcuts) 
			directory_created(eptidyShortcuts)

		#script link
		eptidyLink=os.path.join(eptidyShortcuts, "eptidy.lnk") 
		if os.path.isfile(eptidyLink): 
			os.remove(eptidyLink)	# we want to make a new one
			
		path2py = sys.exec_prefix
		shortcutPath = '"' + path2py + '\\pythonw.exe" "' + os.path.join(sitePackages,'eptidy.py"')
		create_shortcut(shortcutPath, 'Run eptidy', eptidyLink)
		file_created(eptidyLink)

		#homepage 
		homePageLink = os.path.join(eptidyShortcuts, "eptidy project page.lnk") 
		if os.path.isfile(homePageLink): 
			os.remove(homePageLink) #we want to make a new one 
		create_shortcut(r"http://code.google.com/p/eptidy/", 'Link to the eptidy project on google code.', homePageLink) 
		file_created(homePageLink)

		print "All done. Enjoy!"

if len(sys.argv) > 1: 
	if sys.argv[1] == '-install': 
		install()
	else: 
		print "Script was called with option %s" % sys.argv[1] 

