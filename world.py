import random
from util import *
from ansi import *
import numpy as np
import ipdb as pdb
import atexit
import copy
import curses
from time import sleep

class Erasure:
	def __init__(self, co, timestep):
		self.co = co
		self.timestep = timestep

def sign0(v):
	return v and (1, -1)[v < 0]

class World:
	t_bot = 0
	t_empty = 1
	t_human = 2
	t_block = 3
	t_fixedblock = 4
	t_horizon = 5
	t_nearground = 6

	def __init__(self, size=(30,80,80), tsize=(None,None)):
		# Gets terminal width for missing tsize values (y,x)
		self.size = size
		#self.a = [[[0] * self.xs for i in range(self.ys)] for j in range(self.zs)]
		self.a = np.zeros(size)
		txs, tys = get_linux_terminal()

		self.tsize = [None,None]
		if tsize[0] == None: self.tsize[0] = tys
		if tsize[1] == None: self.tsize[1] = txs

		self.tyscale = .7        # Display world y in term height * tyscale
		self.objs = []
		self.status_lines = 15
		self.ui_initted = False
		self.trow_status = tys-self.status_lines
		self.timestep = 0
		self.erasures = []
		self.curses = None
		self.statuses = []
	def update_tsize(self):
		#txs, tys = get_linux_terminal()
		self.tsize = list(self.curses.getmaxyx())
		self.trow_status = self.tsize[0]-self.status_lines

		self.wworldheight, self.wworldwidth = self.winworld.getmaxyx()
		self.wstatusheight, self.wstatuswidth = self.winstatus.getmaxyx()

	# Convenience properties, xs => size[2]
	@property
	def xs(self): return self.size[2]
	@xs.setter
	def xs(self, v): self.size[2] = v

	@property
	def ys(self): return self.size[1]
	@ys.setter
	def ys(self, v): self.size[1] = v

	@property
	def zs(self): return self.size[0]
	@zs.setter
	def zs(self, v): self.size[0] = v

	def screensize(size=(None,None)): # Set or get (if both None)
		if not size[0] == None: self.tsize[0] = size[0]
		elif not size[1] == None: self.tsize[1] = size[1]
		else: return self.tsize
	def is_freespace(self, pos, size):
		#pf(pos, size)
		if pos[0]+size[0] >= self.zs \
		   or pos[1]+size[1] >= self.ys \
		   or pos[2]+size[2] >= self.xs:
			return False
		for tz in range(pos[0], pos[0]+size[0]+1):
			for ty in range(pos[1], pos[1]+size[1]+1):
				for tx in range(pos[2], pos[2]+size[2]+1):
					if self.a[tz][ty][tx]: # Something here
						return False
		return True                   # Found nothing in this area
	def find_freespace(self, size):        # Still using random in a loop
		#pf("size", size)
		# size: (z,y,x)
		# Raises MemoryError() if no room for size
		for tries in range(0, 1000): # Try 1000 times to find a free space
			x = random.randint(0, self.size[2])
			y = random.randint(0, self.ys)
			z = 0
			if self.is_freespace((z,y,x), size): return (z,y,x)
		raise MemoryError("No free space in world for object of size:", size)
	def add_object(self, o, pos=None):
		#pf("o.size", o.size)
		if pos: o.pos = np.array(pos, dtype=np.float64)
		else: o.pos = np.array(self.find_freespace(o.size), dtype=np.float64)
		self.objs.append(o)
		o.windex = len(self.objs)
		o.world = self
		#pf("Added object:", o.type(), o, "at pos", o.pos)
