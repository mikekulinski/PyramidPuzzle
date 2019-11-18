import sys

sys.path.append("..")
from common.core import BaseWidget, run, lookup
from common.gfxutil import (
    topleft_label,
    CEllipse,
    KFAnim,
    AnimGroup,
    CRectangle,
    CLabelRect,
)

from common.audio import Audio
from common.mixer import Mixer
from common.note import NoteGenerator, Envelope
from common.wavegen import WaveGenerator, SpeedModulator
from common.wavesrc import WaveBuffer, WaveFile, make_wave_buffers
from common.synth import Synth

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from PuzzleSound import Note, PuzzleSound
from common.clock import (
    Clock,
    SimpleTempoMap,
    AudioScheduler,
    tick_str,
    kTicksPerQuarter,
    quantize_tick_up,
)

from random import randint, random, choice
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

notes_w_staff_lines = ["E4", "G4", "B4", "D5", "F5"]
names = "CDEFGAB"
all_notes = [n + "4" for n in names]
all_notes.extend([n + "5" for n in "CDEF"])
durations = [120, 240, 480, 960]
duration = choice(durations)
user_notes = [Note(duration, n.get_pitch() + 3) for n in notes]
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


class MainWidget(BaseWidget):
    def __init__(self):
        super().__init__()
        self.music_puzzle = DrumsPuzzle()
        self.canvas.add(self.music_puzzle)

    def on_update(self):
        self.music_puzzle.on_update()

    def on_key_down(self, keycode, modifiers):
        # trigger a note to play with keys 1-8

        if keycode[1] == "p":
            # move now bar across music bar
            self.music_puzzle.play(actual=True)


class DrumsPuzzle(InstructionGroup):
    def __init__(self):
        super().__init__()
        self.animations = AnimGroup()
        self.animations.add(self.music_bar)
        self.add(self.animations)

        self.audio = Audio(2)
        self.synth = Synth("./data/FluidR3_GM.sf2")

        self.tempo_map = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        self.sched.set_generator(self.synth)
        self.audio.set_generator(self.sched)
        self.actual_sound = PuzzleSound(notes, self.sched, self.synth)
        self.user_sound = PuzzleSound(user_notes, self.sched, self.synth)

        self.actual_key = "C"
        self.user_key = choice(key_names)
        self.key_label = CLabelRect(
            (Window.width // 30, 23 * Window.height // 32), f"Key: {self.user_key}", 34
        )
        self.add(Color(rgba=(1, 1, 1, 1)))
        self.add(self.key_label)

        self.game_over_window_color = Color(rgba=(1, 1, 1, 1))
        self.game_over_window = CRectangle(
            cpos=(Window.width // 2, Window.height // 2),
            csize=(Window.width // 2, Window.height // 5),
        )
        self.game_over_text_color = Color(rgba=(0, 0, 0, 1))
        self.game_over_text = CLabelRect(
            (Window.width // 2, Window.height // 2), "You Win!", 70
        )

    def on_update(self):
        self.animations.on_update()
        self.audio.on_update()
        self.key_label.set_text(f"Key: {self.user_key}")
        if self.is_game_over():
            self.add(self.game_over_window_color)
            self.add(self.game_over_window)
            self.add(self.game_over_text_color)
            self.add(self.game_over_text)

    def play(self, actual=False):
        self.music_bar.play()
        if actual:
            self.actual_sound.toggle()
        else:
            self.user_sound.toggle()

    def on_layout(self, win_size):
        self.music_bar.on_layout(win_size)
        self.remove(self.key_label)
        self.key_label = CLabelRect(
            (win_size[0] // 30, 23 * win_size[1] // 32), f"Key: {self.user_key}", 34
        )
        self.add(Color(rgba=(1, 1, 1, 1)))
        self.add(self.key_label)

        self.game_over_window_color = Color(rgba=(1, 1, 1, 1))
        self.game_over_window = CRectangle(
            cpos=(win_size[0] // 2, win_size[1] // 2),
            csize=(win_size[0] // 2, win_size[1] // 5),
        )
        self.game_over_text_color = Color(rgba=(0, 0, 0, 1))
        self.game_over_text = CLabelRect(
            (win_size[0] // 2, win_size[1] // 2), "You Win!", 70
        )


class MusicBar(InstructionGroup):
    def __init__(self, actual_notes, user_notes):
        super().__init__()
        self.win_size = (Window.width, Window.height)
        self.actual_notes = actual_notes
        self.user_notes = user_notes

        self.render_elements()

        self.time = 0
        self.now_bar_moving = False

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



if __name__ == "__main__":
    run(MainWidget)
