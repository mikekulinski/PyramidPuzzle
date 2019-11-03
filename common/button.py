from enum import Enum


class Button(Enum):
    # Main buttons
    B = 0
    A = 1
    Y = 2
    X = 3

    # Bumpers/Triggers
    L = 4
    R = 5
    ZL = 6
    ZR = 7

    # Control Buttons
    MINUS = 8
    PLUS = 9

    # Directions
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

