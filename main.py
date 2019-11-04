# common imports
import sys

sys.path.append("..")
from common.core import BaseWidget, run
from common.gfxutil import (
    topleft_label,
    Cursor3D,
    AnimGroup,
    KFAnim,
    scale_point,
    resize_topleft_label,
    CEllipse,
    CRectangle,
)

from kivy.graphics import Translate, PushMatrix, PopMatrix

from common.synth import Synth
from common.audio import Audio

from kivy.core.window import Window
from kivy.graphics.instructions import InstructionGroup
import numpy as np

import pygame

from pygame.locals import JOYAXISMOTION, JOYBUTTONDOWN, JOYBUTTONUP, JOYHATMOTION, QUIT
import time

from character_movement import Game
from puzzle_graphics import MusicPuzzle

from common.button import Button


class MainWidget(BaseWidget):
    def __init__(self):
        super().__init__()
        # Init pygame controller input
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        pygame.init()

        self.puzzle_pos = (0, Window.height * 0.75)
        self.puzzle = MusicPuzzle()
        self.canvas.add(self.puzzle)

        self.game = Game(self.start_puzzle)
        self.canvas.add(self.game)

        self.state = "MOVEMENT"

    def on_update(self):
        self.puzzle.on_update()

        eventlist = pygame.event.get()
        for e in eventlist:
            if e.type == pygame.locals.JOYHATMOTION:
                x, y = self.joystick.get_hat(0)
                if self.state == "MOVEMENT":
                    cur_location = self.game.character.grid_pos
                    # Must subtract y because in 2d array, up is -1, but for controller up is +1
                    new_location = (cur_location[0] + y, cur_location[1] + x)
                    self.game.character.move_player(new_location)

                elif self.state == "PUZZLE":
                    try:
                        print(Button((x, y)))
                    except:
                        print("Not a valid button")

            elif e.type == pygame.locals.JOYBUTTONDOWN:
                button = Button(e.button)
                if self.state == "MOVEMENT":
                    pass
                elif self.state == "PUZZLE":
                    if button == Button.Y:
                        self.puzzle.play()
                    elif button == Button.B:
                        # Exit puzzle play and go back to movement
                        self.game.character.current_tile.deactivate()
                        self.state = "MOVEMENT"

    # will get called when the window size changes
    def on_layout(self, win_size):
        self.game.on_layout((win_size[0], int(win_size[1] * 0.75)))
        self.puzzle.on_layout((win_size))

    def start_puzzle(self):
        print("This was called")
        self.state = "PUZZLE"


if __name__ == "__main__":
    run(MainWidget)