#		if o.vel[i] - o2.vel[i] < 0:
#			#o.pos[i] = o2.pos[i]+o2.size[i]
#			pass
#		elif o.vel[i]>0:
#			#gyx(co[1], co[0])
#			#pfpl(red, "*", rst)
#			pass
#			#o.pos[i] = o2.pos[i]-o2.size[i]
	def init_ui(self):
		self.ui_initted = True
		#pfpl(chide, rst)
		#cls()
		self.curses = curses.initscr()
		curses.start_color()
		curses.noecho()
		#curses.cbreak()
		curses.curs_set(0)
		self.curses.keypad(1)

		self.tsize = list(self.curses.getmaxyx())

		wworldheight = self.tsize[0]-self.status_lines
		wworldwidth = self.tsize[1]
		wstatusheight = self.status_lines
		wstatuswidth = self.tsize[1]
		wstatuslocy = self.tsize[0]-self.status_lines
		wstatuslocx = 0
		self.wworldheight = wworldheight
		self.wworldwidth = wworldwidth
		self.wstatusheight = wstatusheight
		self.wstatuswidth = wstatuswidth

		#eprint("winworld: {},{} 0,0".format(wworldheight,wworldwidth))
		#eprint("winstatus: {},{} {},{}".format(wstatusheight,wstatuswidth,
			#wstatuslocy,wstatuslocx))
		self.winworld = curses.newwin(wworldheight,wworldwidth, 0,0)
		self.winstatus = curses.newwin(wstatusheight,wstatuswidth, 
			wstatuslocy,wstatuslocx)

		self.winstatus.scrollok(True)
		self.winworld.refresh()
		self.winstatus.refresh()

		self.winworld.nodelay(1)
		self.winstatus.nodelay(1)

		curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
		curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
		curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
		curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
		curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
		curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
		curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
		self.c_red = curses.color_pair(1)
		self.c_gre = curses.color_pair(2)
		self.c_yel = curses.color_pair(3)
		self.c_blu = curses.color_pair(4)
		self.c_mag = curses.color_pair(5)
		self.c_cya = curses.color_pair(6)
		self.c_whi = curses.color_pair(7)
	@atexit.register
	def restore_ui():
		#pfl(cshow)
		#curses.keypad(0)
		curses.nocbreak()
		curses.echo()
		curses.curs_set(1)
		curses.endwin()
		pf("Reset 1")
		os.system("stty sane")
	def restore_ui(self):
		curses.nocbreak()
		curses.echo()
		curses.curs_set(1)
		curses.endwin()
		self.ui_initted = False
		pf("Reset 2")
		os.system("stty sane")
	def log(self, s):
		self.statuses.append(s)
		if len(self.statuses) >= self.status_lines:
			del self.statuses[0]
			#self.winstatus.move(0,0)
			#self.winstatus.deleteln()
		#self.winstatus.move(len(self.statuses), 0)
		#self.winstatus.clrtoeol()
		self.winstatus.addstr(s + "\n")
		self.winstatus.refresh()
	def putatyx(self, co, s, attr):
		#self.
		return
	def erase_erasures(self):
		newlist = []
		for i in range(len(self.erasures)):
			e = self.erasures[i]
			if e.timestep > self.timestep:
				self.winworld.addstr(e.co[0], e.co[1], " ")
			else:
				newlist.append(e)
		self.erasures = newlist
	def draw(self):
		osort = sorted(self.objs, key=lambda o: o.pos[1], reverse=True)
		self.erase_erasures()
		# Erase old positioned objects
		for o in osort:
			if o.oldpos is not None:
				coo = self.world_co_to_screen(o.oldpos)
				co = self.world_co_to_screen(o.pos)
				if coo != co:
					self.draw_object(o, erase=True, manpos=o.oldpos)
		#self.log("Timestep: {}".format(self.timestep))
		# Draw objects
		for o in osort:
			self.draw_object(o)
			# Draw collisions
			# This is pretty slow, comparing all objects to each other
			for o2 in self.objs:
				if o2 == o: continue
				if o.typ == o2.typ:
					if o.fixed: continue
				hitside = self.overlap_obj(o, o2)
				o.hitside = hitside
				if hitside is not None: # If overlap
					self.draw_collision(o, hitside)
					o.handle_overlap(o2, hitside)
					pass
		#if not self.timestep % 10:
		self.winworld.refresh()

	def step(self):
		self.timestep += 1
		oi = -1
		for o in self.objs:
			if o.fixed: continue
			oi += 1
			o.step()
			#self.log("Newpos: {}".format(o.pos))
			#self.log("Oldpos 2: {}".format(oldobj.pos))
			for i in range(3):
				if o.vel[i]<0 and o.pos[i]<0:
					o.pos[i] = 0
					o.vel[i] = 0
				if o.vel[i]>0 and o.pos[i]+o.size[i]-1 >= self.size[i]:
					o.pos[i] = self.size[i]-o.size[i]
					o.vel[i] = 0
			#eprint("poso new: {} -> {}\n".format( o.oldpos, o.pos))
	def world_co_to_screen(self, co, obj=None): # Project along y orthogonally
		ty,tx = self.winworld.getmaxyx()

		sx = int(tx * (co[2] / self.xs))
		sy = ty - 1 - \
			int(ty * (co[0] / self.zs)) - \
			int(ty * (co[1] / self.ys) * self.tyscale)
		#self.log("ty,tx {},{} co:{}, sy,sx {},{}".format(ty,tx,co, sy, sx))
		return sy, sx
		
	def draw_object(self, o, erase=False, manpos=None, color=None): # or Manual position
		if color is None: color = self.c_whi

		pos = o.pos if manpos is None else manpos

		if o.oldpos is None:
				o.oldpos = np.array(pos)
				#eprint("Initial update: {}".format(pos))

		co = self.world_co_to_screen(pos, obj=o)
		if (o.oldpos != pos).any():
				o.oldpos = np.array(pos)
				#eprint("Secondary update: {}".format(pos))

		height = len(o.pic)
		for y in range(0, len(o.pic)):
			#if o.typ == self.t_human: pdb.set_trace()
			#if o.typ != t_nearground and o.typ != t_horizon:
			#	self.log("[" + str(self.timestep) + "] Obj: " + str(o) + " at " + str(co[0]+1+y))

			# GET COORDINATES OF TOP LEFT
			# -height+1 to start at the top
			#self.log("Co {},{}".format(co[0], co[1]))
			ty = co[0]-height+y
			# Don't round up with +.5 cuz we're not at 0, but on the first char
			tx = co[1] - int(o.size[2]/2)
			'''
			if o.typ == self.t_nearground and tx > 80:
				os.system("stty sane")
				pf("o pos: {}".format(o.pos))
				pf("ty,x {},{}".format(ty, tx))
				pdb.set_trace()
			'''

			for x in range(0, len(o.pic[y])):
				# Don't print spaces (just advance right)
				if ty >= 0 and ty < self.wworldheight and \
						tx+x >= 0 and tx+x < self.wworldwidth:
					self.log("Adding @ {},{}".format(ty, tx+x))
					if erase:
						self.winworld.addstr(ty, tx+x, " ")
					else:
						if o.pic[y][x] == ' ': pass
						else:
							self.winworld.addstr(ty, tx+x, o.pic[y][x])
					if ty == co[0] and tx == co[1]:
						self.winworld.addstr(ty, tx, '@', self.c_cya)
			#gyx(co[0]-1, co[1])
			#pfpl(yel, o.windex, rst)

			#gyx(co[0]-2, co[1])
			#pfpl(yel, "@", rst)
		if o.typ == self.t_human:
			self.winworld.refresh()
	def draw_collision(self, o, hitside, erase=None):
		co = self.world_co_to_screen(o.pos)
		xsign = sign0(hitside[2])
		ysign = sign0(hitside[1])
		if hitside[1] and hitside[2]:   # Hit on z side (y on screen)
			ty = int(co[0] + ysign*o.size[1])
			tx = int(co[1] + xsign*o.size[2])
		elif hitside[1]:  # Just on y
			ty = int(co[0] + ysign*o.size[1])
			tx = co[1]
		elif hitside[2]:  # Just on x
			ty = int(co[0] + ysign*(o.size[1]/2 + .5))
			tx = int(co[1] + xsign*(o.size[2]/2 + .5))

		#ty = int(co[0] + hitside[0]*o.size[0]/2)
		#tx = int(co[1] + hitside[2]*o.size[2]/2)
		#ty = int(co[0]-1)
		#tx = int(co[1])
		#self.log("Hit: {} coy.x: {} {}".format(hitside, co[0], co[1]))
		#self.log("Hit: {} coy.x: {} {}".format(hitside, ty, ty))
		#pf("Hit:", hitside, "ty,x:", ty, tx)
		#pf("")
		#eprint("tyx:{},{} tsize:{} h:{}".format(ty,tx, self.tsize, self.wworldheight))
		if ty >= 0 and tx >= 0 and ty < self.wworldheight-1 and tx < self.wworldwidth:
			char = "*"
			self.winworld.addstr(ty, tx, char, self.c_red)
			self.add_timed_erase((ty,tx), 1)
	def pyxr(y, x, s):
		self.winworld.addstr(y, x, s)
	def add_timed_erase(self, co, ticks):
		self.erasures.append(Erasure(co, self.timestep + ticks))
	def wref(self):
		self.winworld.refresh()
	def overlap_obj(self, o, o2):
		# Returns None if false, else hitside = [z,y,x] <= {-1,0,1}+
		# Where -1 means the negative side, while 0 means we're in an overlap
		# (...and the collision side is therefore unknown, because of our
		# simplistic step analysis of collision)
		ocount = 0
		hitside = [0,0,0]
		#self.log("op:{} os:{} || o2p:{} o2s{}".format(o.pos, o.size, o2.pos, o2.size))
		for i in range(3):
			op = o.pos[i]         # Position of object in dimension i
			o2p = o2.pos[i]
			osiz = o.size[i]/2        # Size of obj in dimension i
			o2siz = o2.size[i]/2
			ov = o.vel[i]
			o2v = o2.vel[i]
			dv = ov-o2v
			if i == 0:
				op += osiz
				o2p += o2siz
			if op-osiz >= o2p-o2siz and op+osiz <= o2p+o2siz: # o is Enclosed in this axis
				ocount += 1
				hitside[i] = 0
			elif op+osiz >= o2p-o2siz and op-osiz < o2p+o2siz: # Overlap o right
				ocount += 1
				hitside[i] = (o2p+o2siz)-(op-osiz) if dv else 0
			elif op-osiz <= o2p+o2siz and op+osiz > o2p-o2siz: # Overlap o left
				ocount += 1
				hitside[i] = (o2p-o2siz)-(op+osiz) if dv else 0

		# Now take the minimum overlap area, because [hopefully] we just
		# entered that side.  Ideally we should examine the velocity vector
		# directions, and find the distance traveled into the object that way
		if ocount != 3: return None # Must overlap on all axii, or we aren't overlapped
		else:                       # Here we're overlapped
			if not all(hitside):      #   Fully enclosed
					for i in range(3):
							hitside[i] = min(abs(o.pos[i]-o2.pos[i]), abs(o2.pos[i]-o.pos[i]))
					return hitside
			                          #   Here just a normal overlap
			#self.log("hitside:: {}".format(hitside))
			minoverlap = min([abs(x) for x in hitside if x != 0])
			#self.log("hitside1 {}".format(hitside))
			hitside = [0 if abs(x)>minoverlap else x for x in hitside]
			#self.log("hitside2 {}".format(hitside))

			self.draw_object(o, color=self.c_red)
			self.draw_object(o2, color=self.c_mag)
			self.wref()
			sleep(.5)

			return hitside

