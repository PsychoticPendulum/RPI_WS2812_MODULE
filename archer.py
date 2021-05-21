#! /usr/bin/env python3
# |-------------------------------------------------------------------------|
# |  ____                 _     _      ____                        _        |
# | |  _ \ ___ _   _  ___| |__ (_) ___|  _ \ ___ _ __   __ _ _   _(_)_ __   |
# | | |_) / __| | | |/ __| '_ \| |/ __| |_) / _ \ '_ \ / _` | | | | | '_ \  |
# | |  __/\__ \ |_| | (__| | | | | (__|  __/  __/ | | | (_| | |_| | | | | | |
# | |_|   |___/\__, |\___|_| |_|_|\___|_|   \___|_| |_|\__, |\__,_|_|_| |_| |
# |           |___/                                   |___/                 |
# |-------------------------------------------------------------------------| 
# 
#
#
# |> Raspberry Pi 1 B+, Raspberry Pi 1 A+, Raspberry Pi 2, Raspberry Pi Zero, Raspberry Pi Zero W
# |> Raspberry Pi 3, Raspberry Pi 3 B+, Raspberry Pi 3 A+, Raspberry Pi 4, Raspberry Pi 400
# 
# |-----------------------------------------------------------------------------------------------------------------------|
# | 39. | 37. | 35. | 33. | 31. | 29. | 27. | 25. | 23. | 21. | 19. | 17. | 15. | 13. | 11. | 09. | 07. | 05. | 03. | 01. |
# |-----------------------------------------------------------------------------------------------------------------------|
# | 40. | 38. | 36. | 34. | 32. | 30. | 28. | 26. | 24. | 22. | 20. | 18. | 16. | 14. | 12. | 10. | 08. | 06. | 04. | 02. |
# |-----------------------------------------------------------------------------------------------------------------------|
# 
# |-----------------------------------------------------------------------------------------------------------------------|
# | GND | G26 | G19 | G13 | G06 | G05 | DNC | GND | G11 | G09 | G10 | ~3V | G22 | G27 | G17 | GND | G04 | G03 | G02 | ~3V |
# |-----------------------------------------------------------------------------------------------------------------------|
# | G21 | G20 | G16 | GND | G12 | GND | DNC | G07 | G08 | G25 | GND | G24 | G23 | GND | G18 | G15 | G14 | GND | ~5V | ~5V |
# |-----------------------------------------------------------------------------------------------------------------------|

	###################
	##### IMPORTS #####
	###################

from rpi_ws281x import *
import numpy
import pyaudio
import time
import threading
from gpiozero import LED, Button
from math import sqrt
from datetime import date
from random import randint

	###################
	##### CLASSES #####
	###################

class Module:
	running = True
	light = True
	sound = False
	mode = 0
	last_mode = 0
	modes = 10

class Strip:
	count = 60		# The amount of LEDs on WS2812B
	pin = 18		# The GPIO Pin to connect the WS2812B to
	brightness = 255

class FlipSwitch:
	light = Button(21)
	light_pressed = False
	light_queued = False

	sound = Button(20)
	sound_pressed = False
	sound_queued = False

	mode = Button(16)
	mode_pressed = False
	mode_queued = False

class StatusLED:
	power = LED(13)
	light = LED(19)
	mode = LED(12)
	sound = LED(26)

class DateTime:
	d = 0
	h = 0
	s = 0

class LED:
	def __init__(self, id, r, g, b):
		self.id = id
		self.r = r
		self.g = g
		self.b = b
	id = 0
	r = 240
	g = 0
	b = 0

ledstrip = []
bg_ledstrip = []

	###################
	##### SYSINFO #####
	###################

def sound_control():
	p = pyaudio.PyAudio()
	stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=16)
	data = numpy.frombuffer(stream.read(16, exception_on_overflow=False), dtype=numpy.int16)
	peak = numpy.average(numpy.abs(data))*2
	peak /= 10
	if peak > 255:
		peak = 255
	elif peak < 15:
		peak = 15
	if Module.sound:
		if peak < Strip.brightness:
			Strip.brightness = int(Strip.brightness * 0.67)
		else:
			Strip.brightness = int(peak)
		strip.setBrightness(Strip.brightness)
	stream.close()

