from common.audio import Audio
from common.clock import (
    AudioScheduler,
    SimpleTempoMap,
    kTicksPerQuarter,
    quantize_tick_up,
)
from common.synth import Synth


class PuzzleSound(object):
    def __init__(self, notes, bank=0, preset=0, loop=False, simon_says=False):
        super().__init__()
        self.audio = Audio(2)
        self.synth = Synth("./data/FluidR3_GM.sf2")

        self.tempo_map = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)
        self.sched.set_generator(self.synth)
        self.audio.set_generator(self.sched)

        self.notes = notes
        self.bank = bank
        self.preset = preset
        self.loop = loop
        self.simon_says = simon_says

        self.note_seq = NoteSequencer(
            sched=self.sched,
            synth=self.synth,
            channel=1,
            program=(self.bank, self.preset),
            notes=self.notes,
            loop=self.loop,
        )

    def set_notes(self, notes):
        self.notes = notes
        if self.simon_says:
            self.note_seq = NoteSequencer(
                sched=self.sched,
                synth=self.synth,
                channel=1,
                program=(self.bank, self.preset),
                notes=self.notes,
                loop=self.loop,
            )

        self.note_seq.stop()
        self.note_seq.set_notes(self.notes)

        if self.bank == 0:
            self.letters = [n.get_letter() for n in self.notes]

    def set_cb_ons(self, cb_ons):
        self.note_seq.set_cb_ons(cb_ons)

    def set_cb_offs(self, cb_offs):
        self.note_seq.set_cb_offs(cb_offs)

    def set_on_finished(self, on_finished):
        self.note_seq.set_on_finished(on_finished)

    def toggle(self):
        self.note_seq.toggle()

    def on_update(self):
        self.audio.on_update()


class NoteSequencer(object):
    """Plays a single Sequence of notes. The sequence is a python list containing
    notes. Each note is (dur, pitch)."""

    def __init__(self, sched, synth, channel, program, notes, vel=60, loop=False):
        super().__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program
        self.vel = vel
        self.notes = notes
        self.loop = loop

        self.cb_ons = []
        self.cb_offs = []
        self.on_finished = None

        self.playing = False

        self.cmd = None
        self.idx = 0

    def set_notes(self, notes):
        self.notes = notes

    def set_cb_ons(self, cb_ons):
        self.cb_ons = cb_ons

    def set_cb_offs(self, cb_offs):
        self.cb_offs = cb_offs

    def set_on_finished(self, on_finished):
        self.on_finished = on_finished

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
                notes_list = self.notes[self.idx]
            else:
                notes_list = [self.notes[self.idx]]

            for note in notes_list:
                dur = note.get_dur()
                pitch = note.get_pitch()
                self.synth.noteon(self.channel, pitch, self.vel)  # play note
                self.sched.post_at_tick(
                    self._note_off, tick + dur * 0.9, pitch
                )  # note off a bit later - slightly detached.

            # Call cb_on if it's there
            if self.idx < len(self.cb_ons):
                print("Played now bar")
                cb_on = self.cb_ons[self.idx]
                cb_on()

            # schedule the next note:
            self.idx += 1
            self.cmd = self.sched.post_at_tick(self._note_on, tick + dur)
        else:
            self.playing = False

    def _note_off(self, tick, pitch):
        # terminate current note:
        self.synth.noteoff(self.channel, pitch)

    def simon_says_on(self, tick, ignore):
        if self.idx < len(self.notes):
            note = self.notes[self.idx]
            dur = note.get_dur()
            pitch = note.get_pitch()
            cb_on = self.cb_ons[self.idx]

            # Play note and activate simon says tile
            self.synth.noteon(self.channel, pitch, self.vel)
            cb_on()

            # Schedule note and tile to turn off
            now = self.sched.get_tick()
            self.cmd = self.sched.post_at_tick(self.simon_says_off, now + dur, pitch)
            self.playing = True
        else:
            self.playing = False
            if self.on_finished:
                self.on_finished()

    def simon_says_off(self, tick, pitch):
        self.synth.noteoff(self.channel, pitch)
        cb_off = self.cb_offs[self.idx]
        cb_off()
        self.idx += 1

        now = self.sched.get_tick()
        self.cmd = self.sched.post_at_tick(self.simon_says_on, now + 240)


class Note(object):
    def __init__(self, notedur, midipitch):
        super().__init__()

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
        octave = int(midipitch / 12) - 1
        noteidx = midipitch % 12

        self.noteletter = self.allnotes[noteidx] + str(octave)
        self.midipitch = midipitch
        self.notedur = notedur

        self.sharp = False
        self.flat = False

    def set_note(self, pitch):
        octave = int(pitch / 12) - 1
        noteidx = pitch % 12
        self.noteletter = self.allnotes[noteidx] + str(octave)

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

