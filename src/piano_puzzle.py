from random import choice

from kivy.core.window import Window
from kivy.graphics import (
    Color,
    Ellipse,
    Line,
    PopMatrix,
    PushMatrix,
    Rectangle,
    Translate,
)
from kivy.graphics.instructions import InstructionGroup

from src.button import Button
from common.gfxutil import AnimGroup, CLabelRect, KFAnim
from src.grid import DoorTile, Switch, Tile
from src.puzzle_sound import Note, PuzzleSound

from src.puzzle import Puzzle

levels = {
        0: (
            Note(480, 60),
            Note(480, 62),
            Note(480, 65),
            Note(480, 67),
            Note(480, 70),
            Note(480, 72),
            Note(480, 70),
            Note(480, 72),
        ),
        1: (
            Note(480, 69),
            Note(480, 62),
            Note(480, 64),
            Note(480, 65),
            Note(480, 67),
            Note(480, 69),
            Note(480, 71),
            Note(480, 72),
            Note(480, 60),
            Note(480, 62),
            Note(480, 64),
            Note(480, 65),
            Note(480, 67),
            Note(480, 69),
            Note(480, 71),
            Note(480, 72),
        ),
        2: (
            Note(480, 60),
            Note(480, 62),
            Note(480, 64),
            Note(480, 65),
            Note(480, 67),
            Note(480, 69),
            Note(480, 71),
            Note(480, 72),
        ),
        3: (
            Note(480, 60),
            Note(480, 62),
            Note(480, 64),
            Note(480, 65),
            Note(480, 67),
            Note(480, 69),
            Note(480, 71),
            Note(480, 72),
        ),
}

notes_w_staff_lines = ["E4", "G4", "B4", "D5", "F5"]
names = "CDEFGAB"
all_notes = [n + "4" for n in names]
all_notes.extend([n + "5" for n in "CDEF"])
durations = [120, 240, 480, 960]
key_names = ["C", "G", "D", "F", "Bb", "Eb"]
keys = {
    "C": {"#": [], "b": []},
    "G": {"#": ["F"], "b": []},
    "D": {"#": ["C", "F"], "b": []},
    "F": {"#": [], "b": ["B"]},
    "Bb": {"#": [], "b": ["B", "E"]},
    "Eb": {"#": [], "b": ["B", "E", "A"]},
}


# will have access to note+octave, C4 = 0
# put music bar in instruction group for mike to use
# when receiving instructions from controller, change note object and graphics


