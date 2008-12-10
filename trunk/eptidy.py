#!/usr/bin/python
"""
Eptidy - Tidy up all your tv episodes

TODO: 
* download cache?
* progress bar (with cancel button)
* windows hidden dirs should be ignored
* easter eggs
* pack/distro
* port to a universal gui like tk :-P
* icon for standalone + python based program 
* bmp for installer
* windows uninstaller in linking.py
* SMALL standalone version
* Option to exclude some files
* implement wxChoice for the patterns... http://genotrance.wordpress.com/2006/08/19/wxpython-widgets-part-i/

BUGS:
* Didn't parse S1 10 or S1 E10
* Didn't work when IMDB went down, need some mirror sites or something
* %0e does't work for numbers > 10 - work perfectly for 1-9 but screws when goes to 10
* Ugly in windows
"""
import urllib
import re
import os.path as osp
import os
from os import sys
import shelve
import wx

debug = True
def dp(str):
	"""Debug Print"""
	if debug:
		print(str)
	



class Eptidy:
	"""
	The standalone eptidy class.
	
	Usage:
	
	>>> e = Eptidy()
	>>> files = ["house s1e2.mpg", "scubs 05.02.avi"]
	>>> e.identifyFiles(files)
	(['house s1e2.mpg', 'scubs 05.02.avi'], [('House', None), ('0412142', None)])
	
	"""
	# Set the path to and filename of our database.
	fileName = ".eptidy.dat"
	
	imdbBaseAddress = "http://www.imdb.com/title/tt"
	# Ze German
	#imdbBaseAddress = "http://www.imdb.de/title/tt"
	imdbData = {} # filled by getEpName
	
	def __init__(self):
		"""Find the location of our eptidy files
		And load the data from them. Else load defaults"""
		if self.fileName is None:
			#TODO: find the filename here...
			self.fileName = ".eptidy.dat"		# CHANGEME
		
		db = shelve.open(self.fileName)
		try:
			self.proxy = db['proxy']
		except KeyError:
			self.proxy = db['proxy'] = 'http://proxyhost.tait.co.nz'
		try:
			# load shows
			self.shows = db['shows']
		except KeyError:
			# No data availave - load default shows and save them.
			self.shows = db['shows'] = {
				'Dexter':'0773262',
				'Bones':'0460627',
				'House':'0412142',
				'Scrubs':'0285403',
				'Prison Break':'0455275',
				'Chuck':'0934814',
				'How I Met Your Mother':'0460649',
				'Terminator':'0851851',
				'Californication':'0904208',
				'Top Gear':'0163503',
				'Burn Notice':'0810788',
				'Boston Legal':'0402711',
				'Gossip Girl':'0397442',
				'Pushing Daisies':'0925266',
				'Heroes':'0813715',
				'The Big Bang Theory':'0898266'
				#evryone add their fav!
			}
		try:
			# load patterns
			self.patterns = db['patterns']
		except KeyError:
			self.patterns = db['patterns'] = ["%t %sx%e - %n"]
			
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
		db['patterns'] = [pattern] + db['patterns']
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
		db['shows'][episodeName] = imdbNum
		db.close()
		
	def removeEpisode(self,episodeName):
		"""Remove a show from the list we search for...
		"""
		db = shelve.open(self.fileName)
		del db['shows'][episodeName]
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
		v = None
		for key,val in self.shows.iteritems():
			r = key.replace(" ",".")
			m = re.search(re.compile(r,re.IGNORECASE),fileName)
			if m:
				k = key
				v = val
				return k,v
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
		# concatenate episode names to season numbers and episode numbers
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
			try:
				u = urllib.urlopen(self.imdbBaseAddress + imdbId + '/episodes')
			except Exception, e:
				try:
					#try work proxy
					u = urllib.urlopen(self.imdbBaseAddress + imdbId + '/episodes', proxies={'http':self.proxy})
				except Exception, e:
					print "Internet not available from python. Are you behind a proxy?\n%s" % e
					raise SystemExit
			# get big string of html page
			self.imdbData[imdbId] = ''
			for line in u.readlines():
				self.imdbData[imdbId] += line;
		# parse html page for relevant data
		r = "Season " + season + ", Episode " + epnum + ": <.*?>([^<]+)"
		# Ze German imdb
		#r = "Staffel " + season + ", Folge " + epnum + ": <.*?>([^<]+)"
		m = re.search(re.compile(r),self.imdbData[imdbId])
		if m: return m.group(1)
		else: return ""
	

