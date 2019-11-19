# common imports
from kivy.graphics.instructions import InstructionGroup
from kivy.core.window import Window

from src.character import Character
from src.grid import Grid, Switch
from common.button import Button
from src.piano_puzzle import MusicPuzzle

FLOOR_SIZE = 9


class Game(InstructionGroup):
    def __init__(self):
        super().__init__()

        self.state = "MOVEMENT"

        # Add the puzzle to the game
        self.puzzle_pos = (0, Window.height * 0.75)
        self.puzzle = MusicPuzzle()
        self.add(self.puzzle)

        # Create the grid and add objects on top
        self.pitch_switch = (
            (2, 2),
            lambda size, pos: Switch(
                size, pos, self.on_pitch_mode, "./data/pitch_icon.png"
            ),
        )
        self.rhythm_switch = (
            (6, 4),
            lambda size, pos: Switch(
                size, pos, self.on_rhythm_mode, "./data/rhythm_icon.png"
            ),
        )
        self.key_switch = (
            (2, 6),
            lambda size, pos: Switch(
                size, pos, self.on_key_mode, "./data/key_icon.jpeg"
            ),
        )

        self.grid = Grid(
            num_tiles=9,
            objects=[self.pitch_switch, self.rhythm_switch, self.key_switch],
        )
        self.add(self.grid)

        # Add the character to the game
        self.character = Character(self)
        self.add(self.character)

    def handle_input(self, button):
        if self.state == "MOVEMENT":
            if button.name in ["UP", "DOWN", "LEFT", "RIGHT"]:
                x, y = button.value
                cur_location = self.character.grid_pos
                new_location = (cur_location[0] + y, cur_location[1] + x)
                self.character.move_player(new_location)
        else:
            if self.state == "PITCH":
                if button == Button.UP:
                    self.puzzle.on_up_arrow()
                elif button == Button.DOWN:
                    self.puzzle.on_down_arrow()
            elif self.state == "RHYTHM":
                if button == Button.LEFT:
                    self.puzzle.on_left_arrow()
                elif button == Button.RIGHT:
                    self.puzzle.on_right_arrow()
            elif self.state == "KEY":
                if button == Button.LEFT:
                    self.puzzle.on_L()
                elif button == Button.RIGHT:
                    self.puzzle.on_R()

            if button == Button.MINUS:
                self.puzzle.play(actual=True)
            elif button == Button.PLUS:
                self.puzzle.play(actual=False)
            elif button == Button.B:
                # Exit puzzle play and go back to movement
                self.character.current_tile.deactivate()
                self.state = "MOVEMENT"

    def on_key_mode(self):
        self.state = "KEY"

    def on_rhythm_mode(self):
        self.state = "RHYTHM"

    def on_pitch_mode(self):
        self.state = "PITCH"

    def on_update(self):
        self.puzzle.on_update()

    def on_layout(self, win_size):
        self.remove(self.grid)
        self.remove(self.puzzle)
        self.remove(self.character)

        self.grid.on_layout((win_size[0], int(win_size[1] * 0.75)))
        self.puzzle.on_layout(win_size)
        self.character.on_layout(win_size)

        self.add(self.grid)
        self.add(self.puzzle)
        self.add(self.character)

