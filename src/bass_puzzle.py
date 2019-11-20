from random import choice

from kivy.core.window import Window
from kivy.graphics import Color, Line, PopMatrix, PushMatrix, Rectangle, Translate
from kivy.graphics.instructions import InstructionGroup

from common.audio import Audio
from common.button import Button
from common.clock import AudioScheduler, SimpleTempoMap
from common.gfxutil import AnimGroup, CLabelRect, CRectangle, KFAnim
from common.synth import Synth
from src.grid import Tile, Grid
from src.puzzle_sound import Note, PuzzleSound
from src.character import Character


class Mummy(Tile):
    def __init__(self, size, pos, on_interact, icon_source):
        super().__init__(size, pos)
        self.on_interact = on_interact
        self.icon_source = icon_source

        self.set_color(color=Tile.base_color, source=self.icon_source)

    def interact(self):
        self.on_interact()


class BassPuzzle(InstructionGroup):
    def __init__(self):
        super().__init__()
        self.puzzle_on = False

        self.grid = Grid(num_tiles=9)
        self.add(self.grid)

        self.place_objects()

        # Add the character to the game
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

    def create_mummy(self, pos):
        size = (self.grid.tile_side_len, self.grid.tile_side_len)
        pos = self.grid.grid_to_pixel(pos)
        return Mummy(size, pos, self.on_interact_mummy, "./data/mummy.jpg")

    def place_objects(self):
        self.objects = {}
        self.mummy = self.create_mummy((4, 8))
        self.objects[(4, 8)] = self.mummy

        if self.puzzle_on:
            self.m1 = self.create_mummy((1, 4))
            self.m2 = self.create_mummy((3, 4))
            self.m3 = self.create_mummy((5, 4))
            self.m4 = self.create_mummy((7, 4))

            self.objects[(1, 4)] = self.m1
            self.objects[(3, 4)] = self.m2
            self.objects[(5, 4)] = self.m3
            self.objects[(7, 4)] = self.m4

        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def on_interact_mummy(self):
        self.puzzle_on = True
        print("Interacted with mummy!")
        for pos, obj in self.objects.items():
            self.remove(obj)
        self.place_objects()

    def on_update(self):
        pass

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            self.character.change_direction(button.value)
            self.character.move_player(new_location)
        elif button == Button.A:
            self.character.interact()

    def on_layout(self, win_size):
        self.remove(self.character)
        for pos, obj in self.objects.items():
            self.remove(obj)
        self.remove(self.grid)

        self.grid.on_layout(win_size)
        self.add(self.grid)

        self.place_objects()

        self.character.on_layout(win_size)
        self.add(self.character)
