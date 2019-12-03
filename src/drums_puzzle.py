from kivy.core.window import Window
from kivy.graphics import Color, PopMatrix, PushMatrix, Translate
from kivy.graphics.instructions import InstructionGroup

from common.gfxutil import CRectangle
from src.button import Button
from src.grid import DoorTile, Tile
from src.puzzle_sound import Note, PuzzleSound

from src.puzzle import Puzzle

# make audio loop so notes change in real time
# map a 4 x 4 grid x axis is beat and y axis is instrument (hi-hat, bass drum, etc.)
# no concept of actual sound
levels = {
    0: [" X  ", "XXX ", " X  ", "    "],
    1: ["XX  ", "X  X", "  XX", "   X"],
    2: ["  XX", " X  ", "X  X", "X XX"],
    3: ["X  X", " XX ", "XX  ", "  X "],
}

# hi-hat, snare, bass drum, tambourine
instruments = [42, 38, 36, 54]
all_rests = [[Note(480, 0) for i in instruments] for _ in range(8)]

# character knows which tile its on
# receive tile, toggle that tile and the surrounding ones


class DrumsPuzzle(Puzzle):
    def __init__(self, prev_room, level=0, on_finished_puzzle=None):
        super().__init__()
        self.prev_room = prev_room
        self.level = level
        self.on_finished_puzzle = on_finished_puzzle
        self.pattern = levels[level]
        self.drum_graphics = DrumPatternGraphics(self.pattern)
        self.add(self.drum_graphics)

        self.beats = all_rests
        self.sound = PuzzleSound(self.beats, bank=128, loop=True)
        self.create_objects()
        self.place_objects()

    def on_button_press(self):
        self.objects[self.character.grid_pos].on_button_press()
        self.objects[self.character.grid_pos].toggle_neighbors(
            self.objects, len(self.pattern)
        )
        self.sound.set_notes(self.beats)
        self.sound.toggle()

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        for i in range(len(self.pattern)):
            for j in range(len(self.pattern[i])):
                if self.pattern[i][j] == "X" and not self.sequencer_tiles[i][j].beat_on:
                    return False
                if self.pattern[i][j] == " " and self.sequencer_tiles[i][j].beat_on:
                    return False
        return True

    def create_objects(self):
        self.objects = {}
        size = (self.grid.tile_side_len, self.grid.tile_side_len)
        self.objects[(4, 8)] = DoorTile(
            size, self.grid.grid_to_pixel((4, 8)), self.prev_room
        )
        self.objects[(6, 6)] = ResetButton(size, self.grid.grid_to_pixel((6, 6)))
        x_topleft, y_topleft = (2, 5)

        self.sequencer_tiles = []
        for instrument_id in range(len(instruments)):
            row = []
            for beat_id in range(4):
                size = (self.grid.tile_side_len, self.grid.tile_side_len)
                pos = self.grid.grid_to_pixel(
                    (x_topleft + beat_id, y_topleft - instrument_id)
                )
                tile = SequencerTile(
                    size,
                    pos,
                    beat_id,
                    instrument_id,
                    (x_topleft, y_topleft),
                    self.beats,
                )
                self.objects[(x_topleft + beat_id, y_topleft - instrument_id)] = tile
                row.append(tile)
            self.sequencer_tiles.append(row)

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
            self.character.change_direction(button.value)
            self.character.move_player(new_pos)
            player_pos = self.character.grid_pos

            # Check if we are walking through a door
            if player_pos in self.objects:
                obj = self.objects[player_pos]
                if isinstance(obj, DoorTile):
                    if not isinstance(obj.other_room, Puzzle):
                        # instantiate class when we enter the door
                        self.objects[player_pos].other_room = obj.other_room(
                            prev_room=self,
                            level=self.level + 1,
                            on_finished_puzzle=self.on_finished_puzzle,
                        )
                    return self.objects[player_pos].other_room
        elif button == Button.A:
            if player_pos in self.objects:
                obj = self.objects[player_pos]
                if isinstance(obj, SequencerTile):
                    self.on_button_press()
                if isinstance(obj, ResetButton):
                    for row in self.sequencer_tiles:
                        for tile in row:
                            tile.turn_off()
        elif button == Button.B:
            self.sound.toggle()

    def on_update(self):
        self.sound.on_update()
        if self.sequencer_tiles:
            if not self.game_over and self.is_game_over():
                if self.level == max(levels.keys()):
                    self.on_finished_puzzle()
                    self.on_game_over()
                else:
                    if (4,0) not in self.objects:
                        size = (self.grid.tile_side_len, self.grid.tile_side_len)
                        self.objects[(4, 0)] = DoorTile(
                            size, self.grid.grid_to_pixel((4, 0)), DrumsPuzzle
                        )
                    self.add(PushMatrix())
                    self.add(Translate(*self.grid.pos))
                    self.add(self.objects[(4, 0)])
                    self.add(PopMatrix())

    def on_layout(self, win_size):
        self.remove(self.character)
        for pos, obj in self.objects.items():
            self.remove(obj)
        self.remove(self.grid)

        self.grid.on_layout(win_size)
        self.add(self.grid)
        self.drum_graphics.on_layout(win_size)

        self.place_objects()

        self.character.on_layout(win_size)
        self.add(self.character)

        self.create_game_over_text(win_size)
        if self.game_over:
            self.remove(self.game_over_window_color)
            self.remove(self.game_over_window)
            self.remove(self.game_over_text_color)
            self.remove(self.game_over_text)

            self.on_game_over()


