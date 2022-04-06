"""
Python-IRC - an IRC client written in Python
(c) 2004 Mike Tremoulet
Version 0.5

This work is licensed under the Creative Commons Attribution-NonCommercial License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc/2.0/ or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
"""


import curses
import select
import socket
import sys
import textwrap
import time
import re

class CursesUI:
  """
  May have a problem with inbound messages while typing - blocks the display of new data while typing.
  (the select.select() call triggers on the first keypress but blocks until newline.  too lazy to write
  an internal buffer to pick up on characters as they are typed. :> )

  More to the point, the UI doesn't seem to be doing a 100% good job of splitting up the input.  Occasionally
  messages inbound will not get parsed - this seems to be when multiple items arrive at once.

  Also, server messages (large and all-at-once) are not parsing properly.

  Parts are inspired from http://twistedmatrix.com/documents/current/examples/cursesclient.py
  """
  def __init__(self, irceng):
    """
    Input param:
      socket - open socket to IRC server
      irceng - IRC engine object
    """
    self.lines = []
    self.engine = irceng
    self.sock = self.engine.connect()
    self.linewrap = textwrap.TextWrapper()
    self.stdscr = curses.wrapper(self.evtloop)

  def addline(self, line, screen):
    # First part sanitizes input for the screen - break input buffer into lines (\n), then into
    # screen lines based on width
    line = line.rstrip()
    actuallines = line.split("\n")
    for entry in actuallines:
      try:
        entry = self.engine.parseinput(entry)
      except PingInputError, err:
        self.sock.sendall("PONG :" + err.value + "\n")
	entry = "PING/PONG to " + err.value
      screenlines = self.linewrap.wrap(entry)
      for item in screenlines:
        self.lines.append(item)
    # Now we clear the screen and loop over the formatted lines to display them.
    screen.clear()
    i = 0;
    index = len(self.lines) - 1
    while i < self.nrows - 2 and index >= 0:
      screen.addstr(self.nrows-2-i, 0, self.lines[index])
      i = i + 1
      index = index - 1
    screen.move(self.nrows-1, 0)
    screen.refresh()

  def evtloop(self, screen):
    curses.echo()
    self.nrows, self.ncols = screen.getmaxyx()
    self.linewrap.width = self.ncols
    while True:
      (inlst, outlst, errlst) = select.select([self.sock, sys.stdin], [], [])
      if self.sock in inlst :
        # data coming in
        data = self.sock.recv(8192)
        if len(data) > 0:
	  # self.addline(self.engine.parseinput(data), screen)
	  # Moving the parseinput() call to addline()
	  self.addline(data, screen)
        else :
          # No data from socket - socket may be closed
  	  # Test this and exit gracefully if needed
  	  try :
  	    self.sock.sendall("PING\n")
   	  except socket.error :
	    print "Socket closed by host."
	    break
      elif sys.stdin in inlst :
        # keyboard data to be sent
        data = self.engine.parsecmd(screen.getstr())
        self.sock.sendall(data + "\n")
	self.addline(data, screen)

  def close(self):
    self.engine.shutdown()



