# -*- coding: utf-8 -*-

import os
import re
import sys
import socket
import time
import datetime
import string
import random
import platform
from random import randrange
import signal
import argparse
from time import sleep
import Queue
import threading

import py3270
from py3270 import Emulator,CommandError,FieldTruncateError,TerminatedError,WaitError,KeyboardStateError,FieldTruncateError,x3270App,s3270App


####################################################################################
#			              *******  CICSshot  ********                             
####################################################################################
#
# CICSshot is a tool to screenshot CICS transactions using multithreading.
# It supports authentication if you have credentials
# example: python cicsshot.py 192.168.1.201 23 -a CICS file.txt 
#                                                                              
# Refer to https://github.com/ayoul3                                   
#
# Created by: Ayoul3 (@ayoul3__              	
# Copyright GPL 2016                                             	  
#####################################################################################



SLEEP = 0.5
queue = Queue.Queue()
MAX_THREADS= 5

# Buggy transactions that hang or crash CICS
exceptions = ['AORQ', 'CEJR','CJMJ','CPCT','CKTI','CPSS','CPIR','CRSY','CSFU','CRTP','CSZI','CXCU','CXRE','CMPX','CKAM','CEX2']

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    CYAN="\033[36m"
    PURPLE="\033[35m"
    WHITE=""
    DARKGREY = '\033[1;30m'
    DARKBLUE = '\033[0;34m'

    def disable(self):
        self.HEADER = ''
        self.BLUE = ''
        self.GREEN = ''
        self.YELLOW = ''
        self.RED = ''
        self.ENDC = ''

# Override some behaviour of py3270 library
class EmulatorIntermediate(Emulator):
	def __init__(self, visible=True, delay=0):
		Emulator.__init__(self, visible)
		self.delay = delay

	def send_enter(self): # Allow a delay to be configured
		self.exec_command('Enter')
		if self.delay > 0:
			sleep(self.delay)
    
	def send_clear(self): # Allow a delay to be configured
		self.exec_command('Clear')
		if self.delay > 0:
			sleep(self.delay)
            
	def send_eraseEOF(self): # Allow a delay to be configured
		self.exec_command('EraseEOF')
		if self.delay > 0:
			sleep(self.delay)
      
	def send_pf11(self):
		self.exec_command('PF(11)')
            
	def screen_get(self):
		response = self.exec_command('Ascii()')
		if ''.join(response.data).strip() == "":
		    sleep(0.3)
		    return self.screen_get()
		return response.data

	# Send text without triggering field protection
	def safe_send(self, text):
		for i in xrange(0, len(text)):
			self.send_string(text[i])
			if self.status.field_protection == 'P':
				return False # We triggered field protection, stop
		return True # Safe

	# Fill fields in carefully, checking for triggering field protections
	def safe_fieldfill(self, ypos, xpos, tosend, length):
		if length - len(tosend) < 0:
			raise FieldTruncateError('length limit %d, but got "%s"' % (length, tosend))
		if xpos is not None and ypos is not None:
			self.move_to(ypos, xpos)
		try:
			self.delete_field()
			if safe_send(self, tosend):
				return True # Hah, we win, take that mainframe
			else:
				return False # we entered what we could, bailing
		except CommandError, e:
			# We hit an error, get mad
			return False
			# if str(e) == 'Keyboard locked':

	# Search the screen for text when we don't know exactly where it is, checking for read errors
	def find_response(self, response):
		for rows in xrange(1,int(self.status.row_number)+1):
			for cols in xrange(1, int(self.status.col_number)+1-len(response)):
				try:
					if self.string_found(rows, cols, response):
						return True
				except CommandError, e:
					# We hit a read error, usually because the screen hasn't returned
					# increasing the delay works
					sleep(self.delay)
					self.delay += 1
					whine('Read error encountered, assuming host is slow, increasing delay by 1s to: ' + str(self.delay),kind='warn')
					return False
		return False
	
	# Get the current x3270 cursor position
	def get_pos(self):
		results = self.exec_command('Query(Cursor)')
		row = int(results.data[0].split(' ')[0])
		col = int(results.data[0].split(' ')[1])
		return (row,col)

	def get_hostinfo(self):
		return self.exec_command('Query(Host)').data[0].split(' ')

