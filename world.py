import random
from util import *
from ansi import *
import numpy as np
import ipdb as pdb
import atexit
import copy
import curses
from time import sleep

pf("warning: find_freespace() is just using random position in a loop still")

t_bot = 0
t_empty = 1
t_human = 2
t_block = 3
t_fixedblock = 4
t_horizon = 5
t_nearground = 6

class Erasure:
	def __init__(self, co, timestep):
		self.co = co
		self.timestep = timestep
class World:
	def __init__(self, size=(30,80,80), tsize=(None,None)):
		# Gets terminal width for missing tsize values (y,x)
		self.size = size
		#self.a = [[[0] * self.xs for i in range(self.ys)] for j in range(self.zs)]
		self.a = np.zeros(size)
		txs, tys = get_linux_terminal()

		self.tsize = [None,None]
		if tsize[0] == None: self.tsize[0] = tys
		if tsize[1] == None: self.tsize[1] = txs

		self.tyscale = .5        # Display world y in term height * tyscale
		self.objs = []
		self.ground_offset = 5
		self.ui_initted = False
		self.trow_status = tys-self.ground_offset
		self.timestep = 0
		self.erasures = []
		self.curses = None
	def update_tsize(self):
		#txs, tys = get_linux_terminal()
		self.tsize = list(self.curses.getmaxyx())
		self.trow_status = tys-self.ground_offset

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
		curses.noecho()
		curses.cbreak()
		self.curses.keypad(1)
		self.tsize = list(self.curses.getmaxyx())
		self.winworld = curses.newwin(
			self.tsize[0]-self.ground_offset, self.tsize[1],
			0,0)
		self.winstatus = curses.newwin(
			self.ground_offset, self.tsize[1],
			self.tsize[0]-self.ground_offset, 0)
		self.winworld.refresh()
		self.winstatus.refresh()
	@atexit.register
	def restore_ui():
		#pfl(cshow)
		curses.nocbreak()
		#world.curses.keypad(0)
		curses.echo()
		curses.endwin()
	def restore_ui(self):
		curses.nocbreak()
		self.curses.keypad(0)
		curses.echo()
		curses.endwin()
		self.ui_initted = False
	def status(self, s, row=0):
		gy(self.trow_status)
		pfl(s)
	def putatyx(self, co, s, attr):
		#self.
		return
	def erase_erasures(self):
		for e in self.erasures:
			if e.timestep > self.timestep:
				self.winworld.addstr(e.co[0], e.co[1], " ")
				self.putatyx(e.co, " ", a_blank)
				gyx(e.co[0], e.co[1])
				pfpl(" ")
	def draw(self):
		self.winworld.refresh()
		self.erase_erasures()

		#cls()
		#self.draw_ground()
		for o in sorted(self.objs, key=lambda o: o.pos[1], reverse=True):
			self.draw_object(o)

	def step(self):
		self.timestep += 1
		oi = -1
		for o in self.objs:
			if o.fixed: continue
			oi += 1
			#pfp(self.timestep, ". Obj[{}] ".format(oi), o, " vel: ", o.vel)
			#if self.timestep > 5 and o.typ == t_fixedblock:
					#pdb.set_trace()
			#if o.typ == t_block:
				#if (o.vel != 0).any():
					#pdb.set_trace()
				#pass
			#oldpos = o.pos.copy()
			oldobj = copy.deepcopy(o)
			o.step()
			#if o.vel[2]<0: pdb.set_trace()
			for i in range(3):
				if o.vel[i]<0 and o.pos[i]<0:
					o.pos[i] = 0
					o.vel[i] = 0
				if o.vel[i]>0 and o.pos[i]+o.size[i]-1 >= self.size[i]:
					o.pos[i] = self.size[i]-o.size[i]
					o.vel[i] = 0
			if (oldobj.pos != o.pos).any():
				self.draw_object(oldobj, erase=True, pos=oldobj.pos)
			for o2 in self.objs:
				if o2 == o: continue
				#pfp(self.timestep, ". Obj[{}] ".format(oi), o, " vel: ", o.vel)
				hitside = self.overlap_obj(o, o2)
				o.hitside = hitside
				if hitside is not None: # If overlap
					#pdb.set_trace()
					#hitside = self.overlap_obj(o, o2)
					#pfp(self.timestep, ". Obj[{}] ".format(oi), o, " vel: ", o.vel)
					#self.status("Collision")
					self.draw_collision(o, hitside)
					o.handle_overlap(o2, hitside)
	def world_co_to_screen(self, co, obj=None): # Project along y orthogonally
		if obj != None and obj.typ == t_nearground:
			#pf("")
			##pf("co:", co)
			#pdb.set_trace()
			pass
		sx = int(self.tsize[1] * (co[2] / self.xs))
		sy = self.tsize[0] - 2 - self.ground_offset - \
			int(self.tsize[0] * (co[0] / self.zs)) - \
			int(self.tsize[0] * (co[1] / self.ys) * self.tyscale)
		if obj != None and obj.typ == t_horizon:
			#pf("tco:", sy+1, sx+1)
			pass
		return sy+1, sx+1
		
	def draw_object(self, o, erase=False, pos=None):
		co = self.world_co_to_screen(o.pos if pos is None else pos, obj=o)
		height = len(o.pic)
		for y in range(0, len(o.pic)):
			#pf("Obj:", o, "at", co[0]+1+y, ":")

			# GET COORDINATES OF TOP LEFT
			# -height+1 to start at the top
			ty = co[0]-height+y
			# Don't round up with +.5 cuz we're not at 0, but on the first char
			tx = co[1] - int(o.size[2]/2)

			gyx(ty, tx)
			for x in range(0, len(o.pic[y])):
				# Don't print spaces (just advance right)
				if erase: pfl(" ")
				else:
					if o.pic[y][x] == ' ': gright()
					else: pfl(o.pic[y][x])
			#gyx(co[0]-1, co[1])
			#pfpl(yel, o.windex, rst)

			#gyx(co[0]-2, co[1])
			#pfpl(yel, "@", rst)
			if o.hitside: # If there was a collision
				self.draw_collision(o, o.hitside, erase=erase)
	def draw_ground(self):
		gy(self.tsize[0] - 1 - self.ground_offset - \
			int(self.tsize[0] * self.tyscale))
		pf("_" * self.tsize[1])
		gy(self.tsize[0] - 1 - self.ground_offset)
		# Account for screen scrolling if we draw at the bottom right
		if self.ground_offset > 0: width = self.tsize[1]
		else: width = self.tsize[1]-1
		pf("=" * width)
	def draw_collision(self, o, hitside, erase=None):
		co = self.world_co_to_screen(o.pos)
		ty = int(co[0] + hitside[0]*o.size[0]/2)
		tx = int(co[1] + hitside[2]*o.size[2]/2)
		#pf("Hit:", hitside, "coy,x:", co[0], co[1])
		#pf("Hit:", hitside, "ty,x:", ty, tx)
		#pf("")
		gyx(ty, tx)
		pfpl(red, "*" if not erase else " ", rst)
		self.add_timed_erase((ty,tx), 1)
	def add_timed_erase(self, co, ticks):
		self.erasures.append(Erasure(co, self.timestep + ticks))
	def overlap_obj(self, o, o2):
		# Returns None if false, else hitside = [z,y,x] <= {-1,0,1}+
		# Where -1 means the negative side, while 0 means we're in an overlap
		# (...and the collision side is therefore unknown, because of our
		# simplistic step analysis of collision)
		ocount = 0
		hitside = [0,0,0]
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
			if op-osiz >= o2p-o2siz and op+osiz <= o2p+o2siz: # Enclosed!
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
		minoverlap = min([abs(x) for x in hitside])
		hitside = [0 if abs(x)>minoverlap else x for x in hitside]
		return hitside if ocount == 3 else None

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
	def __init__(self, typ=None, fixed=False, size=(1,1,1), pic="*",
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
	def type(self):
		if self.typ == t_human: return "Human"
		if self.typ == t_fixedblock: return "FixedBlock"
		if self.typ == t_block: return "Block"
		if self.typ == t_bot: return "Bot"
		if self.typ == t_horizon: return "Horizon"
		if self.typ == t_nearground: return "NearGround"
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
		super().__init__(typ=t_human, size=(3,3,3), pic=sc_pic, weight=2)
	def handle_overlap(self, o2, hitside):
		for i in range(3):
			if hitside[i]:
				if max(abs(self.vel[i]), abs(hitside[i])) > .5:
					pdb.set_trace()
				self.vel[i] = -self.vel[i]
				self.pos[i] += hitside[i]
				self.world.status(hitside[i])

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
		super().__init__(typ=t_fixedblock, size=(3,3,12), pic=sc_pic, fixed=True)
	def step(self): return

class Horizon(Object):
	def __init__(self):
		sc_pic = [
			"-",
		]
		super().__init__(typ=t_horizon, size=(1,1,1), pic=sc_pic, fixed=True)
	def step(self): return

class NearGround(Object):
	def __init__(self):
		sc_pic = [
			"=",
		]
		super().__init__(typ=t_nearground, size=(1,1,1), pic=sc_pic, fixed=True)
	def step(self): return


class Block(Object):
	def __init__(self):
		sc_pic = [
			"[#]",
		]
		super().__init__(typ=t_block, size=(1,3,3), pic=sc_pic, weight=1)
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
		super().__init__(typ=t_bot, size=(2,3,3), pic=sc_pic, weight=1)
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
		super().__init__(typ=t_bot, size=(3,3,3), pic=sc_pic, weight=1)

# vim:ts=2 ai