class PianoPuzzle(Puzzle):
    def __init__(self, center_room, level=0):
        super().__init__()
        self.center_room = center_room
        self.animations = AnimGroup()
        self.level = level
        self.notes = levels[level]
        duration = choice(durations)
        pitch_shift = choice(range(-3, 4))
        self.user_notes = [Note(duration, n.get_pitch() + pitch_shift) for n in self.notes]
        self.music_bar = MusicBar(self.notes, self.user_notes)
        self.animations.add(self.music_bar)
        self.add(self.animations)

        self.actual_sound = PuzzleSound(self.notes)
        self.user_sound = PuzzleSound(self.user_notes)

        self.actual_key = "C"
        self.user_key = choice(key_names)

        self.place_objects()

        self.key_label = CLabelRect(
            (Window.width // 30, 23 * Window.height // 32), f"Key: {self.user_key}", 34
        )
        self.add(Color(rgba=(1, 1, 1, 1)))
        self.add(self.key_label)

    def play(self, actual=False):
        if actual:
            print("Should be setting the cb_ons")
            self.actual_sound.set_cb_ons([self.music_bar.play])
            self.actual_sound.toggle()
        else:
            self.user_sound.set_cb_ons([self.music_bar.play])
            self.user_sound.toggle()

    def on_pitch_change(self, pitch_index):
        offset = 1 if self.character.direction == Button.RIGHT.value else -1
        for note in self.user_notes:
            pitch = note.get_pitch()
            note.set_note(pitch + offset)
        self.user_sound.set_notes(self.user_notes)

    def on_duration_change(self, dur_index):
        for note in self.user_notes:
            note.set_dur(durations[dur_index])
        self.user_sound.set_notes(self.user_notes)

    def on_key_change(self, key_index):
        self.user_key = key_names[key_index]
        self.update_key()
        self.user_sound.set_notes(self.user_notes)

    def update_key(self):
        key_sig = keys[self.user_key]
        for note in self.user_notes:
            if note.get_letter()[0] not in key_sig["#"]:
                note.remove_sharp()
            if note.get_letter()[0] not in key_sig["b"]:
                note.remove_flat()

            if note.get_letter()[0] in key_sig["#"]:
                note.add_sharp()
            if note.get_letter()[0] in key_sig["b"]:
                note.add_flat()

    """ Mandatory Puzzle methods """

    def is_game_over(self):
        same_key = self.user_key == self.actual_key
        same_dur = (
            self.music_bar.user_notes[0].get_dur()
            == self.music_bar.actual_notes[0].get_dur()
        )
        same_pitch = (
            self.music_bar.user_notes[0].get_pitch()
            == self.music_bar.actual_notes[0].get_pitch()
        )

        return same_key and same_dur and same_pitch

    def create_objects(self):
        self.objects = {}
        size = (self.grid.tile_side_len, self.grid.tile_side_len)

        #PITCH
        pitch_color = Color(rgba=(.2, .5, 1, 1))
        for i in range(7): #rhythm
            self.grid.get_tile((i+1, 7)).set_color(pitch_color)

        self.pitch_block = MovingBlock(
            size,
            self.grid.grid_to_pixel((4, 7)),
            ((1,7), (8,7)),
            "./data/pitch_icon.png",
            self.on_pitch_change,
        )
        self.objects[(4, 7)] = self.pitch_block

        #RHYTHM
        rhythm_color = Color(rgba=(0, .5, .5, 1))
        for i in range(len(durations)): #rhythm
            self.grid.get_tile((i+3, 2)).set_color(rhythm_color)
        duration = self.user_notes[0].get_dur()
        self.rhythm_block = MovingBlock(
            size,
            self.grid.grid_to_pixel((durations.index(duration)+3, 2)),
            ((3,2), (7,2)),
            "./data/rhythm_icon.png",
            self.on_duration_change,
        )
        self.objects[(durations.index(duration)+3, 2)] = self.rhythm_block

        #KEY
        key_color = Color(rgba=(.2, .5, 0, 1))
        for i in range(len(key_names)):
            self.grid.get_tile((i+1, 5)).set_color(key_color)

        self.key_block = MovingBlock(
            size,
            self.grid.grid_to_pixel((key_names.index(self.user_key)+1, 5)),
            ((1,5), (7,5)),
            "./data/key_icon.jpeg",
            self.on_key_change,
        )
        self.objects[(key_names.index(self.user_key)+1, 5)] = self.key_block
        self.objects[(8, 4)] = DoorTile(
            size, self.grid.grid_to_pixel((8, 4)), self.center_room
        )

        

    def place_objects(self):
        self.create_objects()

        self.add(PushMatrix())
        self.add(Translate(*self.grid.pos))

        for pos, obj in self.objects.items():
            self.add(obj)

        self.add(PopMatrix())

    def move_block(self,new_location,x,y):
        obj_loc = (new_location[0]+ x, new_location[1] + y)

        if self.is_valid_pos(obj_loc) and self.valid_block_move(obj_loc, self.objects[new_location].move_range):
            self.remove(self.objects[new_location])
            obj = MovingBlock(self.objects[new_location].size, self.grid.grid_to_pixel(obj_loc),self.objects[new_location].move_range, self.objects[new_location].icon_source, self.objects[new_location].callback)
            del self.objects[new_location]

            self.add(PushMatrix())
            self.add(Translate(*self.grid.pos))
            self.add(obj)
            self.add(PopMatrix())

            self.objects[obj_loc] = obj
            self.objects[obj_loc].on_block_placement(obj_loc)
            return True
        else:
            return False

    def valid_block_move(self, pos, move_range):
        return move_range[0][0] <= pos[0] < move_range[1][0] and move_range[0][1] <= pos[1] <= move_range[1][1]

    def on_player_input(self, button):
        if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
            move_possible = True
            x, y = button.value
            cur_location = self.character.grid_pos
            new_location = (cur_location[0] + x, cur_location[1] + y)
            self.character.change_direction(button.value)
            if new_location in self.objects:
                if self.objects[new_location].moveable:
                    move_possible = self.move_block(new_location, x,y)
            if move_possible:
                self.character.move_player(new_location)
            if self.character.grid_pos in self.objects:
                if isinstance(self.objects[self.character.grid_pos], DoorTile):
                    if not isinstance(self.objects[self.character.grid_pos].other_room, Puzzle):
                        #instantiate class when we enter the door
                        self.objects[self.character.grid_pos].other_room = self.objects[self.character.grid_pos].other_room(self, self.level+1)
                    return self.objects[self.character.grid_pos].other_room
        if button == Button.MINUS:
            self.play(actual=True)
        elif button == Button.PLUS:
            self.play(actual=False)

    def on_update(self):
        self.animations.on_update()
        self.actual_sound.on_update()
        self.user_sound.on_update()
        self.key_label.set_text(f"Key: {self.user_key}")
        if not self.game_over and self.is_game_over():
            self.center_room.on_finished_puzzle()
            self.on_game_over()
            if self.level < 3:
                size = (self.grid.tile_side_len, self.grid.tile_side_len)
                self.objects[(0, 4)] = DoorTile(
                    size, self.grid.grid_to_pixel((0, 4)), PianoPuzzle
                )
                self.add(PushMatrix())
                self.add(Translate(*self.grid.pos))
                self.add(self.objects[(0, 4)])
                self.add(PopMatrix())

    def on_layout(self, win_size):
        self.remove(self.character)
        self.remove(self.grid)
        self.grid.on_layout((win_size[0], 0.75 * win_size[1]))
        for pos, obj in self.objects.items():
            self.remove(obj)

        self.add(self.grid)
        self.place_objects()
        self.character.on_layout(win_size)
        self.add(self.character)

        self.music_bar.on_layout(win_size)
        self.remove(self.key_label)
        self.key_label = CLabelRect(
            (win_size[0] // 30, 23 * win_size[1] // 32), f"Key: {self.user_key}", 34
        )
        self.add(Color(rgba=(1, 1, 1, 1)))
        self.add(self.key_label)

        self.create_game_over_text(win_size)
        if self.game_over:
            self.remove(self.game_over_window_color)
            self.remove(self.game_over_window)
            self.remove(self.game_over_text_color)
            self.remove(self.game_over_text)

            self.on_game_over()


class MusicBar(InstructionGroup):
    def __init__(self, actual_notes, user_notes):
        super().__init__()
        self.win_size = (Window.width, Window.height)
        self.actual_notes = actual_notes
        self.user_notes = user_notes

        self.render_elements()

        self.time = 0
        self.now_bar_moving = False

    def render_elements(self):
        self.height = self.win_size[1] * 3 / 4
        self.staff_lines_height = (self.win_size[1] / 4) * (2 / 3) / 5
        self.middle_c_h = (self.win_size[1] / 4) / 6
        self.staff_h = self.middle_c_h + self.staff_lines_height

        self.notes_start = self.win_size[0] / 10
        self.notes_width = self.win_size[0] - self.notes_start

        t = (sum(note.get_dur() for note in self.actual_notes) + 480) / 960
        self.now_bar = Line(
            points=(self.notes_start, self.height, self.notes_start, self.win_size[1])
        )
        self.now_bar_pos = KFAnim((0, self.notes_start), (t, self.win_size[0]))
        self.border = Line(points=(0, self.height, self.win_size[0], self.height))

        # loop thru all notes and map positions -only draw lines for certain ones

        self.staff_lines = []
        self.staff_mappings = dict()

        for i in range(len(all_notes)):
            height = self.height + self.middle_c_h + self.staff_lines_height * i / 2.0
            if all_notes[i] in notes_w_staff_lines:

                self.staff_lines.append(
                    Line(points=(0, height, self.win_size[0], height))
                )
            self.staff_mappings[all_notes[i]] = height - self.staff_lines_height / 2.0

        self.place_notes(actual=True)
        self.place_notes(actual=False)
        self.add(Color(a=1))

        self.add(self.now_bar)
        self.add(self.border)
        for line in self.staff_lines:
            self.add(line)
        self.clef = Rectangle(
            source="./data/treble_clef_white.png",
            pos=(self.win_size[0] / 50, self.height + self.middle_c_h),
            size=(self.win_size[0] / 22, self.height / 4.5),
        )
        self.add(self.clef)

    def play(self):
        self.now_bar_moving = True

    def place_notes(self, actual=True):
        notes_to_place = self.actual_notes if actual else self.user_notes
        if actual:
            self.add(Color(a=0.5))
        else:
            self.user_note_instructions = set()

        num_measures = int(sum(note.get_dur() / 480 / 4 for note in self.actual_notes))
        note_index = 0
        # place all measure lines
        x_start = self.notes_start
        for i in range(num_measures):
            # measure = []
            measure_beats = 0
            x_end = self.notes_start + self.notes_width * (i + 1) / num_measures
            while measure_beats < 1 and note_index < len(notes_to_place):
                duration = notes_to_place[note_index].get_dur() / 480 / 4
                # pitch = notes_to_place[note_index].get_pitch()
                n_val = notes_to_place[note_index].get_letter()
                if len(n_val) == 3:
                    n_val = n_val[0::2]
                height = (
                    self.staff_mappings[n_val]
                    if n_val in self.staff_mappings
                    else self.height
                )
                x_pos = x_start + (measure_beats) * (x_end - x_start)
                if n_val == "C4":  # ledger line
                    ledger_width = 15
                    ledger_height = height + self.staff_lines_height / 2.0
                    ledger = Line(
                        points=(
                            x_pos - ledger_width,
                            ledger_height,
                            x_pos + self.staff_lines_height + ledger_width,
                            ledger_height,
                        )
                    )
                    self.add(ledger)
                note_obj = NoteIcon(self.staff_lines_height, x_pos, height)
                self.add(note_obj)
                if not actual:
                    self.user_note_instructions.add(note_obj)
                    if n_val == "C4":
                        self.user_note_instructions.add(ledger)
                measure_beats += duration
                note_index += 1
            self.add(
                Line(
                    points=(
                        x_end,
                        self.height + self.staff_h,
                        x_end,
                        self.win_size[1] - self.middle_c_h,
                    )
                )
            )
            x_start = x_end

    def on_update(self, dt):
        if self.now_bar_moving:
            pos = self.now_bar_pos.eval(self.time)
            self.now_bar.points = (pos, self.height, pos, self.win_size[1])
            self.time += dt
            if pos == self.win_size[0]:
                self.time = 0
                self.now_bar_moving = False
                pos = self.now_bar_pos.eval(self.time)
                self.now_bar.points = (pos, self.height, pos, self.win_size[1])
        for ins in self.user_note_instructions:
            self.remove(ins)
        self.place_notes(actual=False)

        return

    def on_layout(self, win_size):
        self.clear()

        self.win_size = win_size
        self.render_elements()


class NoteIcon(InstructionGroup):
    def __init__(self, radius, x_pos, y_pos):
        super().__init__()
        self.circle = Ellipse(size=(radius, radius), pos=(x_pos, y_pos))
        self.line = Line(
            points=(x_pos + radius, y_pos + radius, x_pos + radius, y_pos + 3 * radius)
        )
        self.add(self.circle)
        self.add(self.line)

    def on_update(self):
        self.circle.on_update()
        self.line.on_update()


class MovingBlock(Tile):
    color = Color(rgba=(.2, .8, .5, 1))
    def __init__(self, size, pos, move_range, icon_source, callback):
        super().__init__(size, pos)
        self.move_range = move_range
        self.icon_source = icon_source
        self.passable = False
        self.moveable = True
        self.callback = callback

        self.set_color(color=MovingBlock.color, source=self.icon_source)

    def on_block_placement(self, pos):
        idx = pos[0] - self.move_range[0][0]
        self.callback(idx)