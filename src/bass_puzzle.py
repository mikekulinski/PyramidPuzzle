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

        self.grid = Grid(num_tiles=9)
        self.add(self.grid)

        self.place_mummy((4, 8))

        # Add the character to the game
        self.character = Character(self)
        self.add(self.character)

    def place_mummy(self, loc):
        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        size = (self.grid.tile_side_len, self.grid.tile_side_len)
        pos = self.grid.grid_to_pixel(loc)
        self.mummy = Mummy(size, pos, self.on_interact_mummy, "./data/mummy.jpg")
        self.add(self.mummy)

        self.add(PopMatrix())

    def on_interact_mummy(self):
        print("Interacted with mummy!")

    def on_update(self):
        pass

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            self.character.move_player(new_location)
        elif button == Button.A:
            # TODO keep track of direction and try to interact in front of character
            self.character.interact()

    def on_layout(self, win_size):
        self.remove(self.character)
        self.remove(self.mummy)
        self.remove(self.grid)

        self.grid.on_layout(win_size)
        self.add(self.grid)

        self.place_mummy((4, 8))

        self.character.on_layout(win_size)
        self.add(self.character)
