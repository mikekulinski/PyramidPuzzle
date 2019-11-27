from kivy.graphics import PopMatrix, PushMatrix, Translate

from src.button import Button
from src.drums_puzzle import DrumsPuzzle
from src.grid import DoorTile, Tile
from src.guitar_puzzle import GuitarPuzzle
from src.piano_puzzle import PianoPuzzle
from src.puzzle import Puzzle


class CenterRoom(Puzzle):
    def __init__(self):
        super().__init__()
        self.up = False
        self.down = False
        self.left = False
        self.right = False

        self.last_entered = (0, 0)

        self.place_objects()

    def on_finished_puzzle(self):
        if self.last_entered == (4, 8):
            self.up = True
        elif self.last_entered == (4, 0):
            self.down = True
        elif self.last_entered == (0, 4):
            self.left = True
        elif self.last_entered == (8, 4):
            self.right = True
        else:
            print("Incorrect dimensions for finished puzzle")

        for pos, obj in self.objects.items():
            self.remove(obj)
        self.place_objects()

        self.character.move_player((4, 4))

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        return self.up and self.down and self.left and self.right

    def place_objects(self):
        self.objects = {}

        size = (self.grid.tile_side_len, self.grid.tile_side_len)

        if self.left:
            self.objects[(0, 4)] = Tile(size, self.grid.grid_to_pixel((0, 4)))
            self.objects[(0, 4)].set_color(Tile.base_color, source="./data/piano.png")
            self.objects[(0, 4)].passable = False
        else:
            self.objects[(0, 4)] = DoorTile(
                size, self.grid.grid_to_pixel((0, 4)), PianoPuzzle
            )

        if self.right:
            self.objects[(8, 4)] = Tile(size, self.grid.grid_to_pixel((8, 4)))
            self.objects[(8, 4)].set_color(Tile.base_color, source="./data/guitar.png")
            self.objects[(8, 4)].passable = False
        else:
            self.objects[(8, 4)] = DoorTile(
                size, self.grid.grid_to_pixel((8, 4)), GuitarPuzzle
            )

        if self.up:
            self.objects[(4, 8)] = Tile(size, self.grid.grid_to_pixel((4, 8)))
            self.objects[(4, 8)].set_color(Tile.base_color, source="./data/drums.png")
            self.objects[(4, 8)].passable = False
        else:
            self.objects[(4, 8)] = DoorTile(
                size, self.grid.grid_to_pixel((4, 8)), DrumsPuzzle
            )

        if self.down:
            self.objects[(4, 0)] = Tile(size, self.grid.grid_to_pixel((4, 0)))
            self.objects[(4, 0)].set_color(Tile.base_color, source="./data/drums.png")
            self.objects[(4, 0)].passable = False
        else:
            self.objects[(4, 0)] = DoorTile(
                size, self.grid.grid_to_pixel((4, 0)), DrumsPuzzle
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
                if isinstance(self.objects[self.character.grid_pos], DoorTile):
                    self.last_entered = self.character.grid_pos
                    return self.objects[self.character.grid_pos].other_room(self)

    def on_update(self):
        if not self.game_over and self.is_game_over():
            self.on_game_over()

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

        if self.game_over:
            self.remove(self.game_over_window_color)
            self.remove(self.game_over_window)
            self.remove(self.game_over_text_color)
            self.remove(self.game_over_text)

            self.on_game_over()
