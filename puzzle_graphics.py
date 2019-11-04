import sys

sys.path.append("..")
from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup, CRectangle

from common.audio import Audio
from common.mixer import Mixer
from common.note import NoteGenerator, Envelope
from common.wavegen import WaveGenerator, SpeedModulator
from common.wavesrc import WaveBuffer, WaveFile, make_wave_buffers

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from PuzzleSound import Note

from random import randint, random
import numpy as np

notes = (
    Note(480, 60),
    Note(480, 62),
    Note(480, 64),
    Note(480, 65),
    Note(480, 67),
    Note(480, 69),
    Note(480, 71),
    Note(480, 72),
)
user_notes = [Note(n.get_dur(),n.get_pitch() + 3) for n in notes] 
notes_w_staff_lines = ['E4', 'G4', 'B4', 'D5', 'F5']
names = "CDEFGAB"
all_notes = [n + '4' for n in names]
all_notes.extend([n + '5' for n in 'CDEF'])

# will have access to note+octave, C4 = 0
# put music bar in instruction group for mike to use
# when receiving instructions from controller, change note object and graphics


class MainWidget(BaseWidget):
    def __init__(self):
        super().__init__()
        self.music_puzzle = MusicPuzzle()
        self.canvas.add(self.music_puzzle)

    def on_update(self):
        self.music_puzzle.on_update()

    def on_key_down(self, keycode, modifiers):
        # trigger a note to play with keys 1-8

        if keycode[1] == "p":
            # move now bar across music bar
            self.music_puzzle.play()

        if keycode[1] == "t":
            # move now bar across music bar
            self.music_puzzle.on_up_arrow()

        if keycode[1] == "g":
            # move now bar across music bar
            self.music_puzzle.on_down_arrow()


class MusicPuzzle(InstructionGroup):
    def __init__(self):
        super().__init__()
        self.animations = AnimGroup()
        self.music_bar = MusicBar(notes, user_notes)
        self.animations.add(self.music_bar)
        self.add(self.animations)

        self.audio = Audio(2)
        self.mixer = Mixer()
        self.mixer.set_gain(0.2)
        self.audio.set_generator(self.mixer)

    def on_update(self):
        self.animations.on_update()
        self.audio.on_update()

    def play(self):
        self.music_bar.play()

    def on_layout(self, win_size):
        self.music_bar.on_layout(win_size)

    def on_up_arrow(self):
        for note in user_notes:
            pitch = note.get_pitch()
            note.set_note(pitch+1)

    def on_down_arrow(self):
        for note in user_notes:
            pitch = note.get_pitch()
            note.set_note(pitch-1)


class MusicBar(InstructionGroup):
    def __init__(self, actual_notes, user_notes):
        super().__init__()
        self.win_size = (Window.width, Window.height)
        self.actual_notes = actual_notes
        self.user_notes = user_notes

        self.height = self.win_size[1] * 3 / 4
        self.staff_lines_height = (self.win_size[1] / 4) * (2/3) / 5
        self.middle_c_h = (self.win_size[1] / 4) / 6
        self.staff_h = self.middle_c_h + self.staff_lines_height

        self.notes_start = self.win_size[0]/10
        self.notes_width = self.win_size[0] - self.notes_start

        self.render_elements()

        self.time = 0
        self.now_bar_moving = False

    def render_elements(self):
        self.now_bar = Line(points=(self.notes_start, self.height, self.notes_start, self.win_size[1]))
        self.now_bar_pos = KFAnim((0, self.notes_start), (3, self.win_size[0]))
        self.border = Line(points=(0, self.height, self.win_size[0], self.height))
        
        #loop thru all notes and map positions to them--only draw lines for certain ones
        self.staff_lines = []
        self.staff_mappings = dict()

        for i in range(len(all_notes)):
            height = self.height + self.middle_c_h + self.staff_lines_height * i / 2.0
            if all_notes[i] in notes_w_staff_lines:
                self.staff_lines.append(Line(points=(0, height, self.win_size[0], height)))
            self.staff_mappings[all_notes[i]] = height - self.staff_lines_height / 2.0

        self.place_notes(actual=True)
        self.place_notes(actual=False)
        self.add(Color(a=1))
        
        self.add(self.now_bar)
        self.add(self.border)
        for line in self.staff_lines:
            self.add(line)
        self.clef = Rectangle(
            source="treble_clef_white.png",
            pos=(self.win_size[0] / 50, self.height + self.middle_c_h),
            size=(self.win_size[0] / 22, self.height / 4.5),
        )
        self.add(self.clef)

    def play(self):
        self.now_bar_moving = True

    def place_notes(self, actual=True):
        notes_to_place = self.actual_notes if actual else self.user_notes
        if not actual:
            self.add(Color(a=.5))
            self.user_note_instructions = set()

        num_measures = int(sum(note.get_dur()/480/4 for note in notes_to_place))
        note_index = 0
        # place all measure lines
        x_start = self.notes_start
        for i in range(num_measures):
            measure = []
            measure_beats = 0
            x_end = self.notes_start + self.notes_width * (i + 1) / num_measures
            while measure_beats < 1:
                duration = notes_to_place[note_index].get_dur() / 480 / 4
                pitch = notes_to_place[note_index].get_pitch()
                n_val = notes_to_place[note_index].get_letter()
                if len(n_val) == 3:
                    n_val = n_val[0::2]
                height = self.staff_mappings[n_val] if n_val in self.staff_mappings else self.height
                x_pos = x_start + (measure_beats) * (x_end - x_start)
                if n_val == 'C4': #ledger line
                    ledger_width = 15
                    ledger_height = height + self.staff_lines_height/2.0
                    ledger = Line(points=(x_pos - ledger_width, ledger_height, x_pos + self.staff_lines_height + ledger_width, ledger_height))
                    self.add(ledger)
                note_obj = Ellipse(
                        size=(self.staff_lines_height, self.staff_lines_height),
                        pos=(x_pos, height),
                    )
                self.add(note_obj)
                if not actual:
                    self.user_note_instructions.add(note_obj)
                    if n_val == 'C4':
                        self.user_note_instructions.add(ledger)
                measure_beats += duration
                note_index += 1
            self.add(Line(points=(x_end, self.height + self.staff_h, x_end, self.win_size[1] - self.middle_c_h)))
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
        self.win_size = win_size
        render_elements()


if __name__ == "__main__":
    run(MainWidget)
