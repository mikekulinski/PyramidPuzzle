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
from src.grid import Tile, Grid
from src.puzzle_sound import Note, PuzzleSound
from src.character import Character
from common.button import Button
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


#hi-hat, snare, bass drum, tambourine
instruments = [42, 38, 36, 54]
all_rests = [[Note(480, 0) for i in instruments] for _ in range(8)]

#character knows which tile its on
#receive tile, toggle that tile and the surrounding ones

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
        self.sound = PuzzleSound(self.beats, self.sched, self.synth, bank=128, loop=True)

        self.grid = Grid(num_tiles=9)
        self.add(self.grid)
        self.place_objects()

        self.character = Character(self)
        self.add(self.character)

    def is_valid_pos(self, pos):
        if pos[0] < 0 or pos[0] >= self.grid.num_tiles:
            return False
        elif pos[1] < 0 or pos[1] >= self.grid.num_tiles:
            return False

        return True

    def get_tile(self, pos):
        assert self.is_valid_pos(pos)
        return self.grid.get_tile(pos)

    def place_objects(self):
        self.objects = {}
        x_topleft, y_topleft = (2,5)

        for instrument_id in range(len(instruments)):
            for beat_id in range(4):
                size = (self.grid.tile_side_len, self.grid.tile_side_len)
                pos = self.grid.grid_to_pixel((x_topleft + beat_id, y_topleft - instrument_id))
                self.objects[(x_topleft + beat_id, y_topleft - instrument_id)] = SequencerTile(size, pos, beat_id, instrument_id, (x_topleft, y_topleft), self.beats)

        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def on_update(self):
        self.audio.on_update()

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            self.character.change_direction(button.value)
            self.character.move_player(new_location)
        elif button == Button.A:
            if self.character.grid_pos in self.objects:
                if isinstance(self.objects[self.character.grid_pos], SequencerTile):
                    self.on_button_press()
        elif button == Button.B:
            self.sound.toggle()

    def on_button_press(self):
        self.objects[self.character.grid_pos].on_button_press()
        self.objects[self.character.grid_pos].toggle_neighbors(self.objects, 4)
        self.sound.update_sounds(self.beats)
        self.sound.toggle()

    def on_layout(self, win_size):
        self.remove(self.character)
        self.remove(self.grid)
        self.grid.on_layout(win_size)
        for pos, obj in self.objects.items():
            self.remove(obj)
        
        self.add(self.grid)
        self.drum_graphics.on_layout(win_size)
        self.place_objects()
        self.character.on_layout(win_size)
        self.add(self.character)
        

class DrumPatternGraphics(InstructionGroup):
    def __init__(self, pattern):
        super().__init__()
        self.win_size = (Window.width, Window.height)
        self.pattern = pattern
        self.render_elements()

    def render_elements(self):
        size = self.win_size[0] / 6
        self.grid = CRectangle(cpos=(self.win_size[0] // 10, self.win_size[1] // 6),
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


class SequencerTile(Tile):
    active_color = Color(rgba=(0, 1, 0, 1))
    inactive_color = Color(rgba=(0, 0.4, 0, 1))
    rest = Note(480, 0)

    def __init__(self, size, pos, beat_idx, instrument_idx, topleft, beats):
        super().__init__(size, pos)
        
        self.beat_id = beat_idx
        self.instrument_id = instrument_idx
        self.instrument_pitch = instruments[instrument_idx]
        self.beats = beats
        self.beat_on = False
        self.beat_note = Note(480, self.instrument_pitch)
        self.topleft = topleft
        self.relative_pos = (beat_idx, instrument_idx)
        self.set_color(color=SequencerTile.inactive_color)

    def on_button_press(self):
        #toggle audio mapped to it
        #toggle tile appearance
        self.toggle()

    def toggle(self):
        #flip tile, toggle audio
        if self.beat_on:
            self.set_beats(rest=True)
            self.set_color(color=SequencerTile.inactive_color)
        else:
            self.set_beats(rest=False)
            self.set_color(SequencerTile.active_color)
        self.beat_on = not self.beat_on

    def set_beats(self, rest=True):
        for i in range(len(self.beats)):
            for j in range(len(self.beats)):
                if self.beat_id % 4 == i and self.instrument_id == j:
                    self.beats[i][j] = SequencerTile.rest if rest else self.beat_note 
        
    def toggle_neighbors(self, objects, sequencer_size):
        x,y = self.relative_pos
        x_left = None if x == 0 else x - 1
        x_right = None if x == sequencer_size - 1 else x + 1
        y_down = None if y == sequencer_size - 1 else y + 1
        y_up = None if y == 0 else y - 1
        coords = [(x_left, y), (x_right, y), (x, y_up), (x, y_down)]
        coords = [(self.topleft[0] + coord[0], self.topleft[1] - coord[1]) for coord in coords if None not in coord]
        for coord in coords:
            if coord in objects:
                objects[coord].toggle()

