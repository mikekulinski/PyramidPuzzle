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

        self.game = Game()
        self.canvas.add(self.game)

    def on_update(self):
        self.puzzle.on_update()

        eventlist = pygame.event.get()
        for e in eventlist:
            if e.type == pygame.locals.JOYHATMOTION:
                x, y = self.joystick.get_hat(0)

                cur_location = self.game.character.grid_pos
                # Must subtract y because in 2d array, up is -1, but for controller up is +1
                new_location = (cur_location[0] + y, cur_location[1] + x)
                self.game.character.move_player(new_location)
                print("hat x:" + str(x) + " hat y:" + str(y))

            elif e.type == pygame.locals.JOYBUTTONDOWN:
                print("button down:" + str(e.button))
                button = Button(e.button)
                if button == Button.Y:
                    self.puzzle.play()
            elif e.type == pygame.locals.JOYBUTTONUP:
                print("button up:" + str(e.button))

    # will get called when the window size changes
    def on_layout(self, win_size):
        self.puzzle_pos = (0, win_size[1] * 0.75)

        self.canvas.add(PushMatrix())
        self.canvas.add(Translate(*self.puzzle_pos))
        self.puzzle.on_layout(win_size)
        self.canvas.add(PopMatrix())

        self.game.on_layout((win_size[0], int(win_size[1] * 0.75)))


if __name__ == "__main__":
    run(MainWidget)
