#!/usr/bin/python
__help__ = """
Eptidy - Tidy up all your tv episodes

Eptidy manages your collection of TV episodes
by scanning their file names, determining season
and episode numbers, and retrieving the corresponding
episode name from IMDB.

You can use this program to organise your
episodes with your preferred naming convention
and folder hierachy

Firstly, select a path by typing it in or using
the browse button, and choose whether you want
a recursive scan. Press Scan to have Eptidy
generate a list of all the episodes in that
location. Type in or select from the drop-down
list a naming convention (for help on these see
the naming pattern help option) and press Process.
After retrieving episode names from IMDB, Eptidy
will produce a list of proposed renames. Select
those you wish to make and press Rename Files.

Note: The Process button will remove unchecked
  entries from its list every time you press it.
"""

"""
TODO: 
* How to use and documentation on project homepage: http://code.google.com/p/eptidy/
* download cache - This should be a priority
* progress bar (with cancel button)
* windows hidden dirs should be ignored
* mac app
* icon for standalone + python based program 
* bmp for installer
* windows uninstaller in linking.py
* Option to exclude some files
* logging instead of debug print... let user choose to enable the log?

BUGS:
* Didn't parse S1 10 or S1 E10
* Didn't work when IMDB went down, need some mirror sites or something
* Ugly in windows // isn't everything?
"""

__version__ = '0.3'

import urllib
import re
import os
import os.path as osp
from os import sys
import shelve, dbhash, anydbm
import wx
from wx import grid as wxgrid
import copy
import string
import logging

debug = False

class EptidyException(Exception):
	pass
class InternetNotAvailable(EptidyException):
	pass

# if debug is on True - all output just goes to stderr, else just log errors to a file.
logFileName = (debug and [None] or ['log.txt'])[0]
logLevel = (debug and [logging.DEBUG] or [logging.ERROR])[0]
logging.basicConfig(level=logLevel, format='%(asctime)s %(levelname)s %(message)s', filename=logFileName)
logging.info("Starting eptidy")

def dp(str, level=logging.DEBUG):
	"""Debug Print"""
	if debug:
		logging.log(level, str)
	
class Show:
	"""
	A TV Series object... eg House M.D
	"""
	def __init__(self, name, imdb, match, enabled=True, comments=None):
		self.name = name
		self.imdb = imdb    # The imdb ID code
		self.match = match
		self.enabled = True
		self.comments = comments
		self.seasons = [{}]
		


