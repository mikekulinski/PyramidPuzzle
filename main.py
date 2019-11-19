# common imports
import sys

import pygame
from kivy.core.window import Window

from common.core import BaseWidget, run
from src.game import Game
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
        self.game = Game()
        self.canvas.add(self.game)

    def on_update(self):
        if self.control_type == "controller":
            button = UserInput.on_controller_input(self.joystick)
            if button:
                self.game.on_player_input(button)

        self.game.on_update()

    def on_key_down(self, keycode, modifiers):
        if self.control_type == "keyboard":
            button = UserInput.on_keyboard_input(keycode, modifiers)
            if button:
                self.game.on_player_input(button)

    # will get called when the window size changes
    def on_layout(self, win_size):
        self.game.on_layout(win_size)


if __name__ == "__main__":
    run(MainWidget, fullscreen=True)
