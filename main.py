import copy
import math

import pygame as pg
import random
import csv
import os
from copy import copy, deepcopy

pg.init()

WIDTH, HEIGHT = 1000, 700
WHITE = (255, 255, 255)

screen = pg.display.set_mode((WIDTH, HEIGHT))
clock = pg.time.Clock()

CHARACTER_SIZE = 50
WALL_SIZE = CHARACTER_SIZE

def compare_rect(rect1, rect2):
    return (rect1.x != rect2.x or
            rect1.y != rect2.y or
            rect1.width != rect2.width or
            rect1.height != rect2.height)


class Animated():
    def __init__(self, images, size, frame_duration, flipped_x=False, flipped_y=False, rotation=0):
        super().__init__()
        self.images = images
        self.image = pg.transform.scale(images[0], size)
        self.frame_duration = frame_duration
        self.last_frame_time = pg.time.get_ticks()
        self.cur_frame = 0
        self.size = size

        self.flipped_x = flipped_x
        self.flipped_y = flipped_y
        self.rotation = rotation

    def animate(self):
        self.last_frame_time = pg.time.get_ticks()
        self.cur_frame = (self.cur_frame + 1) % len(self.images)
        self.image = pg.transform.scale(self.images[self.cur_frame], self.size)
        self.image = pg.transform.flip(self.image, self.flipped_x, self.flipped_y)
        self.image = pg.transform.rotate(self.image, self.rotation)

    def animate_new_frame(self):
        if pg.time.get_ticks() - self.last_frame_time > self.frame_duration:
            self.animate()

class Visual(pg.sprite.Sprite, Animated):
    def __init__(self, images, rect, start_time, duration, flipped_x=False, flipped_y=False, rotation=0):
        pg.sprite.Sprite.__init__(self)
        Animated.__init__(self, images, (rect.width, rect.height), int(duration/len(images)), flipped_x, flipped_y, rotation)

        self.start_time = start_time
        self.duration = duration
        self.image = images[0]
        self.rect = rect

    def update(self, *args, **kwargs):
        self.animate_new_frame()

        if pg.time.get_ticks() - self.start_time >= self.duration:
            # remove yourself from Group
            self.kill()


