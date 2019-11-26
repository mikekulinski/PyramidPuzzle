from common.audio import Audio
from common.clock import (
    AudioScheduler,
    SimpleTempoMap,
    kTicksPerQuarter,
    quantize_tick_up,
)
from common.core import run
from common.synth import Synth


class PuzzleSound(object):
    def __init__(self, notes, bank=0, preset=0, loop=False):
        super().__init__()
        self.audio = Audio(2)
        self.synth = Synth("./data/FluidR3_GM.sf2")

        self.tempo_map = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        self.sched.set_generator(self.synth)
        self.audio.set_generator(self.sched)
        self.bank = bank
        self.preset = preset
        self.loop = loop
        self.noteseq = None

        self.update_sounds(notes)

        self.soundplaying = False

    def update_sounds(
        self, notes, callback_ons=[], callback_offs=[], finished_playing=None
    ):
        self.letters = []
        self.dur_midi = []
        self.notes = notes
        for note in notes:

            if type(note) is not list:
                self.letters.append(note.get_letter())
                self.dur_midi.append((note.get_dur(), note.get_pitch()))
            else:

                self.dur_midi.append([(n.get_dur(), n.get_pitch()) for n in note])
        if not self.noteseq:
            self.noteseq = NoteSequencer(
                self.sched,
                self.synth,
                1,
                (self.bank, self.preset),
                self.dur_midi,
                loop=self.loop,
                callback_ons=callback_ons,
                callback_offs=callback_offs,
                finished_playing=finished_playing,
            )
        self.noteseq.stop()
        self.noteseq.notes = self.dur_midi

    def toggle(self):
        self.noteseq.toggle()

    def on_update(self):
        self.audio.on_update()


class Note(object):
    def __init__(self, notedur, midipitch):
        super(Note, self).__init__()

        self.allnotes = [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B",
        ]
        ocatave = int(midipitch / 12) - 1
        noteidx = midipitch % 12

        self.noteletter = self.allnotes[noteidx] + str(ocatave)
        self.midipitch = midipitch
        self.notedur = notedur

        self.sharp = False
        self.flat = False

    def set_note(self, pitch):
        ocatave = int(pitch / 12) - 1
        noteidx = pitch % 12
        self.noteletter = self.allnotes[noteidx] + str(ocatave)

        self.midipitch = pitch

    def get_letter(self):
        return self.noteletter

    def get_pitch(self):
        return self.midipitch

    def get_pitch_to_play(self):
        return self.adj_pitch

    def set_dur(self, dur):
        self.notedur = dur

    def get_dur(self):
        return self.notedur

    def add_sharp(self):
        if not self.sharp:
            self.set_note(self.get_pitch() + 1)
            self.sharp = True

    def add_flat(self):
        if not self.flat:
            self.set_note(self.get_pitch() - 1)
            self.flat = True

    def remove_sharp(self):
        if self.sharp:
            self.set_note(self.get_pitch() - 1)
            self.sharp = False

    def remove_flat(self):
        if self.flat:
            self.set_note(self.get_pitch() + 1)
            self.flat = False


class NoteSequencer(object):
    """Plays a single Sequence of notes. The sequence is a python list containing
    notes. Each note is (dur, pitch)."""

    def __init__(
        self,
        sched,
        synth,
        channel,
        program,
        notes,
        callback_ons=[],
        callback_offs=[],
        vel=60,
        loop=False,
        finished_playing=None,
    ):
        super(NoteSequencer, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program
        self.vel = vel
        self.notes = notes
        self.loop = loop
        self.playing = False
        self.callback_ons = callback_ons
        self.callback_offs = callback_offs
        self.finished_playing = finished_playing

        self.cmd = None
        self.idx = 0

    def start(self):
        if self.playing:
            return

        self.playing = True
        self.synth.program(self.channel, self.program[0], self.program[1])

        # start from the beginning
        self.idx = 0

        # post the first note on the next quarter-note:
        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, kTicksPerQuarter)
        self.cmd = self.sched.post_at_tick(self._note_on, next_beat)

    def start_simon_says(self):
        if self.playing:
            return

        self.playing = True
        self.synth.program(self.channel, self.program[0], self.program[1])

        # start from the beginning
        self.idx = 0

        # post the first note on the next quarter-note:
        now = self.sched.get_tick()
        self.cmd = self.sched.post_at_tick(self.simon_says_on, now + 240)

    def stop(self):
        if not self.playing:
            return

        self.playing = False
        self.sched.remove(self.cmd)
        self.cmd = None

    def toggle(self):
        if self.playing:
            self.stop()
        else:
            self.start()

    def _note_on(self, tick, ignore):
        # if looping, go back to beginning
        if self.loop and self.idx >= len(self.notes):
            self.idx = 0

        # play new note if available
        if self.idx < len(self.notes):
            if type(self.notes[self.idx]) is list:
                notes_list = self.notes[self.idx].copy()
            else:
                notes_list = [self.notes[self.idx]]
            while notes_list:
                length, pitch = notes_list.pop(0)
                if pitch != 0:  # pitch 0 is a rest
                    self.synth.noteon(self.channel, pitch, self.vel)  # play note
                    self.sched.post_at_tick(
                        self._note_off, tick + length * 0.9, pitch
                    )  # note off a bit later - slightly detached.

            # schedule the next note:
            self.idx += 1
            self.cmd = self.sched.post_at_tick(self._note_on, tick + length)
        else:
            self.playing = False

    def _note_off(self, tick, pitch):
        # terminate current note:
        self.synth.noteoff(self.channel, pitch)

    def simon_says_on(self, tick, ignore):
        if self.idx < len(self.notes):
            length, pitch = self.notes[self.idx]
            cb_on = self.callback_ons[self.idx]

            # Play note and activate simon says tile
            self.synth.noteon(self.channel, pitch, self.vel)
            cb_on()

            # Schedule note and tile to turn off
            now = self.sched.get_tick()
            self.cmd = self.sched.post_at_tick(self.simon_says_off, now + length, pitch)
            self.playing = True
        else:
            self.playing = False
            if self.finished_playing:
                self.finished_playing()

    def simon_says_off(self, tick, pitch):
        self.synth.noteoff(self.channel, pitch)
        cb_off = self.callback_offs[self.idx]
        cb_off()
        self.idx += 1

        now = self.sched.get_tick()
        self.cmd = self.sched.post_at_tick(self.simon_says_on, now + 240)
