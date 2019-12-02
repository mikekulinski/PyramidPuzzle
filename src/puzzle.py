from kivy.graphics.instructions import InstructionGroup
from src.grid import Grid
from kivy.core.window import Window
from kivy.graphics import Color
from common.gfxutil import CLabelRect, CRectangle
from src.character import Character


class Puzzle(InstructionGroup):
    def __init__(self):
        super().__init__()

        self.game_over = False

        self.grid = Grid(num_tiles=9)
        self.add(self.grid)

        self.objects = {}

        self.create_game_over_text((Window.width, Window.height))

        # Add the character to the game
        self.character = Character(self)
        self.add(self.character)

    def is_valid_pos(self, pos):
        if pos[0] < 0 or pos[0] >= self.grid.num_tiles:
            return False
        elif pos[1] < 0 or pos[1] >= self.grid.num_tiles:
            return False

        if pos in self.objects and not self.objects[pos].passable:
            return False
        return True

    def get_tile(self, pos):
        assert self.is_valid_pos(pos)
        return self.grid.get_tile(pos)



    def create_game_over_text(self, win_size):
        self.game_over_window_color = Color(rgba=(1, 1, 1, 1))
        self.game_over_window = CRectangle(
            cpos=(win_size[0] // 2, win_size[1] // 2),
            csize=(win_size[0] // 2, win_size[1] // 5),
        )
        self.game_over_text_color = Color(rgba=(0, 0, 0, 1))
        self.game_over_text = CLabelRect(
            (win_size[0] // 2, win_size[1] // 2), "You Win!", 70
        )

    def on_game_over(self):
        self.game_over = True
        self.add(self.game_over_window_color)
        self.add(self.game_over_window)
        self.add(self.game_over_text_color)
        self.add(self.game_over_text)

    def is_game_over(self):
        raise NotImplementedError

    def place_objects(self):
        raise NotImplementedError

    def on_player_input(self, button):
        raise NotImplementedError

    def on_update(self):
        raise NotImplementedError

    def on_layout(self, win_size):
        raise NotImplementedError
