# common imports
from kivy.graphics import Color
from kivy.graphics.instructions import InstructionGroup

from common.gfxutil import CRectangle
from src.grid import Switch

FLOOR_SIZE = 9


class Character(InstructionGroup):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.grid_pos = (0, 0)
        self.current_tile = self.game.grid.get_tile(self.grid_pos)
        self.sprite = CRectangle()
        self.add(self.sprite)

        self.move_player((FLOOR_SIZE // 2, FLOOR_SIZE // 2))

    def get_valid_pos(self, grid_pos):
        new_pos = list(grid_pos)
        # Check if this is a valid move, if not move them back in bounds
        if grid_pos[0] < 0:
            new_pos[0] = 0
        elif grid_pos[0] >= FLOOR_SIZE:
            new_pos[0] = FLOOR_SIZE - 1

        if grid_pos[1] < 0:
            new_pos[1] = 0
        elif grid_pos[1] >= FLOOR_SIZE:
            new_pos[1] = FLOOR_SIZE - 1

        return tuple(new_pos)

    def move_player(self, grid_pos):
        new_pos = self.get_valid_pos(grid_pos)

        if isinstance(self.current_tile, Switch) and self.current_tile.is_active:
            self.current_tile.deactivate()

        self.remove(self.sprite)

        self.grid_pos = new_pos
        self.current_tile = self.game.grid.get_tile(self.grid_pos)
        tile_size = self.current_tile.size
        self.pixel_pos = self.current_tile.pos + (tile_size // 2) + self.game.grid.pos

        self.size = tile_size // 3

        self.color = Color(1, 0, 0)
        self.add(self.color)
        self.sprite = CRectangle(cpos=self.pixel_pos, csize=self.size)
        self.add(self.sprite)

        if isinstance(self.current_tile, Switch) and not self.current_tile.is_active:
            self.current_tile.activate()

    def on_layout(self, win_size):
        self.move_player(self.grid_pos)
