#!/usr/bin/python

import urllib
import re
import os.path as osp
import os
from os import sys

import wx

debug = True
def dp(str):
	"""Debug Print"""
	if debug:
		print str
	

shows = {
	'Dexter':'0773262',
	'Bones':'0460627',
	'House':'0412142',
	'Scrubs':'0285403',
	'Prison Break':'0455275',
	'Chuck':'0934814',
	'How I Met Your Mother':'0460649',
	'Terminator':'0851851', # Don't know if the rest should be here 'The Sarah Connor Chronicles'
	'Californication':'0904208',
	'Top Gear':'0163503',
	'Burn Notice':'0810788',
	'Boston Legal':'0402711',
	'Gossip Girl':'0397442', # gf...
	'Pushing Daisies':'0925266',
	'Heroes':'0813715',
	'The Big Bang Theory':'0898266'
	#evryone add their fav!
#family guy, futurerama, mythbusters
}

class eptidy:
	"""
	DOC STRINGS!!! man you're anal I know :-P
	"""
	imdbBaseAddress = "http://www.imdb.com/title/tt"
	imdbData = {} # filled by getEpName
	
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
		for key,val in shows.iteritems():
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
		if None in episodes: return None
		
		imdbId = episodes[0]
		season = episodes[1]
		epnum = episodes[2]
		if not imdbId in self.imdbData:
			# retrieve imdb url
			try:
				u = urllib.urlopen(self.imdbBaseAddress + imdbId + '/episodes')
			except Exception, e:
				print "Internet not available from python\n%s" % e
				raise SystemExit
			# get big string of html page
			self.imdbData[imdbId] = ''
			for line in u.readlines():
				self.imdbData[imdbId] += line;
		# parse html page for relevant data
		r = "Season " + season + ", Episode " + epnum + ": <.*?>([^<]+)"
		m = re.search(re.compile(r),self.imdbData[imdbId])
		if m: return m.group(1)
		else: return ""
	

