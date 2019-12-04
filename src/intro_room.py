from kivy.graphics import PopMatrix, PushMatrix, Translate, Color, Rectangle
from kivy.core.window import Window
from common.gfxutil import CLabelRect

from src.button import Button
from src.center_room import CenterRoom
from src.grid import PyramidTile, Tile
from src.puzzle import Puzzle


class IntroRoom(Puzzle):
    def __init__(self):
        super().__init__()
        self.win_size = (Window.width, Window.height)
        self.place_objects()
        self.create_instructions()

    def create_instructions(self):
        margin = self.grid.tile_side_len // 2
        self.instructions_window_color = Color(rgba=(1, 1, 1, 1))
        self.instructions_window = Rectangle(
            pos=(margin, margin),
            size=(
                self.grid.grid_side_len - 2 * margin,
                3 * self.grid.tile_side_len - 2 * margin,
            ),
        )
        self.instructions_text_color = Color(rgba=(0, 0, 0, 1))
        self.instructions_text = CLabelRect(
            (self.win_size[0] // 2, self.win_size[1] // 6),
            "Move around the room with the arrow keys\n"
            + "Press 'a' to interact with objects",
            40,
        )

        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        self.add(self.instructions_window_color)
        self.add(self.instructions_window)

        self.add(PopMatrix())

        self.add(self.instructions_text_color)
        self.add(self.instructions_text)

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        pass

    def place_objects(self):
        self.objects = {}

        size = (3 * self.grid.tile_side_len, 3 * self.grid.tile_side_len)
        pos = self.grid.grid_to_pixel((8, 4))
        pos = (pos[0] - 2 * self.grid.tile_side_len, pos[1])

        self.objects[(8, 4)] = PyramidTile(size, pos, CenterRoom, "./data/pyramid.png")
        for i in range(9):
            for j in range(5,9):
                self.grid.get_tile((i,j)).set_color(color=Color(rgb=(.5, .8, .9)))
            for j in range(5):
                self.grid.get_tile((i,j)).set_color(color=Tile.base_color, source="./data/sand3.png")

        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            self.character.change_direction(button.value)
            self.character.move_player(new_location)
            if self.character.grid_pos in self.objects:
                if isinstance(self.objects[self.character.grid_pos], PyramidTile):
                    return self.objects[self.character.grid_pos].other_room()

    def on_update(self):
        pass

    def on_layout(self, win_size):
        self.win_size = win_size
        self.remove(self.character)
        self.remove(self.grid)
        self.grid.on_layout(win_size)
        for pos, obj in self.objects.items():
            self.remove(obj)
        self.remove(self.instructions_window)
        self.remove(self.instructions_text)

        self.add(self.grid)

        self.character.on_layout(win_size)
        self.add(self.character)

        self.place_objects()
        self.create_instructions()

