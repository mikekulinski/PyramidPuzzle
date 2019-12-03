from random import choice

from kivy.core.window import Window
from kivy.graphics import Color, Line, PopMatrix, PushMatrix, Rectangle, Translate
from kivy.graphics.instructions import InstructionGroup

from common.audio import Audio
from src.button import Button
from common.clock import AudioScheduler, SimpleTempoMap
from common.gfxutil import AnimGroup, CLabelRect, CRectangle, KFAnim
from common.synth import Synth
from src.grid import Tile, DoorTile, Grid
from src.puzzle_sound import Note, PuzzleSound
from src.character import Character
from src.puzzle import Puzzle
from src.puzzle_sound import Note, PuzzleSound





class BassPuzzle(Puzzle):
	def __init__(self, center_room):
		super().__init__()
		self.center_room = center_room
		self.fret_positions = [(1,4), (1,5), (1,6), (1,7)]

		self.string_position_start = [(0,4), (0,5), (0,6), (0,7)]
		self.string_position_end = [(8,4), (8,5), (8,6), (8,7)]
		self.string_pitches = [48, 52, 56, 60]

		self.interacting_block = False
		self.interacting_block_pos = None


		self.notes=[]
		self.place_objects()
	def block_interact(self, pos):
		pass

	'''
	def block_interact(self, pos):
		print('interact', pos)
		if self.interacting_block:
			self.interacting_block_pos = None
		else:
			self.interacting_block_pos = pos
		self.interacting_block = not self.interacting_block'''


	#def move_block(self, block_pos, )









	""" Mandatory Puzzle methods """

	def is_game_over(self):
		pass

	def place_objects(self):
		size = (self.grid.tile_side_len, self.grid.tile_side_len)

		self.objects[(4, 0)] = DoorTile(
			size, self.grid.grid_to_pixel((4, 0)), self.center_room
		)

		self.fsize = (self.grid.tile_side_len, self.grid.tile_side_len)
		stringidx = 0

		for stringp in range(len(self.string_position_start)):
			pixel_pos_start = self.grid.grid_to_pixel(self.string_position_start[stringp])
			pixel_pos_end = self.grid.grid_to_pixel(self.string_position_end[stringp]) 
			half_side = self.grid.tile_side_len // 2
			pixel_pos_start = (pixel_pos_start[0] + half_side, pixel_pos_start[1] + half_side)
			pixel_pos_end = (pixel_pos_end[0] + half_side*2, pixel_pos_end[1] + half_side)
			self.notes.append( Note(480, self.string_pitches[stringp]))
			self.objects[self.string_position_start[stringp]] = BassString(pixel_pos_start, pixel_pos_end, 5,(self.string_position_start[stringp], self.string_position_end[stringp]), self.string_pitches[stringp], stringidx)
			stringidx += 1

		for f in range(len(self.fret_positions)):
			fret = self.fret_positions[f]
			pos = self.grid.grid_to_pixel(fret)
			move_range = (self.string_position_start[f], self.string_position_end[f])
			self.objects[fret] = FretBlock(self.fsize,fret, pos, self.block_interact,move_range, "./data/boulder.jpg")

		self.add(PushMatrix())
		self.add(Translate(*self.grid.pos))

		for pos, obj in self.objects.items():
			self.add(obj)

		self.add(PopMatrix())
		self.audio = PuzzleSound([self.notes])

	def move_block(self,new_location,x,y):
		obj_loc = (new_location[0]+ x, new_location[1] + y)
		if Puzzle.is_valid_pos(self, obj_loc) and self.valid_block_move(obj_loc, self.objects[new_location].move_range):
			self.remove(self.objects[new_location])
			obj = FretBlock(self.fsize, obj_loc, self.grid.grid_to_pixel(obj_loc), self.block_interact, self.objects[new_location].move_range,"./data/boulder.jpg")
			del self.objects[new_location]

			self.add(PushMatrix())
			self.add(Translate(*self.grid.pos))
			self.add(obj)
			self.add(PopMatrix())

			self.objects[obj_loc] = obj
			return True
		else:
			return False

	def valid_block_move(self, pos, move_range):

		if move_range[0][0] < pos[0] < move_range[1][0] and move_range[0][1] <= pos[1] <= move_range[1][1]:
			return True
		else:
			return False
		
	def on_update(self):
		self.audio.on_update()

	def on_player_input(self, button):
		if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:
			self.character.change_direction(button.value)

			move_possible = True
			x, y = button.value
			cur_location = self.character.grid_pos
			new_location = (cur_location[0] + x, cur_location[1] + y)
			if new_location in self.objects:
				if self.objects[new_location].moveable:
					move_possible = self.move_block(new_location, x,y)

			self.character.move_player(new_location)

			if self.character.grid_pos in self.objects:
				if isinstance(obj, DoorTile):
					return obj.other_room
			if new_location in self.string_position_end:
				obj = self.objects[(self.character.grid_pos[0]-8, self.character.grid_pos[1])]

				self.play_string(obj.stringidx)

		elif button == Button.A:
			self.play_string(0)
			#self.character.interact()
			
	def play_string(self, stringidx):
		self.audio.update_sounds([self.notes[stringidx]])
		self.audio.toggle()

	def on_layout(self, win_size):
		self.remove(self.character)
		for pos, obj in self.objects.items():
			self.remove(obj)
		self.remove(self.grid)

		self.grid.on_layout(win_size)
		self.add(self.grid)

		self.place_objects()

		self.character.on_layout(win_size)
		self.add(self.character)


class BassString(InstructionGroup):
	def __init__(self, pos1, pos2, width, grid_start_end, note, idx):
		super().__init__()
		self.bassnote = note

		self.stringidx = idx

		self.grid_start = grid_start_end[0]
		self.grid_end = grid_start_end[1]
		self.pos1 = pos1
		self.pos2 = pos2
		self.width = width
		self.passable = True
		self.moveable = False
		self.makeline()

	def makeline(self):
		self.add(Color(0,0,0))
		poslist = list(self.pos1+self.pos2)
		self.add(Line(points=poslist, width=self.width))


class FretBlock(Tile):
	def __init__(self, size,grid_pos, pos, on_interact, move_range, icon_source):
		super().__init__(size,pos)
		self.move_range = move_range
		self.grid_pos = grid_pos
		self.pos = pos
		self.on_interact = on_interact
		self.icon_source = icon_source
		self.passable = False
		self.moveable = True
		self.set_color(color=Tile.base_color, source=self.icon_source)

	'''def move_block(self, new_pos):
		print('trying to move')
		self.pos = new_pos
		self.set_pos(self.pos)
		self.set_color(color=Tile.base_color, source=self.icon_source)'''

	def interact(self):
		self.on_interact()
