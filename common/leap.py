# leap.py

from ctypes import *
from ctypes.util import find_library

from collections import namedtuple
import os
import numpy as np
import platform

system  = platform.system()

# find correct library to load based on system
if system == 'Windows':
    lib_path, lib_file = 'leap/x64', 'LeapC.dll'
elif system == 'Darwin':
    lib_path, lib_file = 'leap/osx', 'libLeapC.so'
elif system == 'Linux':
    lib_path, lib_file = 'leap/linux', './libLeapC.so'
else:
    print('Unknown system:', system)

# lib_path is actually relative to this here file (leap.py)
lib_path = os.path.join( os.path.dirname(__file__), lib_path )

# this is done for Windows and Linux. cd to the directory with the library
# so that sibling dlls can be loaded from the cwd.
prev_dir = os.getcwd()
os.chdir(lib_path)
_leap = CDLL(lib_file)
os.chdir(prev_dir)

# structures from the LeapC code. These must match exactly with the structures in LeapC.cpp
class cLeapInfo(Structure):
    _fields_ = [
    ('service', c_bool),
    ('connected', c_bool),
    ('has_focus', c_bool),
    ]

class cLeapFinger(Structure):
    _fields_ = [
        ('id', c_int),
        ('pos', c_float*3),
        ]

class cLeapHand(Structure):
    _fields_ = [
        ('id', c_int),
        ('palm_pos', c_float*3),
        ('fingers', cLeapFinger*5),
        ]

class cLeapFrame(Structure):
    _fields_ = [
        ('valid', c_bool),
        ('hands', cLeapHand*2),
    ]


# set up function args
_leap.getInfo.argtypes  = [ POINTER(cLeapInfo) ]
_leap.getFrame.argtypes = [ POINTER(cLeapFrame) ]

def toArray(p):
    return np.array((p[0], p[1], p[2]))

# public interface:
LeapInfo = namedtuple('LeapInfo', 'service connected has_focus')

class LeapHand(namedtuple('LeapHand', 'id palm_pos fingers')):
    def __str__(self):
        'add a custom printing for a hand so it looks nicer'
        fingers = '\n    ' + '\n    '.join([str(f) for f in self.fingers])
        return 'LeapHand(id={}, palm_pos={}, fingers=[{}])'.format(self.id, self.palm_pos, fingers)

class LeapFrame(namedtuple('LeapFrame', 'valid hands')):
    def __str__(self):
        'add a custom printing for a frame so it looks nicer'
        hands = '\n  ' + '\n  '.join([str(h) for h in self.hands])
        return 'LeapFrame(valid={}, hands=[{}])'.format(self.valid, hands)


# public functions
def getLeapInfo():
    info = cLeapInfo()
    _leap.getInfo(info)

    return LeapInfo(service=info.service, connected=info.connected, has_focus=info.has_focus)

def getLeapFrame():
    frame = cLeapFrame()
    _leap.getFrame(frame)

    hands = [LeapHand(id=h.id, 
                      palm_pos=toArray(h.palm_pos),
                      fingers=[toArray(f.pos) for f in h.fingers])
                for h in frame.hands]
    return LeapFrame(valid=frame.valid, hands=hands)

_leap.init()

def run_test():
    import time

    while 1:

        info = getLeapInfo()
        frame = getLeapFrame()

        print(info)
        print(frame)

        time.sleep(.5)


if __name__ == "__main__":
    run_test()