class Eptidy:
	"""
	The standalone eptidy class for identifying tv shows from filenames.
	
	Usage:
	
	>>> e = Eptidy()
	>>> files = ["house s1e2.mpg", "scubs 05.02.avi"]
	>>> e.identifyFiles(files)
	(['house s1e2.mpg', 'scubs 05.02.avi'], [('House', None), ('0412142', None)])
	
	"""
	
	SHOWS = [
             ('Arrested Development', '0367279', 'arrested.development', False),
             ('Bones', '0460627', 'bones', False),
             ('Boston Legal', '0402711', 'boston.legal', False),
             ('Burn Notice', '0810788', 'burn.notice', False),
             ('Californication', '0904208', 'californication', False),
             ('Chuck', '0934814', 'chuck', False),
             ('Cougar Town', '1441109', 'cougar.town', False),
             ('Dexter', '0773262', 'dexter', False),
             ('Extras', '0445114', 'extras', False),
             ('Gossip Girl', '0397442', 'gossip.girl', False),
             ('Heroes', '0813715', 'heroes', False),
             ('House', '0412142', 'house', False),
             ('How I Met Your Mother', '0460649', 'how.i.met.your.mother', False),
             ("It's Always Sunny in Philadelphia",'0472954','its.always.sunny.in.philadelphia', False),
             ('Lie to Me', '1235099', 'lie.to.me', False),
             ('MythBusters', '0383126', 'mythbusters', False),
             ('Outrageous Fortune', '0461097', 'outrageous.fortune', False),
             ('Prison Break', '0455275', 'prison.break', False),
             ('Psych', '0491738', 'psych', False),
             ('Pushing Daisies', '0925266', 'pushing.dasies', False),
             ('Scrubs', '0285403', 'scrubs', False),
             ('South Park', '0472954', 'south.park', False),
             ('Terminator', '0851851', 'terminator|ttscc', False),
             ('The Big Bang Theory', '0898266', 'big.bang.theory|tbbt', False),
             ('The Mentalist', '1196946', 'the.mentalist', False),
             ('Top Gear', '0163503', 'top.gear', False),
             ('Two and a Half Men', '0369179', 'two.and.a.half.men', False),
				
			 # add your fav!
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
	
	#fileName = osp.join(wx.StandardPaths.Get().GetUserConfigDir(),'.eptidy')
	dp('filename: %s' % fileName)
	imdbBaseAddress = "http://www.imdb.com/title/tt"
	# Ze German
	#imdbBaseAddress = "http://www.imdb.de/title/tt"
	imdbData = {} # filled by getEpName
	
	def __init__(self):
		"""Find the location of our eptidy database file
		Load the data. Else load defaults"""
		try:
			db = shelve.open(self.fileName)
		except:
			dp('Unable to open database file: %s \n' % self.fileName)
			if os.path.exists(self.fileName): 
				dp("File was found, deleting now")
				os.remove(self.fileName)
				self.__init__()
			return
	
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
			dp("Couldn't load shows from db")
			# No data availave - load default shows list and save them for future.
			self.shows = db['shows'] = [Show(*show) for show in self.SHOWS]
		try:
			# load patterns
			self.patterns = db['patterns']
		except KeyError:
			self.patterns = db['patterns'] = ["%t %sx%0e - %n","%t.S%0sE%0e.%n", osp.normpath(osp.expanduser('~')+'/%t/Season %s/%0e - %n')]
			
		db.close()
	
	
	def addProxy(self, proxyAddress):
		"""
		If python requires a proxy to access the internet add it here.
		This function overwrites any previous proxy
		"""
		db = shelve.open(self.fileName)
		db['proxy'] = proxyAddress
		db.close()
	
	def savePattern(self, pattern):
		db = shelve.open(self.fileName)
		db['patterns'] += [pattern]
		db.close()

	def getImdbNum(self, episodeName):
		# TODO: search for imdb number 
		raise NotImpementedError 
		
	def addEpisode(self, imdbNum, season, episodeName, match=False):
		"""
		Add an episode to the database, presently requires an imbd id
		"""
		dp("Adding an episode - %s" % episodeName)
		if imdbNum is None:
			imdbNum = getImdbNum(episodeName)
		db = shelve.open(self.fileName)
		db['shows'].append(Show(episodeName, imdbNum, ".".join(episodeName.lower().split(" ")) ))
		
		db.close()
		
	def removeEpisode(self, episodeName):
		"""
		Remove a show from the list we search for...
		"""
		db = shelve.open(self.fileName)
		db['shows'].remove(episodeName)
		db.close()
	
	def saveChanges(self):
		"""
		Save any changes of the tv shows and naming patterns and proxy settings
		"""
		db = shelve.open(self.fileName)
		db['shows'] = self.shows
		db['proxy'] = self.proxy
		db['use_proxy'] = self.use_proxy
		db['patterns'] = self.patterns
		db.close()
			
	def parseFileName(self, fileName):
		"""
		Given a filename, return a tuple containing
		its season and episode number. Returns
		(None, None) if could not be determined
		"""
		#dp("Parsing file: " + fileName)
		m = \
			re.search(r"[sS]0?(\d?\d)[eE]0?(\d?\d)", fileName) or \
			re.search(r"0?(\d?\d)[xX]0?(\d?\d)", fileName) or \
			re.search(r"(\d)0?(\d?\d)", fileName) or \
			re.search(r"0?(\d?\d).*?0?(\d?\d)", fileName)
		if m:
		    return m.groups()
		else:
			dp("Episode not found.")
			return (None, None)

	
	def getImdbId(self, fileName):
		dp("Looking up ImdbId for file: " + fileName)
		for s in [a for a in self.shows if a.enabled]:
			m = re.search(re.compile(s.match, re.IGNORECASE), fileName)
			if m: 
			    return s.name, s.imdb
		return None, None
	
	def identifyFiles(self, files):
		"""
		Given a list of files, return a list of tuples
		containing season number, episode number, episode name
		"""

		# get file name only
		filenames = map(osp.basename, files)
		
		# determine imdb code for each show name supplied
		imdbData = zip(*map(self.getImdbId, filenames))
		return (files, imdbData)
		
	def parseFiles(self, identifiedFiles):
		"""
		For a list of files, parse their episode data.
		"""
		# determine season and episode number from filename
		dp("Identified files: %s" % identifiedFiles)
		#try:
		identifiers = map(self.parseFileName, zip(*identifiedFiles)[0])
		#except Exception, e:
		#	msg = "Couldn't determine season and episode number from filename"
		#	dp(msg)
		#	raise EptidyException(msg)
		# produce list of tuples containing all data required for site parsing
		try:
			episodeData = zip(zip(*identifiedFiles)[2],*zip(*identifiers))
		except Exception, e:
			msg = "Couldn't produce list of tuples containing all data required for site parsing"
			dp(msg)
			raise EptidyException(msg)
		
		# get episode name for each item
		try:
			names = map(self.getEpName, episodeData)
		except InternetNotAvailable, e: #TODO should be a specific exception, shouldn't use a wx message box
			if e is not None:
				wx.MessageBox("We can't seem to connect to the internet\nError: %s" % e, "Error", wx.ICON_ERROR)
			
			names = ['']*len(episodeData)
		# concatenate episode names to season numbers and episode numbers
		results = zip(zip(*identifiedFiles)[1],names,*zip(*identifiers))
		return results
	
	def getEpName(self, episodes):
		"""
		Given a tuple (IMDB id, season, episode), 
		return episode name retrieved from IMDB
		"""
		dp('Retrieving episode names')
		if None in episodes: return None
		
		imdbId, season, epnum = episodes

		if not imdbId in self.imdbData:
			
			# retrieve imdb url
			# First setup proxy
			if self.use_proxy == True:
				if not self.proxy.startswith('http://'):
					self.proxy = 'http://' + self.proxy
				prox = {'http':self.proxy}
			else:
				prox = None
				
			# Scrape imdb site
			dp('Scraping the IMDB website for episode information')
			try:
				u = urllib.urlopen(self.imdbBaseAddress + imdbId + '/episodes', proxies=prox)
			except Exception, e:
				dp('Internet not available\nError was: %s' % e)
				raise InternetNotAvailable("Internet is not available.\nDo you need to set up a proxy?")
			dp('Processing the scraped data')
			# get the html page as a big blob of string data
			self.imdbData[imdbId] = ''
			for line in u.readlines():
				self.imdbData[imdbId] += line;
		# parse html page for relevant data
		r = "Season " + season + ", Episode " + epnum + ": <.*?>([^<]+)"
		
		# Ze German imdb
		#r = "Staffel " + season + ", Folge " + epnum + ": <.*?>([^<]+)"
		
		m = re.search(re.compile(r), self.imdbData[imdbId])
		if m:
			result = m.group(1)
			for old, new in [
					('?','\xc2\xbf'), 
					#('/','\xE2\x81\x84'), 
					#('\\','\xE2\x88\x96'), 
					('*','\xE2\x88\x97'), 
					('&#x27;',"")
								]:
				result = result.replace(old, new)
			
			
			for s in enumerate(self.SHOWS):
				if imdbId == s[1][1]:
					tvshow = s[1][0]
			dp("Show is %s, season is %s, episode name: %s" % (tvshow, season, result))
			self.addEpisode(imdbId, season, result)
			return result
		else:
			dp('Episode Name not found')
			return ""
	
class epEntryBox(wx.Dialog):
	def __init__(self,parent,edit=None):
		self.parent = parent
		self.edit = edit
		wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		rootsizer = wx.BoxSizer(wx.VERTICAL)
		rootpanel = wx.Panel(self, -1)
		mainsizer = wx.BoxSizer(wx.VERTICAL)
		ctrlbuts = wx.BoxSizer(wx.HORIZONTAL)
		controlspace = wx.Panel(rootpanel, -1)
		okbut = wx.Button(rootpanel, -1, "OK")
		self.Bind(wx.EVT_BUTTON, self.OK, okbut)
		canbut = wx.Button(rootpanel, -1, "Cancel")
		self.Bind(wx.EVT_BUTTON, self.Cancel, canbut)
		ctrlbuts.Add(controlspace, 1, wx.ALL|wx.EXPAND, 5)
		ctrlbuts.Add(canbut, 0, wx.ALL, 5)
		ctrlbuts.Add(okbut, 0, wx.ALL, 5)
		grid = wx.GridSizer(3, 2)
		self.controls = [(wx.StaticText(rootpanel, -1, n+": "), wx.TextCtrl(rootpanel, -1, "")) for n in ("Episode", "IMDB Id", "Match Expression")]
		[(grid.Add(n, 0, wx.ALIGN_RIGHT|wx.ALL|wx.EXPAND, 5), grid.Add(m, 1, wx.ALL|wx.EXPAND, 5)) for (n, m) in self.controls]
		if edit is not None:
			tbs = zip(*self.controls)[1]
			tbs[0].SetValue(self.parent.shows[edit].name)
			tbs[1].SetValue(self.parent.shows[edit].imdb)
			tbs[2].SetValue(self.parent.shows[edit].match)
		mainsizer.Add(grid, 0, wx.ALL&~wx.BOTTOM|wx.EXPAND, 5)
		mainsizer.Add(ctrlbuts, 0, wx.ALL&~wx.TOP|wx.EXPAND, 5)
		rootpanel.SetSizer(mainsizer)
		rootsizer.Add(rootpanel, 0, wx.ALL|wx.EXPAND, 0)
		self.SetSizer(rootsizer)
		
	def Cancel(self, event):
	    self.EndModal(0)
	
	def OK(self, event):
		tbs = zip(*self.controls)[1]
		n = [n for (n, m) in self.controls if m.IsEmpty()]
		if n:
			[ewx.MessageBox("%s field must not be empty"%a, "Error", wx.ICON_ERROR) for a in n]
		else:
			if self.edit is not None:
				self.parent.shows[self.edit].name = tbs[0].GetValue()
				ischecked = self.parent.ep_list.IsChecked(self.edit)
				self.parent.ep_list.SetString(self.edit, tbs[0].GetValue())
				self.parent.ep_list.Check(self.edit, ischecked)
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
		self.rootpanel = wx.Panel(self, -1)
		mainsizer = wx.BoxSizer(wx.VERTICAL)
		# TABS
		self.tabs = wx.Notebook(self.rootpanel, -1)
		self.tab_eps = wx.Panel(self.tabs, -1)
		self.tab_network = wx.Panel(self.tabs, -1)
		# CONTROL BUTTONS
		controlbuts = wx.BoxSizer(wx.HORIZONTAL)
		controlspace = wx.Panel(self.rootpanel, -1)
		self.okbut = wx.Button(self.rootpanel, -1, "OK")
		self.canbut = wx.Button(self.rootpanel, -1, "Cancel")
		self.Bind(wx.EVT_BUTTON, self.handleCancel, self.canbut)
		self.Bind(wx.EVT_BUTTON, self.handleOK, self.okbut)
		# EPISODE PANE
		ep_sizer = wx.BoxSizer(wx.HORIZONTAL)
		ep_buts = wx.BoxSizer(wx.VERTICAL)
		self.ep_list = wx.CheckListBox(self.tab_eps, -1) #, style=wxLB_MULTIPLE)
		self.Bind(wx.EVT_CHECKLISTBOX, self.handleEpCheck, self.ep_list)
		self.ep_list.Set([s.name for s in self.shows])
		[self.ep_list.Check(i, n.enabled) for i, n in enumerate(self.shows)]
		self.ep_add = wx.Button(self.tab_eps, -1, "Add")
		self.ep_edt = wx.Button(self.tab_eps, -1, "Edit")
		self.ep_del = wx.Button(self.tab_eps, -1, "Remove")
		self.Bind(wx.EVT_BUTTON, self.handleAdd, self.ep_add)
		self.Bind(wx.EVT_BUTTON, self.handleEdit, self.ep_edt)
		self.Bind(wx.EVT_BUTTON, self.handleRemove, self.ep_del)
		# NETWORK PANE
		nt_sizer = wx.BoxSizer(wx.VERTICAL)
		nt_grsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.nt_usep = wx.CheckBox(self.tab_network, -1, "Use a proxy server")
		self.nt_usep.SetValue(parent.e.use_proxy)
		self.nt_plab = wx.StaticText(self.tab_network, -1, "Proxy Address:")
		self.nt_paddr = wx.TextCtrl(self.tab_network, -1, parent.e.proxy)
		
		# BUILDING IT UP
		#network pane
		nt_grsizer.Add(self.nt_plab, 0, wx.ALL|wx.EXPAND, 5)
		nt_grsizer.Add(self.nt_paddr, 1, wx.ALL|wx.EXPAND, 5)
		nt_sizer.Add(self.nt_usep, 0, wx.ALL|wx.EXPAND, 5)
		nt_sizer.Add(nt_grsizer, 0, wx.ALL|wx.EXPAND, 0)
		self.tab_network.SetSizer(nt_sizer)
		#episode pane
		ep_buts.Add(self.ep_add, 0, wx.ALL|wx.EXPAND, 5)
		ep_buts.Add(self.ep_edt, 0, wx.ALL|wx.EXPAND, 5)
		ep_buts.Add(self.ep_del, 0, wx.ALL|wx.EXPAND, 5)

		ep_sizer.Add(self.ep_list, 1, wx.ALL&~wx.RIGHT|wx.EXPAND, 5)
		ep_sizer.Add(ep_buts, 0, wx.ALL|wx.EXPAND, 0)
		self.tab_eps.SetSizer(ep_sizer)
		#tabs
		self.tabs.AddPage(self.tab_eps, "Episodes")
		self.tabs.AddPage(self.tab_network, "Network")
		mainsizer.Add(self.tabs, 1, wx.ALL&~wx.BOTTOM|wx.EXPAND, 5)
		#control buttons
		controlbuts.Add(controlspace, 1, wx.ALL|wx.EXPAND, 5)
		controlbuts.Add(self.canbut, 0, wx.ALL, 5)
		controlbuts.Add(self.okbut, 0, wx.ALL, 5)
		mainsizer.Add(controlbuts, 0, wx.ALL|wx.EXPAND, 0)
		#frame
		self.rootpanel.SetSizer(mainsizer)
		rootbox.Add(self.rootpanel, 1, wx.ALL|wx.EXPAND, 0)
		self.SetSizer(rootbox)
		rootbox.Fit(self)
		self.Layout()
	
	def handleEpCheck(self, event):
		item = event.GetSelection()
		self.shows[item].enabled = self.ep_list.IsChecked(item)
	
	def handleCancel(self, event):
		dp('Options: Cancel Button Pressed')
		del self.shows
		self.EndModal(0)
	
	def handleOK(self, event):
		dp('Options: Ok Button Pressed')
		self.parent.e.proxy = self.nt_paddr.GetValue()
		self.parent.e.use_proxy = self.nt_usep.GetValue()
		self.parent.e.shows = copy.deepcopy(self.shows)
		self.parent.e.saveChanges()
		self.EndModal(0)
	
	def handleAdd(self, event): epEntryBox(self).ShowModal()
	
	def handleEdit(self,event):
		item = self.ep_list.GetSelection()
		if item == wx.NOT_FOUND:
			wx.MessageBox("First select an item to edit", "Error", wx.ICON_ERROR)
		else:
			epEntryBox(self, item).ShowModal()
	
	def handleRemove(self, event):
		item = self.ep_list.GetSelection()
		self.shows.pop(item)
		self.ep_list.Delete(item)
	
	def AddItem(self, item):
		self.shows.append(Show(*item))
		self.ep_list.Append(item[0])
		self.ep_list.Check(self.ep_list.GetCount())

class mainFrame(wx.Frame):

	def __init__(self):
		# Create the back end
		self.e = Eptidy()
		self.doFiles = None
		self.fileMap = None
		wx.Frame.__init__(self, None, -1, "")
		#MENUBAR
		
		m_file = wx.Menu()
		m_file.Append(0, "&Options", "Configure EpTidy")
		wx.EVT_MENU(self, 0, self.handleOpts)
		m_file.AppendSeparator()
		m_file.Append(wx.ID_EXIT, "E&xit")
		wx.EVT_MENU(self, wx.ID_EXIT, self.Quit)
		
		m_help = wx.Menu()
		m_help.Append(1, "&How to Use", "How to use Eptidy")
		wx.EVT_MENU(self, 1, self.handleHelp)
		m_help.Append(2, "&Naming Patterns", "Naming patterns explained")
		wx.EVT_MENU(self, 2, self.handleNp)
		m_help.Append(3, "&About", "About Eptidy")
		wx.EVT_MENU(self, 3, self.handleAbout)
		
		m = wx.MenuBar()
		m.Append(m_file, "File")
		m.Append(m_help, "Help")
		self.SetMenuBar(m)
		#END MENUBAR
		
		self.panmain = wx.Panel(self, -1)
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
		self.Bind(wx.EVT_BUTTON, self.handleNp, self.pattern_help)
		self.Bind(wx.EVT_BUTTON, self.handleScan, self.button_2)
		self.Bind(wx.EVT_BUTTON, self.handleProcess, self.button_3)
		self.Bind(wx.EVT_BUTTON, self.handleBrowse, self.button_1)
		self.Bind(wx.EVT_BUTTON, self.handleRename, self.button_4)
		self.status.SetStatusText("Ready")
	
	def handleHelp(self,event):
		wx.MessageBox(__help__,"Eptidy Help",wx.ICON_INFORMATION)
	
	def handleNp(self,event):
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
	
	def handleAbout(self,event):
		info = wx.AboutDialogInfo()
		info.SetName("Eptidy")
		info.SetDevelopers(["Og: ogtifs+eptidy@gmail.com","Brian: hardbyte+eptidy@gmail.com","With thanks to Hamish, Kieran and Alex"])
		info.SetDescription("A program to flexibly organise your TV episodes")
		info.SetVersion(__version__)
		info.SetCopyright("Copyright (C) 2008 BOG Enterprises")
		info.SetLicense("GNU General Public License v3.0")
		info.SetWebSite("http://code.google.com/p/eptidy/")
		wx.AboutBox(info)

	
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
					# don't scan hidden dirs, TODO is there a way we can ask windows if a dir is hidden? - It'd be a stat type command, no?
					[d.remove(a) for a in d if a.startswith('.')]
					files += [osp.join(r, a) for a in f if os.path.splitext(a)[1].lower() in extensions]
			else:
				files = [a for a in os.listdir(p) if os.path.splitext(a)[1].lower() in extensions]
			d = self.e.identifyFiles(files)
			
			self.doFiles = [z for z in zip(d[0], *d[1]) if not None in z]
			
			if self.doFiles:
				entries = zip(*self.doFiles)[0]
				self.eplist.Set(entries)
				[self.eplist.Check(i) for i in range(len(entries))]
			else: self.eplist.Set([])
			self.status.SetStatusText("Ready")
			self.button_3.SetDefault()
		else:
			wx.MessageBox("Invalid path", "Error", wx.ICON_ERROR)
		
	def handleProcess(self, event):
		self.status.SetStatusText("Processing...")
		namePattern = self.namepatts.GetValue()
		self.doFiles = [a for i, a in enumerate(self.doFiles) if self.eplist.IsChecked(i)]
		if self.doFiles is None:
			wx.MessageBox("No files to process","Error", wx.ICON_ERROR)
			self.status.SetStatusText("Ready")
			return
		dp('Parsing files...')
		dp(self.doFiles)
		# This can fail if internet is not working
		preFiles = self.e.parseFiles(self.doFiles)
		
		if preFiles is None:
			dp("Parsing error occured.")
			return
		dp('Processing "%s" files.' % preFiles)
		inFiles = zip(*self.doFiles)[0]
		outFiles = []
		for epfile in enumerate(preFiles):
			n = namePattern
			if int(epfile[1][2]) < 10:
				n = n.replace('%0s','0%s')
			else:
				n = n.replace('%0s','%s')
			if int(epfile[1][3]) < 10:
				n = n.replace('%0e','0%e')
			else:
				n = n.replace('%0e','%e')
			# Replace codes with values
			for x, y in zip(('%t', '%n', '%s', '%e'), epfile[1]): 
				n = n.replace(x, y) 
			inFilePath = osp.split(inFiles[epfile[0]])[0]
			inFileExt = osp.splitext(inFiles[epfile[0]])[1]
			outFiles.append(osp.join(inFilePath, n+inFileExt))
		self.fileMap = [(a,b) for (a,b) in zip(inFiles, outFiles) if a != b]
		self.eplist.Set(["%s => %s" % x for x in self.fileMap])
		[self.eplist.Check(i) for i in range(len(self.fileMap))]
		self.e.savePattern(namePattern)
		dp("Done processing files")
		self.status.SetStatusText("Ready")
		self.button_4.SetDefault()
	
	def handleRename(self, event):
		self.status.SetStatusText("Renaming...")
		if not self.fileMap:
			wx.MessageBox("No files to rename","Error", wx.ICON_ERROR)
		else:
			for old,new in self.fileMap:
				os.renames(old, new)
		self.fileMap = None
		self.status.SetStatusText("Ready")
	
	def Quit(self, event): self.Close()


class gui(wx.App):
	def OnInit(self):
		"""Override OnInit to create our Frame"""
		wx.InitAllImageHandlers()
		mf = mainFrame()
		try:
			icon = wx.Icon(self.getAppIcon(), type=wx.BITMAP_TYPE_ICO)
			mf.SetIcon(icon)
		except:
			dp('icon not found')
		self.SetTopWindow(mf)
		mf.Show()
		return 1

	def getAppIcon(self):
		"""Get the path to the icon resource"""
		if hasattr(sys, 'frozen'):
			# Running from exe -> load icon from itself...
			return sys.argv[0]
		else:
			# Hope that the .ico file is in same dir...
			return 'tvi.ico'

if __name__ == "__main__":
	g = gui(0)
	g.MainLoop()

