#These three lines import the different functions that we need to make the program work. Time lets us have pauses in our code. RPi.GPIO as GP makes the Pins on the Pi 
#active, and we are calling them GP so that it is easier to use.
import sys
import time
import RPi.GPIO as GP
from subprocess import Popen, PIPE, STDOUT
from threading import Thread

#function to setup queue for non blocking read of stdin
#def queueSetup():
try:
	from Queue import Queue, Empty
except ImportError:
	from queue import Queue, Empty

ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(out, queue):
	for line in iter(out.readline,b''):
		queue.put(line)
	out.close()


#Create a process p to run mpg321
p = Popen(['mpg321', '-R', 'testplayer'],stdin=PIPE, stdout=PIPE,bufsize=1, close_fds=ON_POSIX)#, stderr=PIPE)
q=Queue()
t= Thread(target=enqueue_output, args=(p.stdout,q))
t.daemon = True
t.start()

#Build class to track button state, rather than global list
class MyButtonStateClass:
	def __init__(self):
		self.state = [0,0,0,0,0,0]
		
	def playPause(self,n):
		for x in range (6):
			if (x==n):
				if (self.state[x]==1):
					p.stdin.write('PAUSE\n'.format(tracks[x]))
					self.state[x]=2
				elif (self.state[x]==2):
					p.stdin.write('PAUSE\n'.format(tracks[x]))
					self.state[x]=1
				else:
					p.stdin.write('LOAD {0}\n'.format(tracks[x]))
					self.state[x]=1
			else:
				self.state[x]=0
				
	def stop (self):
		self.state = [0,0,0,0,0,0]
		
	def getState(self):
		return self.state

buttons = MyButtonStateClass()



#These two lines mop up previous codes that use the GPIO pins.
#It also sets the mode of the pins to (GP.BOARD)
GP.cleanup()
GP.setmode(GP.BOARD)

#These are the variables for the progect.
#The different numbers are for the progect.
#lPins = Pins for the LEDs.
#bPins = Pins for the buttons.
#Then we list out the different tracks that we want to use.
lPins=[11,15,7,21,19,13]
bPins = [10,24,22,12,16,18]


#create list of the tracks for each button
tracks = ["track1.mp3","track2.mp3","track3.mp3","track4.mp3","track5.mp3","track6.mp3"]


def button_press(channel):
	button = bPins.index(channel)
	buttons.playPause(button)	

for x in range (len(lPins)):
	GP.setup(lPins[x],GP.OUT)
	GP.output(lPins[x],1)	
	time.sleep(0.5)
	GP.output(lPins[x],0)
	GP.setup(bPins[x],GP.IN, pull_up_down=GP.PUD_DOWN)
	GP.add_event_detect(bPins[x], GP.RISING, callback=button_press,bouncetime=500)

while True:
	state= (buttons.getState())
	for x in range (6):
		if (state[x]==0):
			GP.output(lPins[x],0)
		elif(state[x]==2):
			GP.output(lPins[x],not(GP.input(lPins[x])))
		else:
			GP.output(lPins[x],1)
	try:	status = q.get_nowait()
	except Empty:
		status=""
	if (status=="@P 3\n"):
		buttons.stop()
	time.sleep(.5)
