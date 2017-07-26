import random
from util import *
from ansi import *
import numpy as np
import ipdb as pdb

pf("warning: find_freespace() is just using random position in a loop still")

t_empty = 0
t_human = 1
t_block = 2
t_bot = 3

class World:
	size = [None,None,None]
	tsize = [None,None]
	a = None
	objs = []
	xs = None
	ys = None
	zs = None
	ground_offset = 5
	def __init__(self, size=(30,80,80), tsize=(None,None)):
		# Gets terminal width for missing tsize values (y,x)
		self.size = size
		#self.a = [[0] * width for i in range(height)]  # 2d
		self.a = np.zeros(size, dtype=np.int16)
		self.a = [[[0] * self.xs for i in range(self.ys)] for j in range(self.zs)]
		txs, tys = get_linux_terminal()
		if tsize[0] == None: self.tsize[0] = tys
		if tsize[1] == None: self.tsize[1] = txs
		pf("Tsize set:", self.tsize)

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
		pf(pos, size)
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
		pf("size", size)
		# size: (z,y,x)
		# Raises MemoryError() if no room for size
		for tries in range(0, 1000): # Try 1000 times to find a free space
			x = random.randint(0, self.size[2])
			y = random.randint(0, self.ys)
			z = 0
			if self.is_freespace((z,y,x), size): return (z,y,x)
		raise MemoryError("No free space in world for object of size:", size)
	def add_object(self, o):
		pf("o.size", o.size)
		o.pos = self.find_freespace(o.size)
		self.objs.append(o)
		pf("Added object:", o.type(), o, "at pos", o.pos)
	def world_co_to_screen(self, co): # Project along y orthogonally
		sx = int(self.tsize[1] * (co[2] / self.xs))
		sy = self.tsize[0] - 2 - self.ground_offset - \
			int(self.tsize[0] * (co[0] / self.zs)) - \
			int(self.tsize[0] * (co[1] / self.zs) / 4)
		return sy+1, sx+1
		
	def draw_object(self, o):
		co = self.world_co_to_screen(o.pos)
		height = len(o.pic)
		for y in range(0, len(o.pic)):
			#pf("Obj:", o, "at", co[0]+1+y, ":")
			gxy(co[0]-height+y, co[1])
			for x in range(0, len(o.pic[y])):
				# Don't print spaces (just advance right)
				if o.pic[y][x] == ' ': gright()
				else: pfp(o.pic[y][x])
	def draw_ground(self):
		gy(self.tsize[0] - 1 - self.ground_offset)
		# Account for screen scrolling if we draw at the bottom right
		if self.ground_offset > 0: width = self.tsize[1]
		else: width = self.tsize[1]-1
		pf("=" * width)
	def draw(self):
		pfp(rst)
		clr()
		self.draw_ground()
		for o in sorted(self.objs, key=lambda o: o.pos[1], reverse=True):
			self.draw_object(o)
	def step(self):
		for o in self.objs:
			o.step()
			for i in range(3):
				if o.vel[i]<0 and o.pos[i]<0:
					o.pos[i] = 0
					o.vel[i] = 0
				if o.vel[i]>0 and o.pos[i]+o.size[i]-1>=self.size[i]:
					o.pos[i] = self.size[i]-o.size[i]
					o.vel[i] = 0

class Size: # Unused
	x = y = z = 0
	def __init__(x, y, z):
		raise ValueError("Unimplemented/Incomplete Size class")
		self.x = x; self.y = y, self.z = z
	def x(self):
		return x
	def y(self):
		return y
	def z(self):
		return z

class Object:
	typ = None
	size = None  # (z,y,x)
	pic = None
	weight = None
	pos = None
	__vel = (0,0,0)
	def __init__(self, **kwargs):
		self.typ = kwargs["typ"]
		self.size = kwargs["size"]
		self.pic = kwargs["pic"]
		self.weight = kwargs["weight"]
	def type(self):
		if self.typ == t_human: return "Human"
		if self.typ == t_block: return "Block"
		if self.typ == t_bot: return "Bot"
		return "UNKNOWN-TYPE"
	@property
	def vel(self): return self.__vel
	@vel.setter
	def vel(self, v): self.__vel = v

	def step(self):
		self.pos = [x+y for x,y in zip(self.pos, self.vel)]

class Human(Object):
	health = 1
	def __init__(self):
		sc_pic = [
			" o ",
			"-|-",
			"/ \\",
		]
		super().__init__(typ=t_human, size=(3,3,3), pic=sc_pic, weight=2)

class Block(Object):
	def __init__(self):
		sc_pic = [
			"[#]",
		]
		super().__init__(typ=t_block, size=(1,3,3), pic=sc_pic, weight=1)

class Bot(Object):
	health = 1
	def __init__(self):
		sc_pic = [
			".O.",
			"o o",
		]
		super().__init__(typ=t_bot, size=(2,3,3), pic=sc_pic, weight=1)