class Size: # Unused
	def __init__(x, y, z):
		raise ValueError("Unimplemented/Incomplete Size class")
		self.x = x
		self.y = y
		self.z = z
	def x(self):
		return x
	def y(self):
		return y
	def z(self):
		return z

class Object:
	#def __init__(self, **kwargs):
	def __init__(self, typ=None, fixed=False, size=(1,1,1), pic="x",
			weight=1, animated=False, hitside=None):
		self.pos = None    # np array
		self.__vel = np.array([0,0,0], dtype=np.float64)
		self.acc = np.array([0,0,0], dtype=np.float64)
		self.typ = typ
		self.size = size
		self.pic = pic
		self.weight = np.array(weight, dtype=np.float64)
		self.fixed = fixed
		self.animated = animated  # If object is self-animating
		self.hitside = hitside
		self.oldpos = None
	def type(self):
		if self.typ == World.t_human: return "Human"
		if self.typ == World.t_fixedblock: return "FixedBlock"
		if self.typ == World.t_block: return "Block"
		if self.typ == World.t_bot: return "Bot"
		if self.typ == World.t_horizon: return "Horizon"
		if self.typ == World.t_nearground: return "NearGround"
		return "UNKNOWN-TYPE"
	def step(self): return
	@property
	def vel(self): return self.__vel
	@vel.setter
	def vel(self, v): self.__vel = np.array(v, dtype=np.float64)
	def handle_overlap(self, o2, hitside): return

