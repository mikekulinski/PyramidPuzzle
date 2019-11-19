import pygame.locals
from common.button import Button


class UserInput(object):
    @staticmethod
    def on_controller_input(joystick):
        button = None
        eventlist = pygame.event.get()
        for e in eventlist:
            try:
                if e.type == pygame.locals.JOYHATMOTION:
                    x, y = joystick.get_hat(0)
                    button = Button((x, y))
                    break
                elif e.type == pygame.locals.JOYBUTTONDOWN:
                    button = Button(e.button)
                    break

            except Exception:
                pass

        return button

    @staticmethod
    def on_keyboard_input(keycode, modifiers):
        button = None
        if keycode[1] == "left":
            button = Button((-1, 0))
        elif keycode[1] == "right":
            button = Button((1, 0))
        elif keycode[1] == "up":
            button = Button((0, 1))
        elif keycode[1] == "down":
            button = Button((0, -1))
        elif keycode[1] == "p":
            button = Button(8)
        elif keycode[1] == "q":
            button = Button(9)
        elif keycode[1] == "b":
            button = Button(0)
        else:
            print(f"UNMAPPED KEYPRESS: {keycode[1]}")

        return button
