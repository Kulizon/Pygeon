import random
from copy import deepcopy, copy

from tiles import MapTile, AnimatedMapTile
from shared import WALL_SIZE, decorations, items, traps, ground, walls
from utility import convert_csv_to_2d_list, load_tileset
from items import Key, Chest, Trapdoor
from traps import FlamethrowerTrap, ArrowTrap, SpikeTrap

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

# ground, walls, decorations, items, traps
objects_map = {}
room_objects = {
    "ground": [],
    "walls": [],
    "decorations": [],
    "items": [],
    "traps": []
}

#def generate_overworld():


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
                    number_of_adjacent_rooms = count_adjacent_rooms(map, adj_position)

                    if (number_of_adjacent_rooms == 4 and random.random() < 0.25) \
                        or (number_of_adjacent_rooms == 3 and random.random() < 0.5) \
                        or (number_of_adjacent_rooms <= 2):
                            place_room(map, rooms[room_index], adj_position)
                            connected_rooms.append(adj_position)
                            placed = True
                            break

        if not placed:
            print("Could not place room at index", room_index)
    return map


def count_adjacent_rooms(map, position):
    row, col = position
    count = 0
    for i in range(row - 1, row + 2):
        for j in range(col - 1, col + 2):
            if (i != row or j != col) and map[i][j] != 0:
                count += 1
    return count


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


def traverse_rooms_in_random_order(room_layout, decorations_layout, x_off, y_off, room_id, callback, to_add=1):
    for i in range(to_add):
        coordinates = [(row, col) for row in range(len(room_layout)) for col in range(len(room_layout[row]))]
        random.shuffle(coordinates)

        for row, col in coordinates:
            pos_x = col + x_off
            pos_y = row + y_off

            added = callback(room_layout, decorations_layout, (row, col), pos_x, pos_y, room_id)
            if added:
                decorations_layout[row][col] = 1000  # mark as occupied
                break

def generate_key(room_layout, decorations_layout, x_off, y_off, room_id):
    def place_key(room_layout, decorations_layout, grid_position, pos_x, pos_y, room_id):
        row, col = grid_position
        room_tile_id = room_layout[row][col]
        decorations_tile_id = decorations_layout[row][col]

        if room_tile_id != void_tile_id and room_tile_id not in wall_ids and decorations_tile_id == -1:
            key = Key(pos_x * WALL_SIZE, pos_y * WALL_SIZE)
            #items.add(key)
            objects_map[room_id]["items"].append(key)

            return True
        return False

    traverse_rooms_in_random_order(room_layout, decorations_layout, x_off, y_off, room_id, place_key)

def generate_flamethrower(room_layout, decorations_layout, x_off, y_off, room_id):

    def place_flamethrower(room_layout, decorations_layout, grid_position, pos_x, pos_y, room_id):
        row, col = grid_position
        room_tile_id = room_layout[row][col]
        decorations_tile_id = decorations_layout[row][col]

        if room_tile_id in wall_ids and decorations_tile_id == -1:
            for direction in ['down', 'left', 'right']:
                attack_dir = find_wall_with_free_n_spaces(room_layout, decorations_layout, direction, col, row, 3)

                if attack_dir[0] or attack_dir[1]:
                    flamethrower = FlamethrowerTrap(pos_x * WALL_SIZE, pos_y * WALL_SIZE, attack_dir)
                    #traps.add(flamethrower)
                    objects_map[room_id]["traps"].append(flamethrower)

                    return True
        return False

    traverse_rooms_in_random_order(room_layout, decorations_layout, x_off, y_off, room_id, place_flamethrower)


def generate_arrow_trap(room_layout, decorations_layout, x_off, y_off, room_id):
    def place_arrow_trap(room_layout, decorations_layout, grid_position, pos_x, pos_y, room_id):
        row, col = grid_position
        room_tile_id = room_layout[row][col]
        decorations_tile_id = decorations_layout[row][col]

        middle_tile = room_width // 2 - 1

        if row == middle_tile or row == middle_tile + 1 or col == middle_tile or col == middle_tile + 1:
            return False

        if room_tile_id in wall_ids and decorations_tile_id == -1:
            for direction in ['down', 'left', 'right']:
                attack_dir = find_wall_with_free_n_spaces(room_layout, decorations_layout, direction, col, row, 6)

                if attack_dir[0] and room_tile_id in [1, 2, 3, 4]: # fix visual bug
                    continue

                if attack_dir[0] or attack_dir[1]:
                    arrow_trap = ArrowTrap(pos_x * WALL_SIZE, pos_y * WALL_SIZE, attack_dir)
                    #traps.add(arrow_trap)
                    objects_map[room_id]["traps"].append(arrow_trap)
                    return True

        return False

    traverse_rooms_in_random_order(room_layout, decorations_layout, x_off, y_off, room_id, place_arrow_trap)

