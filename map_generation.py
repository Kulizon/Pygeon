rooms = [i+1 for i in range(2)]
room_map = connect_rooms(rooms)
mini_map = trim_matrix(room_map)
discovered_mini_map = deepcopy(mini_map)
for y, row in enumerate(discovered_mini_map):
    for x, el in enumerate(row):
        if el != 1:
            discovered_mini_map[y][x] = 0

characters = pg.sprite.Group()
traps = pg.sprite.Group()
items = pg.sprite.Group()

room_tile_maps = []
for i in range(1, 7):
    structure_tiles = convert_csv_to_2d_list(csv_file="rooms/room" + str(i) + "_l1.csv")
    decoration_tiles = convert_csv_to_2d_list(csv_file="rooms/room" + str(i) + "_l2.csv")
    room_tile_maps.append([structure_tiles, decoration_tiles])

tiles_images = load_tileset("tileset.png", 16, 16)
ROOM_WIDTH = len(room_tile_maps[0][0][0])
ROOM_HEIGHT = len(room_tile_maps[0][0])

wall_ids = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 41, 42, 43, 44, 45, 50, 51, 52, 53, 54, 55]
# todo: for testing, remove later
wall_ids.append(66)
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

empty_decorations_layout = [[-1 for _ in range(ROOM_HEIGHT)] for _ in range(ROOM_WIDTH)]

for i in range(len(room_map)):
    for j in range(len(room_map[0])):
        room_id = room_map[i][j]
        x_off = ROOM_WIDTH * j
        y_off = ROOM_HEIGHT * i

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


        middle_tile = ROOM_WIDTH // 2 - 1
        end_tile = ROOM_WIDTH - 1

        # room above
        if room_map[i - 1][j] == 0:
            room_layout[0][middle_tile - 1] = 78  # dark tile
            room_layout[0][middle_tile + 2] = 78
            room_layout[0][middle_tile] = 78
            room_layout[0][middle_tile + 1] = 78
            room_layout[1][middle_tile] = 2 # wall tile
            room_layout[1][middle_tile + 1] = 2

        # room below
        if room_map[i + 1][j] == 0:
            room_layout[end_tile][middle_tile-1] = 78  # dark tile
            room_layout[end_tile][middle_tile+2] = 78
            room_layout[end_tile][middle_tile] = 78
            room_layout[end_tile][middle_tile+1] = 78
            room_layout[end_tile-1][middle_tile] = 41 # wall tile
            room_layout[end_tile-1][middle_tile+1] = 41
            room_layout[end_tile-1][middle_tile-1] = 41 # wall tile
            room_layout[end_tile-1][middle_tile+2] = 41

        # right room
        if room_map[i][j + 1] == 0:
            room_layout[middle_tile-1][end_tile] = 78  # dark tile
            room_layout[middle_tile][end_tile] = 78
            room_layout[middle_tile+1][end_tile] = 78
            room_layout[middle_tile+2][end_tile] = 78

            room_layout[middle_tile-1][end_tile-1] = 15  # wall tile
            room_layout[middle_tile][end_tile-1] = 15
            room_layout[middle_tile+1][end_tile-1] = 15
            room_layout[middle_tile+2][end_tile-1] = 15

            # left room
        if room_map[i][j - 1] == 0:
            room_layout[middle_tile-1][0] = 78  # dark tile
            room_layout[middle_tile][0] = 78
            room_layout[middle_tile+1][0] = 78
            room_layout[middle_tile+2][0] = 78

            room_layout[middle_tile-1][1] = 10  # wall tile
            room_layout[middle_tile][1] = 10
            room_layout[middle_tile+1][1] = 10
            room_layout[middle_tile+2][1] = 10

        # generate traps and items

        # search for a wall that has two free spaces in the way that flamethrower will be facing
        if room_id != 1:
            added_flamethrower = False
            coordinates = [(row, col) for row in range(len(room_layout)) for col in range(len(room_layout[row]))]
            random.shuffle(coordinates)

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
                            74: ["items_and_traps_animations/flag", 350],
                            93: ["items_and_traps_animations/candlestick_1", 250],
                            95: ["items_and_traps_animations/candlestick_2", 250],
                            90: ["items_and_traps_animations/torch_front", 250],
                            91: ["items_and_traps_animations/torch_sideways", 250],
                        }

                        if id in animations_images_data:
                            path, time = animations_images_data[id]
                            obj = AnimatedMapTile(path, pos_x, pos_y, time)
                        else:
                            obj = MapTile(tiles_images[id], pos_x, pos_y)

                        decorations.add(obj)

map_width_px = len(room_map[0]) * WALL_SIZE * ROOM_WIDTH
map_height_px = len(room_map) * WALL_SIZE * ROOM_HEIGHT