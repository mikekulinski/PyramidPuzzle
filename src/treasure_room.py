from kivy.graphics import PopMatrix, PushMatrix, Translate, Color
from kivy.core.window import Window
from common.gfxutil import CLabelRect, CRectangle

from src.button import Button
from src.grid import DoorTile, Tile
from src.puzzle import Puzzle


class TreasureRoom(Puzzle):
    def __init__(self, level=0, prev_room=None, on_finished_puzzle=None):
        super().__init__()
        self.create_objects()
        self.place_objects()
        self.blocks_placed = 0
        self.create_treasure_popup((Window.width, Window.height))

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        pass

    def create_objects(self):
        self.objects = {}

        size = (self.grid.tile_side_len, self.grid.tile_side_len)
        icons = [
            "./data/guitar.png",
            "./data/bass.png",
            "./data/drums.png",
            "./data/piano.png",
        ]
        init_positions = [(1, 1), (1, 7), (7, 1), (7, 7)]
        final_positions = [(2, 4), (3, 4), (5, 4), (6, 4)]
        colors = [
            Color(hsv=(0, 0.5, 1)),  # Green
            Color(hsv=(0.15, 0.5, 1)),  # Red
            Color(hsv=(0.25, 0.5, 1)),  # Yellow
            Color(hsv=(0.5, 0.5, 1)),  # Blue
        ]
        for i in range(len(icons)):
            self.objects[init_positions[i]] = MovingBlock(
                size,
                self.grid.grid_to_pixel(init_positions[i]),
                ((1, 1), (8, 8)),
                colors[i],
                icons[i],
                final_positions[i],
            )
            self.grid.get_tile(final_positions[i]).set_color(colors[i])

    def place_objects(self):
        self.create_objects()
        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def valid_block_move(self, pos, move_range):
        return (
            move_range[0][0] <= pos[0] < move_range[1][0]
            and move_range[0][1] <= pos[1] < move_range[1][1]
        )

    def move_block(self, new_location, x, y):
        obj_loc = (new_location[0] + x, new_location[1] + y)

        if self.is_valid_pos(obj_loc) and self.valid_block_move(
            obj_loc, self.objects[new_location].move_range
        ):
            self.remove(self.objects[new_location])
            obj = MovingBlock(
                self.objects[new_location].size,
                self.grid.grid_to_pixel(obj_loc),
                self.objects[new_location].move_range,
                self.objects[new_location].color,
                self.objects[new_location].icon_source,
                self.objects[new_location].final_position,
            )
            del self.objects[new_location]

            self.add(PushMatrix())
            self.add(Translate(*self.grid.pos))
            self.add(obj)
            self.add(PopMatrix())

            self.objects[obj_loc] = obj
            self.blocks_placed += self.objects[obj_loc].on_block_placement(obj_loc)
            return True
        else:
            return False

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            move_possible = True
            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            self.character.change_direction(button.value)
            if new_location in self.objects:
                if self.objects[new_location].moveable:
                    move_possible = self.move_block(new_location, x, y)
            if move_possible:
                self.character.move_player(new_location)
            if self.character.grid_pos in self.objects:
                if isinstance(self.objects[self.character.grid_pos], DoorTile):
                    if not isinstance(
                        self.objects[self.character.grid_pos].other_room, Puzzle
                    ):
                        # instantiate class when we enter the door
                        self.objects[self.character.grid_pos].other_room = self.objects[
                            self.character.grid_pos
                        ].other_room(self, self.level + 1)
                    return self.objects[self.character.grid_pos].other_room
            if self.blocks_placed == 4:
                self.on_game_over()


    def create_treasure_popup(self, win_size):
        self.game_over_window_color = Color(rgba=(1, 1, 1, 1))
        self.game_over_window = CRectangle(
            cpos=(win_size[0] // 2, win_size[1] // 2),
            csize=(win_size[0] // 2, win_size[1] // 5),
        )
        self.game_over_text_color = Color(rgba=(0, 0, 0, 1))
        self.game_over_text = CLabelRect(
            (win_size[0] // 2, win_size[1] // 2), "You unlocked the pharaoh's treasure!\nYou WIN!", 40
        )
        self.treasure = CRectangle(
            cpos=(win_size[0] // 2, win_size[1] // 4),
            csize=(win_size[0] // 4, win_size[1] // 4),
            source='./data/treasure.png'
        )

    def on_game_over(self):
        self.game_over = True
        self.add(self.game_over_window_color)
        self.add(self.game_over_window)
        self.add(self.game_over_text_color)
        self.add(self.game_over_text)
        self.add(self.game_over_window_color)
        self.add(self.treasure)


    def on_update(self):
        pass

    def on_layout(self, win_size):
        self.remove(self.character)
        self.remove(self.grid)
        self.grid.on_layout(win_size)
        for pos, obj in self.objects.items():
            self.remove(obj)

        self.add(self.grid)
        self.place_objects()
        self.character.on_layout(win_size)
        self.add(self.character)
        self.create_treasure_popup(win_size)
        if self.game_over:
            self.remove(self.game_over_window_color)
            self.remove(self.game_over_window)
            self.remove(self.game_over_text_color)
            self.remove(self.game_over_text)
            self.remove(self.treasure)

            self.on_game_over()


class MovingBlock(Tile):
    def __init__(self, size, pos, move_range, color, icon_source, final_position):
        super().__init__(size, pos)
        self.icon_source = icon_source
        self.passable = False
        self.moveable = True
        self.move_range = move_range
        self.final_position = final_position
        self.color = color

        self.set_color(color=color, source=self.icon_source)

    def on_block_placement(self, pos):
        if pos == self.final_position:
            self.moveable = False
            return 1
        return 0
