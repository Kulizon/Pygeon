from copy import deepcopy
import pygame as pg
from characters import Player, Merchant, Enemy
from map_generation import connect_rooms, generate_map
from shared import WALL_SIZE, characters, CHARACTER_SIZE, ground, walls, decorations, items, traps, visuals
from ui import trim_matrix
from utility import Camera


class Map():
    def __init__(self):
        rooms = [i + 1 for i in range(50)]
        self.room_map = connect_rooms(rooms)
        self.mini_map = trim_matrix(self.room_map)
        self.discovered_mini_map = deepcopy(self.mini_map)
        for y, row in enumerate(self.discovered_mini_map):
            for x, el in enumerate(row):
                if el != 1:
                    self.discovered_mini_map[y][x] = 0

        w, h, objects_map = generate_map(self.room_map)

        self.width_px = w
        self.height_px = h
        self.objects_map = objects_map

        self.current_map_cell = 0

    def update(self, player):
        new_cell = self.room_map[int(player.rect.y // WALL_SIZE // 16)][int(player.rect.x // WALL_SIZE // 16)]

        if self.current_map_cell != new_cell:
            #update mini-map
            for y, row in enumerate(self.mini_map):
                for x, el in enumerate(row):
                    if el == new_cell:
                        self.discovered_mini_map[y][x] = new_cell
            self.current_map_cell = new_cell
            return True
        else:
            self.current_map_cell = new_cell
            # update the decorations and etc to the ones within the room
            return False


class Game():
    def __init__(self, gmap, current_player=None):
        self.camera = Camera(gmap.width_px, gmap.height_px)
        player_start_x = gmap.width_px // 2 - CHARACTER_SIZE
        player_start_y = gmap.height_px // 2 - CHARACTER_SIZE
        self.defeat_timer_start = pg.time.get_ticks()
        self.objects_map = gmap.objects_map

        if not current_player:
            self.player = Player(player_start_x, player_start_y)
        else:
            self.player = current_player
            self.player.rect.x = player_start_x
            self.player.rect.y = player_start_y

        merchant = Merchant(gmap.width_px // 2 - CHARACTER_SIZE, gmap.height_px // 2 - 220 - CHARACTER_SIZE)
        ch1 = Enemy(gmap.width_px // 2, gmap.height_px // 2 + 220)
        characters.add(self.player, ch1, merchant)
        #characters.add(self.player, self.merchant)


    def clear_groups(self):
        groups = [ground, walls, decorations, items, traps, visuals]
        for grp in groups:
            grp.empty()

    def render_appropriate_room(self, current_map_cell, room_map):
        self.clear_groups()
        #print(self.objects_map)

        cells = [current_map_cell]
        for i, row in enumerate(room_map):
            for j, cell in enumerate(row):
                if cell == current_map_cell:
                    if j - 1 >= 0:
                        cells.append(room_map[i][max(0, j - 1)])
                    if j + 1 < len(row):
                        cells.append(room_map[i][min(len(row) - 1, j + 1)])
                    if i - 1 >= 0:
                        cells.append(room_map[max(0, i - 1)][j])
                    if i + 1 < len(room_map):
                        cells.append(room_map[min(len(room_map) - 1, i + 1)][j])
                    if i - 1 >= 0 and j - 1 >= 0:
                        cells.append(room_map[max(0, i - 1)][max(0, j - 1)])
                    if i + 1 < len(room_map) and j - 1 >= 0:
                        cells.append(room_map[min(len(room_map) - 1, i + 1)][max(0, j - 1)])
                    if i - 1 >= 0 and j + 1 < len(row):
                        cells.append(room_map[max(0, i - 1)][min(len(row) - 1, j + 1)])
                    if i + 1 < len(room_map) and j + 1 < len(row):
                        cells.append(room_map[min(len(room_map) - 1, i + 1)][min(len(row) - 1, j + 1)])

        for cell in cells:
            objects = self.objects_map[cell]
            for label in objects:
                if label == "ground":
                    ground.add(objects[label])
                elif label == "decorations":
                    decorations.add(objects[label])
                elif label == "walls":
                    walls.add(objects[label])
                elif label == "items":
                    items.add(objects[label])
                elif label == "traps":
                    traps.add(objects[label])


        pass

        # changed the place where objects end up in in map_generation.py
        # from this map i think select the appropriate room with self.current_map_cell
        # add to decorations, walls, traps etc.



