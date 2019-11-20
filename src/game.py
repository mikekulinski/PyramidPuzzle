# common imports
from kivy.graphics.instructions import InstructionGroup
from kivy.core.window import Window

from src.character import Character
from src.grid import Grid, Switch
from common.button import Button
from src.piano_puzzle import MusicPuzzle
from src.bass_puzzle import BassPuzzle
from src.drums_puzzle import DrumsPuzzle
from src.center_room import CenterRoom

FLOOR_SIZE = 9


class Game(InstructionGroup):
    """
    Game keeps track of the overall game state
    Ex. What room/puzzle the player is in, sending player input to that puzzle,
        changing rooms etc.
    """

    def __init__(self):
        super().__init__()
        self.puzzle = CenterRoom()
        self.win_size = (Window.width, Window.height)

    def on_player_input(self, button):
        transition = self.puzzle.on_player_input(button)
        if transition:
            self.remove(self.puzzle)
            self.puzzle = transition
            self.puzzle.on_layout(self.win_size)
            self.add(self.puzzle)

    def on_update(self):
        self.puzzle.on_update()

    def on_layout(self, win_size):
        self.win_size = win_size
        self.remove(self.puzzle)
        self.puzzle.on_layout(win_size)
        self.add(self.puzzle)

