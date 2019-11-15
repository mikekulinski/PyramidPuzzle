# common imports
import sys

sys.path.append("..")
from common.gfxutil import (
	CRectangle,
)
from kivy.graphics import (
	Color,
	Rectangle,
	Line,
	Translate,
	PushMatrix,
	PopMatrix,
)

from kivy.core.window import Window
from kivy.graphics.instructions import InstructionGroup
import numpy as np

FLOOR_SIZE = 9


class Character(InstructionGroup):
	def __init__(self, game):
		super().__init__()
		self.game = game
		self.grid_pos = (0, 0)
		self.current_tile = self.game.tiles[self.grid_pos[0]][self.grid_pos[1]]
		self.sprite = CRectangle()
		self.add(self.sprite)

		self.move_player((FLOOR_SIZE // 2, FLOOR_SIZE // 2))

	def get_valid_pos(self, grid_pos):
		new_pos = list(grid_pos)
		# Check if this is a valid move, if not move them back in bounds
		if grid_pos[0] < 0:
			new_pos[0] = 0
		elif grid_pos[0] >= FLOOR_SIZE:
			new_pos[0] = FLOOR_SIZE - 1

		if grid_pos[1] < 0:
			new_pos[1] = 0
		elif grid_pos[1] >= FLOOR_SIZE:
			new_pos[1] = FLOOR_SIZE - 1

		return tuple(new_pos)

	def move_player(self, grid_pos):
		new_pos = self.get_valid_pos(grid_pos)

		if self.current_tile.is_switch and self.current_tile.is_active:
			self.current_tile.deactivate()

		self.remove(self.sprite)

		self.grid_pos = new_pos
		self.current_tile = self.game.tiles[self.grid_pos[0]][self.grid_pos[1]]
		tile_size = self.current_tile.size
		self.pixel_pos = self.current_tile.pos + (tile_size // 2) + self.game.pos

		self.size = tile_size // 3

		self.color = Color(1, 0, 0)
		self.add(self.color)
		self.sprite = CRectangle(cpos=self.pixel_pos, csize=self.size)
		self.add(self.sprite)

		if self.current_tile.is_switch and not self.current_tile.is_active:
			self.current_tile.activate()

	def on_layout(self, win_size):
		self.move_player(self.grid_pos)


class Tile(InstructionGroup):
	border_color = (0.6, 0.3, 0, 1)
	base_color = (1, 0.9, 0.8, 1)
	active_color = (1, 0.9, 0.8, 1)
	inactive_color = (0.8, 0.4, 0, 1)

	def __init__(self, size=(150, 150), pos=(200, 200), onStand=None):
		super().__init__()

		self.onStand = onStand

		# inside rectangle coordinates
		self.size = np.array(size)
		self.pos = np.array(pos)

		# inside part
		if self.onStand != None:
			self.inside_color = Color(rgba=Tile.inactive_color)
			self.is_switch = True
			self.is_active = False
		else:
			self.inside_color = Color(rgba=Tile.base_color)
			self.is_switch = False
			self.is_active = False
		self.add(self.inside_color)
		self.inside_rect = Rectangle(size=self.size, pos=self.pos)
		self.add(self.inside_rect)

		# border of button
		self.add(Color(rgba=Tile.border_color))
		self.add(Line(rectangle=(pos[0], pos[1], size[0], size[1])))

	def activate(self):
		self.is_active = True
		self.set_color(Tile.active_color)
		self.onStand()

	def deactivate(self):
		self.is_active = False
		self.set_color(Tile.inactive_color)

	def set_color(self, color):
		self.remove(self.inside_rect)

		self.inside_color = Color(rgba=color)
		self.add(self.inside_color)
		self.inside_rect = Rectangle(size=self.size, pos=self.pos)
		self.add(self.inside_rect)

		# border of button
		self.add(Color(rgba=Tile.border_color))
		self.add(Line(rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1])))


class Game(InstructionGroup):
	def __init__(self, on_pitch_mode):
		super().__init__()
		self.pitch = (2, 2)
		self.on_pitch_mode = on_pitch_mode

		self.create_grid((Window.width, Window.height))
		self.character = Character(self)
		self.add(self.character)

	def create_grid(self, win_size):
		# Add them back in at the right position
		grid_margin = 20
		grid_side_len = min(
			win_size[0] - 2 * grid_margin, win_size[1] - 2 * grid_margin
		)
		self.size = (grid_side_len, grid_side_len)

		# grid geometry calculations
		tile_side_len = grid_side_len / FLOOR_SIZE
		tile_size = (tile_side_len, tile_side_len)

		self.pos = (
			int((win_size[0] / 2) - grid_side_len / 2),
			int(win_size[1] / 2 - grid_side_len / 2),
		)

		# locate entire grid to position pos
		self.add(PushMatrix())
		self.add(Translate(*self.pos))

		self.tiles = []
		for r in range(FLOOR_SIZE):
			self.tiles.append([])
			for c in range(FLOOR_SIZE):
				if self.pitch == (r, c):
					tile = Tile(
						size=tile_size,
						pos=(c * tile_side_len, r * tile_side_len),
						onStand=self.on_pitch_mode,
					)
				else:
					tile = Tile(
						size=tile_size, pos=(c * tile_side_len, r * tile_side_len)
					)

				self.tiles[r].append(tile)
				self.add(tile)

		self.add(PopMatrix())

	def on_layout(self, win_size):

		# Remove all old tiles
		for row in self.tiles:
			for tile in row:
				self.remove(tile)
		self.remove(self.character)

		self.create_grid(win_size)
		self.character.on_layout(win_size)
		self.add(self.character)
