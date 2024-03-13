from copy import deepcopy
import pygame as pg
from characters import Player, Merchant, Enemy
from map_generation import connect_rooms, generate_map
from shared import WALL_SIZE, characters, CHARACTER_SIZE
from ui import trim_matrix
from utility import Camera

class Map():
    def __init__(self):
        rooms = [i + 1 for i in range(10)]
        self.room_map = connect_rooms(rooms)
        self.mini_map = trim_matrix(self.room_map)
        self.discovered_mini_map = deepcopy(self.mini_map)
        for y, row in enumerate(self.discovered_mini_map):
            for x, el in enumerate(row):
                if el != 1:
                    self.discovered_mini_map[y][x] = 0

        w, h = generate_map(self.room_map)

        self.width_px = w
        self.height_px = h

        self.current_mini_map_cell = 0

    def update(self, player):
        new_cell = self.room_map[int(player.rect.y // WALL_SIZE // 16)][int(player.rect.x // WALL_SIZE // 16)]
        if self.current_mini_map_cell != new_cell:
            for y, row in enumerate(self.mini_map):
                for x, el in enumerate(row):
                    if el == new_cell:
                        self.discovered_mini_map[y][x] = new_cell

        self.current_mini_map_cell = self.room_map[int(player.rect.y // WALL_SIZE // 16)][
            int(player.rect.x // WALL_SIZE // 16)]
        return


class Game():
    def __init__(self, gmap, current_player=None):
        self.camera = Camera(gmap.width_px, gmap.height_px)
        player_start_x = gmap.width_px // 2 - CHARACTER_SIZE
        player_start_y = gmap.height_px // 2 - CHARACTER_SIZE
        self.defeat_timer_start = pg.time.get_ticks()

        if not current_player:
            self.player = Player(player_start_x, player_start_y)
        else:
            self.player = current_player
            self.player.rect.x = player_start_x
            self.player.rect.y = player_start_y

        self.merchant = Merchant(gmap.width_px // 2 - CHARACTER_SIZE, gmap.height_px // 2 - 220 - CHARACTER_SIZE)
        self.ch1 = Enemy(gmap.width_px // 2, gmap.height_px // 2 + 220)
        characters.add(self.player, self.ch1, self.merchant)
        #characters.add(self.player, self.merchant)



