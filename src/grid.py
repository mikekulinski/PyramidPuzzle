from kivy.core.window import Window
from kivy.graphics import Color, Line, PopMatrix, PushMatrix, Rectangle, Translate
from kivy.graphics.instructions import InstructionGroup


class Tile(InstructionGroup):
    border_color = Color(rgba=(0.6, 0.3, 0, 0))
    base_color = Color(rgba=(1, 0.9, 0.8, 1))

    def __init__(self, size, pos):
        super().__init__()
        self.size = size
        self.pos = pos

        self.passable = True
        self.moveable = False
        self.inside_color = Tile.base_color
        self.inside_rect = Rectangle(size=self.size, pos=self.pos)
        self.add(self.inside_color)
        self.add(self.inside_rect)

        self.border_color = Tile.border_color
        self.border_line = Line(rectangle=(pos[0], pos[1], size[0], size[1]))
        self.add(self.border_color)
        self.add(self.border_line)

    def set_color(self, color, source=None):
        self.remove(self.inside_rect)
        self.remove(self.border_line)

        self.inside_color = Color(rgba=color.rgba)
        self.inside_rect = Rectangle(size=self.size, pos=self.pos, source=source)
        self.add(self.inside_color)
        self.add(self.inside_rect)

        self.add(self.border_color)
        self.add(self.border_line)


class Switch(Tile):
    active_color = Color(rgba=(1, 0.9, 0.8, 1))
    inactive_color = Color(rgba=(0.8, 0.4, 0, 1))

    def __init__(self, size, pos, on_stand, icon_source=None):
        super().__init__(size, pos)

        self.on_stand = on_stand
        self.icon_source = icon_source

        self.is_active = False
        self.set_color(color=Switch.inactive_color, source=self.icon_source)

    def activate(self):
        self.is_active = True
        self.set_color(Switch.active_color)
        self.on_stand()

    def deactivate(self):
        self.is_active = False
        self.set_color(color=Switch.inactive_color, source=self.icon_source)


class DoorTile(Tile):
    def __init__(self, size, pos, other_room, source=None):
        super().__init__(size, pos)
        self.set_color(color=Tile.base_color, source=source)
        self.other_room = other_room
        self.moveable = False


class PyramidTile(Tile):
    def __init__(self, size, pos, other_room, source=None):
        super().__init__(size, pos)
        self.set_color(color=Tile.base_color, source=source)
        self.other_room = other_room


class Grid(InstructionGroup):
    def __init__(self, num_tiles=9, objects=[]):
        super().__init__()
        self.win_size = (Window.width, Window.height)
        self.num_tiles = num_tiles
        self.objects = objects

        self.calculate_dims()
        self.place_tiles()
        for loc, obj in self.objects:
            self.place_object(loc, obj)
        self.place_walls()

    def calculate_dims(self):
        # Finds the largest grid size that fits the current dimensions
        grid_margin = 20
        self.grid_side_len = min(
            self.win_size[0] - 2 * grid_margin, self.win_size[1] - 2 * grid_margin
        )
        self.tile_side_len = self.grid_side_len / (self.num_tiles + 2)

        self.pos = (
            int((self.win_size[0] / 2) - self.grid_side_len / 2) + self.tile_side_len,
            int(self.win_size[1] / 2 - self.grid_side_len / 2) + self.tile_side_len,
        )

        self.left_wall_pos = (self.pos[0] * 3 / 4, self.pos[1])
        self.right_wall_pos = (self.pos[0] + self.grid_side_len, self.pos[1])

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
                tile.set_color(Color(1, 1, 1), source="./data/sand1.png")

                self.tiles[r].append(tile)
                self.add(tile)

        self.add(PopMatrix())

    def place_walls(self):
        # locate entire grid to position pos
        self.add(PushMatrix())
        self.add(Translate(*self.pos))

        self.walls = {}
        for i in range(9):
            # Sides
            self.walls[(-1, i)] = Wall(
                (self.tile_side_len, self.tile_side_len), self.grid_to_pixel((-1, i))
            )
            self.walls[(9, i)] = Wall(
                (self.tile_side_len, self.tile_side_len), self.grid_to_pixel((9, i))
            )
            self.walls[(i, -1)] = Wall(
                (self.tile_side_len, self.tile_side_len), self.grid_to_pixel((i, -1))
            )
            self.walls[(i, 9)] = Wall(
                (self.tile_side_len, self.tile_side_len), self.grid_to_pixel((i, 9))
            )

            # Corners
            self.walls[(-1, -1)] = Wall(
                (self.tile_side_len, self.tile_side_len), self.grid_to_pixel((-1, -1))
            )
            self.walls[(-1, 9)] = Wall(
                (self.tile_side_len, self.tile_side_len), self.grid_to_pixel((-1, 9))
            )
            self.walls[(9, 9)] = Wall(
                (self.tile_side_len, self.tile_side_len), self.grid_to_pixel((9, 9))
            )
            self.walls[(9, -1)] = Wall(
                (self.tile_side_len, self.tile_side_len), self.grid_to_pixel((9, -1))
            )

        for loc, wall in self.walls.items():
            self.add(wall)

        self.add(PopMatrix())

    def get_tile(self, pos):
        x, y = pos
        return self.tiles[y][x]

    def grid_to_pixel(self, pos):
        x, y = pos
        return (x * self.tile_side_len, y * self.tile_side_len)

    def on_layout(self, win_size):
        for row in self.tiles:
            for tile in row:
                self.remove(tile)
        for loc, wall in self.walls.items():
            self.remove(wall)

        self.win_size = win_size

        self.calculate_dims()
        self.place_walls()
        self.place_tiles()
        for loc, obj in self.objects:
            self.place_object(loc, obj)


class Wall(Tile):
    def __init__(self, size, pos):
        super().__init__(size, pos)
        self.moveable = False
        self.passable = False
        self.set_color(color=Tile.base_color, source="./data/brickfloor.png")