class Human(Object):
	def __init__(self):
		self.health = 1
		self.velmax = np.array([2,2,2], dtype=np.float64)
		self.accmax = np.array([0,.02,.02], dtype=np.float64)
		self.acc_likelihood = .2
		sc_pic = [
			" o ",
			"-|-",
			"/ \\",
		]
		self.animated = 1
		super().__init__(typ=World.t_human, size=(3,3,3), pic=sc_pic, weight=2)
	def handle_overlap(self, o2, hitside):
		for i in range(3):
			if hitside[i]:
				if max(abs(self.vel[i]), abs(hitside[i])) > .5:
					pass
					#self.world.log(" self vel[{}] {} > hitside {}".format(i, self.vel[i], hitside[i]))
					#pdb.set_trace()
				#self.vel[i] = -self.vel[i]
				#self.pos[i] += hitside[i]
				#self.world.log("Hitside: " + hitside[i])

	def step(self):
		if random.random() < self.acc_likelihood * self.health:
			self.acc = np.array([random.uniform(-v,v) for v in self.accmax],
				dtype=np.float64)
			self.vel += self.acc
		self.pos += self.vel * self.health

class FixedBlock(Object):
	def __init__(self):
		sc_pic = [
			"############",
			"############",
			"############",
		]
		super().__init__(typ=World.t_fixedblock, size=(3,3,12), pic=sc_pic, fixed=True)
	def step(self): return

