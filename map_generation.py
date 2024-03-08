import random
import pygame as pg
from copy import deepcopy

from shared import WALL_SIZE, decorations, items, traps, ground, walls
from utility import load_images_from_folder, Animated, convert_csv_to_2d_list, load_tileset
from items import Key, Chest
from traps import FlamethrowerTrap, ArrowTrap, SpikeTrap


class MapTile(pg.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = pg.transform.scale(image, (WALL_SIZE, WALL_SIZE))
        self.col = x
        self.row = y
        self.rect = self.image.get_rect(topleft=(x * WALL_SIZE, y * WALL_SIZE))

class AnimatedMapTile(MapTile, Animated):
    def __init__(self, images_path, x, y, frame_duration, flip_x=False, flip_y=False, rotate=0, size=None):
        images = load_images_from_folder(images_path)

        MapTile.__init__(self, images[0], x, y)
        if size:
            self.rect.size = size
        Animated.__init__(self, images, self.rect.size, frame_duration, flip_x, flip_y, rotate)

    def update(self):
        self.animate_new_frame()


def place_room(map, room, position):
    x, y = position
    map[x][y] = room

def is_valid_position(map, position):
    x, y = position
    return 0 <= x < len(map) and 0 <= y < len(map[0])

def is_room_position_empty(map, position):
    x, y = position
    return map[x][y] == 0

def get_adjacent_positions(position):
    x, y = position
    return [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]

def connect_rooms(rooms):
    map_size = (len(rooms) * 2 + 1)

    map = [[0] * map_size for _ in range(map_size)]
    start_position = (map_size // 2, map_size // 2)
    place_room(map, rooms[0], start_position)
    connected_rooms = [start_position]
    for room_index in range(1, len(rooms)):
        placed = False
        while not placed:
            connecting_room = random.choice(connected_rooms)
            adjacent_positions = get_adjacent_positions(connecting_room)
            random.shuffle(adjacent_positions)
            for adj_position in adjacent_positions:
                if is_valid_position(map, adj_position) and is_room_position_empty(map, adj_position):
                    place_room(map, rooms[room_index], adj_position)
                    connected_rooms.append(adj_position)
                    placed = True
                    break
    return map


room_tile_maps = []
for i in range(1, 7):
    structure_tiles = convert_csv_to_2d_list(csv_file="assets/rooms/room" + str(i) + "_l1.csv")
    decoration_tiles = convert_csv_to_2d_list(csv_file="assets/rooms/room" + str(i) + "_l2.csv")
    room_tile_maps.append([structure_tiles, decoration_tiles])

tiles_images = load_tileset("assets/tileset.png", 16, 16)
room_width = len(room_tile_maps[0][0][0])
room_height = len(room_tile_maps[0][0])

wall_ids = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 41, 42, 43, 44, 45, 50, 51, 52, 53, 54, 55]
void_tile_id = 78

def is_empty_space(layout, decorations_layout, x, y):
    return (0 <= y < len(layout) and (0 <= x < len(layout[y])
            and layout[y][x] not in wall_ids
            and layout[y][x] != void_tile_id)
            and decorations_layout[y][x] == -1)


def find_wall_with_free_n_spaces(layout, decorations_layout, direction, x, y, n):
    directions = {
        'up': (0, -1),
        'down': (0, 1),
        'left': (-1, 0),
        'right': (1, 0)
    }

    dx, dy = directions[direction]

    if layout[y][x] in wall_ids:
        if all(is_empty_space(layout, decorations_layout, x + i * dx, y + i * dy) for i in range(1, n + 1)):
            return directions[direction]
    return (0, 0)

empty_decorations_layout = [[-1 for _ in range(room_height)] for _ in range(room_width)]


def find_furthest_room(room_map):
    rows = len(room_map)
    cols = len(room_map[0])

    center_row = rows // 2
    center_col = cols // 2

    max_distance = -1
    furthest_room = None

    for i in range(rows):
        for j in range(cols):
            distance = abs(i - center_row) + abs(j - center_col)
            if distance > max_distance and room_map[i][j] != 0:
                max_distance = distance
                furthest_room = room_map[i][j]

    return furthest_room


def make_doorways(i, j, room_map, room_layout):
    middle_tile = room_width // 2 - 1
    end_tile = room_width - 1

    # room above
    if room_map[i - 1][j] == 0:
        room_layout[0][middle_tile - 1] = 78  # dark tile
        room_layout[0][middle_tile + 2] = 78
        room_layout[0][middle_tile] = 78
        room_layout[0][middle_tile + 1] = 78
        room_layout[1][middle_tile] = 2  # wall tile
        room_layout[1][middle_tile + 1] = 2

    # room below
    if room_map[i + 1][j] == 0:
        room_layout[end_tile][middle_tile - 1] = 78  # dark tile
        room_layout[end_tile][middle_tile + 2] = 78
        room_layout[end_tile][middle_tile] = 78
        room_layout[end_tile][middle_tile + 1] = 78
        room_layout[end_tile - 1][middle_tile] = 41  # wall tile
        room_layout[end_tile - 1][middle_tile + 1] = 41
        room_layout[end_tile - 1][middle_tile - 1] = 41  # wall tile
        room_layout[end_tile - 1][middle_tile + 2] = 41

    # right room
    if room_map[i][j + 1] == 0:
        room_layout[middle_tile - 1][end_tile] = 78  # dark tile
        room_layout[middle_tile][end_tile] = 78
        room_layout[middle_tile + 1][end_tile] = 78
        room_layout[middle_tile + 2][end_tile] = 78

        room_layout[middle_tile - 1][end_tile - 1] = 15  # wall tile
        room_layout[middle_tile][end_tile - 1] = 15
        room_layout[middle_tile + 1][end_tile - 1] = 15
        room_layout[middle_tile + 2][end_tile - 1] = 15

        # left room
    if room_map[i][j - 1] == 0:
        room_layout[middle_tile - 1][0] = 78  # dark tile
        room_layout[middle_tile][0] = 78
        room_layout[middle_tile + 1][0] = 78
        room_layout[middle_tile + 2][0] = 78

        room_layout[middle_tile - 1][1] = 10  # wall tile
        room_layout[middle_tile][1] = 10
        room_layout[middle_tile + 1][1] = 10
        room_layout[middle_tile + 2][1] = 10


def traverse_rooms_in_random_order(room_layout, decorations_layout, x_off, y_off, callback):
    coordinates = [(row, col) for row in range(len(room_layout)) for col in range(len(room_layout[row]))]



    for row, col in coordinates:
        pos_x = col + x_off
        pos_y = row + y_off

        room_tile_id = room_layout[row][col]
        decorations_tile_id = room_layout[row][col]

        added = callback(room_tile_id, decorations_tile_id, pos_x, pos_y)
        if added:
            decorations_layout[row][col] = 1000             # mark as occupied

def generate_key(room_layout, decorations_layout, x_off, y_off):
    def place_key(tile_id, decorations_tile_id, pos_x, pos_y):
        if tile_id != void_tile_id and tile_id not in wall_ids and decorations_tile_id == -1:
            key = Key(pos_x * WALL_SIZE, pos_y * WALL_SIZE)
            items.add(key)

            return True
        return False

    traverse_rooms_in_random_order(room_layout, decorations_layout, x_off, y_off, place_key)






def generate_level(room_map):
    furthest_room_id = find_furthest_room(room_map)

    for i in range(len(room_map)):
        for j in range(len(room_map[0])):
            room_id = room_map[i][j]
            x_off = room_width * j
            y_off = room_height * i

            if room_id == 0:
                continue
            elif room_id == 1:
                room_layout = deepcopy(room_tile_maps[0][0])
                decorations_layout = deepcopy(room_tile_maps[0][1])
            else:
                random_room_index = random.randint(0, 5)
                room_layout = deepcopy(room_tile_maps[random_room_index][0])
                if random_room_index != 0:
                    decorations_layout = deepcopy(room_tile_maps[random_room_index][1])
                else:
                    decorations_layout = empty_decorations_layout


            make_doorways(i, j, room_map, room_layout)

            # generate key if is the furthest room
            if room_id == furthest_room_id:
                generate_key(room_layout, decorations_layout, x_off, y_off)


            # generate traps and items

            # search for a wall that has two free spaces in the way that flamethrower will be facing
            if room_id != 1:
                coordinates = [(row, col) for row in range(len(room_layout)) for col in range(len(room_layout[row]))]
                random.shuffle(coordinates)

                added_flamethrower = False
                for row, col in coordinates:
                    if room_layout[row][col] in wall_ids and decorations_layout[row][col] == -1:
                        for direction in ['down', 'left', 'right']:
                            attack_dir = find_wall_with_free_n_spaces(room_layout, decorations_layout, direction, col, row, 3)

                            pos_x = col + x_off
                            pos_y = row + y_off

                            if attack_dir[0] or attack_dir[1]:
                                flamethrower = FlamethrowerTrap(pos_x * WALL_SIZE, pos_y * WALL_SIZE, attack_dir)
                                traps.add(flamethrower)

                                decorations_layout[row][col] = 1000 # mark as occupied
                                added_flamethrower = True
                                break
                    if added_flamethrower:
                        break

                added_arrowTrap = False
                for row, col in coordinates:
                    if room_layout[row][col] in wall_ids and decorations_layout[row][col] == -1:
                        for direction in ['left', 'right']:
                            # 'down' , 'left', 'right'
                            attack_dir = find_wall_with_free_n_spaces(room_layout, decorations_layout, direction, col, row, 10)

                            pos_x = col + x_off
                            pos_y = row + y_off

                            if attack_dir[0] or attack_dir[1]:
                                arrowTrap = ArrowTrap(pos_x * WALL_SIZE, pos_y * WALL_SIZE, attack_dir)
                                traps.add(arrowTrap)

                                decorations_layout[row][col] = 1000 # mark as occupied
                                added_arrowTrap = True
                                break
                    if added_arrowTrap:
                        break

                added_spike_traps = 0
                for row, col in coordinates:
                    if room_layout[row][col] != void_tile_id and room_layout[row][col] not in wall_ids and decorations_layout[row][col] == -1:
                        pos_x = col + x_off
                        pos_y = row + y_off

                        spikeTrap = SpikeTrap(pos_x * WALL_SIZE, pos_y * WALL_SIZE)
                        traps.add(spikeTrap)

                        decorations_layout[row][col] = 1000  # mark as occupied
                        added_spike_traps += 1

                    if added_spike_traps >= 1:
                        break

                #generate a chest
                added_chest = False
                for row, col in coordinates:
                    if room_layout[row][col] != void_tile_id and room_layout[row][col] not in wall_ids and \
                            decorations_layout[row][col] == -1:
                        pos_x = col + x_off
                        pos_y = row + y_off

                        chest = Chest(pos_x * WALL_SIZE, pos_y * WALL_SIZE, 10, 0)
                        items.add(chest)

                        decorations_layout[row][col] = 1000  # mark as occupied
                        added_chest = True

                    if added_chest:
                        break

            for row in range(len(room_layout)):
                for col in range(len(room_layout[row])):
                    pos_x = col + x_off
                    pos_y = row + y_off

                    id = room_layout[row][col]
                    if id in wall_ids:
                        walls.add(MapTile(tiles_images[id], pos_x, pos_y))
                    else:
                        ground.add(MapTile(tiles_images[id], pos_x, pos_y))

                    if decorations_layout != None:
                        id = decorations_layout[row][col]

                        if 0 <= id < len(tiles_images):
                            animations_images_data = {
                                74: ["assets/items_and_traps_animations/flag", 350],
                                93: ["assets/items_and_traps_animations/candlestick_1", 250],
                                95: ["assets/items_and_traps_animations/candlestick_2", 250],
                                90: ["assets/items_and_traps_animations/torch_front", 250],
                                91: ["assets/items_and_traps_animations/torch_sideways", 250],
                            }

                            if id in animations_images_data:
                                path, time = animations_images_data[id]
                                obj = AnimatedMapTile(path, pos_x, pos_y, time)
                            else:
                                obj = MapTile(tiles_images[id], pos_x, pos_y)

                            decorations.add(obj)

    map_width_px = len(room_map[0]) * WALL_SIZE * room_width
    map_height_px = len(room_map) * WALL_SIZE * room_height

    return map_width_px, map_height_px

