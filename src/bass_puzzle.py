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


class BassPuzzle(Puzzle):
    def __init__(self, center_room):
        super().__init__()
        self.center_room = center_room
        self.fret_positions = [(1, 4), (1, 5), (1, 6), (1, 7)]
        self.correct_blocks = [1, 2, 3, 4]
        self.winning = {}  # stringidx : [fret in pos, string played]
        self.string_position_start = [(0, 4), (0, 5), (0, 6), (0, 7)]
        self.string_position_end = [(8, 4), (8, 5), (8, 6), (8, 7)]
        self.string_pitches = [
            [48, 49, 50, 51, 52, 53, 54],
            [52, 53, 54, 55, 56, 57, 58],
            [56, 57, 58, 59, 60, 61, 62],
            [60, 61, 62, 63, 64, 65, 66],
        ]
        self.place_objects()

    def block_interact(self, pos):
        pass

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        for pos, win in self.winning.items():
            if not win[0] or not win[1]:
                return False

        return True

    def place_objects(self):
        size = (self.grid.tile_side_len, self.grid.tile_side_len)

        self.objects[(4, 0)] = DoorTile(
            size, self.grid.grid_to_pixel((4, 0)), self.center_room
        )

        self.fsize = (self.grid.tile_side_len, self.grid.tile_side_len)
        for stringp in range(len(self.string_position_start)):
            pixel_pos_start = self.grid.grid_to_pixel(
                self.string_position_start[stringp]
            )
            pixel_pos_end = self.grid.grid_to_pixel(self.string_position_end[stringp])
            half_side = self.grid.tile_side_len // 2
            pixel_pos_start = (
                pixel_pos_start[0] + half_side,
                pixel_pos_start[1] + half_side,
            )
            pixel_pos_end = (
                pixel_pos_end[0] + half_side * 2,
                pixel_pos_end[1] + half_side,
            )
            self.objects[self.string_position_start[stringp]] = BassString(
                (pixel_pos_start, pixel_pos_end),
                5,
                (
                    self.string_position_start[stringp],
                    self.string_position_end[stringp],
                ),
                self.string_pitches[stringp],
                stringp,
            )
            self.winning[stringp] = [False, False]
        for f in range(len(self.fret_positions)):
            fret = self.fret_positions[f]
            pos = self.grid.grid_to_pixel(fret)
            move_range = (self.string_position_start[f], self.string_position_end[f])
            self.objects[fret] = FretBlock(
                self.fsize,
                fret,
                pos,
                self.block_interact,
                move_range,
                self.correct_blocks[f],
                "./data/boulder.jpg",
            )

        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

        self.audio = PuzzleSound([])

    def move_block(self, new_location, x, y):
        obj_loc = (new_location[0] + x, new_location[1] + y)
        if Puzzle.is_valid_pos(self, obj_loc) and self.valid_block_move(
            obj_loc, self.objects[new_location].move_range
        ):
            self.remove(self.objects[new_location])
            obj = FretBlock(
                self.fsize,
                obj_loc,
                self.grid.grid_to_pixel(obj_loc),
                self.block_interact,
                self.objects[new_location].move_range,
                self.objects[new_location].correct_fret,
                "./data/boulder.jpg",
            )
            del self.objects[new_location]

            self.add(PushMatrix())
            self.add(Translate(*self.grid.pos))
            self.add(obj)
            self.add(PopMatrix())
            correct = obj.check_win()
            self.objects[obj_loc] = obj
            self.winning[obj_loc[1] - 4] = [correct, self.winning[obj_loc[1] - 4][1]]

            self.update_string(obj_loc, obj.get_fret_pos())

    # 	def check_correct_block(self):

    def valid_block_move(self, pos, move_range):

        if (
            move_range[0][0] < pos[0] < move_range[1][0]
            and move_range[0][1] <= pos[1] <= move_range[1][1]
        ):
            return True
        else:
            return False

    def on_update(self):
        self.audio.on_update()

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            if self.game_over and self.is_game_over():
                self.on_game_over()

            self.character.change_direction(button.value)

            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            if new_location in self.objects:
                if self.objects[new_location].moveable:
                    self.move_block(new_location, x, y)

            self.character.move_player(new_location)

            if self.character.grid_pos in self.objects:
                obj = self.objects[
                    (self.character.grid_pos[0], self.character.grid_pos[1])
                ]
                if isinstance(obj, DoorTile):
                    return obj.other_room
            if new_location in self.string_position_end:
                obj = self.objects[
                    (self.character.grid_pos[0] - 8, self.character.grid_pos[1])
                ]

                self.play_string(obj)
            self.game_over = self.is_game_over()

        elif button == Button.A:
            self.play_string(0)
            # self.character.interact()

    def play_string(self, string):

        stringidx = string.stringidx
        if stringidx == 0:
            self.winning[stringidx] = [
                self.winning[stringidx][0],
                self.winning[stringidx][0],
            ]
        else:
            if self.winning[stringidx - 1][1]:
                self.winning[stringidx] = [
                    self.winning[stringidx][0],
                    self.winning[stringidx - 1][1],
                ]
            else:
                for s, w in self.winning:
                    self.winning[s] == [w[0], False]

        note = string.get_note()
        self.audio.set_notes([note])
        self.audio.toggle()

    def update_string(self, block_loc, fret_pos):
        string = self.objects[(0, block_loc[1])]
        string.update_pitch(fret_pos)

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
    def __init__(self, pos1_2, width, grid_start_end, pitches, idx):
        super().__init__()
        self.passable = True
        self.moveable = False
        self.width = width

        self.grid_start, self.grid_end = grid_start_end
        self.pos1, self.pos2 = pos1_2

        self.stringidx = idx
        self.pitches = pitches
        self.update_pitch()

        self.makeline()

    def update_pitch(self, fret_pos=0):
        self.note = Note(480, self.pitches[fret_pos])

    def get_note(self):
        return self.note

    def makeline(self):
        self.add(Color(0, 0, 0))
        poslist = list(self.pos1 + self.pos2)
        self.add(Line(points=poslist, width=self.width))


class FretBlock(Tile):
    def __init__(
        self, size, grid_pos, pos, on_interact, move_range, correct_fret, icon_source
    ):
        super().__init__(size, pos)
        self.move_range = move_range
        self.grid_pos = grid_pos
        self.correct_fret = correct_fret
        self.correct = (grid_pos[0] - 1) == correct_fret

        self.on_interact = on_interact
        self.icon_source = icon_source
        self.passable = False
        self.moveable = True
        self.set_color(color=Tile.base_color, source=self.icon_source)

    # def move_block(self, new_pos):
    #     print("trying to move")
    #     self.pos = new_pos
    #     self.set_pos(self.pos)
    #     self.set_color(color=Tile.base_color, source=self.icon_source)

    def check_win(self):
        return self.correct

    def get_fret_pos(self):
        return self.grid_pos[0] - 1

    def interact(self):
        self.on_interact()