class Horizon(Object):
	def __init__(self):
		pic = "------"
		sc_pic = [
			pic,
		]
		super().__init__(typ=World.t_horizon, size=(1,1,len(pic)), pic=sc_pic, fixed=True)
	def step(self): return

class NearGround(Object):
	def __init__(self):
		pic = "======"
		sc_pic = [
			pic,
		]
		super().__init__(typ=World.t_nearground, size=(1,1,len(pic)), pic=sc_pic, fixed=True)
	def step(self): return


class Block(Object):
	def __init__(self):
		sc_pic = [
			"[#]",
		]
		super().__init__(typ=World.t_block, size=(1,3,3), pic=sc_pic, weight=1)
	def step(self): return

class Bot(Object):
	def __init__(self):
		self.health = 1
		self.velmax = np.array([2,2,2], dtype=np.float64)
		self.accmax = np.array([0,.02,.02], dtype=np.float64)
		self.acc_likelihood = .2
		sc_pic = [
			".O.",
			"o o",
		]
		super().__init__(typ=World.t_bot, size=(2,3,3), pic=sc_pic, weight=1)
		self.animated = 1
	def step(self):
		if random.random() < self.acc_likelihood * self.health:
			self.acc = np.array([
					random.uniform(-self.accmax[0], self.accmax[0]),
					random.uniform(-self.accmax[1], self.accmax[1]),
					random.uniform(-self.accmax[2], self.accmax[2]),
				], dtype=np.float64)
			self.vel += self.acc
		self.pos += self.vel * self.health

class Goal(Object):
	def __init__(self):
		sc_pic = [
			"/~\\",
			"\\~/",
		]
		super().__init__(typ=World.t_bot, size=(3,3,3), pic=sc_pic, weight=1)

# vim:ts=2 ai sw=2
