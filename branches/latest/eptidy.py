#!/usr/bin/python
# coding: utf8
"""
Eptidy - Tidy up all your tv episodes

TODO: 
* How to use and documentation on project homepage: http://code.google.com/p/eptidy/
* download cache?
* progress bar (with cancel button)
* windows hidden dirs should be ignored
* easter eggs
* icon for standalone + python based program 
* bmp for installer
* windows uninstaller in linking.py
* Option to exclude some files

BUGS:
* Didn't parse S1 10 or S1 E10
* Didn't work when IMDB went down, need some mirror sites or something
* %0e does't work for numbers > 10 - work perfectly for 1-9 but screws when goes to 10 //FIXED
* Ugly in windows // isn't everything?
"""

__version__ = '0.3'

import urllib
import re
import os.path as osp
import os
from os import sys
import shelve
import wx
from wx import grid as wxgrid
import copy
import string


debug = True
def dp(str):
	"""Debug Print"""
	if debug:
		print(str)
	

class Show:
	"""A show object..."""
	def __init__(self,name,imdb,match,enabled=True,comments=None):
		self.name = name
		self.imdb = imdb
		self.match = match
		self.enabled = True
		self.comments = comments




class Eptidy:
	"""
	The standalone eptidy class.
	
	Usage:
	
	>>> e = Eptidy()
	>>> files = ["house s1e2.mpg", "scubs 05.02.avi"]
	>>> e.identifyFiles(files)
	(['house s1e2.mpg', 'scubs 05.02.avi'], [('House', None), ('0412142', None)])
	
	"""
	
	SHOWS = [
				('Dexter','0773262','dexter'),
				('Bones','0460627','bones'),
				('House','0412142','house'),
				('Scrubs','0285403','scrubs'),
				('Prison Break','0455275','prison.break'),
				('Chuck','0934814','chuck'),
				('How I Met Your Mother','0460649','how.i.met.your.mother'),
				('Terminator','0851851','terminator|ttscc'),
				('Californication','0904208','californication'),
				('Top Gear','0163503','top.gear',False),
				('Burn Notice','0810788','burn.notice'),
				('Boston Legal','0402711','boston.legal'),
				('Gossip Girl','0397442','gossip.girl'),
				('Pushing Daisies','0925266','pushing.dasies'),
				('Heroes','0813715','heroes'),
				('The Big Bang Theory','0898266','big.bang.theory|tbbt'),
				('Arrested Development','0367279','arrested.development'),
				('MythBusters','0383126','mythbusters'),
				('Outrageous Fortune','0461097','outrageous.fortune'),
				('Psych','0491738','psych'),
				('Two and a Half Men','0369179','two.and.a.half.men')
				#evryone add their fav!
			]
	
	# Set the path to and filename of our database.
	if os.name == 'posix':
		fileName = "%s/.eptidy" % os.environ["HOME"]
	elif os.name == 'mac':
		fileName = "%s/Library/Application Support/eptidy" % os.environ["HOME"]
	elif os.name == 'nt':
		fileName = "%s\Application Data\EpTidy" % os.environ["USERPROFILE"]
	else:
		fileName = ".eptidy"
	
	dp('filename: %s' % fileName)
	imdbBaseAddress = "http://www.imdb.com/title/tt"
	# Ze German
	#imdbBaseAddress = "http://www.imdb.de/title/tt"
	imdbData = {} # filled by getEpName
	
	def __init__(self):
		"""Find the location of our eptidy files
		And load the data from them. Else load defaults"""
		try:
			db = shelve.open(self.fileName)
		except Exception, e:
			dp('Unable to open file\nError: %s' % e)
		try:
			self.use_proxy = db['use_proxy']
		except KeyError:
			self.use_proxy = False
		try:
			self.proxy = db['proxy']
		except KeyError:
			self.proxy = db['proxy'] = '' #'http://202.37.97.11:3128'
		try:
			# load shows
			self.shows = db['shows']
		except KeyError:
			# No data availave - load default shows list and save them for future.
			self.shows = db['shows'] = [Show(*show) for show in self.SHOWS]
		try:
			# load patterns
			self.patterns = db['patterns']
		except KeyError:
			self.patterns = db['patterns'] = ["%t %sx%0e - %n","%t.S%0sE%0e.%n",osp.normpath(osp.expanduser('~')+'/%t/Season %s/%0e - %n')]
			
		db.close()
	
	
	def addProxy(self,proxyAddress):
		"""If python requires a proxy to access the interwebs add it here.
		This function overwrites any previous proxy
		"""
		db = shelve.open(self.fileName)
		db['proxy'] = proxyAddress
		db.close()
	
	def savePattern(self,pattern):
		db = shelve.open(self.fileName)
		db['patterns'] += [pattern]
		db.close()

	def getImdbNum(self,episodeName):
		# TODO: search for imdb number 
		raise NotImpementedError 
		
	def addEpisode(self,episodeName,imdbNum=None):
		"""Add an episode to the database, presently requires a imbd id
		"""
		if imdbNum is None:
			imdbNum = getImdbNum(episodeName)
		db = shelve.open(self.fileName)
		db['shows'].append(Show(episodeName,imdbNum))
		db.close()
		
	def removeEpisode(self,episodeName):
		"""Remove a show from the list we search for...
		"""
		db = shelve.open(self.fileName)
		db['shows'].remove(episodeName) #can't you just do this?
		db.close()
	
	def saveChanges(self):
		"""Save the shows and patterns and proxy settings"""
		db = shelve.open(self.fileName)
		db['shows'] = self.shows
		db['proxy'] = self.proxy
		db['use_proxy'] = self.use_proxy
		db['patterns'] = self.patterns
		db.close()
			
	def parseFileName(self,fileName):
		'''
			Given a filename, return a tuple containing
			its season and episode number. Returns
			(None,None) if could not be determined
		'''
		m = \
			re.search(r"[sS]0?(\d?\d)[eE]0?(\d?\d)",fileName) or \
			re.search(r"0?(\d?\d)[xX]0?(\d?\d)",fileName) or \
			re.search(r"(\d)0?(\d?\d)",fileName) or \
			re.search(r"0?(\d?\d).*?0?(\d?\d)",fileName)
		if m: return m.groups()
		else: return (None,None)
	
	def getImdbId(self,fileName):
		for s in [a for a in self.shows if a.enabled]:
			m = re.search(re.compile(s.match,re.IGNORECASE),fileName)
			if m: return s.name,s.imdb
		return None,None
	
	def identifyFiles(self,files):
		'''
		Given a list of files, return a list of tuples
		containing season number, episode number, episode name
		'''
		# get file name only
		filenames = map(osp.basename,files)
		# determine imdb code for each show name supplied
		# showNames,imdbCodes = map(self.getImdbId,filenames)
		imdbData = zip(*map(self.getImdbId,filenames))
		return (files,imdbData)
		
	def parseFiles(self,identifiedFiles):
		# determine season and episode number from filename
		identifiers = map(self.parseFileName,zip(*identifiedFiles)[0])
		# produce list of tuples containing all data required for site parsing
		episodeData = zip(zip(*identifiedFiles)[2],*zip(*identifiers))
		# get episode name for each item
		names = map(self.getEpName,episodeData)
		# concatenate episode names to season numgnuradiobers and episode numbers
		results = zip(zip(*identifiedFiles)[1],names,*zip(*identifiers))
		return results
	
	def getEpName(self,episodes):
		'''
			Given a tuple (IMDB id, season, episode), return
			episode name retrieved from IMDB
		'''
		dp('getting ep names')
		if None in episodes: return None
		
		imdbId = episodes[0]
		season = episodes[1]
		epnum = episodes[2]
		if not imdbId in self.imdbData:
			# retrieve imdb url
			if self.use_proxy == True:
				proxies = {'http':self.proxy}
			else:
				proxies = None
			try:
				u = urllib.urlopen(self.imdbBaseAddress + imdbId + '/episodes',proxies)
			except Exception, e:
				wx.MessageBox("Internet not available from python. Are you behind a proxy?\n%s" % e, "Error", wx.ICON_ERROR)
				return ""
			# get big string of html page
			self.imdbData[imdbId] = ''
			for line in u.readlines():
				self.imdbData[imdbId] += line;
		# parse html page for relevant data
		r = "Season " + season + ", Episode " + epnum + ": <.*?>([^<]+)"
		# Ze German imdb
		#r = "Staffel " + season + ", Folge " + epnum + ": <.*?>([^<]+)"
		m = re.search(re.compile(r),self.imdbData[imdbId])
		if m:
			t = string.maketrans(u"?:/\\*\"<>|",u"¿?//??‹›¦")
			return string.translate(encode(m.group(1),'utf8'),t)
		else: return ""
	