def get_time():
	now = time.localtime()
	today = date.today()
	if time.strftime("%S", now) != str(DateTime.s):
		DateTime.d = int(today.strftime("%d"))
		DateTime.h = int(time.strftime("%H", now))
		DateTime.s = str(time.strftime("%S", now))

	##################
	##### COLORS #####
	##################

def prevent_overflow(c, m):
	if c > m:
		c = m
	elif c < 0:
		c = 0
	return c

def cycle_colors(r,g,b,v,m):
	if r == m and b > 0:
		b -= v
	if r == m and b == 0:
		g += v
	if g == m and r > 0:
		r -= v
	if g == m and r == 0:
		b += v
	if b == m and g > 0:
		g -= v
	if b == m and g == 0:
		r += v
	r = prevent_overflow(r,m)
	g = prevent_overflow(g,m)
	b = prevent_overflow(b,m)
	return r,g,b

	################
	##### INIT #####
	################

strip = Adafruit_NeoPixel(Strip.count, Strip.pin, 800000, 10, False, 24, 0)
strip.begin()

def flush_leds():
	print("Flushing leds")
	for i in range(Strip.count):
		j = Strip.count - (1 + i)
		ledstrip[j].r = 240
		ledstrip[j].g = 240
		ledstrip[j].b = 240
		strip.setPixelColor(j, Color(ledstrip[j].r, ledstrip[j].g, ledstrip[j].b))
		strip.show()
		time.sleep(0.01)

def set_leds(id, r, g, b, t):
	ledstrip[id].r = r
	ledstrip[id].g = g
	ledstrip[id].b = b
	strip.setPixelColor(id, Color(ledstrip[id].r, ledstrip[id].g, ledstrip[id].b))
	strip.show()
	time.sleep(t)

def init_mode(mode):
	print("Entering modeswitcher")
	flush_leds()
	r = 240
	g = 0
	b = 0
	if mode == 0:		# Circlefade Rainbow
		print("Circlefade Rainbow")
		for i in range(Strip.count):
			set_leds(i, r,g,b, 0.01)
			r,g,b = cycle_colors(r,g,b,24,240)
	elif mode == 1:		# Circlefade Ice
		print("Circlefade Ice")
		r = 0
		g = 240
		b = 240
		v = 16
		w = 0
		for i in range(Strip.count):
			if w == 0:
				if g > 0:
					g -= v
				else:
					r += v
					if r == 240:
						w = 1
			else:
				if r > 0:
					r -= v
				else:
					g += v
			set_leds(i, r,g,b, 0.01)
	elif mode == 2:		# Circlefade Fire
		print("Circlefade Fire")
		r = 240
		g = 120
		b = 0
		v = 8
		w = 1
		for i in range(Strip.count):
			if w == 0:
				if g > 0:
					g -= v
				else:
					w = 1
			else:
				if g < 120:
					g += v
				else:
					w = 0
			set_leds(i, r,g,b, 0.01)
	elif mode == 3:		# Circlefade Landscape
		print("Circlefade Landscape")
		r = 0
		g = 240
		b = 120
		w = 0
		v = 8
		for i in range(Strip.count):
			if w == 0:
				if b > 0:
					b -= v
				else:
					w = 1
			else:
				if b < 120:
					b += v
				else:
					w = 0
			set_leds(i, r,g,b, 0.01)
	elif mode == 4:		# Fade
		print("Fade")
		r = 240
		g = 0
		b = 0
		v = 12
		for i in range(Strip.count):
			set_leds(i, r,g,b, 0.01)
	elif mode == 5:		# Circle
		print("Circle")
		r = 240
		g = 0
		b = 0
		for i in range(Strip.count):
			set_leds(i, r,g,b, 0.01)
	elif mode == 6:		# Static Violet
		print("Static Violet")
		r = 240
		g = 0
		b = 240
		for i in range(Strip.count):
			if i % 2 == 0:
				r = 240
			else:
				r = 0
			set_leds(i, r,g,b, 0.01)
	elif mode == 7:		# Static Landscape
		print("Static Hell")
		r = 240
		g = 0
		b = 0
		for i in range(Strip.count):
			if i % 2 == 0:
				g = 120
			else:
				g = 0
			set_leds(i, r,g,b, 0.01)
	elif mode == 8:		# Static static
		print("Static static")
		r = 240
		g = 240
		b = 240
		for i in range(Strip.count):
			if i % 2 == 0:
				r = 0
			else:
				r = 240
			set_leds(i, r,r,r, 0.01)
	elif mode == 9:		# Snake
		r = 240
		g = 0
		b = 0
		w = 0
		for i in range(Strip.count):
			if w < 3:
				r = 240
				w += 1
			else:
				r = 0
				w += 1
				if w == 12:
					w = 0
			set_leds(i, r,g,b, 0.01)
	elif mode == 10:	# Campfire
		r = 240
		g = 0
		b = 0
		for i in range(Strip.count):
			g = randint(0, 120)
			set_leds(i, r,g,b, 0.01)
	else:			# Undefined Mode
		print("Mode undefined")
		for i in range(Strip.count):
			set_leds(i, 24,24,24, 0.01)	
	
	StatusLED.mode.off()
	print("----------------------------------------------------------------------------------")


