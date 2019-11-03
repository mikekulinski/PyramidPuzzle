import sys

sys.path.append("..")
from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup, CRectangle

from common.audio import Audio
from common.mixer import Mixer
from common.note import NoteGenerator, Envelope
from common.wavegen import WaveGenerator, SpeedModulator
from common.wavesrc import WaveBuffer, WaveFile, make_wave_buffers

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate

from random import randint, random
import numpy as np

notes = (
    (0.25, 60),
    (0.25, 72),
    (0.25, 71),
    (0.25, 67),
    (0.25, 69),
    (0.25, 71),
    (0.25, 0),
    (0.25, 72),
)
pitch_mappings = {60: "C", 62: "D", 64: "E", 65: "F", 67: "G", 69: "A", 71: "B"}
note_names = "CDEFGAB"
notes_w_staff_lines = "EGBD"
staff_mappings = dict()

# will have access to note+octave, C4 = 0
# put music bar in instruction group for mike to use
# when receiving instructions from controller, change note object and graphics


class MusicPuzzle(InstructionGroup):
    def __init__(self):
        super().__init__()
        self.animations = AnimGroup()
        self.music_bar = MusicBar(notes)
        self.animations.add(self.music_bar)
        self.add(self.animations)

        self.audio = Audio(2)
        self.mixer = Mixer()
        self.mixer.set_gain(0.2)
        self.audio.set_generator(self.mixer)

    def on_update(self):
        self.animations.on_update()
        self.audio.on_update()

    def on_layout(self, win_size):
        pass

    def play(self):
        self.music_bar.play()


class MusicBar(InstructionGroup):
    def __init__(self, notes_list):
        super().__init__()

        self.height = Window.height * 3 / 4
        self.staff_lines_height = (Window.height / 4) / (1.5 * 5)
        self.h = (Window.height / 4) / 6

        self.now_bar = Line(points=(10, self.height, 10, Window.height))
        self.now_bar_pos = KFAnim((0, 10), (3, Window.width))
        self.border = Line(points=(0, self.height, Window.width, self.height))
        self.actual_notes = notes_list
        self.notes_width = Window.width - 120
        self.notes_start = 120
        self.place_notes()
        # loop thru all notes and map positions to them--only draw lines for certain ones
        self.staff_lines = []
        for i in range(6):
            height = self.height + self.h + self.staff_lines_height * i
            self.staff_lines.append(Line(points=(0, height, Window.width, height)))
            staff_mappings

        self.add(self.now_bar)
        self.add(self.border)
        for line in self.staff_lines:
            self.add(line)
        self.clef = Rectangle(
            source="treble_clef_white.png",
            pos=(30, self.height),
            size=(70, self.height / 3.75),
        )
        self.add(self.clef)
        self.time = 0
        self.now_bar_moving = False

    def play(self):
        self.now_bar_moving = True

    def place_notes(self):
        num_measures = int(sum(note[0] for note in self.actual_notes))
        note_index = 0
        # place all measure lines
        x_start = self.notes_start
        for i in range(num_measures):
            measure = []
            measure_beats = 0
            x_end = self.notes_start + self.notes_width * (i + 1) / num_measures
            while measure_beats < 1:
                duration, pitch = self.actual_notes[note_index]
                self.add(
                    Ellipse(
                        size=(50, 50),
                        pos=(
                            x_start + (measure_beats) * (x_end - x_start),
                            self.height,
                        ),
                    )
                )
                measure_beats += duration
                note_index += 1
            self.add(Line(points=(x_end, self.height, x_end, Window.height)))
            x_start = x_end

    def on_update(self, dt):
        if self.now_bar_moving:
            pos = self.now_bar_pos.eval(self.time)
            self.now_bar.points = (pos, self.height, pos, Window.height)
            self.time += dt
            if pos == Window.width:
                self.time = 0
                self.now_bar_moving = False
                pos = self.now_bar_pos.eval(self.time)
                self.now_bar.points = (pos, self.height, pos, Window.height)


if __name__ == "__main__":
    run(MainWidget)