class Wall(pg.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = pg.transform.scale(image, (WALL_SIZE, WALL_SIZE))
        self.col = x
        self.row = y
        self.rect = self.image.get_rect(topleft=(x * WALL_SIZE, y * WALL_SIZE))

class Character(pg.sprite.Sprite, Animated):
    def __init__(self, x, y, images_path):
        super().__init__()
        self.health = 0
        self.full_health = 0
        images = load_images_from_folder(images_path)
        Animated.__init__(self, images, (WALL_SIZE, WALL_SIZE), 400)
        self.last_attack_time = pg.time.get_ticks()
        self.attack_cooldown = 700
        self.attack_cooldown = 0
        self.rect = self.image.get_rect(topleft=(x, y))
        self.attacks = []

    def flip_model_on_move(self, dx):
        if dx < 0 and not self.flipped_x:
            self.flipped_x = True
            self.animate()
        elif dx > 0 and self.flipped_x:
            self.flipped_x = False
            self.animate()


    def slash_attack(self, direction):
        if pg.time.get_ticks() - self.last_attack_time < self.attack_cooldown:
            return

        self.last_attack_time = pg.time.get_ticks()

        if direction[1] == 1:
            dim = (CHARACTER_SIZE * 3, CHARACTER_SIZE)
            dest = (self.rect.x - CHARACTER_SIZE, self.rect.y - CHARACTER_SIZE)
        elif direction[1] == -1:
            dim = (CHARACTER_SIZE * 3, CHARACTER_SIZE)
            dest = (self.rect.x - CHARACTER_SIZE, self.rect.y + CHARACTER_SIZE)
        elif direction[0] == -1:
            dim = (CHARACTER_SIZE, CHARACTER_SIZE * 3)
            dest = (self.rect.x - CHARACTER_SIZE, self.rect.y - CHARACTER_SIZE)
        elif direction[0] == 1:
            dim = (CHARACTER_SIZE, CHARACTER_SIZE * 3)
            dest = (self.rect.x + CHARACTER_SIZE, self.rect.y - CHARACTER_SIZE)
        else:
            return

        scale = 0.90
        dest = tuple(int(dest[i] + dim[i] * (1-scale)/2) for i in range(len(dest)))
        dim = tuple(int(x * scale) for x in dim)

        attack = {
            'dim': dim,
            'dest': dest,
            'start_time': pg.time.get_ticks(),
            'duration': 150,
            'flipped_x': direction[0] == -1,
            'flipped_y': direction[1] == 1,
            "damage": 34
        }

        self.attacks.append(attack)


class Enemy(Character):
    def __init__(self, x, y):
        super().__init__(x, y, "skeleton_enemy_1")
        self.attack_dir = None
        self.speed = 1
        self.health = 100
        self.full_health = 100
        self.last_known_player_position = None
        self.roam_position = None
        self.last_roam_time = pg.time.get_ticks()
        self.roam_wait_time = random.randint(1500, 2500)
        self.last_turn_around_animation_time = pg.time.get_ticks()
        self.attack_cooldown = 1500
        self.about_to_attack_time = 0

    def change_position(self, move_x, move_y):
        if not self.is_colliding_with_walls(move_x, move_y):
            self.rect.x += move_x
            self.rect.y += move_y
            return True
        else:
            # fix bug where enemy gets stuck in a wall
            if not self.is_colliding_with_walls(math.copysign(max(1, abs(move_x)), move_x), 0):
                self.rect.x += move_x
                return True
            elif not self.is_colliding_with_walls(0, math.copysign(max(1, abs(move_y)), move_y)):
                self.rect.y += move_y
                return True

        return False

    def move_in_direction(self, goal_position):
        pos_x, pos_y = goal_position
        dx = pos_x - self.rect.x
        dy = pos_y - self.rect.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance != 0:
            dx /= distance
            dy /= distance

        move_x = math.copysign(max(1, abs(dx * self.speed)), dx)
        move_y = math.copysign(max(1, abs(dy * self.speed)), dy)

        self.flip_model_on_move(dx)

        moved = self.change_position(move_x, move_y)

        if distance <= 2 or not moved:
            self.last_known_player_position = None
            self.roam_position = None
            self.last_roam_time = pg.time.get_ticks()
            self.last_turn_around_animation_time = pg.time.get_ticks()
            self.roam_wait_time = random.randint(1500, 2500)


    def update(self, player_rect, obstacles, *args, **kwargs):

        if self.about_to_attack_time != 0:
            if self.attack_dir and pg.time.get_ticks() - self.about_to_attack_time > 500:
                self.slash_attack(self.attack_dir)
                self.attack_dir = None
                self.about_to_attack_time = 0
        elif self.in_line_of_sight(player_rect, obstacles):
            # if self.last_known_player_position == None:
                #visuals.add(Visual(self.dash_animation_images, self.rect.copy(), pg.time.get_ticks(), 200, not(self.flipped_x), rotation=dash_rotation))

            self.move_in_direction((player_rect.x, player_rect.y))
            self.last_known_player_position = (player_rect.x, player_rect.y)

            distance_to_player = (self.rect.x - player_rect.x) ** 2 + (self.rect.y - player_rect.y) ** 2
            if distance_to_player < 9000 and pg.time.get_ticks() - self.last_attack_time > self.attack_cooldown:

                if abs(self.rect.x - player_rect.x) > abs((self.rect.y - player_rect.y)):
                    self.attack_dir = [math.copysign(1, player_rect.x - self.rect.x), 0]
                else:
                    self.attack_dir = [0, math.copysign(1, self.rect.y - player_rect.y)]

                self.about_to_attack_time = pg.time.get_ticks()

        elif self.last_known_player_position:
            self.move_in_direction(self.last_known_player_position)
        elif self.roam_position:
            random_point = pg.Rect(self.rect)
            random_point.x = self.roam_position[0]
            random_point.y = self.roam_position[1]
            random_point.width = 1
            random_point.height = 1

            self.in_line_of_sight(random_point, obstacles, True)
            self.move_in_direction(self.roam_position)
        else:
            wait_dt = pg.time.get_ticks() - self.last_roam_time
            animation_dt = pg.time.get_ticks() - self.last_turn_around_animation_time

            if wait_dt < self.roam_wait_time - 50:
                if animation_dt < self.roam_wait_time/2:
                    self.flipped_x = not self.flipped_x
                    self.animate_new_frame()
                    self.last_turn_around_animation_time = pg.time.get_ticks()
                return

            # chose random point, check if in line of sight
            random_point = pg.Rect(self.rect)
            random_point.x += random.randint(150, 350) * [-1, 1][random.randint(0, 1)]
            random_point.y += random.randint(150, 350) * [-1, 1][random.randint(0, 1)]
            random_point.width = 1
            random_point.height = 1

            if self.in_line_of_sight(random_point, obstacles, True):
                self.roam_position = (random_point.x, random_point.y)

        self.animate_new_frame()

    def is_colliding_with_walls(self, dx, dy):
        new_rect = self.rect.move(dx, dy)
        for wall in walls:
            if wall.rect.colliderect(new_rect):
                return True
        return False

    def in_line_of_sight(self, position_rect, obstacles, ignore_view_distance=False):
        # draw the vision ray
        vision_start = self.rect.centerx + camera.rect.x, self.rect.centery + camera.rect.y
        pos = position_rect.centerx + camera.rect.x, position_rect.centery + camera.rect.y

        pg.draw.line(screen, (255, 255, 0), vision_start, pos, 2)

        if not ignore_view_distance and math.dist(vision_start, pos) > 250:
            return False

        for obstacle in obstacles:
            if obstacle.rect.clipline((self.rect.center, position_rect.center)):
                return False
        return True


class Player(Character):
    def __init__(self, start_x, start_y):
        super().__init__(start_x, start_y, "player_character")
        self.dest_x = self.rect.x
        self.dest_y = self.rect.y
        self.coins = 0
        self.health = 3
        self.full_health = 6
        self.dashing = False
        self.last_dash_time = pg.time.get_ticks()
        self.dash_cooldown = 500
        self.dash_animation_images = load_images_from_folder("effects/dash")
        self.move_animation_images = load_images_from_folder("effects/step")
        self.last_move_animation = pg.time.get_ticks()
        self.direction = [0, 0]

    def update(self, *args, **kwargs):
        self.animate_new_frame()
        self.update_dash()

    def update_dash(self):
        if self.dashing:
            if self.rect.x != self.dest_x or self.rect.y != self.dest_y:
                move_x = min(12, abs(self.rect.x - self.dest_x))
                move_y = min(12, abs(self.rect.y - self.dest_y))
                self.move(math.copysign(move_x, self.direction[0]), math.copysign(move_y, self.direction[1]), True)

            if self.rect.x == self.dest_x and self.rect.y == self.dest_y:
                self.dashing = False

    def move(self, dx, dy, ignore_dash_check=False):
        if self.dashing and not ignore_dash_check:
            return

        moved = True

        new_x = self.rect.x + dx
        new_y = self.rect.y + dy

        self.direction = (0 if dx == 0 else math.copysign(1, dx), 0 if dy == 0 else math.copysign(1, dy))

        new_rect = pg.Rect(new_x, new_y, CHARACTER_SIZE, CHARACTER_SIZE)
        objs = [characters, walls]

        is_collision = False
        for obj in walls:
            if obj.rect.colliderect(new_rect) and obj != self:
                is_collision = True
                break
        if is_collision:
            print("Collision, cannot move")
            self.dashing = False
            self.last_dash_time = pg.time.get_ticks()

        if not is_collision:
            self.rect = new_rect
            if dx != 0:
                self.flip_model_on_move(dx)
        else:
            # if collision occurred, try moving along each axis individually
            new_x_rect = pg.Rect(new_x, self.rect.y, CHARACTER_SIZE, CHARACTER_SIZE)
            new_y_rect = pg.Rect(self.rect.x, new_y, CHARACTER_SIZE, CHARACTER_SIZE)

            is_collision_along_x = any(obj.rect.colliderect(new_x_rect) and obj != self for group in objs for obj in group)
            is_collision_along_y = any(obj.rect.colliderect(new_y_rect) and obj != self for group in objs for obj in group)

            if not is_collision_along_x:
                self.rect.x = new_x
                self.flip_model_on_move(dx)
            elif not is_collision_along_y:
                self.rect.y = new_y
            else:
                # both axes have collisions, cannot move
                self.dashing = False
                moved = False
                self.last_dash_time = pg.time.get_ticks()
                print("Collision, cannot move")

        if moved and pg.time.get_ticks() - self.last_move_animation > 220:
            visuals.add(Visual(self.move_animation_images, self.rect.move(-25 * self.direction[0], -25 * self.direction[1]).inflate(-35,-35), pg.time.get_ticks(), 250))
            self.last_move_animation = pg.time.get_ticks()

    def dash(self):
        if pg.time.get_ticks() - self.last_dash_time < self.dash_cooldown:
            return

        dash_distance = 150

        if self.direction[0] and self.direction[1]:
            dash_distance = int(dash_distance/math.sqrt(2))

        dx = dash_distance * self.direction[0]
        dy = dash_distance * self.direction[1]

        new_x = self.rect.x + dx
        new_y = self.rect.y + dy

        self.last_dash_time = pg.time.get_ticks()
        self.dest_x = new_x
        self.dest_y = new_y
        self.dashing = True

        self.flip_model_on_move(dx)

        dash_rotation = 90 if dy < 0 else -90 if dy > 0 else 0
        visuals.add(Visual(self.dash_animation_images, self.rect.copy(), pg.time.get_ticks(), 200, not(self.flipped_x), rotation=dash_rotation))


class Camera:
    def __init__(self, width, height):
        self.rect = pg.Rect(0, 0, width, height)

        self.width = width
        self.height = height
        self.initial_width = width
        self.initial_height = height

    def update(self, target):
        x = -target.rect.x + (WIDTH // 2)
        y = -target.rect.y + (HEIGHT // 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - WIDTH), x)
        y = max(-(self.height - HEIGHT), y)

        self.rect = pg.Rect(x, y, self.width, self.height)


def load_images_from_folder(path):
    images = []
    for filename in os.listdir(path):
        img_path = os.path.join(path, filename)
        if os.path.isfile(img_path):
            image = pg.image.load(img_path).convert_alpha()
            images.append(image)
    return images

def convert_csv_to_2d_list(csv_file: str):
    tile_map = []
    with open(csv_file, "r") as f:
        for map_row in csv.reader(f):
            tile_map.append(list(map(int, map_row)))
    return tile_map

def load_tileset(image_path, tile_width, tile_height):
    image = pg.image.load(image_path).convert_alpha()
    image_width, image_height = image.get_size()

    tiles = []
    for y in range(0, image_height, tile_height):
        for x in range(0, image_width, tile_width):
            tile = image.subsurface((x, y, tile_width, tile_height)).convert_alpha()
            tiles.append(tile)

    return tiles



walls = pg.sprite.Group()
ground = pg.sprite.Group()

rooms_tile_maps = []

#todo: here
# read all the available rooms
# every room has a certain size like 32x32, but there can be a lot of black spaces
# entrances only in the middle and corridors are like 2x2


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


heart_image = pg.transform.scale(pg.image.load('heart.png'), (30, 28))
coin_images = load_tileset("coin.png", 13, 13)
coin_animated = Animated(coin_images, (30, 30), 200)


def display_health(health):
    for i in range(health):
        screen.blit(heart_image, (10 + i * 40, 10))


def display_coins(coins):
    screen.blit(coin_animated.image, (10, 50))
    font = pg.font.Font("retro_font.ttf", 22)
    text = font.render("0" * (3 - int(math.log10(coins+1))) + str(coins), True, WHITE)
    screen.blit(text, (50, 52))
    coin_animated.animate_new_frame()



def display_full_map(map, current_cell):
    gap = 5
    cell_size = 40
    map = trim_matrix(map)

    map_width = len(map[0]) * cell_size + (len(map[0]) - 1) * gap
    map_height = len(map) * cell_size + (len(map) - 1) * gap

    offset_x = (WIDTH - map_width) // 2
    offset_y = (HEIGHT - map_height) // 2

    bg_width = max(400, map_width + 100)
    bg_height = max(400, map_height + 100)

    pg.draw.rect(screen, (0, 0, 0), ((WIDTH - bg_width)//2, (HEIGHT - bg_height)//2, bg_width, bg_width))

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

    pg.draw.rect(screen, (0, 0, 0), (WIDTH - screen_gap - map_size_px, screen_gap, map_size_px, map_size_px))

    for y in range(5):
        for x in range(5):
            display_x = WIDTH - cells_gap - map_size_px + (x+1) * (cell_width + gap)
            display_y = cells_gap + 2 + y * cell_height + gap * y
            cell_value = mini_map[y][x]
            color = (255, 0, 0) if cell_value == current_cell else (0, 255, 0) if cell_value != 0 else (0, 0, 0)
            pg.draw.rect(screen, color, (display_x, display_y, cell_width, cell_height))



def display_ui(coins, health, mini_map, current_cell):
    display_health(health)
    display_coins(coins)
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


rooms = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
tile_map = connect_rooms(rooms)
mini_map = trim_matrix(tile_map)
discovered_mini_map = deepcopy(mini_map)
for y, row in enumerate(discovered_mini_map):
    for x, el in enumerate(row):
        if el != 1:
            discovered_mini_map[y][x] = 0

characters = pg.sprite.Group()

room_tile_map = convert_csv_to_2d_list(csv_file="room.csv")
tiles_images = load_tileset("tileset.png", 16, 16)
ROOM_WIDTH = len(room_tile_map[0])
ROOM_HEIGHT = len(room_tile_map)

for i in range(len(tile_map)):
    for j in range(len(tile_map[0])):

        room = tile_map[i][j]
        x_off = ROOM_WIDTH * j
        y_off = ROOM_HEIGHT * i

        if room == 0:
            continue

        room_layout = deepcopy(room_tile_map)

        middle_tile = ROOM_WIDTH // 2 - 1
        end_tile = ROOM_WIDTH - 1

        # room above
        if tile_map[i - 1][j] == 0:
            room_layout[0][middle_tile - 1] = 78  # dark tile
            room_layout[0][middle_tile + 2] = 78
            room_layout[0][middle_tile] = 78
            room_layout[0][middle_tile + 1] = 78
            room_layout[1][middle_tile] = 2 # wall tile
            room_layout[1][middle_tile + 1] = 2

        # room below
        if tile_map[i + 1][j] == 0:
            room_layout[end_tile][middle_tile-1] = 78  # dark tile
            room_layout[end_tile][middle_tile+2] = 78
            room_layout[end_tile][middle_tile] = 78
            room_layout[end_tile][middle_tile+1] = 78
            room_layout[end_tile-1][middle_tile] = 41 # wall tile
            room_layout[end_tile-1][middle_tile+1] = 41
            room_layout[end_tile-1][middle_tile-1] = 41 # wall tile
            room_layout[end_tile-1][middle_tile+2] = 41

        # right room
        if tile_map[i][j + 1] == 0:
            room_layout[middle_tile-1][end_tile] = 78  # dark tile
            room_layout[middle_tile][end_tile] = 78
            room_layout[middle_tile+1][end_tile] = 78
            room_layout[middle_tile+2][end_tile] = 78

            room_layout[middle_tile-1][end_tile-1] = 15  # wall tile
            room_layout[middle_tile][end_tile-1] = 15
            room_layout[middle_tile+1][end_tile-1] = 15
            room_layout[middle_tile+2][end_tile-1] = 15

            # left room
        if tile_map[i][j - 1] == 0:
            room_layout[middle_tile-1][0] = 78  # dark tile
            room_layout[middle_tile][0] = 78
            room_layout[middle_tile+1][0] = 78
            room_layout[middle_tile+2][0] = 78

            room_layout[middle_tile-1][1] = 10  # wall tile
            room_layout[middle_tile][1] = 10
            room_layout[middle_tile+1][1] = 10
            room_layout[middle_tile+2][1] = 10


        for row in range(len(room_layout)):
            for col in range(len(room_layout[row])):
                pos_x = col + x_off
                pos_y = row + y_off

                id = room_layout[row][col]
                if id in [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 41, 42, 43, 44, 45, 50, 51, 52, 53, 54, 55]:
                    walls.add(Wall(tiles_images[id], pos_x, pos_y))
                else:
                    ground.add(Wall(tiles_images[id], pos_x, pos_y))

map_width_px = len(tile_map[0]) * WALL_SIZE * ROOM_WIDTH
map_height_px = len(tile_map) *  WALL_SIZE * ROOM_HEIGHT

player = Player(map_width_px//2, map_height_px//2)
ch1 = Enemy(map_width_px//2, map_height_px//2 + 250)

visuals = pg.sprite.Group()
characters.add(player, ch1)

camera = Camera(map_width_px, map_height_px)

current_cell = tile_map[int(player.rect.y // WALL_SIZE // 16)][int(player.rect.x // WALL_SIZE // 16)]

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        keys = pg.key.get_pressed()
        if event.type == pg.KEYDOWN:
            dx, dy = 0, 0

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

    speed = 4

    dx = speed if keys[pg.K_d] else -speed if keys[pg.K_a] else 0
    dy = speed if keys[pg.K_w] else -speed if keys[pg.K_s] else 0

    if dx != 0 or dy != 0:
        player.move(dx, -dy)

    screen.fill("#25141A")
    
    game_objs_groups = [ground, walls, characters, visuals]
    for group in game_objs_groups:
        for obj in group:
            screen.blit(obj.image, (obj.rect.x + camera.rect.x, obj.rect.y + camera.rect.y))

    camera.update(player)

    for char in characters:
        # display health bar
        if char != player:
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

            for testedChar in characters:
                if attackRect.colliderect(testedChar) and testedChar != char:
                    if testedChar == player:
                        player.health -= 1
                    else:
                        testedChar.health -= dmg
                        if testedChar.health <= 0:
                            characters.remove(testedChar)
                            images = load_images_from_folder("effects/explosion")
                            visuals.add(Visual(images, testedChar.rect.inflate(20, 20), pg.time.get_ticks(), 400))

                    print('hit')

            char.attacks.remove(attack)

            images = load_images_from_folder("effects/slash_attack")
            attackVisual = Visual(images, attackRect, attack['start_time'], attack['duration'], attack['flipped_x'], attack['flipped_y'])

            visuals.add(attackVisual)

    wx = len(tile_map[0]) * 16
    wy = len(tile_map) * 16

    new_cell = tile_map[int(player.rect.y // WALL_SIZE // 16)][int(player.rect.x // WALL_SIZE // 16)]
    if current_cell != new_cell:
        for y, row in enumerate(mini_map):
            for x, el in enumerate(row):
                if el == new_cell:
                    discovered_mini_map[y][x] = new_cell

    current_cell = new_cell
    display_ui(player.coins, player.health, discovered_mini_map, current_cell)

    visuals.update()
    characters.update(player.rect, walls)

    pg.display.flip()
    clock.tick(60)

pg.quit()
