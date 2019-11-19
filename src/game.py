# common imports
from kivy.graphics.instructions import InstructionGroup

from src.character import Character
from src.grid import Grid, Switch

FLOOR_SIZE = 9


class Game(InstructionGroup):
    def __init__(self, on_pitch_mode, on_rhythm_mode, on_key_mode):
        super().__init__()

        self.pitch_switch = (
            (2, 2),
            lambda size, pos: Switch(size, pos, on_pitch_mode, "./data/pitch_icon.png"),
        )
        self.rhythm_switch = (
            (6, 4),
            lambda size, pos: Switch(
                size, pos, on_rhythm_mode, "./data/rhythm_icon.png"
            ),
        )
        self.key_switch = (
            (2, 6),
            lambda size, pos: Switch(size, pos, on_key_mode, "./data/key_icon.jpeg"),
        )

        self.grid = Grid(
            num_tiles=9,
            objects=[self.pitch_switch, self.rhythm_switch, self.key_switch],
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
