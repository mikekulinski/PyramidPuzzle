# lab5.py


# common imports
import sys

sys.path.append("..")
from common.core import BaseWidget, run
from common.gfxutil import (
    topleft_label,
    Cursor3D,
    AnimGroup,
    KFAnim,
    scale_point,
    CEllipse,
)
from common.synth import Synth
from common.audio import Audio

from kivy.core.window import Window
import numpy as np

# Choose your mode:
# MODE = 'kinect'
MODE = "leap"

if MODE == "leap":
    from common.leap import getLeapInfo, getLeapFrame

if MODE == "kinect":
    from common.kinect import Kinect


# Create a "one-handed Leap Theramin" according to this spec:
#
#  a. When the hand breaks through the XY plane (at some value of z), a note will play.
#     The pitch of the note is determined by the height of the hand, and mapped to a
#     1-octave c-major scale. The note turns off when the hand is pulled out of the XY plane.
#     Also, choose a sustaining sound - like a string, wind, or brass instrument.
#
#  b. Modify the system so as the hand moves up and down, the sounding note changes according
#     to the same mapping of height to c-major scale.
#
#  c. Add volume control, mapping the x position of the hand to volume. Recall that volume is
#     sent as: synth.cc(channel, 7, v) where v = [0, 127]


class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth("../data/FluidR3_GM.sf2")
        self.audio.set_generator(self.synth)

        self.channel = 1
        self.program = (0, 44)
        self.playing = False
        self.pitches = [60, 62, 64, 65, 67, 69, 71, 72]
        self.current_pitch = None

        self.synth.program(self.channel, self.program[0], self.program[1])

        if MODE == "kinect":
            self.kinect = Kinect()
            self.kinect.add_joint(Kinect.kRightHand)

        # set up size / location of 3DCursor object
        kMargin = Window.width * 0.05
        kCursorSize = Window.width - 2 * kMargin, Window.height - 2 * kMargin
        kCursorPos = kMargin, kMargin

        self.hand_disp = Cursor3D(kCursorSize, kCursorPos, (0.2, 0.6, 0.2))
        self.canvas.add(self.hand_disp)

        self.label = topleft_label()
        self.add_widget(self.label)

    def on_update(self):
        self.audio.on_update()

        self.label.text = ""

        if MODE == "leap":
            self.label.text += str(getLeapInfo()) + "\n"
            leap_frame = getLeapFrame()
            pt = leap_frame.hands[0].palm_pos
            norm_pt = scale_point(pt, kLeapRange)

        elif MODE == "kinect":
            self.kinect.on_update()
            pt = self.kinect.get_joint(Kinect.kRightHand)
            norm_pt = scale_point(pt, kKinectRange)

        self.hand_disp.set_pos(norm_pt)
        self.set_pitch(norm_pt[1])
        self.set_volume(norm_pt[0])

        self.label.text += "x=%d y=%d z=%d\n" % (pt[0], pt[1], pt[2])
        self.label.text += "x=%.2f y=%.2f z=%.2f\n" % (
            norm_pt[0],
            norm_pt[1],
            norm_pt[2],
        )

    def get_pitch_index(self, y_pos):
        index = int(y_pos * 7.99)
        return self.pitches[index]

    def set_pitch(self, y_pos):
        if y_pos != 0:
            new_pitch = self.get_pitch_index(y_pos)
            if self.current_pitch != new_pitch:
                if self.current_pitch != None:
                    self.synth.noteoff(self.channel, self.current_pitch)
                self.synth.noteon(self.channel, new_pitch, 100)
                self.current_pitch = new_pitch
                self.playing = True
        elif self.playing:
            self.synth.noteoff(self.channel, self.current_pitch)
            self.current_pitch = None
            self.playing = False

    def get_volume_level(self, x_pos):
        return int(x_pos * 127)

    def set_volume(self, x_pos):
        volume = self.get_volume_level(x_pos)
        self.synth.cc(self.channel, 7, volume)


# for use with scale_point:
# x, y, and z ranges to define a 3D bounding box
kKinectRange = ((-250, 700), (-200, 700), (-500, 0))
kLeapRange = ((-250, 250), (100, 500), (-200, 250))


run(MainWidget)
