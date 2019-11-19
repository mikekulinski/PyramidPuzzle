# common imports
import sys

import numpy as np
from kivy.core.window import Window
from kivy.graphics import Color, Line, PopMatrix, PushMatrix, Rectangle, Translate
from kivy.graphics.instructions import InstructionGroup

sys.path.append("..")


class Tile(InstructionGroup):
    border_color = (0.6, 0.3, 0, 1)
    base_color = (1, 0.9, 0.8, 1)
    active_color = (1, 0.9, 0.8, 1)
    inactive_color = (0.8, 0.4, 0, 1)

    def __init__(
        self, size=(150, 150), pos=(200, 200), icon_source=None, on_stand=None
    ):
        super().__init__()

        self.on_stand = on_stand

        # inside rectangle coordinates
        self.size = np.array(size)
        self.pos = np.array(pos)
        self.icon_source = icon_source

        # inside part
        if self.on_stand is not None:
            self.inside_color = Color(rgba=Tile.inactive_color)
            self.is_switch = True
            self.is_active = False
        else:
            self.inside_color = Color(rgba=Tile.base_color)
            self.is_switch = False
            self.is_active = False
        self.add(self.inside_color)
        self.inside_rect = Rectangle(
            size=self.size, pos=self.pos, source=self.icon_source
        )
        self.add(self.inside_rect)

        # border of button
        self.add(Color(rgba=Tile.border_color))
        self.add(Line(rectangle=(pos[0], pos[1], size[0], size[1])))

    def activate(self):
        self.is_active = True
        self.set_color(Tile.active_color)
        self.on_stand()

    def deactivate(self):
        self.is_active = False
        self.set_color(Tile.inactive_color, self.icon_source)

    def set_color(self, color, source=None):
        self.remove(self.inside_rect)

        self.inside_color = Color(rgba=color)
        self.add(self.inside_color)
        self.inside_rect = Rectangle(size=self.size, pos=self.pos, source=source)
        self.add(self.inside_rect)

        # border of button
        self.add(Color(rgba=Tile.border_color))
        self.add(Line(rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1])))


class Grid(InstructionGroup):
    def __init__(self, num_tiles=9, objects=[]):
        self.win_size = (Window.width, Window.height)
        self.num_tiles = num_tiles
        self.objects = objects

        self.calculate_dims()
        self.place_tiles()
        for loc, icon, callback in self.objects:
            self.place_object(loc, icon, callback)

    def calculate_dims(self):
        # Finds the largest grid size that fits the current dimensions
        grid_margin = 20
        self.grid_side_len = min(
            self.win_size[0] - 2 * grid_margin, self.win_size[1] - 2 * grid_margin
        )
        self.tile_side_len = self.grid_side_len / self.num_tiles

        self.pos = (
            int((self.win_size[0] / 2) - self.grid_side_len / 2),
            int(self.win_size[1] / 2 - self.grid_side_len / 2),
        )

    def place_tiles(self):
        # locate entire grid to position pos
        self.add(PushMatrix())
        self.add(Translate(*self.pos))

        self.tiles = []
        for r in range(self.num_tiles):
            self.tiles.append([])
            for c in range(self.num_tiles):
                tile = Tile(
                    size=(self.tile_side_len, self.tile_side_len),
                    pos=(c * self.tile_side_len, r * self.tile_side_len),
                )

                self.tiles[r].append(tile)
                self.add(tile)

        self.add(PopMatrix())

    def place_object(self, loc, icon, callback):
        r, c = loc
        old_tile = self.tiles[r][c]
        self.remove(old_tile)
        new_tile = Tile(
            size=(self.tile_side_len, self.tile_side_len),
            pos=(c * self.tile_side_len, r * self.tile_side_len),
            icon_source=icon,
            on_stand=callback,
        )
        self.tiles[r][c] = new_tile
        self.add(new_tile)

    def get_tile(self, loc):
        r, c = loc
        return self.tiles[r][c]

    def on_layout(self, win_size):
        for row in self.tiles:
            for tile in row:
                self.remove(tile)

        self.win_size = win_size

        self.calculate_dims()
        self.place_tiles()
        for loc, icon, callback in self.objects:
            self.place_object(loc, icon, callback)
