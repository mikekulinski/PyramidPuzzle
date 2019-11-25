from kivy.graphics import PopMatrix, PushMatrix, Translate
from kivy.graphics.instructions import InstructionGroup

from src.button import Button
from src.character import Character
from src.drums_puzzle import DrumsPuzzle
from src.grid import DoorTile, Grid
from src.guitar_puzzle import GuitarPuzzle
from src.piano_puzzle import MusicPuzzle


class CenterRoom(InstructionGroup):
    def __init__(self):
        super().__init__()
        self.grid = Grid(num_tiles=9)
        self.add(self.grid)
        self.place_objects()

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

    def place_objects(self):
        self.objects = {}

        size = (self.grid.tile_side_len, self.grid.tile_side_len)

        self.objects[(0, 4)] = DoorTile(
            size, self.grid.grid_to_pixel((0, 4)), MusicPuzzle(self)
        )
        self.objects[(4, 0)] = DoorTile(
            size, self.grid.grid_to_pixel((4, 0)), GuitarPuzzle(self)
        )
        self.objects[(8, 4)] = DoorTile(
            size, self.grid.grid_to_pixel((8, 4)), DrumsPuzzle(self)
        )
        self.objects[(4, 8)] = DoorTile(
            size, self.grid.grid_to_pixel((4, 8)), DrumsPuzzle(self)
        )

        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def on_update(self):
        pass

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            self.character.change_direction(button.value)
            self.character.move_player(new_location)
            if self.character.grid_pos in self.objects:
                if isinstance(self.objects[self.character.grid_pos], DoorTile):
                    return self.objects[self.character.grid_pos].other_room

    def on_layout(self, win_size):
        self.remove(self.character)
        self.remove(self.grid)
        self.grid.on_layout(win_size)
        for pos, obj in self.objects.items():
            self.remove(obj)

        self.add(self.grid)
        self.place_objects()
        self.character.on_layout(win_size)
        self.add(self.character)
