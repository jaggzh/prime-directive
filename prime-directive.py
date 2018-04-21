#!/usr/bin/python3
#import config
from __future__ import print_function
#import sys
#sys.settrace
#from hyperopt import Trials, STATUS_OK, tpe
#from hyperas import optim
#from hyperas.distributions import choice, uniform, conditional
import os

os.environ['TF_CPP_MIN_LOG_LEVEL']='3'
import tensorflow as tf
sess = tf.Session(config=tf.ConfigProto(log_device_placement=False))

import keras
import errno
from keras.models import Sequential, Model
from keras.layers import Dense, Reshape, UpSampling2D, Flatten, Conv1D, MaxPooling1D, Input, ZeroPadding1D, Activation, Dropout, Embedding, Permute, LSTM
from keras.layers.merge import Concatenate
#from keras.layers import Deconvolution2D
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img
from keras.utils.layer_utils import print_summary
from keras.layers.advanced_activations import LeakyReLU
from keras.optimizers import Adam, SGD
from keras.callbacks import ModelCheckpoint, LambdaCallback
from keras.utils.np_utils import to_categorical
import numpy as numpy
import sys
from os import listdir
from os.path import isdir, isfile, islink, join
from random import randint, uniform, randrange, random as rand
import random, re, time, sys, math, shutil, itertools, argparse
from time import sleep
from math import ceil
import math
from keras.callbacks import EarlyStopping
import shutil
from keras import backend as K
from ansi import *
#import cPickle as pickle
import os
from world import World, Human, NearGround, Horizon, Block, FixedBlock, Bot, Goal
import kbnb
from util import *
import atexit
import signal

#from seya.layers.attention import SpatialTransformer, ST2

def getargs():
	parser = argparse.ArgumentParser(description='Page undeformer')
	parser.add_argument('-f', '--viewfirst', action='store_true', help='View images before training')
	parser.add_argument('-D', '--nodraw', action='store_true', help='Disable Drawing')
	return parser.parse_args()
args = getargs()
termwidth = None
termheight = None
weight_file = "tmp/weights.h5"

verbose=0
load_weights=1      # load prior run stored weights
save_weights=1      # load prior run stored weights
test_fraction = .15  # fraction of the data set for the test set
valid_fraction = .1  # fraction of the data set for the validation set
checkpoint_epoch = None

last_epoch_time = time.time()
save_weight_secs = 30
start_time = time.time()
opt_lrate = 0.001
opt_epochs = 20
opt_iters = 3   # Training iterations

def init():
	# fix random seed for reproducibility
	global termwidth, termheight
	termwidth, termheight = get_linux_terminal()
	seed = 18
	random.seed(seed)
	numpy.random.seed(seed)
	numpy.set_printoptions(threshold=64, linewidth=termwidth-1, edgeitems=3)

	global checkpoint_epoch
	checkpoint_epoch = SaveWeights()
	numpy.set_printoptions(edgeitems=5)

	kbnb.init()

def view_weights(model, name=None):
	if name == None:
		raise ValueError("Call with layer")
	layer = model.get_layer(name)
	weights = layer.get_weights()
	pf(weights[1])

class SaveWeights(keras.callbacks.Callback):
	def on_epoch_end(self, epoch, logs={}):
		global last_epoch_time
		sleep(.5)
		if time.time()-last_epoch_time > save_weight_secs:
			last_epoch_time = time.time()
			pf("Saving weights, timed (", save_weight_secs, "s).  Time elapsed: ",
					int(time.time()-start_time), "s.  Fit time elapsed: ",
					int(time.time()-fit_start_time), "s.",
					sep=''
				)
			save_weights(model, weight_file)
		return

def show_shape(inputs, x, predict=False):
	# we can predict with the model and print the shape of the array.

	model = Model(inputs=[inputs], outputs=[x])
	pf("MODEL SUMMARY:")
	model.summary()
	pf("/MODEL SUMMARY:")
	if predict:
		dummy_input = numpy.ones((1,window,1), dtype='float32')
		pf("MODEL PREDICT: ",)
		preds = model.predict(dummy_input)
		pf(preds.shape)
		pf("/MODEL PREDICT:")

def model():
	global actouts
	act='sigmoid'
	trackers=[]
	leakalpha=.2

	x = inputs = Input(shape=(1, 1), name='gen_input', dtype='float32')
	x = Dense(1, activation='sigmoid')(x)
	output = x
	lrate = opt_lrate
	epochs = opt_epochs
	decay = 1/epochs
	adam_opt_gen=Adam(lr=lrate, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=decay)
	opt = 'sgd'
	opt = adam_opt_gen
	loss = 'mae'
	actmodels.compile(
			loss=loss,
			optimizer=opt,
			metrics=['accuracy'],
		)
	pf("Loading weights")
	if load_weights and isfile(weight_file):
		pf("Loading weights")
		actmodels.load_weights(weight_file)
	return actmodels