class optionsBox(wx.Dialog):
	def __init__(self,parent):
		wx.Dialog.__init__(self,parent,-1,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
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
		# EPISODE PANE
		ep_sizer = wx.BoxSizer(wx.HORIZONTAL)
		ep_buts = wx.BoxSizer(wx.VERTICAL)
		self.ep_list = wx.ListCtrl(self.tab_eps,-1)
		self.ep_add = wx.Button(self.tab_eps,-1,"Add")
		self.ep_edt = wx.Button(self.tab_eps,-1,"Edit")
		self.ep_del = wx.Button(self.tab_eps,-1,"Remove")
		
		
		# BUILDING IT UP
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

class mainFrame(wx.Frame):
	def __init__(self):
		# Create the back end
		self.e = Eptidy()
		#kwds["style"] = wx.DEFAULT_FRAME_STYLE
		wx.Frame.__init__(self, None, -1, "")
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
		self.text_ctrl_2 = wx.TextCtrl(self.panel_1, -1, self.e.patterns[0])
		nptt = wx.ToolTip("%t : Show Title\n%n : Episode Name\n%s : Season Number\n%0s : Zero-padded Season Number\n%e : Episode Number\n%0e : Zero-padded Episode Number")
		self.text_ctrl_2.SetToolTip(nptt)
		self.checkbox_save_pattern = wx.CheckBox(self.panel_1,-1,"Save Pattern?")
		self.checkbox_save_pattern.SetValue(0)
		self.button_opts = wx.Button(self.panel_1,-1,"Options")
		self.button_2 = wx.Button(self.panel_1, -1, "Scan")
		self.button_3 = wx.Button(self.panel_1, -1, "Process")
		self.button_4 = wx.Button(self.panel_1, -1, "Rename Files")
		self.label_3 = wx.StaticText(self.panel_1, -1, "Search for:")
		self.text_ctrl_3 = wx.TextCtrl(self.panel_1, -1, "", style=wx.TE_MULTILINE)
		self.text_ctrl_3.SetEditable(False)
		self.SetTitle("Episode Renamer")
		self.SetSize((650, 400))
		self.status = self.CreateStatusBar()
		sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_2 = wx.BoxSizer(wx.VERTICAL)
		sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
		#EPISODE GRID SQUARE
		w = (len(self.e.shows)+1)/3
		grid_sizer_1 = wx.GridSizer(w, 3, 2, 2)
		self.cbs = [wx.CheckBox(self.panel_1,-1,k) for k,v in self.e.shows.iteritems()]
		[a.SetValue(1) for a in self.cbs]
		[grid_sizer_1.Add(a,0,0,0) for b,a in enumerate(self.cbs)]
		#END EPISODE GRID SQUARE
		sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_3.Add(self.label_1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
		sizer_3.Add(self.text_ctrl_1, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
		sizer_3.Add(self.button_1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
		sizer_3.Add(self.checkbox_1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
		sizer_2.Add(sizer_3, 0, wx.EXPAND, 0)
		sizer_4.Add(self.label_2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
		sizer_4.Add(self.text_ctrl_2, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
		sizer_4.Add(self.checkbox_save_pattern,0,wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
		sizer_2.Add(sizer_4, 0, wx.EXPAND, 0)
		sizer_6.Add(self.label_3, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
		sizer_6.Add(grid_sizer_1, 1, wx.EXPAND, 0)
		sizer_2.Add(sizer_6, 0, wx.EXPAND, 0)
		sizer_5.Add(self.button_opts, 2, wx.ALL, 2)
		sizer_5.Add(self.button_2, 2, wx.ALL, 2)
		sizer_5.Add(self.button_3, 2, wx.ALL, 2)
		sizer_5.Add(self.button_4, 2, wx.ALL, 2)
		sizer_2.Add(sizer_5, 0, wx.EXPAND, 0)
		sizer_2.Add(self.text_ctrl_3, 1, wx.ALL|wx.EXPAND, 2)
		self.panel_1.SetSizer(sizer_2)
		
		sizer_1.Add(self.panel_1, 1, wx.ALL|wx.EXPAND,5)
		self.panmain.SetSizer(sizer_1)
		rootbox.Add(self.panmain,1, wx.ALL|wx.EXPAND,0)
		self.SetSizer(rootbox)
		rootbox.Fit(self)
		self.Layout()
		self.Bind(wx.EVT_BUTTON, self.handleOpts, self.button_opts)
		self.Bind(wx.EVT_BUTTON, self.handleScan, self.button_2)
		self.Bind(wx.EVT_BUTTON, self.handleProcess, self.button_3)
		self.Bind(wx.EVT_BUTTON, self.handleBrowse, self.button_1)
		self.Bind(wx.EVT_BUTTON, self.handleRename, self.button_4)
		self.status.SetStatusText("Ready")

	
	def handleBrowse(self,event):
		"""
		change the current directory to that selected by a pop up dir chooser (wxDirDialog)
		"""
		dlg = wx.DirDialog(self,"Choose a directory:")
		if dlg.ShowModal() == wx.ID_OK:
			self.text_ctrl_1.Remove(0,self.text_ctrl_1.GetLastPosition())
			self.text_ctrl_1.SetInsertionPoint(0)
			self.text_ctrl_1.WriteText(dlg.GetPath())
		dlg.Destroy()
	
	def handleOpts(self,event):
		opts = optionsBox(self)
		opts.Show()
		
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
			self.text_ctrl_3.Remove(0,self.text_ctrl_3.GetLastPosition())
			self.text_ctrl_3.SetInsertionPoint(0)
			if self.doFiles: self.text_ctrl_3.WriteText('\n'.join(zip(*self.doFiles)[0]))
			self.status.SetStatusText("Ready")
		else:
			print "Invalid path"
		
	def handleProcess(self,event):
		self.status.SetStatusText("Processing...")
		namePattern = self.text_ctrl_2.GetValue()
		preFiles = self.e.parseFiles(self.doFiles)
		inFiles = zip(*self.doFiles)[0]
		outFiles = []
		for file in enumerate(preFiles):
			n = namePattern
			# Zero padding for season and episode numbers
			# Doesn't work in python 2.4...
			#n = n.replace('%0s','0%s') if int(file[1][2]) < 10 else n.replace('%0s','%s')
			#n = n.replace('%0e','0%e') if int(file[1][3]) < 10 else n.replace('%0e','%e')
			if int(file[1][2]) < 10: n = n.replace('%0s','0%s')
			else: n = n.replace('%0s','%s')
			if int(file[1][3]) < 10: n = n.replace('%0e','0%e')
			else: n = n.replace('%0e','%e')
			# Replace codes with values
			for x,y in zip(('%t','%n','%s','%e'),file[1]): n = n.replace(x,y) 
			inFilePath = osp.split(inFiles[file[0]])[0]
			inFileExt = osp.splitext(inFiles[file[0]])[1]
			outFiles.append(osp.join(inFilePath,n+inFileExt))
		self.fileMap = zip(inFiles,outFiles)
		
		self.text_ctrl_3.Remove(0,self.text_ctrl_3.GetLastPosition())
		self.text_ctrl_3.SetInsertionPoint(0)
		self.text_ctrl_3.WriteText("\n".join([x[0]+" => "+x[1] for x in self.fileMap]))
		if self.checkbox_save_pattern.GetValue():
			self.e.savePattern(namePattern)
		self.status.SetStatusText("Ready")
	
	def handleRename(self,event):
		self.status.SetStatusText("Renaming...")
		for old,new in self.fileMap:
			if old != new:
				os.renames(old,new)
		self.status.SetStatusText("Ready")


class gui(wx.App):
	def OnInit(self):
		"""Override OnInit to create our Frame"""
		wx.InitAllImageHandlers()
		mf = mainFrame()
		self.SetTopWindow(mf)
		mf.Show()
		return 1


if __name__ == "__main__":
	g = gui(0)
	g.MainLoop()

