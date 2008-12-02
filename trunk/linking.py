#!/usr/bin/python
#http://docs.python.org/distutils/builtdist.html
#this script gets run after the module has been installed - it makes the shortcut


import sys, os

def install(): 
	print "Adding shortcuts to >>Start>Programs>eptidy" 
	progsFolder= get_special_folder_path("CSIDL_COMMON_PROGRAMS") 
	sitePackages = os.path.join(sys.prefix , 'lib','site-packages')

	#Eptidy Programs folder 
	eptidyShortcuts = os.path.join(progsFolder, 'eptidy') 
	if not os.path.isdir(eptidyShortcuts): 
		os.mkdir(eptidyShortcuts) 
		directory_created(eptidyShortcuts)

	#script link
	eptidyLink=os.path.join(eptidyShortcuts, "eptidy.lnk") 
	if os.path.isfile(eptidyLink): 
		os.remove(eptidyLink)#we want to make a new one

	create_shortcut(os.path.join(sitePackages,'eptidy.py'), 'eptidy', eptidyLink)
	file_created(eptidyLink)

	#homepage 
	homePageLink = os.path.join(eptidyShortcuts, "eptidyWWW.lnk") 
	if os.path.isfile(homePageLink): 
		os.remove(homePageLink) #we want to make a new one 
	create_shortcut(r"http://code.google.com/p/eptidy/", 'eptidy HomePage', homePageLink) 
	file_created(homePageLink)

	print "All done. Enjoy!"

if len(sys.argv) > 1: 
	if sys.argv[1] == '-install': 
		install()
	else: 
		print "Script was called with option %s" % sys.argv[1] 

