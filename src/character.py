# common imports
import numpy as np
from kivy.graphics import Color
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color
from common.gfxutil import CRectangle
from src.button import Button


class Character(InstructionGroup):
    def __init__(self, puzzle):
        super().__init__()
        self.puzzle = puzzle

        self.direction = (0, 1)
        self.source = "./data/character_down.png"
        self.grid_pos = (
            self.puzzle.grid.num_tiles // 2,
            self.puzzle.grid.num_tiles // 2,
        )
        self.sprite = CRectangle()
        self.add(Color(1, 1, 1))
        self.add(self.sprite)
        self.move_player(self.grid_pos)

    def move_player(self, new_pos):
        self.remove(self.sprite)
        is_valid_pos = self.puzzle.is_valid_pos(new_pos)
        if is_valid_pos:
            self.grid_pos = new_pos
            self.current_tile = self.puzzle.get_tile(self.grid_pos)
            tile_size = np.array(self.current_tile.size)
            self.pixel_pos = (
                self.current_tile.pos + (tile_size // 2) + self.puzzle.grid.pos
            )

            self.size = tile_size

        self.sprite = CRectangle(
            cpos=self.pixel_pos, csize=self.size, source=self.source
        )

        self.add(Color(1, 1, 1))
        self.add(self.sprite)

    def change_direction(self, direction):
        self.direction = direction
        if self.direction == Button.UP.value:
            self.source = "./data/character_up.png"
        elif self.direction == Button.DOWN.value:
            self.source = "./data/character_down.png"
        elif self.direction == Button.LEFT.value:
            self.source = "./data/character_left.png"
        elif self.direction == Button.RIGHT.value:
            self.source = "./data/character_right.png"

    def interact(self):
        in_front = (
            self.grid_pos[0] + self.direction[0],
            self.grid_pos[1] + self.direction[1],
        )
        # TODO REMOVE THE TRY, IT CAUSES PROBLEMS
        try:
            obj = self.puzzle.objects[in_front]
            obj.interact()
        except Exception as e:
            print(type(e), e)
            print("Tile not interactable")

    def on_layout(self, win_size):
        self.move_player(self.grid_pos)