def train(model=None, itercount=0):
	preview = True if args.viewfirst else False
	preview = True
	do_train = False
	do_train = True
	#if 1 or (itercount>0 or preview):
	#if 0 and (itercount>0 or preview):
	if itercount>0 or preview:
		generator = generate_texts_rnd('test')
		for i in range(0,5):
			x, y = next(generator)
			#pf(bred, "X is ", x, rst)
			#pf(bred, "Y is ", y, rst)
			pred = model.predict(x, batch_size=1, verbose=0)
			#pf(pred)
			# pred[2] is the 3rd output: c1_2
			# pred[2][0] is the first sample (of the batch)'s output
			# pred[2][0][i] is the first sample output's letter i
			# pred[2][0][i][0] is letter's conv filter (there are f = 100)
			#pf("Pred len:", len(pred))
			#pf("Pred[0] shape (output layer):", pred[0].shape)
			#pf("Pred[1] shape:", pred[1].shape)
			#pf("Pred[2] shape:", pred[2].shape)

			pfp("\n  Pred sentence w/punct:\n", glob_last_wpunct)
			s = arr1_to_sentence(x[0])
			pfp("  Pred sentence input (x):\n", s)

			#lyr_c1_1_out = pred[2][0] # Output#2, for the first of batch (0)
			#for f in range(len(lyr_c1_1_out[0])):  # f = 0..filter count
			#	lyr_c1_1_out = pred[2][0] # Output#2, for the first of batch (0)
			#	ltr_values = lyr_c1_1_out[:,f]
			#	str_colorize(s, ltr_values, aseq_gb)

			pfpl("  Y gndtrth : ")
			[ pfpl(n) for n in y[0][0].astype(numpy.uint8)]

			pfpl("  Y pred    : ")
			#pf(pred[0])
			#[ pfpl(n) for n in pred[0][0].astype(numpy.uint8)]
			#pf("")

			for loc in range(len(pred[0])-1, -1, -1):
				#pf("pred loc:", loc)
				#pf("pred[0] len:", len(pred[0][0]))
				#pf("pred[0]:", pred[0][0])
				val = int(pred[0][int(loc)]+.2)  # Add .2 for "close to 1 (true)"
				if val: # true == insert space
					s = s[:loc+1] + '/' + s[loc+2:] # use if replacing
					#s = s[:loc+1] + '/' + s[loc+1:] # use if inserting
			#pfp("  Y sentence (breaks inserted):\n", s)

			#for off in ((pred[0]*window).astype(numpy.int8)[::-1]):
			#for off in ((pred[0]*window).astype(numpy.int8)):
				#for off in (pred[0]):
				#pf(" . at", off)

	if not do_train:
		pf(yel, "Skipping training", rst)
		pf(bred, "Returning early and never running fit_generator", rst)
	if do_train:
		global fit_start_time, last_epoch_time
		#total_sets = total_wpunc = total_wopunc = 0  # Reset stats
		fit_start_time = time.time()
		last_epoch_time = time.time()

		generator = generate_texts_rnd('train')
		generator_val = generate_texts_rnd('val')

		pf("Total snippets:", total_sets)
		pf("Total snippets w/ punc:", total_wpunc)
		pf("Total snippets w/o punc:", total_wopunc)
		pf("Calling fit_generator")
		pf("Model:", model)
		model.fit_generator(
				generator,
				steps_per_epoch=samp_per_epoch_txt,
				epochs=epochs_txt,
				verbose=2,
				validation_data=generator_val,
				validation_steps=30,
				callbacks=[checkpoint_epoch],
			)
		pf("Saving weights")
		save_weights(model, weight_file)

def save_weights(model, fn):
	model.save_weights(fn)
	pf("Saved weights to", fn)

def siggy(signum, frame):
	if signum == signal.SIGINT:
		pf("Interrupted")
		cleanup()
		exit(0)
	elif signum == signal.SIGWINCH:
		world.update_tsize()
def cleanup():
	world.restore_ui() # Restores cursor
	#kbnb.reset_flags() # Restore terminal echo and icanon
	gy(termheight-1)

init()
world_size = (30*2, 20, termwidth*2)
#model = model()
world = World(size=world_size)
world.init_ui()
signal.signal(signal.SIGINT, siggy)
signal.signal(signal.SIGWINCH, siggy)

#cls()
#sleep(3)

# Add wall
#for y in range(0,world_size[1],20):
fblock = FixedBlock()
world.add_object(fblock, pos=(0, world_size[1]/2, int(world_size[2]*.6)))
# Add other objects
horizon = Horizon()
ground = NearGround()
for i in range(0, int(world_size[2]), horizon.size[2]): # Skip size[2] (x width)
	horizon = Horizon()
	ground = NearGround()
	world.add_object(horizon, pos=(0, world_size[1]-1, i))
	world.add_object(ground, pos=(0, 0, i))
for i in range(10):
	human = Human()
	human.vel = (0,uniform(-.5,.5),uniform(-.5,.5))
	world.add_object(human)
for i in range(5):
	block = Block()
	world.add_object(block)
# Add bot
bot = Bot()
world.add_object(bot)
for t in range(0,10000):
	if not args.nodraw: world.draw()
	time.sleep(.01)  # Delay before step cuz step erases

	#else: break

	world.step()
	if world.winworld.getch() != -1:
			break

cleanup()
pf("Finished")
	
# vim:ts=2 ai
