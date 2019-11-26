from kivy.graphics import PopMatrix, PushMatrix, Translate

from src.button import Button
from src.center_room import CenterRoom
from src.grid import PyramidTile
from src.puzzle import Puzzle


class IntroRoom(Puzzle):
    def __init__(self):
        super().__init__()
        self.place_objects()

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        pass

    def place_objects(self):
        self.objects = {}

        size = (3 * self.grid.tile_side_len, 3 * self.grid.tile_side_len)
        pos = self.grid.grid_to_pixel((8, 4))
        pos = (pos[0] - 2 * self.grid.tile_side_len, pos[1])

        self.objects[(8, 4)] = PyramidTile(
            size, pos, CenterRoom(), "./data/pyramid.png"
        )

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
                    return self.objects[self.character.grid_pos].other_room

    def on_update(self):
        pass

    def on_layout(self, win_size):
        self.remove(self.character)
        self.remove(self.grid)
        self.grid.on_layout(win_size)
        for pos, obj in self.objects.items():
            self.remove(obj)

        self.add(self.grid)

        self.character.on_layout(win_size)
        self.add(self.character)

        self.place_objects()