class epEntryBox(wx.Dialog):
	def __init__(self,parent,edit=None):
		self.parent = parent
		self.edit = edit
		wx.Dialog.__init__(self,parent,-1,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		rootsizer = wx.BoxSizer(wx.VERTICAL)
		rootpanel = wx.Panel(self,-1)
		mainsizer = wx.BoxSizer(wx.VERTICAL)
		ctrlbuts = wx.BoxSizer(wx.HORIZONTAL)
		controlspace = wx.Panel(rootpanel,-1)
		okbut = wx.Button(rootpanel,-1,"OK")
		self.Bind(wx.EVT_BUTTON, self.OK, okbut)
		canbut = wx.Button(rootpanel,-1,"Cancel")
		self.Bind(wx.EVT_BUTTON, self.Cancel, canbut)
		ctrlbuts.Add(controlspace,1,wx.ALL|wx.EXPAND,5)
		ctrlbuts.Add(canbut,0,wx.ALL,5)
		ctrlbuts.Add(okbut,0,wx.ALL,5)
		grid = wx.GridSizer(3,2)
		self.controls = [(wx.StaticText(rootpanel,-1,n+": "),wx.TextCtrl(rootpanel,-1,"")) for n in ("Episode","IMDB Id","Match Expression")]
		[(grid.Add(n,0,wx.ALIGN_RIGHT|wx.ALL|wx.EXPAND,5),grid.Add(m,1,wx.ALL|wx.EXPAND,5)) for (n,m) in self.controls]
		if edit is not None:
			tbs = zip(*self.controls)[1]
			tbs[0].SetValue(self.parent.shows[edit].name)
			tbs[1].SetValue(self.parent.shows[edit].imdb)
			tbs[2].SetValue(self.parent.shows[edit].match)
		mainsizer.Add(grid,0,wx.ALL&~wx.BOTTOM|wx.EXPAND,5)
		mainsizer.Add(ctrlbuts,0,wx.ALL&~wx.TOP|wx.EXPAND,5)
		rootpanel.SetSizer(mainsizer)
		rootsizer.Add(rootpanel,0,wx.ALL|wx.EXPAND,0)
		self.SetSizer(rootsizer)
		
	def Cancel(self,event): self.EndModal(0)
	
	def OK(self,event):
		tbs = zip(*self.controls)[1]
		n = [n for (n,m) in self.controls if m.IsEmpty()]
		if n:
			[ewx.MessageBox("%s field must not be empty"%a,"Error",wx.ICON_ERROR) for a in n]
		else:
			if self.edit is not None:
				self.parent.shows[self.edit].name = tbs[0].GetValue()
				ischecked = self.parent.ep_list.IsChecked(self.edit)
				self.parent.ep_list.SetString(self.edit,tbs[0].GetValue())
				self.parent.ep_list.Check(self.edit,ischecked)
				self.parent.shows[self.edit].imdb = tbs[1].GetValue()
				self.parent.shows[self.edit].match = tbs[2].GetValue()
			else:
				self.parent.AddItem([n.GetValue() for n in zip(*self.controls)[1]])
		self.EndModal(0)
	

class optionsBox(wx.Dialog):
	def __init__(self,parent):
		dp('Init called')
		self.parent = parent
		self.shows = copy.deepcopy(parent.e.shows)
		wx.Dialog.__init__(self,parent,-1,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.nEps = 0
		# MAIN LAYOUT
		rootbox = wx.BoxSizer(wx.VERTICAL)
		self.rootpanel = wx.Panel(self,-1)
		mainsizer = wx.BoxSizer(wx.VERTICAL)
		# TABS
		self.tabs = wx.Notebook(self.rootpanel,-1)
		self.tab_eps = wx.Panel(self.tabs,-1)
		self.tab_network = wx.Panel(self.tabs,-1)
		# CONTROL BUTTONS
		controlbuts = wx.BoxSizer(wx.HORIZONTAL)
		controlspace = wx.Panel(self.rootpanel,-1)
		self.okbut = wx.Button(self.rootpanel,-1,"OK")
		self.canbut = wx.Button(self.rootpanel,-1,"Cancel")
		self.Bind(wx.EVT_BUTTON, self.handleCancel, self.canbut)
		self.Bind(wx.EVT_BUTTON, self.handleOK, self.okbut)
		# EPISODE PANE
		ep_sizer = wx.BoxSizer(wx.HORIZONTAL)
		ep_buts = wx.BoxSizer(wx.VERTICAL)
		self.ep_list = wx.CheckListBox(self.tab_eps,-1)
		self.Bind(wx.EVT_CHECKLISTBOX, self.handleEpCheck, self.ep_list)
		self.ep_list.Set([s.name for s in self.shows])
		[self.ep_list.Check(i,n.enabled) for i,n in enumerate(self.shows)]
		self.ep_add = wx.Button(self.tab_eps,-1,"Add")
		self.ep_edt = wx.Button(self.tab_eps,-1,"Edit")
		self.ep_del = wx.Button(self.tab_eps,-1,"Remove")
		self.Bind(wx.EVT_BUTTON, self.handleAdd, self.ep_add)
		self.Bind(wx.EVT_BUTTON, self.handleEdit, self.ep_edt)
		self.Bind(wx.EVT_BUTTON, self.handleRemove, self.ep_del)
		# NETWORK PANE
		nt_sizer = wx.BoxSizer(wx.VERTICAL)
		nt_grsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.nt_usep = wx.CheckBox(self.tab_network,-1,"Use a proxy server")
		self.nt_usep.SetValue(parent.e.use_proxy)
		self.nt_plab = wx.StaticText(self.tab_network,-1,"Proxy Address:")
		self.nt_paddr = wx.TextCtrl(self.tab_network,-1,parent.e.proxy)
		
		# BUILDING IT UP
		#network pane
		nt_grsizer.Add(self.nt_plab,0,wx.ALL|wx.EXPAND,5)
		nt_grsizer.Add(self.nt_paddr,1,wx.ALL|wx.EXPAND,5)
		nt_sizer.Add(self.nt_usep,0,wx.ALL|wx.EXPAND,5)
		nt_sizer.Add(nt_grsizer,0,wx.ALL|wx.EXPAND,0)
		self.tab_network.SetSizer(nt_sizer)
		#episode pane
		ep_buts.Add(self.ep_add,0,wx.ALL|wx.EXPAND,5)
		ep_buts.Add(self.ep_edt,0,wx.ALL|wx.EXPAND,5)
		ep_buts.Add(self.ep_del,0,wx.ALL|wx.EXPAND,5)

		ep_sizer.Add(self.ep_list,1,wx.ALL&~wx.RIGHT|wx.EXPAND,5)
		ep_sizer.Add(ep_buts,0,wx.ALL|wx.EXPAND,0)
		self.tab_eps.SetSizer(ep_sizer)
		#tabs
		self.tabs.AddPage(self.tab_eps,"Episodes")
		self.tabs.AddPage(self.tab_network,"Network")
		mainsizer.Add(self.tabs,1,wx.ALL&~wx.BOTTOM|wx.EXPAND,5)
		#control buttons
		controlbuts.Add(controlspace,1,wx.ALL|wx.EXPAND,5)
		controlbuts.Add(self.canbut,0,wx.ALL,5)
		controlbuts.Add(self.okbut,0,wx.ALL,5)
		mainsizer.Add(controlbuts,0,wx.ALL|wx.EXPAND,0)
		#frame
		self.rootpanel.SetSizer(mainsizer)
		rootbox.Add(self.rootpanel,1, wx.ALL|wx.EXPAND,0)
		self.SetSizer(rootbox)
		rootbox.Fit(self)
		self.Layout()
	
	def handleEpCheck(self,event):
		item = event.GetSelection()
		self.shows[item].enabled = self.ep_list.IsChecked(item)
	
	def handleCancel(self,event):
		dp('Options: Cancel Button Pressed')
		del self.shows
		self.EndModal(0)
	
	def handleOK(self,event):
		dp('Options: Ok Button Pressed')
		self.parent.e.proxy = self.nt_paddr.GetValue()
		self.parent.e.use_proxy = self.nt_usep.GetValue()
		self.parent.e.shows = copy.deepcopy(self.shows)
		self.parent.e.saveChanges()
		self.EndModal(0)
	
	def handleAdd(self,event): epEntryBox(self).ShowModal()
	
	def handleEdit(self,event):
		item = self.ep_list.GetSelection()
		if item == wx.NOT_FOUND:
			wx.MessageBox("First select an item to edit","Error",wx.ICON_ERROR)
		else:
			epEntryBox(self,item).ShowModal()
	
	def handleRemove(self,event):
		item = self.ep_list.GetSelection()
		self.shows.pop(item)
		self.ep_list.Delete(item)
	
	def AddItem(self,item):
		self.shows.append(Show(*item))
		self.ep_list.Append(item[0])
		self.ep_list.Check(self.ep_list.GetCount())

class mainFrame(wx.Frame):
	def test(self,event):
		print event

	def __init__(self):
		# Create the back end
		self.e = Eptidy()
		wx.Frame.__init__(self, None, -1, "")
		#MENUBAR
		
		m_file = wx.Menu()
		m_file.Append(0,"&Options","Configure EpTidy")
		wx.EVT_MENU(self,0,self.handleOpts)
		m_file.AppendSeparator()
		m_file.Append(wx.ID_EXIT,"E&xit")
		wx.EVT_MENU(self,wx.ID_EXIT,self.Quit)
		
		m_help = wx.Menu()
		m_help.Append(1,"&How to Use")
		m_help.Append(2,"&Naming Patterns")
		wx.EVT_MENU(self,2,self.handleHelp)
		m_help.Append(3,"&About")
		
		m = wx.MenuBar()
		m.Append(m_file,"File")
		m.Append(m_help,"Help")
		self.SetMenuBar(m)
		#END MENUBAR
		
		self.panmain = wx.Panel(self,-1)
		rootbox = wx.BoxSizer(wx.VERTICAL)
		self.panel_1 = wx.Panel(self.panmain, -1)
		self.label_1 = wx.StaticText(self.panel_1, -1, "Path:")
		self.text_ctrl_1 = wx.TextCtrl(self.panel_1, -1, "")
		self.text_ctrl_1.WriteText(os.path.expanduser('~'))
		self.button_1 = wx.Button(self.panel_1, -1, "Browse")
		self.checkbox_1 = wx.CheckBox(self.panel_1, -1, "Recursive")
		self.checkbox_1.SetValue(1)
		self.label_2 = wx.StaticText(self.panel_1, -1, "Naming Pattern:")
		self.namepatts = wx.ComboBox(self.panel_1,-1, self.e.patterns[0], choices = self.e.patterns)
		self.pattern_help = wx.Button(self.panel_1,-1,"?")
		self.button_2 = wx.Button(self.panel_1, -1, "Scan")
		self.button_2.SetDefault()
		self.button_3 = wx.Button(self.panel_1, -1, "Process")
		self.button_4 = wx.Button(self.panel_1, -1, "Rename Files")
		self.eplist = wx.CheckListBox(self.panel_1,-1,size=(-1,150))
		self.SetTitle("Episode Renamer")
		self.SetSize((650, 400))
		self.status = self.CreateStatusBar()
		sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_2 = wx.BoxSizer(wx.VERTICAL)
		sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_3.Add(self.label_1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer_3.Add(self.text_ctrl_1, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer_3.Add(self.button_1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer_3.Add(self.checkbox_1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer_2.Add(sizer_3, 0, wx.EXPAND, 0)
		sizer_4.Add(self.label_2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer_4.Add(self.namepatts, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer_4.Add(self.pattern_help,0,wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
		sizer_2.Add(sizer_4, 0, wx.EXPAND, 0)
		sizer_5.Add(self.button_2, 2, wx.ALL, 5)
		sizer_5.Add(self.button_3, 2, wx.ALL, 5)
		sizer_5.Add(self.button_4, 2, wx.ALL, 5)
		sizer_2.Add(sizer_5, 0, wx.EXPAND, 0)
		sizer_2.Add(self.eplist, 1, wx.ALL|wx.EXPAND, 5)
		self.panel_1.SetSizer(sizer_2)
		
		sizer_1.Add(self.panel_1, 1, wx.ALL|wx.EXPAND,5)
		self.panmain.SetSizer(sizer_1)
		rootbox.Add(self.panmain,1, wx.ALL|wx.EXPAND,0)
		self.SetSizer(rootbox)
		rootbox.Fit(self)
		self.Layout()
		self.Bind(wx.EVT_BUTTON, self.handleHelp, self.pattern_help)
		self.Bind(wx.EVT_BUTTON, self.handleScan, self.button_2)
		self.Bind(wx.EVT_BUTTON, self.handleProcess, self.button_3)
		self.Bind(wx.EVT_BUTTON, self.handleBrowse, self.button_1)
		self.Bind(wx.EVT_BUTTON, self.handleRename, self.button_4)
		self.status.SetStatusText("Ready")
	
	def handleHelp(self,event):
		wx.MessageBox('''
%t : Show Title
%n : Episode Name
%s : Season Number
%0s : Zero-padded Season Number
%e : Episode Number
%0e : Zero-padded Episode Number


For example, given "dexter203.avi":

"%t %sx%0e" produces
"Dexter 2x03.avi"

"C:\TV\%t\Season %s\%t" produces
"C:\TV\Dexter\Season 2\An Inconvenient Lie.avi"'''
		,"Naming Pattern Help",wx.ICON_INFORMATION)

	
	def handleBrowse(self,event):
		"""
		change the current directory to that selected by a pop up dir chooser (wxDirDialog)
		"""
		p = wx.DirSelector("Choose a directory:",self.text_ctrl_1.GetValue())
		if p != "":
			self.text_ctrl_1.SetValue(p)
	
	def handleOpts(self,event):
		opts = optionsBox(self)
		opts.ShowModal()
		
	def handleScan(self,event):
		"""
		This responds to the event when a search is initiated.
		It must get path, and work out what are movie/tv files.
		"""
		p = self.text_ctrl_1.GetValue();
		if osp.isdir(p):
			self.status.SetStatusText("Scanning...")
			extensions = ['.mp4','.avi','.mpg','.divx','.mkv','.wmv']
			if self.checkbox_1.GetValue() == True:
				files = []
				for (r,d,f) in os.walk(p):
					# don't scan hidden dirs,(note to self) is there a way we can get it to ask windows if a dir is hidden? - It'd be a stat type command, no?
					[d.remove(a) for a in d if a.startswith('.')]
					files += [osp.join(r,a) for a in f if os.path.splitext(a)[1].lower() in extensions]
			else:
				files = [a for a in os.listdir(p) if os.path.splitext(a)[1].lower() in extensions]
			d = self.e.identifyFiles(files)
			self.doFiles = [z for z in zip(d[0],*d[1]) if not None in z]
			#self.text_ctrl_3.Remove(0,self.text_ctrl_3.GetLastPosition())
			#self.text_ctrl_3.SetInsertionPoint(0)
			
			if self.doFiles:
				entries = zip(*self.doFiles)[0]
				self.eplist.Set(entries) #self.text_ctrl_3.WriteText('\n'.join(zip(*self.doFiles)[0]))
				[self.eplist.Check(i) for i in range(len(entries))]
			else: self.eplist.Set([])
			self.status.SetStatusText("Ready")
			self.button_3.SetDefault()
		else:
			wx.MessageBox("Invalid path","Error",wx.ICON_ERROR)
		
	def handleProcess(self,event):
		self.status.SetStatusText("Processing...")
		namePattern = self.namepatts.GetValue()
		self.doFiles = [a for i,a in enumerate(self.doFiles) if self.eplist.IsChecked(i)]
		preFiles = self.e.parseFiles(self.doFiles)
		inFiles = zip(*self.doFiles)[0]
		outFiles = []
		for file in enumerate(preFiles):
			n = namePattern
			if int(file[1][2]) < 10: n = n.replace('%0s','0%s')
			else: n = n.replace('%0s','%s')
			if int(file[1][3]) < 10: n = n.replace('%0e','0%e')
			else: n = n.replace('%0e','%e')
			# Replace codes with values
			for x,y in zip(('%t','%n','%s','%e'),file[1]): n = n.replace(x,y) 
			inFilePath = osp.split(inFiles[file[0]])[0]
			inFileExt = osp.splitext(inFiles[file[0]])[1]
			outFiles.append(osp.join(inFilePath,n+inFileExt))
		self.fileMap = [(a,b) for (a,b) in zip(inFiles,outFiles) if a != b]
		self.eplist.Set(["%s => %s" % x for x in self.fileMap])
		[self.eplist.Check(i) for i in range(len(self.fileMap))]
		self.e.savePattern(namePattern)
		self.status.SetStatusText("Ready")
		self.button_4.SetDefault()
	
	def handleRename(self,event):
		self.status.SetStatusText("Renaming...")
		for old,new in self.fileMap:
			os.renames(old,new)
		self.status.SetStatusText("Ready")
	
	def Quit(self,event): self.Close()


class gui(wx.App):
	def OnInit(self):
		"""Override OnInit to create our Frame"""
		wx.InitAllImageHandlers()
		mf = mainFrame()
		try:
			icon = wx.Icon(name='tvi.ico', type=wx.BITMAP_TYPE_ICO)
			mf.SetIcon(icon)
		except:
			dp('icon not found')
		self.SetTopWindow(mf)
		mf.Show()
		return 1


if __name__ == "__main__":
	g = gui(0)
	g.MainLoop()

