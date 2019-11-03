# common imports
import sys

sys.path.append("..")
from common.core import BaseWidget, run
from common.gfxutil import (
    topleft_label,
    Cursor3D,
    AnimGroup,
    KFAnim,
    scale_point,
    resize_topleft_label,
    CEllipse,
    CRectangle,
)
from kivy.graphics import (
    Color,
    Ellipse,
    Rectangle,
    Line,
    Translate,
    PushMatrix,
    PopMatrix,
)
from common.synth import Synth
from common.audio import Audio

from kivy.core.window import Window
from kivy.graphics.instructions import InstructionGroup
import numpy as np

import pygame

from pygame.locals import JOYAXISMOTION, JOYBUTTONDOWN, JOYBUTTONUP, JOYHATMOTION, QUIT
import time

FLOOR_SIZE = 9


class Character(InstructionGroup):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.grid_pos = (FLOOR_SIZE // 2, FLOOR_SIZE // 2)
        self.sprite = CRectangle()
        self.add(self.sprite)

        self.move_player(self.grid_pos)

    def set_valid_pos(self, grid_pos):
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

        self.grid_pos = tuple(new_pos)

    def move_player(self, grid_pos):
        self.remove(self.sprite)
        self.set_valid_pos(grid_pos)

        current_tile = self.game.tiles[self.grid_pos[0]][self.grid_pos[1]]
        tile_size = current_tile.size
        self.pixel_pos = current_tile.pos + (tile_size // 2) + self.game.pos

        self.size = tile_size // 3

        self.color = Color(1, 0, 0)
        self.add(self.color)
        self.sprite = CRectangle(cpos=self.pixel_pos, csize=self.size)
        self.add(self.sprite)

    def on_layout(self, win_size):
        self.remove(self.sprite)

        self.move_player(self.grid_pos)


class Tile(InstructionGroup):
    border_color = (0.4, 0.6, 0.5)
    active_color = (0.4, 0.6, 0.3)
    on_color = (0.4, 0.6, 0.7)

    def __init__(self, size=(150, 150), pos=(200, 200)):
        super().__init__()

        # button state
        self.is_on = False
        self.active_progress = 0

        # bounds of this button, for intersection detection
        self.x_bounds = (pos[0], pos[0] + size[0])
        self.y_bounds = (pos[1], pos[1] + size[1])

        # inside rectange coordinates

        self.size = np.array(size)
        self.pos = np.array(pos)
        # inside part
        self.inside_color = Color(hsv=Tile.active_color)
        self.add(self.inside_color)
        self.inside_rect = Rectangle(size=(0, 0), pos=self.pos)
        self.add(self.inside_rect)

        # border of button
        self.add(Color(hsv=Tile.border_color))
        self.add(Line(rectangle=(pos[0], pos[1], size[0], size[1])))


class Game(InstructionGroup):
    def __init__(self):
        super().__init__()

        self.create_grid((Window.width, Window.height))
        self.character = Character(self)
        self.add(self.character)

    def create_grid(self, win_size):
        # Add them back in at the right position
        grid_margin = 20
        grid_side_len = min(
            win_size[0] - 2 * grid_margin, win_size[1] - 2 * grid_margin
        )
        size = (grid_side_len, grid_side_len)

        # grid geometry calculations
        tile_side_len = grid_side_len / FLOOR_SIZE
        tile_size = (tile_side_len, tile_side_len)

        self.pos = (
            int(win_size[0] / 2 - grid_side_len / 2),
            int(win_size[1] / 2 - grid_side_len / 2),
        )

        # locate entire grid to position pos
        self.add(PushMatrix())
        self.add(Translate(*self.pos))

        self.tiles = [
            [
                Tile(size=tile_size, pos=(x * tile_side_len, y * tile_side_len))
                for x in range(FLOOR_SIZE)
            ]
            for y in range(FLOOR_SIZE)
        ]
        for row in self.tiles:
            for tile in row:
                self.add(tile)

        self.add(PopMatrix())

    def on_layout(self, win_size):

        # Remove all old tiles
        for row in self.tiles:
            for tile in row:
                self.remove(tile)

        self.create_grid(win_size)
        self.character.on_layout(win_size)