def init_module():
	StatusLED.power.on()
	time.sleep(0.33)
	StatusLED.light.on()
	time.sleep(0.33)
	StatusLED.mode.on()
	time.sleep(0.33)
	StatusLED.sound.on()
	time.sleep(0.33)
	
	r = 240
	g = 0
	b = 0

	for i in range(Strip.count):
		ledstrip.append(LED(i, r,g,b))
		bg_ledstrip.append(LED(i, r,g,b))
		strip.setPixelColor(i, Color(ledstrip[i].r, ledstrip[i].g, ledstrip[i].b))
		strip.show()
		r,g,b = cycle_colors(r,g,b,24,240)
		time.sleep(0.01)

init_module()

	#################
	##### MODES #####
	#################

def copy_states():
	for i in range(Strip.count):
		bg_ledstrip[i].r = ledstrip[i].r
		bg_ledstrip[i].g = ledstrip[i].g
		bg_ledstrip[i].b = ledstrip[i].b

def circlefade():
	copy_states()
	for i in range(Strip.count):
		if i == 0:
			ledstrip[i].r = bg_ledstrip[Strip.count-1].r
			ledstrip[i].g = bg_ledstrip[Strip.count-1].g
			ledstrip[i].b = bg_ledstrip[Strip.count-1].b
		else:
			ledstrip[i].r = bg_ledstrip[i-1].r
			ledstrip[i].g = bg_ledstrip[i-1].g
			ledstrip[i].b = bg_ledstrip[i-1].b
	
	for led in ledstrip:
		strip.setPixelColor(led.id, Color(led.r, led.g, led.b))

	strip.show()
	time.sleep(1 / 24)

def snake():
	circlefade()
	for i in range(Strip.count):
		ledstrip[i].r, ledstrip[i].g, ledstrip[i].b = cycle_colors(ledstrip[i].r, ledstrip[i].g, ledstrip[i].b, 30, 240)
	

def fade():
	for i in range(Strip.count):
		ledstrip[i].r, ledstrip[i].g, ledstrip[i].b = cycle_colors(ledstrip[i].r, ledstrip[i].g, ledstrip[i].b, 12, 240)
		strip.setPixelColor(i, Color(ledstrip[i].r, ledstrip[i].g, ledstrip[i].b))
		strip.show()
		time.sleep(0.01)

def circle():
	for l in range(Strip.count):
		ledstrip[l].r, ledstrip[l].g, ledstrip[l].b = cycle_colors(ledstrip[l].r, ledstrip[l].g, ledstrip[l].b, 120, 240)
	for i in range(Strip.count):
		set_leds(i, ledstrip[i].r, ledstrip[i].g, ledstrip[i].b, 0.05)
	for j in range(Strip.count):
		set_leds(j, ledstrip[j].b, ledstrip[j].r, ledstrip[j].g, 0.05)
	for k in range(Strip.count):
		set_leds(k, ledstrip[k].g, ledstrip[k].b, ledstrip[k].r, 0.05)

