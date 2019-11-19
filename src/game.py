# common imports
from kivy.graphics.instructions import InstructionGroup

from src.character import Character
from src.grid import Grid

FLOOR_SIZE = 9


class Game(InstructionGroup):
    def __init__(self, on_pitch_mode, on_rhythm_mode, on_key_mode):
        super().__init__()
        self.pitch = (2, 2)
        self.rhythm = (6, 4)
        self.key = (2, 6)
        self.on_pitch_mode = on_pitch_mode
        self.on_rhythm_mode = on_rhythm_mode
        self.on_key_mode = on_key_mode
        self.pitch_source = "./data/pitch_icon.png"
        self.rhythm_source = "./data/rhythm_icon.png"
        self.key_source = "./data/key_icon.jpeg"

        self.grid = Grid(
            num_tiles=9,
            objects=[
                (self.pitch, self.pitch_source, self.on_pitch_mode),
                (self.rhythm, self.rhythm_source, self.on_rhythm_mode),
                (self.key, self.key_source, self.on_key_mode),
            ],
        )
        self.add(self.grid)

        self.character = Character(self)
        self.add(self.character)

    def on_layout(self, win_size):
        self.remove(self.grid)
        self.remove(self.character)

        self.grid.on_layout(win_size)
        self.character.on_layout(win_size)

        self.add(self.grid)
        self.add(self.character)
