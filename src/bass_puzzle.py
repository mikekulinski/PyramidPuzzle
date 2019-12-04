from random import choice

from kivy.core.window import Window
from kivy.graphics import Color, Line, PopMatrix, PushMatrix, Rectangle, Translate
from kivy.graphics.instructions import InstructionGroup

from common.audio import Audio
from src.button import Button
from common.clock import AudioScheduler, SimpleTempoMap
from common.gfxutil import AnimGroup, CLabelRect, CRectangle, KFAnim
from common.synth import Synth
from src.grid import Tile, DoorTile, Grid
from src.puzzle_sound import Note, PuzzleSound
from src.character import Character
from src.puzzle import Puzzle
from src.puzzle_sound import Note, PuzzleSound


string_pitches = [
    [48, 49, 50, 51, 52, 53, 54],
    [52, 53, 54, 55, 56, 57, 58],
    [56, 57, 58, 59, 60, 61, 62],
    [60, 61, 62, 63, 64, 65, 66],
]

string_heights = {0: [4], 1: [4, 5], 2: [3, 4, 5], 3: [3, 4, 5, 6]}

actual_frets = {0: [3], 1: [7, 2], 2: [2, 6, 4], 3: [1, 7, 5, 3]}


class BassPuzzle(Puzzle):
    def __init__(self, level=0, prev_room=None, on_finished_puzzle=None):
        super().__init__()

        self.door_sources = {
            (4, 9): "./data/Door_up.png",  # UP
            (4, -1): "./data/door_down.png",  # DOWN
            (-1, 4): "./data/door_left.png",  # LEFT
            (9, 4): "./data/Door_right.png",  # RIGHT
        }

        self.level = level
        self.prev_room = prev_room
        self.next_room = None
        self.on_finished_puzzle = on_finished_puzzle

        self.num_strings = level + 1
        self.string_heights = string_heights[level]
        self.string_pitches = string_pitches[: self.num_strings]

        # Start the blocks all the way to the left every time
        self.current_frets = [1 for _ in range(self.num_strings)]
        self.actual_frets = actual_frets[level]

        self.played_strings = []

        self.tile_size = (self.grid.tile_side_len, self.grid.tile_side_len)
        self.fret_move_range = [1, 7]

        self.create_objects()
        self.place_objects()

        self.audio = PuzzleSound([], bass_puzzle=True)

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        return len(self.played_strings) == self.num_strings

    def create_objects(self):
        self.objects = {}
        self.objects[(4, -1)] = DoorTile(
            self.tile_size,
            self.grid.grid_to_pixel((4, -1)),
            self.prev_room,
            self.door_sources[(4, -1)],
        )

        self.strings = []
        for i in range(self.num_strings):
            # Create each string
            height = self.string_heights[i]
            self.strings.append(self.create_string(height, i))

            # Create the play buttons
            button_pos = (0, height)
            self.objects[button_pos] = self.create_play_button(button_pos)

            # Create the corresponding fret
            fret_x = self.current_frets[i]
            fret_y = self.string_heights[i]
            grid_loc = (fret_x, fret_y)
            self.objects[grid_loc] = self.create_fret(grid_loc, i)

    def create_string(self, height, idx):
        half_tile = self.grid.tile_side_len // 2

        string_start = self.grid.grid_to_pixel((0, height))
        string_start = (string_start[0] + half_tile, string_start[1] + half_tile)

        string_end = self.grid.grid_to_pixel((8, height))
        string_end = (string_end[0] + 2 * half_tile, string_end[1] + half_tile)

        return BassString(string_start + string_end, idx)

    def create_fret(self, grid_loc, string_idx):
        pos = self.grid.grid_to_pixel(grid_loc)
        return FretBlock(self.tile_size, grid_loc, pos, string_idx)

    def create_play_button(self, grid_loc):
        wall_location = (grid_loc[0] - 1, grid_loc[1])
        pos = self.grid.grid_to_pixel(wall_location)
        return PlayButton(self.tile_size, pos)

    def place_objects(self):
        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for string in self.strings:
            self.add(string)

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def move_block(self, block, new_pos):
        if self.is_valid_pos(new_pos) and self.valid_block_move(block, new_pos):
            self.remove(self.objects[block.grid_pos])
            del [self.objects[block.grid_pos]]

            self.add(PushMatrix())
            self.add(Translate(*self.grid.pos))
            obj = self.create_fret(new_pos, block.string_idx)
            self.objects[new_pos] = obj
            self.add(obj)
            self.add(PopMatrix())

            self.current_frets[block.string_idx] = new_pos[0]

    def valid_block_move(self, block, pos):
        same_height = pos[1] == block.grid_pos[1]
        in_range = self.fret_move_range[0] <= pos[0] <= self.fret_move_range[1]
        return same_height and in_range

    def on_update(self):
        self.audio.on_update()
        if not self.game_over and self.is_game_over():
            if self.level >= max(string_heights.keys()):
                self.on_finished_puzzle()
                self.on_game_over()
            else:
                if self.next_room is None:
                    self.next_room = DoorTile(
                        self.tile_size,
                        self.grid.grid_to_pixel((4, 9)),
                        BassPuzzle,
                        self.door_sources[(4, 9)],
                    )
                    self.objects[(4, 9)] = self.next_room
                self.add(PushMatrix())
                self.add(Translate(*self.grid.pos))
                self.add(self.next_room)
                self.add(PopMatrix())

    def on_player_input(self, button):
        player_pos = self.character.grid_pos
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            x, y = button.value
            new_pos = (player_pos[0] + x, player_pos[1] + y)
            self.character.change_direction(button.value)

            if new_pos in self.objects:
                obj = self.objects[new_pos]
                if isinstance(obj, DoorTile):
                    if not isinstance(obj.other_room, Puzzle):
                        # instantiate class when we enter the door
                        self.objects[new_pos].other_room = obj.other_room(
                            prev_room=self,
                            level=self.level + 1,
                            on_finished_puzzle=self.on_finished_puzzle,
                        )
                    next_room_pos = (8 - new_pos[0] + x, 8 - new_pos[1] + y)
                    self.objects[new_pos].other_room.character.change_direction(
                        button.value
                    )
                    self.objects[new_pos].other_room.character.move_player(
                        next_room_pos
                    )
                    return self.objects[new_pos].other_room

            if new_pos in self.objects:
                block = self.objects[new_pos]
                if block.moveable:
                    new_block_pos = (new_pos[0] + x, new_pos[1] + y)
                    self.move_block(block, new_block_pos)

            self.character.move_player(new_pos)
            player_pos = self.character.grid_pos

            if player_pos[0] == 8 and player_pos[1] in self.string_heights:
                string_idx = self.string_heights.index(player_pos[1])
                self.play_current(string_idx)

        elif button == Button.A:
            if player_pos in self.objects:
                obj = self.objects[player_pos]
                if isinstance(obj, PlayButton):
                    print("Playing actual note")
                    string_idx = self.string_heights.index(player_pos[1])
                    self.play_actual(string_idx)

    def play_current(self, string_idx):
        fret_pos = self.current_frets[string_idx]
        pitch = self.string_pitches[string_idx][fret_pos - 1]
        note = Note(480, pitch)
        self.audio.set_notes([note])
        self.audio.note_seq.start_now()

        correct_string = string_idx == len(self.played_strings)
        correct_fret = self.current_frets[string_idx] == self.actual_frets[string_idx]
        if correct_string and correct_fret:
            self.played_strings.append(string_idx)
        else:
            self.played_strings = []

    def play_actual(self, string_idx):
        fret_pos = self.actual_frets[string_idx]
        pitch = self.string_pitches[string_idx][fret_pos - 1]
        note = Note(480, pitch)
        self.audio.set_notes([note])
        self.audio.note_seq.start_now()

    def on_layout(self, win_size):
        self.remove(self.character)
        for pos, obj in self.objects.items():
            self.remove(obj)
        self.remove(self.grid)

        self.grid.on_layout(win_size)
        self.add(self.grid)

        self.place_objects()

        self.character.on_layout(win_size)
        self.add(self.character)


class BassString(InstructionGroup):
    def __init__(self, pos, idx):
        super().__init__()
        self.pos = pos
        self.width = 5

        self.idx = idx

        self.add(Color(0, 0, 0))
        self.add(Line(points=self.pos, width=self.width))

    def update_pitch(self, fret_pos=0):
        self.note = Note(480, self.pitches[fret_pos])

    def get_note(self):
        return self.note


class FretBlock(Tile):
    def __init__(self, size, grid_pos, pos, string_idx):
        super().__init__(size, pos)
        self.grid_pos = grid_pos
        self.string_idx = string_idx

        self.icon_source = "./data/boulder.jpg"
        self.passable = False
        self.moveable = True
        self.set_color(color=Tile.base_color, source=self.icon_source)


class PlayButton(Tile):
    def __init__(self, size, pos):
        super().__init__(size, pos)

        self.icon_source = "./data/button_down.png"
        self.passable = True
        self.moveable = False
        self.set_color(color=Tile.base_color, source=self.icon_source)