def logo():

  print bcolors.BLUE + '''
              
            ▄████▄      ██▓    ▄████▄       ██████      ██████  ██░ ██  ▒█████  ▄▄▄█████▓
           ▒██▀ ▀█     ▓██▒   ▒██▀ ▀█     ▒██    ▒    ▒██    ▒ ▓██░ ██▒▒██▒  ██▒▓  ██▒ ▓▒
           ▒▓█    ▄    ▒██▒   ▒▓█    ▄    ░ ▓██▄      ░ ▓██▄   ▒██▀▀██░▒██░  ██▒▒ ▓██░ ▒░   '''+bcolors.DARKBLUE+''' 
           ▒▓▓▄ ▄██▒   ░██░   ▒▓▓▄ ▄██▒     ▒   ██▒     ▒   ██▒░▓█ ░██ ▒██   ██░░ ▓██▓ ░ 
           ▒ ▓███▀ ░   ░██░   ▒ ▓███▀ ░   ▒██████▒▒   ▒██████▒▒░▓█▒░██▓░ ████▓▒░  ▒██▒ ░ 
           ░ ░▒ ▒  ░   ░▓     ░ ░▒ ▒  ░   ▒ ▒▓▒ ▒ ░   ▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒░ ▒░▒░▒░   ▒ ░░   
             ░  ▒       ▒ ░     ░  ▒      ░ ░▒  ░ ░   ░ ░▒  ░ ░ ▒ ░▒░ ░  ░ ▒ ▒░     ░    
           ░            ▒ ░   ░           ░  ░  ░     ░  ░  ░   ░  ░░ ░░ ░ ░ ▒    ░      
           ░ ░          ░     ░ ░               ░           ░   ░  ░  ░    ░ ░           
           ░                  ░                                                          
                  
                            Screenshotting CICS transactions !\t\tAuthor: @Ayoul3__\n'''+ bcolors.ENDC
                            
