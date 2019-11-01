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
    CEllipse,
)
from common.synth import Synth
from common.audio import Audio

from kivy.core.window import Window
import numpy as np

import pygame
from pygame.locals import *
import time


from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.properties import ObjectProperty, ListProperty


class MainWidget(BaseWidget):
    def __init__(self):
        super().__init__()

        self.label = topleft_label()
        self.add_widget(self.label)

        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        pygame.init()

    def on_update(self):
        eventlist = pygame.event.get()

        for e in eventlist:
            if e.type == QUIT:
                return

            # if e.type == pygame.locals.JOYAXISMOTION:
            #     x, y = self.joystick.get_axis(0), self.joystick.get_axis(1)
            #     print("axis x:" + str(x) + " axis y:" + str(y))
            if e.type == pygame.locals.JOYHATMOTION:
                x, y = self.joystick.get_hat(0)
                print("hat x:" + str(x) + " hat y:" + str(y))
            elif e.type == pygame.locals.JOYBUTTONDOWN:
                print("button:" + str(e.button))

        self.label.text = "Started Kivy"


if __name__ == "__main__":
    run(MainWidget)
