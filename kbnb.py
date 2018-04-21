# kbnb.py
# Description:
#   Python non-blocking input for Unix/Linux with callback support for wait loops
#   (The main termios routine lines came from a stackexchange post by swdev)
#   Ctrl-c interrupt is not taken over, so ctrl-c should still break out.
# Date: 2017-07-01
# Version: 0.1b
# Author: jaggz.h who happens to be @ gmail.com
# Usage:
#   Setup:
#      kbnb.init() or kbnb.init(cb=some_function)
#      kbnb.reset_flags() when done
#      Example callback function:
#        def some_function():
#            plt.pause(0.05)
#        This I use to call matplotlib's pyplot's pause() to benefit from its
#        event handler (for window updates or mouse events).
#   Later, to wait for a key in your own code:
#      print("Hit any key")
#      ch = kbnb.waitch() or waitch(cb=different_callback)
#   To check (and get any pending) key:
#      ch = kbnb.getch()
#      Returns: None if no input is pending
#   To check (and get any pending) char sequence as a list:
#      str = kbnb.getstrnb()
#      Returns:
#        [] If no input is pending, or
#        A list of integer values
#   To check (and get any pending) char sequence as a string:
#      str = kbnb.getstrnb()
#      Returns: "" or "string of input characters"
#   Set a new callback post-init(): kbnb.setcb(new_cb_function)

# Full example using waitch() to wait for a kb char input:
#   import kbnb, time
#   plt = None
#   def plt_sleep():
#       # waitch()'s default loop will call our function instead of
#       # its built-in time.sleep(delay), so we are sleeping, ourselves,
#       # because we really don't need high time resolution in our loop.
#   	if plt: plt.pause(.1) # In case we didn't setup plt
#       else: time.sleep(.1)
#   kbnb.init(cb=plt_sleep)
#   # ...Do something here that needs our callback called even while
#   # we're waiting for input.
#   # ...In this example, we would have popped up a pyplot window which
#   # requires its event handler to be called for window updates and
#   # mouse/kb events.
#   print("Hit any key to continue")
#   kbnb.waitch()
#   kbnb.gobble() # Consume remaining pending input before leaving
#                 # (Useful if a key was hit, like up or down, which
#                 # Might send a multi-character sequence)

# Full example using getch() to do something while waiting for input:
#   import kbnb, time
#   kbnb.init()
#   while True:
#     ch=kbnb.getch()
#     if ch == 'q': break
#     print("I'm not thrown for a loop! (And 'q' to quit)")
#     time.sleep(1)
#   kbnb.gobble() # Consume remaining pending input before leaving
#                 # (Useful if a key was hit, like up or down, which
#                 # Might send a multi-character sequence)

from __future__ import print_function
import sys, atexit, termios, time, os

orig_flags=None
loop_callback=None
loop_delay=0.1 # Init sets this, but we'll put .1 for "safety"

def init(cb=None, delay=.05):
	global orig_flags
	global loop_callback
	if cb: loop_callback = cb
	loop_delay = delay

	orig_flags = termios.tcgetattr(sys.stdin)
	new_flags = termios.tcgetattr(sys.stdin)
	# Disable echo and disable blocking (disable canonical mode)
	new_flags[3] = new_flags[3] & ~(termios.ECHO | termios.ICANON)
	new_flags[6][termios.VMIN] = 0  # cc (dunno what swdev meant by cc)
	new_flags[6][termios.VTIME] = 0 # cc
	termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new_flags)

@atexit.register
def reset_flags():
	#print("kbnb cleanup")
	if orig_flags:
		#print("kbnb reset")
		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_flags)

def setcb(cb):
	loop_callback = cb
def setdelay(delay):
	loop_delay = delay
def getch():
	return os.read(sys.stdin.fileno(), 1)
def getlist():
	ch_set = []
	ch = os.read(sys.stdin.fileno(), 1)
	while ch != None and len(ch) > 0:
		ch_set.append( ord(ch[0]) )
		ch = os.read(sys.stdin.fileno(), 1)
	return ch_set;
def getstr():
	ch_str = ""
	ch = os.read(sys.stdin.fileno(), 1)
	while ch != None and len(ch) > 0:
		ch_str += ch
		ch = os.read(sys.stdin.fileno(), 1)
	return ch_str;
def gobble():
	while getch(): pass
def waitch(prompt="Hit a key to continue", cb='default'):
	if prompt:
		print(prompt, end="")
		sys.stdout.flush()
	while True:
		key = getch()
		if len(key): return key
		else:
			if cb == 'default':
				if loop_callback: loop_callback()
			else:
				time.sleep(loop_delay)

