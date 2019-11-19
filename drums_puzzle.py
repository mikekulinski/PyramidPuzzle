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
            "X  X",
            " XX ",
            "XX  ",
            "  X "
            ]
#pressing (0,0) toggles (0,2) and (2,0)
#pressing (1,0) toggles (0,0) and (1,0)
#pressing () 


#hi-hat, snare, bass drum, tambourine
instruments = [42, 38, 36, 54]
all_rests = [Note(480, 0) for _ in range(8)]

#character knows which tile its on
#receive tile, toggle that tile and the surrounding ones
class MainWidget(BaseWidget):
    def __init__(self):
        super().__init__()
        self.music_puzzle = DrumsPuzzle()
        self.canvas.add(self.music_puzzle)

    def on_update(self):
        self.music_puzzle.on_update()

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "p":
            self.music_puzzle.on_p()


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
    
        self.beats = all_rests
        self.sound = PuzzleSound(self.beats, self.sched, self.synth, bank=128, preset=0)


    def on_update(self):
        self.audio.on_update()

    def on_layout(self, win_size):
        self.drum_graphics.on_layout(win_size)
        pass

    def on_p(self):
        self.sound.toggle()

class DrumPatternGraphics(InstructionGroup):
    def __init__(self, pattern):
        super().__init__()
        self.win_size = (Window.width, Window.height)
        self.pattern = pattern
        self.render_elements()

    def render_elements(self):
        size = self.win_size[0] / 5
        self.grid = CRectangle(cpos=(self.win_size[0] // 5, self.win_size[1] // 5),
            csize=(size, size),
        )
        self.squares = []
        square_size = size / 4
        top_left = (self.grid.cpos[0] - size/2 + square_size/2, self.grid.cpos[1] + size/2 - square_size/2)
        self.add(self.grid)
        for i in range(len(pattern)):
            for j in range(len(pattern[i])):
                if pattern[i][j] == "X":
                    sq = CRectangle(cpos=(top_left[0] + j * square_size, top_left[1] - i * square_size),
                                        csize=(square_size, square_size),
                                    )
                    self.add(Color(rgb=(0,1,0)))
                    self.add(sq)
                    self.squares.append(sq)

    def on_layout(self, win_size):
        self.clear()
        self.win_size = win_size
        self.render_elements()


class SequencerTile(InstructionGroup):
    def __init__(self, size, position):
        super().__init__()
        instrument_id, self.beat = position
        self.instrument_pitch = instruments[instrument_id]
        self.beats[beat::4] = [Note(480, self.instrument_pitch) for _ in range(self.beats[beat::4])]
        self.rest_beats = [Note(480, self.instrument_pitch) for _ in range(self.beats[beat::4])]

    def on_button_press(self):
        #toggle audio mapped to it as well as all audio around it
        #toggle tile appearance
        pass

    def tiles_to_flip(self):
        pass



if __name__ == "__main__":
    run(MainWidget)
