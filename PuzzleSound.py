
import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.clock import Clock, SimpleTempoMap, AudioScheduler, tick_str, kTicksPerQuarter, quantize_tick_up
from common.gfxutil import topleft_label
from common.synth import Synth


from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate
from kivy.clock import Clock as kivyClock

import numpy as np


class MainWidget(BaseWidget) :
	def __init__(self):
		super(MainWidget, self).__init__()

		self.audio = Audio(2)
		self.synth = Synth('../data/FluidR3_GM.sf2')

		self.tempo_map  = SimpleTempoMap(120)
		self.sched = AudioScheduler(self.tempo_map)

		self.sched.set_generator(self.synth)
		self.audio.set_generator(self.sched)

		song = [(480,60), (480,62), (480,64), (480,62), (480,64), (480,59), (960, 60)]
		#self.notes = [Note(240, (60)+i*2*(-1)**(i)) for i in range(8)]
		self.notes = [Note(*n) for n in song]
		self.sound = PuzzleSound(self.notes, self.sched, self.synth)

		self.label = topleft_label()
		self.add_widget(self.label)



	def on_key_down(self, keycode, modifiers):
		if keycode[1] == 'p':
			self.sound.toggle()
	def on_update(self) :
		self.audio.on_update()
		self.label.text = self.sched.now_str() + '\n'
		

class PuzzleSound(object):
	def __init__(self, notes, sched, synth):
		super().__init__()
		self.sched = sched
		self.synth = synth

		self.update_sounds(notes)

		self.soundplaying = False
		
	def update_sounds(self, notes):
		self.letters = []
		self.dur_midi= []
		self.notes = notes
		for note in notes:
			self.letters.append(note.get_letter())
			self.dur_midi.append((note.get_dur(), note.get_pitch()))
		self.noteseq = NoteSequencer(self.sched, self.synth, 1, (0,0), self.dur_midi)

	def toggle(self):
		self.noteseq.toggle()
		


class Note(object):
	def __init__(self, notedur, midipitch):
		super(Note, self).__init__()

		self.allnotes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
		ocatave = int(midipitch/12)-1
		noteidx = midipitch%12

		self.noteletter = self.allnotes[noteidx] + str(ocatave)
		self.midipitch = midipitch
		self.notedur = notedur

		self.sharp = False
		self.flat = False

	def set_note(self, pitch):
		ocatave = int(pitch/12)-1
		noteidx = pitch%12
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
			self.set_note(self.get_pitch()+1)
			self.sharp = True

	def add_flat(self):
		if not self.flat:
			self.set_note(self.get_pitch()-1)
			self.flat = True

	def remove_sharp(self):
		if self.sharp:
			self.set_note(self.get_pitch()-1)
			self.sharp = False

	def remove_flat(self):
		if self.flat:
			self.set_note(self.get_pitch()+1)
			self.flat = False





class NoteSequencer(object):
	"""Plays a single Sequence of notes. The sequence is a python list containing
	notes. Each note is (dur, pitch)."""
	def __init__(self, sched, synth, channel, program, notes, vel=60, loop=False):
		super(NoteSequencer, self).__init__()
		self.sched = sched
		self.synth = synth
		self.channel = channel
		self.program = program
		self.vel = vel
		self.notes = notes
		self.loop = loop
		self.playing = False

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
			length, pitch = self.notes[self.idx]
			if pitch != 0: # pitch 0 is a rest
				self.synth.noteon(self.channel, pitch, self.vel)  # play note
				self.sched.post_at_tick(self._note_off, tick + length * .9, pitch) # note off a bit later - slightly detached. 

			# schedule the next note:
			self.idx += 1
			self.cmd = self.sched.post_at_tick(self._note_on, tick + length)
		else:
			self.playing = False


	def _note_off(self, tick, pitch):
		# terminate current note:
		self.synth.noteoff(self.channel, pitch)






if __name__ == "__main__":
	run(MainWidget)


