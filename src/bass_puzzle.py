from kivy.core.window import Window
from kivy.graphics import Color, PopMatrix, PushMatrix, Translate
from kivy.graphics.instructions import InstructionGroup

from common.button import Button
from common.gfxutil import CLabelRect, CRectangle
from src.character import Character
from src.grid import Grid, Tile
from src.puzzle_sound import Note, PuzzleSound


class SimonSays(InstructionGroup):
    def __init__(self, size, pos, color, idx, on_interact, puzzle):
        super().__init__()
        self.size = size
        self.pos = pos

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

        self.current_color = Color(rgba=color.rgba)
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
        print("Done playing audio")
        self.puzzle.play_game(self.idx)


class Mummy(Tile):
    def __init__(self, size, pos, on_interact, icon_source):
        super().__init__(size, pos)
        self.on_interact = on_interact
        self.icon_source = icon_source

        self.set_color(color=Tile.base_color, source=self.icon_source)

    def interact(self):
        self.on_interact()


class BassPuzzle(InstructionGroup):
    def __init__(self):
        super().__init__()
        self.puzzle_on = False
        self.note_index = 1
        self.cpu_turn = True
        self.user_sequence = []
        self.correct_sequence = [0, 1, 3, 2, 3]

        self.colors = [
            Color(rgb=(0, 1, 0)),  # Green
            Color(rgb=(1, 0, 0)),  # Red
            Color(rgb=(1, 1, 0)),  # Yellow
            Color(rgb=(0, 0, 1)),  # Blue
            Color(rgb=(1, 165 / 255, 0)),  # Orange
        ]

        self.game_over_window_color = Color(rgba=(1, 1, 1, 1))
        self.game_over_window = CRectangle(
            cpos=(Window.width // 2, Window.height // 2),
            csize=(Window.width // 2, Window.height // 5),
        )
        self.game_over_text_color = Color(rgba=(0, 0, 0, 1))
        self.game_over_text = CLabelRect(
            (Window.width // 2, Window.height // 2), "You Win!", 70
        )

        # Setup audio
        self.notes = [Note(480, p) for p in (60, 64, 67, 72)]
        self.audio = PuzzleSound(self.notes)

        # Setup visuals
        self.grid = Grid(num_tiles=9)
        self.add(self.grid)

        self.place_objects()

        # Add the character to the game
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

    def create_mummy(self, pos):
        size = (self.grid.tile_side_len, self.grid.tile_side_len)
        pos = self.grid.grid_to_pixel(pos)
        return Mummy(size, pos, self.on_interact_mummy, "./data/mummy.jpg")

    def create_simon_says(self, pos, idx):
        size = (self.grid.tile_side_len * 0.75, self.grid.tile_side_len * 0.75)
        pos = self.grid.grid_to_pixel(pos)
        pos = (
            pos[0] + self.grid.tile_side_len // 2,
            pos[1] + self.grid.tile_side_len // 2,
        )
        color = self.colors[idx]
        return SimonSays(size, pos, color, idx, self.on_interact_simon_says, self)

    def place_objects(self):
        self.objects = {}
        self.mummy = self.create_mummy((4, 8))
        self.objects[(4, 8)] = self.mummy

        if self.puzzle_on:
            self.simons = []
            for idx in range(4):
                pos = (2 * idx + 1, 4)
                simon = self.create_simon_says(pos, idx)
                self.simons.append(simon)
                self.objects[pos] = simon

        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def play_game(self, idx=None):
        if self.note_index == len(self.correct_sequence) + 1:
            self.game_over()
            return

        if self.cpu_turn:
            notes = []
            cb_ons = []
            cb_offs = []
            for i in self.correct_sequence[: self.note_index]:
                notes.append(self.notes[i])
                cb_ons.append(self.simons[i].activate)
                cb_offs.append(self.simons[i].deactivate)

            self.audio.update_sounds(notes, cb_ons, cb_offs)
            self.audio.noteseq.start_simon_says()
            self.cpu_turn = False
            self.user_sequence = []
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

    def game_over(self):
        self.add(self.game_over_window_color)
        self.add(self.game_over_window)
        self.add(self.game_over_text_color)
        self.add(self.game_over_text)

    def on_interact_mummy(self):
        print("Interacted with mummy!")
        self.puzzle_on = True
        for pos, obj in self.objects.items():
            self.remove(obj)
        self.place_objects()

        self.note_index = 1
        self.cpu_turn = True
        self.play_game()

    def on_interact_simon_says(self, idx):
        print("Playing simon says")
        self.audio.update_sounds(
            [self.notes[idx]],
            [self.simons[idx].activate],
            [self.simons[idx].deactivate],
            self.simons[idx].on_finished_playing,
        )
        self.audio.noteseq.start_simon_says()

    def on_update(self):
        self.audio.on_update()

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            self.character.change_direction(button.value)
            self.character.move_player(new_location)
        elif button == Button.A:
            self.character.interact()

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

        self.game_over_window_color = Color(rgba=(1, 1, 1, 1))
        self.game_over_window = CRectangle(
            cpos=(Window.width // 2, Window.height // 2),
            csize=(Window.width // 2, Window.height // 5),
        )
        self.game_over_text_color = Color(rgba=(0, 0, 0, 1))
        self.game_over_text = CLabelRect(
            (Window.width // 2, Window.height // 2), "You Win!", 70
        )
