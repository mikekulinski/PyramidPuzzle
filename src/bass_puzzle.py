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





class BassPuzzle(Puzzle):
	def __init__(self, center_room):
		super().__init__()
		self.center_room = center_room
		self.fret_positions = [(1,4), (1,5), (1,6), (1,7)]
		self.string_position_start = [(0,4), (0,5), (0,6), (0,7)]
		self.string_position_end = [(8,4), (8,5), (8,6), (8,7)]

		self.interacting_block = False
		self.interacting_block_pos = None

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
		for stringp in range(len(self.string_position_start)):
			pixel_pos_start = self.grid.grid_to_pixel(self.string_position_start[stringp])
			pixel_pos_end = self.grid.grid_to_pixel(self.string_position_end[stringp]) 
			half_side = self.grid.tile_side_len // 2
			pixel_pos_start = (pixel_pos_start[0] + half_side, pixel_pos_start[1] + half_side)
			pixel_pos_end = (pixel_pos_end[0] + half_side*2, pixel_pos_end[1] + half_side)

			self.objects[self.string_position_start[stringp]] = BassString(pixel_pos_start, pixel_pos_end, 5)
		for fret in self.fret_positions:
			pos = self.grid.grid_to_pixel(fret)
			self.objects[fret] = FretBlock(self.fsize,fret, pos, self.block_interact, "./data/boulder.jpg")

		self.add(PushMatrix())
		self.add(Translate(*self.grid.pos))

		for pos, obj in self.objects.items():
			self.add(obj)

		self.add(PopMatrix())


	def move_block(self):
		pass
	def on_update(self):
		pass

	def on_player_input(self, button):
		if button in [Button.UP, Button.DOWN, Button.LEFT, Button.RIGHT]:

			x, y = button.value
			cur_location = self.character.grid_pos
			new_location = (cur_location[0] + x, cur_location[1] + y)
			if new_location in self.objects:
				if self.objects[new_location].moveable:
					obj_loc = (new_location[0]+ x, new_location[1] + y)
					self.remove(self.objects[new_location])
					del self.objects[new_location]
					obj = FretBlock(self.fsize, obj_loc, self.grid.grid_to_pixel(obj_loc), self.block_interact, "./data/boulder.jpg")
					self.add(PushMatrix())
					self.add(Translate(*self.grid.pos))

					self.add(obj)
					self.add(PopMatrix())

					self.objects[obj_loc] = obj

			self.character.change_direction(button.value)
			self.character.move_player(new_location)
			if self.character.grid_pos in self.objects:
				if isinstance(self.objects[self.character.grid_pos], DoorTile):
					return self.objects[self.character.grid_pos].other_room
		elif button == Button.A:
			self.character.interact()
			



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
	def __init__(self, pos1, pos2, width):
		super().__init__()
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
	def __init__(self, size,grid_pos, pos, on_interact, icon_source):
		super().__init__(size,pos)
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






























