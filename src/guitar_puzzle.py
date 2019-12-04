from kivy.graphics import Color, PopMatrix, PushMatrix, Translate
from kivy.graphics.instructions import InstructionGroup

from common.gfxutil import CRectangle
from src.button import Button
from src.grid import DoorTile, Tile
from src.puzzle_sound import Note, PuzzleSound

from src.puzzle import Puzzle

levels = {
    0: [0, 1, 2, 3],
    1: [2, 1, 4, 2, 0],
    2: [3, 0, 0, 4, 2, 0],
    3: [4, 2, 0, 1, 3, 2, 4],
}

sources = ["./data/sarco.jpg", "./data/mummy.jpg", "./data/anubis.jpg", "./data/ra.png"]


class GuitarPuzzle(Puzzle):
    def __init__(self, prev_room=None, level=0, on_finished_puzzle=None):
        super().__init__()
        self.prev_room = prev_room
        self.next_room = None
        self.level = level
        self.on_finished_puzzle = on_finished_puzzle

        self.note_index = 1
        self.cpu_turn = True
        self.user_sequence = []
        self.correct_sequence = levels[level]
        self.mummy_source = sources[level]

        self.colors = [
            Color(rgb=(0, 1, 0)),  # Green
            Color(rgb=(1, 0, 0)),  # Red
            Color(rgb=(1, 1, 0)),  # Yellow
            Color(rgb=(0, 0, 1)),  # Blue
            Color(rgb=(1, 165 / 255, 0)),  # Orange
        ]

        # Setup audio
        self.notes = [Note(480, p) for p in (60, 64, 67, 72, 74)]
        self.audio = PuzzleSound(self.notes, simon_says=True)

        self.tile_size = (self.grid.tile_side_len, self.grid.tile_side_len)

        self.create_objects()
        self.place_objects()

    def create_mummy(self, pos):
        pos = self.grid.grid_to_pixel(pos)
        return Mummy(self.tile_size, pos, self.on_interact_mummy, self.mummy_source)

    def create_simon_says(self, pos, idx):
        size = (self.tile_size[0] * 0.75, self.tile_size[1] * 0.75)
        pos = self.grid.grid_to_pixel(pos)
        pos = (
            pos[0] + self.grid.tile_side_len // 2,
            pos[1] + self.grid.tile_side_len // 2,
        )
        color = self.colors[idx]
        return SimonSays(size, pos, color, idx, self.on_interact_simon_says, self)

    def play_game(self, idx=None):
        if self.is_game_over():
            return

        if self.cpu_turn:
            notes = []
            cb_ons = []
            cb_offs = []
            for i in self.correct_sequence[: self.note_index]:
                notes.append(self.notes[i])
                cb_ons.append(self.simons[i].activate)
                cb_offs.append(self.simons[i].deactivate)

            self.audio.set_notes(notes)
            self.audio.set_cb_ons(cb_ons)
            self.audio.set_cb_offs(cb_offs)
            self.audio.set_on_finished(self.change_to_user_turn)
            self.audio.note_seq.start_now()

        else:
            if idx == self.correct_sequence[len(self.user_sequence)]:
                self.user_sequence.append(idx)
                if len(self.user_sequence) == (self.note_index):
                    self.note_index += 1
                    self.cpu_turn = True
                    self.play_game()
            else:
                self.cpu_turn = True
                self.play_game()

    def change_to_user_turn(self):
        self.cpu_turn = False
        self.user_sequence = []

    def on_interact_mummy(self):
        self.user_sequence = []
        self.note_index = 1
        self.cpu_turn = True
        self.play_game()

    def on_interact_simon_says(self, idx):
        if not self.cpu_turn:
            self.audio.set_notes([self.notes[idx]])
            self.audio.set_cb_ons([self.simons[idx].activate])
            self.audio.set_cb_offs([self.simons[idx].deactivate])
            self.audio.set_on_finished(self.simons[idx].on_finished_playing)
            self.audio.note_seq.start_now()

    def create_objects(self):
        self.objects = {}
        # Add door to switch between rooms
        self.objects[(0, 4)] = DoorTile(
            self.tile_size, self.grid.grid_to_pixel((0, 4)), self.prev_room
        )

        self.mummy = self.create_mummy((4, 8))
        self.objects[(4, 8)] = self.mummy

        self.simons = []
        for idx in range(5):
            pos = (idx + 2, 3)
            simon = self.create_simon_says(pos, idx)
            self.simons.append(simon)
            self.objects[pos] = simon

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        return self.note_index == len(self.correct_sequence) + 1

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
                    next_room_pos = (8 - player_pos[0], 8 - player_pos[1])
                    self.objects[player_pos].other_room.character.move_player(
                        next_room_pos
                    )
                    return self.objects[player_pos].other_room

        elif button == Button.A:
            self.character.interact()

    def on_update(self):
        self.audio.on_update()

        if not self.game_over and self.is_game_over():
            if self.level >= max(levels.keys()):
                self.on_finished_puzzle()
                self.on_game_over()
            else:
                if self.next_room is None:
                    self.next_room = DoorTile(
                        self.tile_size, self.grid.grid_to_pixel((8, 4)), GuitarPuzzle
                    )
                    self.objects[(8, 4)] = self.next_room
                self.add(PushMatrix())
                self.add(Translate(*self.grid.pos))
                self.add(self.next_room)
                self.add(PopMatrix())

    def on_layout(self, win_size):
        self.remove(self.character)
        for pos, obj in self.objects.items():
            self.remove(obj)
        self.remove(self.grid)

        self.grid.on_layout(win_size)
        self.add(self.grid)
        self.tile_size = (self.grid.tile_side_len, self.grid.tile_side_len)

        self.place_objects()

        self.character.on_layout(win_size)
        self.add(self.character)

        self.create_game_over_text(win_size)


class SimonSays(InstructionGroup):
    def __init__(self, size, pos, color, idx, on_interact, puzzle):
        super().__init__()
        self.size = size
        self.pos = pos
        self.moveable = False
        self.passable = False
        self.unactive_color = Color(rgba=(*color.rgb, 1 / 3))
        self.active_color = Color(rgba=(*color.rgb, 1))
        self.active = False
        self.idx = idx
        self.on_interact = on_interact
        self.puzzle = puzzle

        self.current_color = Color(rgba=self.unactive_color.rgba)
        self.rect = CRectangle(csize=self.size, cpos=self.pos)
        self.add(self.current_color)
        self.add(self.rect)

        self.deactivate()

    def set_color(self, color):
        self.remove(self.rect)

        self.current_color = Color(rgba=(*color.rgba,))
        self.rect = CRectangle(csize=self.size, cpos=self.pos)
        self.add(self.current_color)
        self.add(self.rect)

    def interact(self):
        self.on_interact(self.idx)

    def activate(self):
        self.set_color(color=self.active_color)

    def deactivate(self):
        self.set_color(color=self.unactive_color)

    def on_finished_playing(self):
        self.puzzle.play_game(self.idx)


class Mummy(Tile):
    def __init__(self, size, pos, on_interact, icon_source):
        super().__init__(size, pos)
        self.on_interact = on_interact
        self.icon_source = icon_source
        self.passable = False

        self.set_color(color=Tile.base_color, source=self.icon_source)

    def interact(self):
        self.on_interact()