class mainFrame(wx.Frame):
	def __init__(self, *args, **kwds):
		kwds["style"] = wx.DEFAULT_FRAME_STYLE
		wx.Frame.__init__(self, *args, **kwds)
		self.panel_1 = wx.Panel(self, -1)
		self.label_1 = wx.StaticText(self.panel_1, -1, "Path:")
		self.text_ctrl_1 = wx.TextCtrl(self.panel_1, -1, "")
		self.text_ctrl_1.WriteText(os.path.expanduser('~'))
		self.button_1 = wx.Button(self.panel_1, -1, "Browse")
		self.checkbox_1 = wx.CheckBox(self.panel_1, -1, "Recursive")
		self.checkbox_1.SetValue(1)
		self.label_2 = wx.StaticText(self.panel_1, -1, "Naming Pattern:")
		self.text_ctrl_2 = wx.TextCtrl(self.panel_1, -1, "%t %sx%e - %n")
		self.button_2 = wx.Button(self.panel_1, -1, "Scan")
		self.button_3 = wx.Button(self.panel_1, -1, "Process")
		self.button_4 = wx.Button(self.panel_1, -1, "Rename Files")
		self.label_3 = wx.StaticText(self.panel_1, -1, "Search for:")
		self.text_ctrl_3 = wx.TextCtrl(self.panel_1, -1, "", style=wx.TE_MULTILINE)
		self.text_ctrl_3.SetEditable(False)
		self.SetTitle("Episode Renamer")
		self.SetSize((650, 400))
		sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_2 = wx.BoxSizer(wx.VERTICAL)
		sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
		#EPISODE GRID SQUARE
		w = (len(shows)+1)/3
		grid_sizer_1 = wx.GridSizer(w, 3, 2, 2)
		self.cbs = [wx.CheckBox(self.panel_1,-1,k) for k,v in shows.iteritems()]
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
		sizer_2.Add(sizer_4, 0, wx.EXPAND, 0)
		sizer_6.Add(self.label_3, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
		sizer_6.Add(grid_sizer_1, 1, wx.EXPAND, 0)
		sizer_2.Add(sizer_6, 0, wx.EXPAND, 0)
		sizer_5.Add(self.button_2, 2, wx.ALL, 2)
		sizer_5.Add(self.button_3, 2, wx.ALL, 2)
		sizer_5.Add(self.button_4, 2, wx.ALL, 2)
		sizer_2.Add(sizer_5, 0, wx.EXPAND, 0)
		sizer_2.Add(self.text_ctrl_3, 1, wx.ALL|wx.EXPAND, 2)
		self.panel_1.SetSizer(sizer_2)
		sizer_1.Add(self.panel_1, 1, wx.ALL|wx.EXPAND, 5)
		self.SetSizer(sizer_1)
		self.Layout()
		self.Bind(wx.EVT_BUTTON, self.handleScan, self.button_2)
		self.Bind(wx.EVT_BUTTON, self.handleProcess, self.button_3)
		self.Bind(wx.EVT_BUTTON, self.handleBrowse, self.button_1)
		self.Bind(wx.EVT_BUTTON, self.handleRename, self.button_4)

		#important shit happens here
		self.e = eptidy()
	
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

		
	def handleScan(self,event):
		"""
		This responds to the event when a search is initiated.
		It must get path, and work out what are movie/tv files.
		"""
		p = self.text_ctrl_1.GetValue();
		if osp.isdir(p):
			extensions = ['.mp4','.avi','.mpg','.divx','.mkv','.wmv']
			files = []
			for (r,d,f) in os.walk(p):
				# don't scan hidden dirs,(note to self) is there a way we can get it to ask windows if a dir is hidden? - It'd be a stat type command, no?
				[d.remove(a) for a in d if a.startswith('.')]
				files += [osp.join(r,a) for a in f if os.path.splitext(a)[1].lower() in extensions]
			d = self.e.identifyFiles(files)
			self.doFiles = [z for z in zip(d[0],*d[1]) if not None in z]
			self.text_ctrl_3.Remove(0,self.text_ctrl_3.GetLastPosition())
			self.text_ctrl_3.SetInsertionPoint(0)
			self.text_ctrl_3.WriteText('\n'.join(zip(*self.doFiles)[0]))

		else:
			print "Invalid path"
		
	def handleProcess(self,event):
		namePattern = self.text_ctrl_2.GetValue()
		preFiles = self.e.parseFiles(self.doFiles)
		inFiles = zip(*self.doFiles)[0]
		outFiles = []
		for file in enumerate(preFiles):
			n = namePattern
			# Zero padding for season and episode numbers
			n = n.replace('%0s','0%s') if int(file[1][2]) < 10 else n.replace('%0s','%s')
			n = n.replace('%0e','0%e') if int(file[1][3]) < 10 else n.replace('%0e','%e')
			# Replace codes with values
			for x,y in zip(('%t','%n','%s','%e'),file[1]): n = n.replace(x,y) 
			inFilePath = osp.split(inFiles[file[0]])[0]
			inFileExt = osp.splitext(inFiles[file[0]])[1]
			outFiles.append(osp.join(inFilePath,n+inFileExt))
		self.fileMap = zip(inFiles,outFiles)
		
		self.text_ctrl_3.Remove(0,self.text_ctrl_3.GetLastPosition())
		self.text_ctrl_3.SetInsertionPoint(0)
		self.text_ctrl_3.WriteText("\n".join([x[0]+" => "+x[1] for x in self.fileMap]))
	
	def victory(self):
		dlg = wx.Dialog(self,"All done!")
		if dlg.ShowModal() == wx.ID_OK:
			pass
		dlg.Destroy()

	def handleRename(self,event):
		for old,new in self.fileMap:
			if old != new:
				os.renames(old,new)
		victory()




class gui(wx.App):
	def OnInit(self):
		"""Override OnInit to create our Frame"""
		wx.InitAllImageHandlers()
		mf = mainFrame(None, -1, "")
		self.SetTopWindow(mf)
		mf.Show()
		return 1


if __name__ == "__main__":
	g = gui(0)
	g.MainLoop()