def campfire():
	strip.setBrightness(randint(25, 125))
	for i in range(Strip.count):
		offset = randint(25, 125)
		strip.setPixelColor(i, Color(offset, randint(0, int(offset/4)), 0))
	strip.show()
	time.sleep(0.125)

	#################
	##### INPUT #####
	#################

def handle_input():
	# Lightswitch
	FlipSwitch.light_pressed = FlipSwitch.light.is_active
	if FlipSwitch.light_pressed and not FlipSwitch.light_queued:
		FlipSwitch.light_queued = True
	if FlipSwitch.light_queued and not FlipSwitch.light_pressed:
		FlipSwitch.light_queued = False
		if Module.light:
			Module.light = False
		else:
			Module.light = True
	
	# Soundswitch
	FlipSwitch.sound_pressed = FlipSwitch.sound.is_active
	if FlipSwitch.sound_pressed and not FlipSwitch.sound_queued:
		FlipSwitch.sound_queued = True
	if FlipSwitch.sound_queued and not FlipSwitch.sound_pressed:
		FlipSwitch.sound_queued = False
		if Module.sound:
			Module.sound = False
		else:
			Module.sound = True

	# Modeswitch
	FlipSwitch.mode_pressed = FlipSwitch.mode.is_active
	if FlipSwitch.mode_pressed and not FlipSwitch.mode_queued:
		FlipSwitch.mode_queued = True
		StatusLED.mode.on()
		Module.light = True
	if FlipSwitch.mode_queued and not FlipSwitch.mode_pressed:
		print("Switching mode ...")
		FlipSwitch.mode_queued = False
		Module.mode += 1
		if Module.mode > Module.modes:
			Module.mode = 0

def handle_output():
	# Light
	if Module.light:
		StatusLED.light.on()
	else:
		StatusLED.light.off()
	# Sound
	if Module.sound:
		StatusLED.sound.on()
	else:
		StatusLED.sound.off()

def controller():
	while Module.running:
		handle_input()
		handle_output()
		time.sleep(0.05)

controller_thread = threading.Thread(target=controller)
controller_thread.start()

	#####################
	##### MAIN LOOP #####
	#####################

def poweroff():
	print("Poweroff ...")
	Module.running = False
	time.sleep(1)	# Wait for controller to finish
	
	for i in range(Strip.count):
		j = Strip.count - (1 + i)
		ledstrip[j].r = 0
		ledstrip[j].g = 0
		ledstrip[j].b = 0
		strip.setPixelColor(j, Color(ledstrip[j].r, ledstrip[j].g, ledstrip[j].b))
		strip.show()
		time.sleep(0.01)
	quit()

def set_strip():
	if not Module.light:
		for i in range(Strip.count):
			strip.setPixelColor(i, Color(0,0,0))
		strip.show()
		return

	if Module.last_mode != Module.mode:
		print("Mode switched from " + str(Module.last_mode) + " to " + str(Module.mode))
		init_mode(Module.mode)
	Module.last_mode = Module.mode

	if Module.mode == 0:		# Circlefade Rainbow
		circlefade()
	elif Module.mode == 1:		# Circlefade Ice
		circlefade()
	elif Module.mode == 2:		# Circlefade Fire
		circlefade()
	elif Module.mode == 3:		# Circlefade Landscape
		circlefade()
	elif Module.mode == 4:		# Fade
		fade()
	elif Module.mode == 5:		# Circle
		circle()
	elif Module.mode == 9:		# Snake
		snake()
	elif Module.mode == 10:		# Campfire
		campfire()

def loop():
	while Module.running:
		try:
			get_time()
			set_strip()
			sound_control()
		except KeyboardInterrupt:
			poweroff()
		except:
			print("Something went wrong")
			try:
				init_mode(-1)
				time.sleep(10)
			except KeyboardInterrupt:
				poweroff()
loop()		# Start mainloop
