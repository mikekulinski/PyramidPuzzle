from kivy.graphics import PopMatrix, PushMatrix, Translate, Color

from src.button import Button
from src.drums_puzzle import DrumsPuzzle
from src.grid import DoorTile, Tile
from src.guitar_puzzle import GuitarPuzzle
from src.piano_puzzle import PianoPuzzle
from src.puzzle import Puzzle
from src.bass_puzzle import BassPuzzle
from src.treasure_room import TreasureRoom


class CenterRoom(Puzzle):
    def __init__(self):
        super().__init__()

        self.puzzles = {
            (4, 9): BassPuzzle,  # UP
            (4, -1): DrumsPuzzle,  # DOWN
            (-1, 4): PianoPuzzle,  # LEFT
            (9, 4): GuitarPuzzle,  # RIGHT
        }

        self.puzzle_finished = {
            (4, 9): False,  # UP
            (4, -1): False,  # DOWN
            (-1, 4): False,  # LEFT
            (9, 4): False,  # RIGHT
        }

        self.icon_sources = {
            (4, 9): "./data/bass.png",  # UP
            (4, -1): "./data/drums.png",  # DOWN
            (-1, 4): "./data/piano.png",  # LEFT
            (9, 4): "./data/guitar.png",  # RIGHT
        }

        self.door_sources = {
            (4, 9): "./data/Door_up.png",  # UP
            (4, -1): "./data/door_down.png",  # DOWN
            (-1, 4): "./data/door_left.png",  # LEFT
            (9, 4): "./data/Door_right.png",  # RIGHT
        }

        self.last_entered = (0, 0)

        self.tile_size = (self.grid.tile_side_len, self.grid.tile_side_len)
        self.treasure_room = DoorTile(
            self.tile_size, self.grid.grid_to_pixel((4, 4)), TreasureRoom
        )
        self.treasure_room.set_color(Color(rgba=(0, 0, 0, 1)))

        self.create_objects()
        self.place_objects()

    def on_finished_puzzle(self):
        if self.last_entered in self.puzzle_finished:
            self.puzzle_finished[self.last_entered] = True
        else:
            print("Incorrect dimensions for finished puzzle")

        for pos, obj in self.objects.items():
            self.remove(obj)
        self.create_objects()
        self.place_objects()

    def create_icon(self, loc, source):
        tile = Tile(self.tile_size, self.grid.grid_to_pixel(loc))
        tile.set_color(Tile.base_color, source=source)
        tile.passable = False
        return tile

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        for loc, finished in self.puzzle_finished.items():
            if not finished:
                return False
        return True

    def create_objects(self):
        self.objects = {}
        for loc, puzzle in self.puzzles.items():
            if self.puzzle_finished[loc]:
                self.objects[loc] = self.create_icon(loc, self.icon_sources[loc])
            else:
                self.objects[loc] = DoorTile(
                    self.tile_size,
                    self.grid.grid_to_pixel(loc),
                    puzzle,
                    source=self.door_sources[loc],
                )

        if self.is_game_over():
            self.objects[(4, 4)] = self.treasure_room

    def place_objects(self):
        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def on_player_input(self, button):
        player_pos = self.character.grid_pos
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            # Move the player
            x, y = button.value
            new_pos = (player_pos[0] + x, player_pos[1] + y)

            # Check if we are walking through a door
            if new_pos in self.objects:
                obj = self.objects[new_pos]
                if isinstance(obj, DoorTile):
                    self.last_entered = new_pos
                    if not isinstance(obj.other_room, Puzzle):
                        # instantiate class when we enter the door
                        self.objects[new_pos].other_room = obj.other_room(
                            prev_room=self, on_finished_puzzle=self.on_finished_puzzle
                        )

                    next_room_pos = (8 - new_pos[0] + x, 8 - new_pos[1] + y)
                    self.objects[new_pos].other_room.character.change_direction(
                        button.value
                    )
                    self.objects[new_pos].other_room.character.move_player(
                        next_room_pos
                    )
                    return self.objects[new_pos].other_room

            self.character.change_direction(button.value)
            self.character.move_player(new_pos)
            player_pos = self.character.grid_pos

    def on_update(self):
        if not self.game_over and self.is_game_over():
            self.add(PushMatrix())
            self.add(Translate(*self.grid.pos))
            self.add(self.treasure_room)
            self.add(PopMatrix())

    def on_layout(self, win_size):
        self.remove(self.character)
        self.remove(self.grid)
        self.grid.on_layout(win_size)
        for pos, obj in self.objects.items():
            self.remove(obj)
        self.tile_size = (self.grid.tile_side_len, self.grid.tile_side_len)

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
