# common imports
from kivy.core.window import Window
from kivy.graphics.instructions import InstructionGroup

from src.center_room import CenterRoom


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