def generate_spike_trap(room_layout, decorations_layout, x_off, y_off, room_id, to_add):

    def place_spike_trap(room_layout, decorations_layout, grid_position, pos_x, pos_y, room_id):
        row, col = grid_position
        room_tile_id = room_layout[row][col]
        decorations_tile_id = decorations_layout[row][col]

        if room_tile_id != void_tile_id and room_tile_id not in wall_ids and decorations_tile_id == -1:

            spike_trap = SpikeTrap(pos_x * WALL_SIZE, pos_y * WALL_SIZE)
            #traps.add(spike_trap)
            objects_map[room_id]["traps"].append(spike_trap)

            return True
        return False

    traverse_rooms_in_random_order(room_layout, decorations_layout, x_off, y_off, room_id, place_spike_trap, to_add)


def generate_chest(room_layout, decorations_layout, x_off, y_off, room_id, to_add=1):
    def place_chest(room_layout, decorations_layout, grid_position, pos_x, pos_y, room_id):
        row, col = grid_position
        room_tile_id = room_layout[row][col]
        decorations_tile_id = decorations_layout[row][col]

        # generate in the middle of room (kinda)
        row_border_indexes = [0, 1, 2, room_width-1, room_width-2, room_width-3]
        col_border_indexes = [0, 1, 2, room_height-1, room_height-2, room_height-3]
        if row in row_border_indexes or col in col_border_indexes:
            return False

        if room_tile_id != void_tile_id and room_tile_id not in wall_ids and decorations_tile_id == -1:
            chest = Chest(pos_x * WALL_SIZE, pos_y * WALL_SIZE, 10, 0)
            #items.add(chest)
            objects_map[room_id]["items"].append(chest)

            return chest
        return None

    traverse_rooms_in_random_order(room_layout, decorations_layout, x_off, y_off, room_id, place_chest, to_add)


def generate_map(room_map):
    empty_decorations_layout = [[-1 for _ in range(room_height)] for _ in range(room_width)]
    furthest_room_id = find_furthest_room(room_map)

    number_of_added = {
        "chests": 0,
    }

    indices = [(i, j) for i in range(len(room_map)) for j in range(len(room_map[0]))]

    for i, j in indices:
        room_id = room_map[i][j]
        objects_map[room_id] = deepcopy(room_objects)

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
            generate_key(room_layout, decorations_layout, x_off, y_off, room_id)

        # generate traps and items
        if room_id != 1:
            for prob in [1, 0.5, 0.25]:
                if random.random() < prob:
                    generate_flamethrower(room_layout, decorations_layout, x_off, y_off, room_id)
            for prob in [0.7, 0.4, 0.25]:
                if random.random() < prob:
                    generate_arrow_trap(room_layout, decorations_layout, x_off, y_off, room_id)

            generate_spike_trap(room_layout, decorations_layout, x_off, y_off, room_id, random.randint(0, 4))

            if number_of_added["chests"] < 3 \
                    or (3 <= number_of_added["chests"] <= 10 and random.random() < 0.3) \
                    or (10 < number_of_added["chests"] and random.random() < 0.15):
                generate_chest(room_layout, decorations_layout, x_off, y_off, room_id)
                number_of_added["chests"] += 1

        # generate sprites
        for row in range(len(room_layout)):
            for col in range(len(room_layout[row])):
                pos_x = col + x_off
                pos_y = row + y_off

                room_tile_id = room_layout[row][col]
                decorations_tile_id = decorations_layout[row][col]
                if not(0 <= room_tile_id < len(tiles_images)):
                    continue

                obj = MapTile(tiles_images[room_tile_id], pos_x, pos_y)
                if room_tile_id in wall_ids:
                    #walls.add(obj)
                    objects_map[room_id]["walls"].append(obj)
                else:
                    objects_map[room_id]["ground"].append(obj)
                    #ground.add(obj)

                if not(0 <= decorations_tile_id < len(tiles_images)):
                    continue

                animations_images_data = {
                    74: ["assets/items_and_traps_animations/flag", 350],
                    93: ["assets/items_and_traps_animations/candlestick_1", 250],
                    95: ["assets/items_and_traps_animations/candlestick_2", 250],
                    90: ["assets/items_and_traps_animations/torch_front", 250],
                    91: ["assets/items_and_traps_animations/torch_sideways", 250],
                }

                if decorations_tile_id in animations_images_data:
                    path, time = animations_images_data[decorations_tile_id]
                    obj = AnimatedMapTile(path, pos_x, pos_y, time)
                elif decorations_tile_id == 38:
                    obj = Trapdoor(pos_x, pos_y)
                else:
                    obj = MapTile(tiles_images[decorations_tile_id], pos_x, pos_y)

                objects_map[room_id]["decorations"].append(obj)
                #decorations.add(obj)

    map_width_px = len(room_map[0]) * WALL_SIZE * room_width
    map_height_px = len(room_map) * WALL_SIZE * room_height

    return map_width_px, map_height_px, objects_map

