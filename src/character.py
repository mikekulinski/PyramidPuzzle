# common imports
import numpy as np
from kivy.graphics import Color
from kivy.graphics.instructions import InstructionGroup

from common.gfxutil import CRectangle
from common.button import Button


class Character(InstructionGroup):
    def __init__(self, puzzle):
        super().__init__()
        self.puzzle = puzzle

        self.direction = Button.UP
        self.grid_pos = (
            self.puzzle.grid.num_tiles // 2,
            self.puzzle.grid.num_tiles // 2,
        )
        self.add(Color(1, 0, 0))
        self.sprite = CRectangle()
        self.add(self.sprite)
        self.move_player(self.grid_pos)

    def move_player(self, new_pos):
        self.remove(self.sprite)
        if self.puzzle.is_valid_pos(new_pos):
            self.grid_pos = new_pos
            self.current_tile = self.puzzle.grid.get_tile(self.grid_pos)
            tile_size = np.array(self.current_tile.size)
            self.pixel_pos = (
                self.current_tile.pos + (tile_size // 2) + self.puzzle.grid.pos
            )

            self.size = tile_size // 3
            self.sprite = CRectangle(cpos=self.pixel_pos, csize=self.size)

        self.add(Color(1, 0, 0))
        self.add(self.sprite)

    def change_direction(self, direction):
        self.direction = direction

    def on_layout(self, win_size):
        self.move_player(self.grid_pos)
