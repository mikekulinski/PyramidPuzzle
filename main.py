# common imports
import sys

import pygame
from kivy.core.window import Window

from common.button import Button
from common.core import BaseWidget, run
from src.game import Game
from src.piano_puzzle import MusicPuzzle
from src.user_input import UserInput


class MainWidget(BaseWidget):
    def __init__(self):
        super().__init__()
        # Determine what controller type should be used
        num_args = len(sys.argv)
        self.control_type = "keyboard"
        if num_args > 1:
            self.control_type = sys.argv[1].lower()

        # Init control input
        if self.control_type == "controller":
            # Init pygame controller input
            print("Initiated controller")
            pygame.joystick.init()
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            pygame.init()
        elif self.control_type == "keyboard":
            pass
        else:
            print("INVALID CONTROL TYPE")
            return

        # Init game
        self.game = Game(self.pitch_mode, self.rhythm_mode, self.key_mode)
        self.canvas.add(self.game)

        self.puzzle_pos = (0, Window.height * 0.75)
        self.puzzle = MusicPuzzle()
        self.canvas.add(self.puzzle)

        self.state = "MOVEMENT"

    def on_update(self):
        if self.control_type == "controller":
            button = UserInput.on_controller_input(self.joystick)
            if button:
                self.handle_input(button)

        self.puzzle.on_update()

    def on_key_down(self, keycode, modifiers):
        if self.control_type == "keyboard":
            button = UserInput.on_keyboard_input(keycode, modifiers)
            if button:
                self.handle_input(button)

    def handle_input(self, button):
        if self.state == "MOVEMENT":
            if button.name in ["UP", "DOWN", "LEFT", "RIGHT"]:
                x, y = button.value
                cur_location = self.game.character.grid_pos
                new_location = (cur_location[0] + y, cur_location[1] + x)
                self.game.character.move_player(new_location)
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
                self.game.character.current_tile.deactivate()
                self.state = "MOVEMENT"

    # will get called when the window size changes
    def on_layout(self, win_size):
        self.game.on_layout((win_size[0], int(win_size[1] * 0.75)))
        self.puzzle.on_layout((win_size))

    def key_mode(self):
        self.state = "KEY"

    def rhythm_mode(self):
        self.state = "RHYTHM"

    def pitch_mode(self):
        self.state = "PITCH"


if __name__ == "__main__":
    run(MainWidget, fullscreen=True)
