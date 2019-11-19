import sys

sys.path.append("..")
from common.core import BaseWidget, run, lookup
from common.gfxutil import (
    topleft_label,
    CEllipse,
    KFAnim,
    AnimGroup,
    CRectangle,
    CLabelRect,
)

from common.audio import Audio
from common.mixer import Mixer
from common.note import NoteGenerator, Envelope
from common.wavegen import WaveGenerator, SpeedModulator
from common.wavesrc import WaveBuffer, WaveFile, make_wave_buffers
from common.synth import Synth

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from PuzzleSound import Note, PuzzleSound
from common.clock import (
    Clock,
    SimpleTempoMap,
    AudioScheduler,
    tick_str,
    kTicksPerQuarter,
    quantize_tick_up,
)

from random import randint, random, choice
import numpy as np

#make audio loop so notes change in real time
#map a 4 x 4 grid x axis is beat and y axis is instrument (hi-hat, bass drum, etc.)
#no concept of actual sound

pattern = [
            "X X ",
            " X X",
            "X   ",
            " X X"
            ]


class MainWidget(BaseWidget):
    def __init__(self):
        super().__init__()
        self.music_puzzle = DrumsPuzzle()
        self.canvas.add(self.music_puzzle)

    def on_update(self):
        self.music_puzzle.on_update()

    def on_key_down(self, keycode, modifiers):
        pass
        # if keycode[1] == "p":
        #     # move now bar across music bar
        #     self.music_puzzle.play(actual=True)


class DrumsPuzzle(InstructionGroup):
    def __init__(self):
        super().__init__()
        self.audio = Audio(2)
        self.drum_graphics = DrumPatternGraphics(pattern)
        self.add(self.drum_graphics)
        self.synth = Synth("./data/FluidR3_GM.sf2")

        self.tempo_map = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        self.sched.set_generator(self.synth)
        self.audio.set_generator(self.sched)
        #self.user_sound = PuzzleSound(user_notes, self.sched, self.synth, 128, 0)


    def on_update(self):
        pass
        #self.audio.on_update()

    def on_layout(self, win_size):
        self.drum_graphics.on_layout(win_size)
        pass

def DrumPatternGraphics(InstructionGroup):
    def __init__(self, pattern):
        super().__init__()
        self.win_size = (Window.width, Window.height)
        self.pattern = pattern

    def render_elements(self):
        self.grid = CRectangle(cpos=(self.win_size[0] // 4, self.win_size[1] // 8),
            csize=(self.win_size[0] // 4, self.win_size[1] // 4),
        )
        self.add(self.grid)

    def on_update(self):
        pass

    def on_layout(self, win_size):
        #self.clear()
        self.win_size = win_size
        #self.render_elements()
        pass


if __name__ == "__main__":
    run(MainWidget)
