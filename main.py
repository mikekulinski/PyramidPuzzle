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

        self.game = Game(self.pitch_mode, self.rhythm_mode, self.key_mode)
        self.canvas.add(self.game)

        self.puzzle_pos = (0, Window.height * 0.75)
        self.puzzle = MusicPuzzle()
        self.canvas.add(self.puzzle)

        self.state = "MOVEMENT"

    def on_update(self):
        eventlist = pygame.event.get()
        for e in eventlist:
            if e.type == pygame.locals.JOYHATMOTION:
                x, y = self.joystick.get_hat(0)
                if self.state == "MOVEMENT":
                    cur_location = self.game.character.grid_pos
                    new_location = (cur_location[0] + y, cur_location[1] + x)
                    self.game.character.move_player(new_location)
                else:
                    try:
                        button = Button((x, y))
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
                    except:
                        pass

            elif e.type == pygame.locals.JOYBUTTONDOWN:
                button = Button(e.button)
                if self.state == "MOVEMENT":
                    pass
                else:
                    if button == Button.Y:
                        self.puzzle.play(actual=True)
                    elif button == Button.X:
                        self.puzzle.play(actual=False)
                    elif button == Button.B:
                        # Exit puzzle play and go back to movement
                        self.game.character.current_tile.deactivate()
                        self.state = "MOVEMENT"

        self.puzzle.on_update()

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
