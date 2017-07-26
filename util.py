from __future__ import print_function # For * **
import sys
import os

def runsep(method, args):
	def queue_wrapper(q, params):
		r = method(*params)
		q.put(r)
	q = Queue()
	p = Process(target=queue_wrapper, args=(q, args))
	p.start()
	return_val = q.get()
	p.join()
	return return_val

## Functions
def exit(ec=0):
	sys.exit(ec)
def pf(*x, **y):
	print(*x, **y)
	sys.stdout.flush()
def pfp(*x, **y):
	y.setdefault('sep', '')
	print(*x, **y)
	sys.stdout.flush()
def pfl(*x, **y):
	y.setdefault('end', '')
	print(*x, **y)
	sys.stdout.flush()
def pfpl(*x, **y):
	y.setdefault('sep', '')
	y.setdefault('end', '')
	print(*x, **y)
	sys.stdout.flush()
def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)
def vprint(verbosity, *args, **kwargs):
	if (verbose >= verbosity):
		pf(*args, **kwargs)

def get_linux_terminal():
	env = os.environ
	def ioctl_GWINSZ(fd):
		try:
			import fcntl, termios, struct, os
			cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
		except:
			return
		return cr
	cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
	if not cr:
		try:
			fd = os.open(os.ctermid(), os.O_RDONLY)
			cr = ioctl_GWINSZ(fd)
			os.close(fd)
		except:
			pass
	if not cr:
		cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

		### Use get(key[, default]) instead of a try/catch
		#try:
		#	cr = (env['LINES'], env['COLUMNS'])
		#except:
		#	cr = (25, 80)
	return int(cr[1]), int(cr[0])

# vim:ts=4 ai