class PythonIRC:
  def __init__(self, svr="irc.freenode.net", prt=6667, nck="PythIRC", rname="Python-IRC User"):
    self.server = svr
    self.port = prt
    self.nick = nck
    self.realname = rname
    self.channel = ""
    self.usercmd = re.compile('^/(\w+)( (.*))?$')
    self.usermsg = re.compile('^(#?\w+)( (.*))?$')
    self.svrmsg = re.compile('^:([a-zA-Z0-9\.]+) [0-9]+ ' + self.nick + '(.*)')
    self.chanmsg = re.compile('^:(.+)![~]?(.+)@(.+) (\w+) #?(\w+) :(.*)$')
    self.genmsg = re.compile('^:(.+)!~?(.+)@([a-zA-Z0-9\-\.]+) (\w+) :?(.*)$')
    self.pingmsg = re.compile('^PING :(.*)$', re.IGNORECASE)

  def connect(self):
    # Connect to the IRC server.
    # ... insert socket code here ...
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((self.server, self.port))
    # ... add error handling for the commands?
    nickcmd = "NICK " + self.nick + "\n"
    usercmd = "USER Python-IRC host server :" + self.realname + "\n" # Might want to not hardcode those
    self.sock.sendall(nickcmd) # Need to check for collision here
    self.sock.sendall(usercmd) # Watch for errors here
    return self.sock # The established connection

  def parseinput(self, input):
    if self.svrmsg.match(input) is not None:
      # Server message
      parse = self.svrmsg.match(input)
      result = parse.group(1) + ": " + parse.group(2)
    elif self.chanmsg.match(input) is not None:
      # Channel msg
      parse = self.chanmsg.match(input)
      if parse.group(4).upper() == "PRIVMSG":
        result = "[#" + parse.group(5) + " || " + parse.group(1) + "]: " + parse.group(6)
      else:
        # Unhandled
	result = input.rstrip()
    elif self.genmsg.match(input) is not None:
      # General messages
      parse = self.genmsg.match(input)
      if parse.group(4).upper() == "QUIT":
        result = "-- " + parse.group(1) + " has quit: " + parse.group(5)
      elif parse.group(4).upper() == "JOIN":
        result = "++ " + parse.group(1) + " has joined " + parse.group(5)
      elif parse.group(4).upper() == "NICK":
        result = "-+ " + parse.group(1) + " has morphed into " + parse.group(5)
      else:
        # Unhandled input
	result = input.rstrip()
    elif self.pingmsg.match(input):
      parse = self.pingmsg.match(input)
      raise PingInputError, parse.group(1)
    else:
      # Unhandled input
      result = input.rstrip()
    return result

  def parsecmd(self, input):
    """
    This function parses user supplied input and reformats into IRC commands
    """
    # If first char is a /, then this is a command.
    output = input
    if input[0] == "/" :
      parsedcmd = self.usercmd.match(input)
      output = parsedcmd.group(1).upper() # group(0) is the raw match, not the group
      # Insert a bunch of if..elif..else statements
      if (output == "MSG") :
        # private message to a user.  format: /msg user text
        # break off the first word of group(3) to get userid
        splitcmd = self.usermsg.match(parsedcmd.group(3))
        output = "PRIVMSG " + splitcmd.group(1) + " :" + splitcmd.group(3) # Note - no error checking for existence of groups
      elif (output == "JOIN") :
        # Only supports one channel, no keys, at this time
        if parsedcmd.group(3) is not None:
          output = output + " " + parsedcmd.group(3) # Note - group(2) contains that space
   	  # Store channel for later use
  	  self.channel = parsedcmd.group(3)
        else :
          # Raise a USER=ID10T error
  	  pass
      elif (output == "QUIT") :
        # map add'l params i.e. reason for quitting
        if parsedcmd.group(3) is not None:
          output = output + " :" + parsedcmd.group(3)
      elif (output == "PART") :
        # add'l param = channel to leave
        if parsedcmd.group(3) is not None:
          output = output + " " + parsedcmd.group(3)
      elif (output == "NICK") :
        output = "NICK " + parsedcmd.group(3)
    elif input[0] == "#" :
      splitcmd = self.usermsg.match(input)
      output = "PRIVMSG " + splitcmd.group(1) + " :" + splitcmd.group(3)
      self.channel = splitcmd.group(1) # Update the CHANNEL variable - allows for easier multiple messages
    else :
      # This is a msg for a channel.
      # look for null input!
      output = "PRIVMSG " + self.channel + " :" + output # Retrieves channel from above
    return output.rstrip()

  def shutdown(self):
    self.sock.close()



class PingInputError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)



def usage():
  print("Python-IRC (c) 2004 Mike Tremoulet.  Some rights reserved (http://creativecommons.org)")
  print("USAGE: " + sys.argv[0] + " server port nick realname")

if (__name__ == "__main__"):
  # Expect server port nick realname
  if len(sys.argv) != 5:
    usage()
  else:
    client = PythonIRC(svr=sys.argv[1], prt=int(sys.argv[2]), nck=sys.argv[3], rname=sys.argv[4])
    cursesui = CursesUI(client)
    # Event loop happens ... need more graceful way
    cursesui.close()
