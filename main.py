import copy
import math

import pygame as pg
import random
from copy import copy, deepcopy

from characters import Character, Player, Enemy, Merchant
from shared import WALL_SIZE, CHARACTER_SIZE, characters, items, traps, visuals, font
from utility import Animated, Visual, load_images_from_folder, load_tileset, convert_csv_to_2d_list
from items import Chest, Key, Item
from traps import Trap, ArrowTrap, FlamethrowerTrap, SpikeTrap

pg.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700

screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pg.time.Clock()


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










class Camera:
    def __init__(self, width, height):
        self.rect = pg.Rect(0, 0, width, height)

        self.width = width
        self.height = height
        self.initial_width = width
        self.initial_height = height

    def update(self, target):
        x = -target.rect.x + (SCREEN_WIDTH // 2)
        y = -target.rect.y + (SCREEN_HEIGHT // 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - SCREEN_WIDTH), x)
        y = max(-(self.height - SCREEN_HEIGHT), y)

        self.rect = pg.Rect(x, y, self.width, self.height)


walls = pg.sprite.Group()
ground = pg.sprite.Group()
decorations = pg.sprite.Group()


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


heart_image = pg.transform.scale(pg.image.load('assets/heart.png'), (30, 28))
coin_images = load_tileset("assets/coin.png", 13, 13)
coin_animated = Animated(coin_images, (30, 30), 200)
key_images = load_images_from_folder("assets/items_and_traps_animations/keys/silver_resized")
key_animated = Animated(key_images, (30, 22), 200)

def display_health(health):
    for i in range(health):
        screen.blit(heart_image, (10 + i * 40, 10))


def display_coins(coins):
    screen.blit(coin_animated.image, (10, 50))
    text = font.render("0" * (3 - int(math.log10(coins+1))) + str(coins), True, (255, 255, 255))
    screen.blit(text, (50, 52))
    coin_animated.animate_new_frame()


def display_full_map(map, current_cell):
    gap = 5
    cell_size = 40
    map = trim_matrix(map)

    map_width = len(map[0]) * cell_size + (len(map[0]) - 1) * gap
    map_height = len(map) * cell_size + (len(map) - 1) * gap

    offset_x = (SCREEN_WIDTH - map_width) // 2
    offset_y = (SCREEN_HEIGHT - map_height) // 2

    bg_width = max(400, map_width + 100)
    bg_height = max(400, map_height + 100)

    pg.draw.rect(screen, (0, 0, 0), ((SCREEN_WIDTH - bg_width) // 2, (SCREEN_HEIGHT - bg_height) // 2, bg_width, bg_width))

    for y, row in enumerate(map):
        for x, cell in enumerate(row):
            display_x = offset_x + x * (cell_size + gap)
            display_y = offset_y + y * (cell_size + gap)

            color = (0, 0, 120) if cell == 0 else (255, 0, 0) if cell == current_cell else (0, 255, 0)
            pg.draw.rect(screen, color, (display_x, display_y, cell_size, cell_size))


def display_mini_map(map, current_cell):
    gap = 5
    screen_gap = 15
    mini_map_size = 140

    cell_position = [-1, -1]

    for y, row in enumerate(map):
        for x, cell in enumerate(row):
            if cell == current_cell:
                cell_position = [x, y]
                break

    mini_map = [[0 for _ in range(5)] for _ in range(5)]

    start_x = max(0, cell_position[0] - 2)
    end_x = min(len(map[0]), cell_position[0] + 3)
    start_y = max(0, cell_position[1] - 2)
    end_y = min(len(map), cell_position[1] + 3)

    center_x = 2
    center_y = 2

    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            mini_map[center_y - (cell_position[1] - y)][center_x - (cell_position[0] - x)] = map[y][x]

    cell_width = (mini_map_size - 2 * screen_gap) // (2 * 2 + 1)
    cell_height = (mini_map_size - 2 * screen_gap) // (2 * 2 + 1)

    map_size_px = (cell_width + gap) * 6
    cells_gap = screen_gap - (mini_map_size - map_size_px) // 2

    pg.draw.rect(screen, (0, 0, 0), (SCREEN_WIDTH - screen_gap - map_size_px, screen_gap, map_size_px, map_size_px))

    for y in range(5):
        for x in range(5):
            display_x = SCREEN_WIDTH - cells_gap - map_size_px + (x + 1) * (cell_width + gap)
            display_y = cells_gap + 2 + y * cell_height + gap * y
            cell_value = mini_map[y][x]
            color = (255, 0, 0) if cell_value == current_cell else (0, 255, 0) if cell_value != 0 else (0, 0, 0)
            pg.draw.rect(screen, color, (display_x, display_y, cell_width, cell_height))

def display_keys(number_of_keys):
    screen.blit(key_animated.image, (10, 92))

    text = font.render(str(number_of_keys), True, (255, 255, 255))
    screen.blit(text, (50, 90))

    key_animated.animate_new_frame()

def display_timer(timer_seconds):
    mini_map_size = 140
    screen_gap = 15

    seconds = timer_seconds % 60
    minutes = timer_seconds // 60

    text_color = (255, 0, 0) if minutes == 1 else (255, 255, 255)

    text = str(minutes) + ":"
    if seconds < 10:
        text += "0"
    text += str(seconds)

    text = font.render(text, True, text_color)
    screen.blit(text, (SCREEN_WIDTH - text.get_width() - screen_gap, mini_map_size + screen_gap + text.get_height()))


def display_ui(coins, health, mini_map, current_cell, number_of_keys, timer_seconds):
    display_health(health)
    display_coins(coins)
    display_keys(number_of_keys)
    display_timer(timer_seconds)
    display_mini_map(mini_map, current_cell)
    #display_full_map(mini_map, current_cell)


def trim_matrix(matrix):
    min_row = len(matrix)
    max_row = 0
    min_col = len(matrix[0])
    max_col = 0

    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            if matrix[i][j] != 0:
                min_row = min(min_row, i)
                max_row = max(max_row, i)
                min_col = min(min_col, j)
                max_col = max(max_col, j)

    # Extract the trimmed matrix
    trimmed_matrix = []
    for i in range(min_row, max_row + 1):
        row = matrix[i][min_col:max_col + 1]
        trimmed_matrix.append(row)

    return trimmed_matrix


rooms = [i+1 for i in range(10)]
room_map = connect_rooms(rooms)
mini_map = trim_matrix(room_map)
discovered_mini_map = deepcopy(mini_map)
for y, row in enumerate(discovered_mini_map):
    for x, el in enumerate(row):
        if el != 1:
            discovered_mini_map[y][x] = 0



room_tile_maps = []
for i in range(1, 7):
    structure_tiles = convert_csv_to_2d_list(csv_file="assets/rooms/room" + str(i) + "_l1.csv")
    decoration_tiles = convert_csv_to_2d_list(csv_file="assets/rooms/room" + str(i) + "_l2.csv")
    room_tile_maps.append([structure_tiles, decoration_tiles])

tiles_images = load_tileset("assets/tileset.png", 16, 16)
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


furthest_room_id = find_furthest_room(room_map)

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

        # generate key if is the furthest room

        if room_id == furthest_room_id:
            coordinates = [(row, col) for row in range(len(room_layout)) for col in range(len(room_layout[row]))]

            for row, col in coordinates:
                if room_layout[row][col] != void_tile_id and room_layout[row][col] not in wall_ids and \
                        decorations_layout[row][col] == -1:
                    pos_x = col + x_off
                    pos_y = row + y_off

                    key = Key(pos_x * WALL_SIZE, pos_y * WALL_SIZE)
                    items.add(key)

                    decorations_layout[row][col] = 1000  # mark as occupied
                    break

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

map_width_px = len(room_map[0]) * WALL_SIZE * ROOM_WIDTH
map_height_px = len(room_map) * WALL_SIZE * ROOM_HEIGHT

player = Player(map_width_px//2 - CHARACTER_SIZE, map_height_px//2 - CHARACTER_SIZE)
merchant = Merchant(map_width_px//2 - CHARACTER_SIZE, map_height_px//2 - 220 - CHARACTER_SIZE)
ch1 = Enemy(map_width_px//2, map_height_px//2 + 250)

characters.add(player, ch1, merchant)

camera = Camera(map_width_px, map_height_px)

current_cell = room_map[int(player.rect.y // WALL_SIZE // 16)][int(player.rect.x // WALL_SIZE // 16)]
defeat_timer_start = pg.time.get_ticks()

running = True
while running:
    defeat_timer_seconds = 600 - (pg.time.get_ticks() - defeat_timer_start) // 1000

    fps = round(clock.get_fps())
    print(fps)

    action_objects = []
    for char in characters:
        if isinstance(char, Merchant):
            action_objects += char.items_to_sell


    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        keys = pg.key.get_pressed()
        if event.type == pg.KEYDOWN:
            dx, dy = 0, 0

            if keys[pg.K_e]:
                for obj in action_objects:
                    performed = obj.perform_action(player)

                    if performed:
                        break

            if keys[pg.K_UP] or keys[pg.K_DOWN] or keys[pg.K_RIGHT] or keys[pg.K_LEFT]:
                direction = [0, 0]

                if event.key == pg.K_UP:
                    direction = [0, 1]
                elif event.key == pg.K_DOWN:
                    direction = [0, -1]
                elif event.key == pg.K_RIGHT:
                    direction = [1, 0]
                elif event.key == pg.K_LEFT:
                    direction = [-1, 0]

                player.slash_attack(direction)

            if keys[pg.K_SPACE]:
                player.dash()

    keys = pg.key.get_pressed()

    dx = 1 if keys[pg.K_d] else -1 if keys[pg.K_a] else 0
    dy = 1 if keys[pg.K_w] else -1 if keys[pg.K_s] else 0

    if dx != 0 or dy != 0:
        player.move_player(dx, -dy, walls)

    screen.fill("#25141A")

    arrows = []
    [arrows.extend(trap.arrows) for trap in traps if hasattr(trap, 'arrows')]

    higher_order_traps = []
    spikes = []
    for trap in traps:
        if isinstance(trap, SpikeTrap):
            spikes.append(trap)
        else:
            higher_order_traps.append(trap)


    game_objs_groups = [ground, walls, decorations, spikes, items, characters, higher_order_traps, visuals, arrows]
    for group in game_objs_groups:
        for obj in group:
            screen.blit(obj.image, (obj.rect.x + camera.rect.x, obj.rect.y + camera.rect.y))

            if isinstance(obj, Merchant):
                obj.render_items(camera, player, screen)

    camera.update(player)

    for trap in traps:
        if player.rect.colliderect(trap.rect) and trap.damage > 0:
            if isinstance(trap, SpikeTrap) and player.rect.bottom - CHARACTER_SIZE >= trap.rect.top:
                continue

            player.take_damage(trap.damage)
            trap.already_hit = True

        if hasattr(trap, 'arrows'):
            for arrow in trap.arrows:
                if arrow.rect.colliderect(player.rect):
                    player.take_damage(1)
                    trap.already_hit = True
                    trap.arrows.remove(arrow)
                if any(arrow.rect.colliderect(wall) for wall in walls):
                    trap.arrows.remove(arrow)

    chests = []
    for item in items:
        if isinstance(item, Chest):
            chests.append(item)
        else:
            if item.rect.colliderect(player.rect):
                player.add_item(item)
                item.remove(items)

    for char in characters:
        # display health bar
        if isinstance(char, Enemy) and char.health < char.full_health:
            health_bar_length = 60
            health_bar_height = 10
            current_health_length = (char.health / char.full_health) * health_bar_length

            pos_x = char.rect.x - (health_bar_length - CHARACTER_SIZE) // 2 + camera.rect.x
            pos_y = char.rect.y - 14 - health_bar_height // 2 + camera.rect.y

            pg.draw.rect(screen, (0, 0, 0), (pos_x, pos_y, health_bar_length, health_bar_height))
            pg.draw.rect(screen, (255, 0, 0), (pos_x, pos_y, current_health_length, health_bar_height))

        for attack in char.attacks:
            dest = attack['dest']
            effect = pg.Surface(attack['dim'])
            dmg = attack['damage']

            attackRect = effect.get_rect()
            attackRect.x = dest[0]
            attackRect.y = dest[1]

            if char == player:
                for chest in chests:
                    if chest.rect.colliderect(attackRect):
                        chest.open()

            for testedChar in characters:
                if attackRect.colliderect(testedChar) and testedChar != char:
                    if testedChar == player:
                        player.take_damage(1)
                    else:
                        testedChar.health -= dmg
                        if isinstance(testedChar, Enemy) and testedChar.health <= 0:
                            characters.remove(testedChar)
                            images = load_images_from_folder("assets/effects/explosion")
                            visuals.add(Visual(images, testedChar.rect.inflate(20, 20), pg.time.get_ticks(), 400))
                    print('hit')

            char.attacks.remove(attack)

            images = load_images_from_folder("assets/effects/slash_attack")
            attackVisual = Visual(images, attackRect, attack['start_time'], attack['duration'], attack['flipped_x'], attack['flipped_y'])

            visuals.add(attackVisual)


    wx = len(room_map[0]) * 16
    wy = len(room_map) * 16

    new_cell = room_map[int(player.rect.y // WALL_SIZE // 16)][int(player.rect.x // WALL_SIZE // 16)]
    if current_cell != new_cell:
        for y, row in enumerate(mini_map):
            for x, el in enumerate(row):
                if el == new_cell:
                    discovered_mini_map[y][x] = new_cell

    current_cell = new_cell
    display_ui(player.coins, player.health, discovered_mini_map, current_cell, player.number_of_keys, defeat_timer_seconds)

    visuals.update()
    decorations.update()
    traps.update(player)
    items.update(player)
    characters.update(walls, player.rect)

    pg.display.flip()
    clock.tick(60)

pg.quit()
