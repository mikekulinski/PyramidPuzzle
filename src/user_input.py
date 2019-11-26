import pygame.locals

from src.button import Button


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
            button = Button.LEFT
        elif keycode[1] == "right":
            button = Button.RIGHT
        elif keycode[1] == "up":
            button = Button.UP
        elif keycode[1] == "down":
            button = Button.DOWN
        elif keycode[1] == "p":
            button = Button.MINUS
        elif keycode[1] == "q":
            button = Button.PLUS
        elif keycode[1] == "a":
            button = Button.A
        elif keycode[1] == "b":
            button = Button.B
        elif keycode[1] == "escape":
            button = Button.ESC
        else:
            print(f"UNMAPPED KEYPRESS: {keycode[1]}")

        return button
