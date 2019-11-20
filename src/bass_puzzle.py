from random import choice

from kivy.core.window import Window
from kivy.graphics import Color, Line, PopMatrix, PushMatrix, Rectangle, Translate
from kivy.graphics.instructions import InstructionGroup

from common.audio import Audio
from common.button import Button
from common.clock import AudioScheduler, SimpleTempoMap
from common.gfxutil import AnimGroup, CLabelRect, CRectangle, KFAnim
from common.synth import Synth
from src.grid import Tile, Grid
from src.puzzle_sound import Note, PuzzleSound
from src.character import Character


class SimonSays(InstructionGroup):
    def __init__(self, size, pos, color, idx, on_interact):
        super().__init__()
        self.size = size
        self.pos = pos

        self.unactive_color = Color(rgba=(*color.rgb, 1 / 3))
        self.active_color = Color(rgba=(*color.rgb, 1))
        self.active = False
        self.idx = idx
        self.on_interact = on_interact

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
        self.colors = [
            Color(rgb=(0, 1, 0)),  # Green
            Color(rgb=(1, 0, 0)),  # Red
            Color(rgb=(1, 1, 0)),  # Yellow
            Color(rgb=(0, 0, 1)),  # Blue
            Color(rgb=(1, 165 / 255, 0)),  # Orange
        ]

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
        return SimonSays(size, pos, color, idx, self.on_interact_simon_says)

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

    def on_interact_mummy(self):
        print("Interacted with mummy!")
        self.puzzle_on = True
        for pos, obj in self.objects.items():
            self.remove(obj)
        self.place_objects()

        self.audio.update_sounds(
            self.notes,
            [s.activate for s in self.simons],
            [s.deactivate for s in self.simons],
        )
        self.audio.noteseq.start_simon_says()

    def on_interact_simon_says(self, idx):
        print("Playing simon says")
        self.audio.noteseq.simon_says_on(
            self.notes[idx].get_pitch(), self.simons[idx].deactivate
        )
        self.simons[idx].activate()

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
