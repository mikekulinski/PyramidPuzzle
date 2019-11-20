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
from src.piano_puzzle import MusicPuzzle
from src.bass_puzzle import BassPuzzle
from src.drums_puzzle import DrumsPuzzle
from src.grid import Tile, Grid, DoorTile
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


class CenterRoom(InstructionGroup):
    def __init__(self):
        super().__init__()
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

        size = (self.grid.tile_side_len, self.grid.tile_side_len)

        self.objects[(0, 4)] = DoorTile(
            size, self.grid.grid_to_pixel((0, 4)), MusicPuzzle(self)
        )
        self.objects[(4, 0)] = DoorTile(
            size, self.grid.grid_to_pixel((4, 0)), BassPuzzle(self)
        )
        self.objects[(8, 4)] = DoorTile(
            size, self.grid.grid_to_pixel((8, 4)), DrumsPuzzle(self)
        )
        self.objects[(4, 8)] = DoorTile(
            size, self.grid.grid_to_pixel((4, 8)), DrumsPuzzle(self)
        )

        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def on_update(self):
        pass

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            self.character.change_direction(button.value)
            self.character.move_player(new_location)
            if self.character.grid_pos in self.objects:
                if isinstance(self.objects[self.character.grid_pos], DoorTile):
                    return self.objects[self.character.grid_pos].other_room

    def on_layout(self, win_size):
        self.remove(self.character)
        self.remove(self.grid)
        self.grid.on_layout(win_size)
        for pos, obj in self.objects.items():
            self.remove(obj)

        self.add(self.grid)
        self.place_objects()
        self.character.on_layout(win_size)
        self.add(self.character)