class DrumPatternGraphics(InstructionGroup):
    def __init__(self, pattern):
        super().__init__()
        self.win_size = (Window.width, Window.height)
        self.pattern = pattern
        self.render_elements()

    def render_elements(self):
        size = self.win_size[0] / 6
        self.grid = CRectangle(
            cpos=(self.win_size[0] // 10, self.win_size[1] // 6), csize=(size, size)
        )
        self.squares = []
        square_size = size / 4
        top_left = (
            self.grid.cpos[0] - size / 2 + square_size / 2,
            self.grid.cpos[1] + size / 2 - square_size / 2,
        )
        self.add(self.grid)
        for i in range(len(self.pattern)):
            for j in range(len(self.pattern[i])):
                if self.pattern[i][j] == "X":
                    sq = CRectangle(
                        cpos=(
                            top_left[0] + j * square_size,
                            top_left[1] - i * square_size,
                        ),
                        csize=(square_size, square_size),
                    )
                    self.add(Color(rgb=(0, 1, 0)))
                    self.add(sq)
                    self.squares.append(sq)

    def on_layout(self, win_size):
        self.clear()
        self.win_size = win_size
        self.render_elements()


class SequencerTile(Tile):
    active_color = Color(rgba=(0, 1, 0, 1))
    inactive_color = Color(rgba=(0, 0.4, 0, 1))
    rest = Note(480, 0)

    def __init__(self, size, pos, beat_idx, instrument_idx, topleft, beats):
        super().__init__(size, pos)

        self.beat_id = beat_idx
        self.instrument_id = instrument_idx
        self.instrument_pitch = instruments[instrument_idx]
        self.beats = beats
        self.beat_on = False
        self.beat_note = Note(480, self.instrument_pitch)
        self.topleft = topleft
        self.relative_pos = (beat_idx, instrument_idx)
        self.set_color(color=SequencerTile.inactive_color)

    def on_button_press(self):
        # toggle audio mapped to it
        # toggle tile appearance
        self.toggle()

    def toggle(self):
        # flip tile, toggle audio
        if self.beat_on:
            self.set_beats(rest=True)
            self.set_color(color=SequencerTile.inactive_color)
        else:
            self.set_beats(rest=False)
            self.set_color(SequencerTile.active_color)
        self.beat_on = not self.beat_on

    def turn_off(self):
        self.set_beats(rest=True)
        self.set_color(color=SequencerTile.inactive_color)
        self.beat_on = False

    def set_beats(self, rest=True):
        for i in range(len(self.beats)):
            for j in range(len(self.beats)):
                if self.beat_id % 4 == i and self.instrument_id == j:
                    self.beats[i][j] = SequencerTile.rest if rest else self.beat_note

    def toggle_neighbors(self, objects, sequencer_size):
        x, y = self.relative_pos
        x_left = None if x == 0 else x - 1
        x_right = None if x == sequencer_size - 1 else x + 1
        y_down = None if y == sequencer_size - 1 else y + 1
        y_up = None if y == 0 else y - 1
        coords = [(x_left, y), (x_right, y), (x, y_up), (x, y_down)]
        coords = [
            (self.topleft[0] + coord[0], self.topleft[1] - coord[1])
            for coord in coords
            if None not in coord
        ]
        for coord in coords:
            if coord in objects:
                objects[coord].toggle()


class ResetButton(Tile):
    def __init__(self, size, pos):
        super().__init__(size, pos)

        self.set_color(color=Tile.base_color, source="./data/reset_button.jpg")