class Thread3270(threading.Thread):
    """Threaded client connection"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):        
        while not queue.empty():
            tran = queue.get()
            #~ print tran + ": " + str(threading.current_thread())
            try:
                em = WrappedEmulator(False)                
                if connect_zOS(em, results.IP+":"+results.PORT):
                    main(em, tran)
                    em.terminate()
                
            except Exception, e:
                whine(tran+': '+str(e),'err')
        #~ print "ending" + str(threading.current_thread())
            
def signal_handler(signal, frame):
        print 'Done !'
        sys.exit(0)

        
def show_screen(em):
    data = em.screen_get()
    for d in data:
        print d

def whine(text, kind='clear', level=0):
  """
    Handles screen messages display
  """
  typdisp = ''
  lvldisp = ''
  color =''
  if kind == 'warn': typdisp = '[!] ';color=bcolors.YELLOW
  elif kind == 'info': typdisp = '[+] ';color=bcolors.WHITE
  elif kind == 'err': typdisp = '[#] ';color=bcolors.RED
  elif kind == 'good': typdisp = '[*] ';color=bcolors.GREEN
  if level == 1: lvldisp = "\t"
  elif level == 2: lvldisp = "\t\t"
  elif level == 3: lvldisp = "\t\t\t"
  print color+lvldisp+typdisp+text+ (bcolors.ENDC if color!="" else "")

def connect_zOS(em, target):
    """
    Connects to z/OS server. If Port 992 is used, instructs 3270 to use SSL
    """
    #~ whine('Connecting to target '+target,kind='info')
    if "992" in target or "10024" in target:
        em.connect('L:'+target)
    else:
        em.connect(target)
    em.send_enter()
    if not em.is_connected():
        raise Exception('Could not connect to ' + target + '. Aborting.')
        return False
    return True
    
def do_authenticate(em, userid, password, pos_pass):
   """
       It starts writting the userid, then moves to pos_pass to write the password
       Works for VTAM and CICS authentication
   """
   
   posx, posy = em.get_pos()
      
   em.safe_send(results.userid)   
         
   em.move_to(pos_pass,posy+1)
   em.safe_send(results.password)
   em.send_enter()
  
   data = em.screen_get()
   
   if any("Your userid is invalid" in s for s in data):
      whine('Incorrect userid information','err')
      sys.exit()
   elif any("Your password is invalid" in s for s in data):
      whine('Incorrect password information','err')
      sys.exit()
   elif "DFHCE3549" in data[23]:
      pass
    
def check_valid_applid(em, applid, do_authent, method = 1):
    """
       Tries to access a CICS app in VTAM screen. If VTAM needs
       authentication, it calls do_authenticate()
       If CICS appid is valid, it tries to access the CICS terminal
    """
    
    em.send_string(applid) #CICS APPLID in VTAM
    em.send_enter()   
    sleep(SLEEP)
    
    if do_authent:
        pos_pass=1;
        data = em.screen_get()   
        for d in data:
            if "Password" in d or "Code" in d or "passe" in d:
                break;
            else:
               pos_pass +=1
            if pos_pass > 23:
                whine("Could not find a password field. Was looking for \"password\", \"code\" or \"pass\" strings",'err')
                sys.exit();
        do_authenticate(em, results.userid, results.password, pos_pass)
        #whine("Successful authentication",'good')
    
    if method ==1:
      em.send_clear()
      
    if method ==3:
      em.send_pf3()
      sleep(SLEEP)
      em.send_clear()
            
    if method ==2:
      em.send_clear()
      sleep(SLEEP)
      em.send_clear()    
      
    em.move_to(1,1)  
    #em.send_string('CESF') #CICS CESF is the Signoff command
    em.send_pf3()
    em.send_enter()
    sleep(SLEEP)
    
    if em.find_response( 'DFHAC2001'):
        #~ whine('Access to CICS Terminal is possible with APPID '+applid,'good')
        em.send_clear()
        return True
    elif method > 2:
        return False
    else:
        method += 1
        whine('Returning to CICS terminal via method '+str(method),kind='info')
        return check_valid_applid(em, applid, False, method)

def main(em, tran):
    do_authent = False
    
    if (results.userid != None and results.password !=None):
       
       do_authent = True
       data = em.screen_get()   
       pos_pass=1;
       logon_screen=False
       
       for d in data:
         if "Password" in d or "Code" in d:
           logon_screen=True
           break
         else:
           pos_pass +=1
       if logon_screen:
           do_authenticate(em, results.userid, results.password, pos_pass)
           whine("Successful authentication", 'info')
            
    # Checking if APPLID provided is valid
    if not check_valid_applid(em, results.applid, do_authent):
        raise Exception("Applid "+results.applid+" not valid, try again maybe it's a network lag")
        
    
        
    em.move_to(1,2)
    em.safe_send(tran)    
    em.send_enter()
    
    
    em.save_screen('./screens/'+tran+'_'+results.applid+'.html')
    whine('Got transaction '+tran,kind='good')

if __name__ == "__main__" :
    
    logo() 
        
        # Set the emulator intelligently based on your platform
    if platform.system() == 'Darwin':
      class WrappedEmulator(EmulatorIntermediate):
        x3270App.executable = 'x3270'
        s3270App.executable = 's3270'
    elif platform.system() == 'Linux':
      class WrappedEmulator(EmulatorIntermediate):
        x3270App.executable = 'x3270'
        s3270App.executable = 's3270'
    elif platform.system() == 'Windows':
      class WrappedEmulator(EmulatorIntermediate):
        x3270App.executable = 'wc3270.exe'
    else:
      whine('Your Platform:' + platform.system() + 'is not supported at this time.',kind='err')
      sys.exit(1)    
    
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='CicsScreen: a tool to screenshot transactions on CIS transaction servers on z/OS')
    parser.add_argument('IP',help='The z/OS Mainframe IP or Hostname')
    parser.add_argument('PORT',help='CICS/VTAM server Port')
    parser.add_argument('FILE',help='File containing a list of transactions')
    parser.add_argument('-a','--applid',help='CICS ApplID on VTAM, default is CICS',default="CICS",dest='applid')
    parser.add_argument('-U',help='Username for CICS in case authentication is needed',default=None,dest='userid')
    parser.add_argument('-P',help='Password in case authentication is needed',default=None,dest='password')
    results = parser.parse_args()
    
    whine('Launching '+str(MAX_THREADS)+' threads connecting to '+results.IP+':'+results.PORT+', APPLID='+results.applid,kind='info')
    
    if (results.userid != None and results.password !=None):
        whine("Using credentials "+results.userid+"/********",'info')
    
    whine('Launching '+str(MAX_THREADS)+' threads connecting to '+results.IP+':'+results.PORT+', APPLID='+results.applid,kind='info')
    whine('Saving results to folder ./screens',kind='info')
    if not os.path.isdir("./screens"):
         os.makedirs('./screens')
    #~ f = open(results.FILE, 'r')
    #~ trans = f.readlines()
    #~ trans = map(lambda s: s.strip(), trans)
    #~ number_trans = len(trans)
    
      
    with open(results.FILE, "r") as ins:
        for line in ins:
            tran = line.strip()
            if tran.upper() not in exceptions:
                queue.put(tran)
        
    for i in xrange(MAX_THREADS):
        t = Thread3270(queue)
        t.setDaemon(True)
        t.start()
    
    while threading.active_count() > 1:
        time.sleep(0.1)
