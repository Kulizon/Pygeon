import copy
import math

import pygame as pg
import random
from copy import copy, deepcopy

from characters import Character
from constans import WALL_SIZE, CHARACTER_SIZE
from utility import Animated, Visual, load_images_from_folder, load_tileset, convert_csv_to_2d_list

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



class Item(pg.sprite.Sprite, Animated):
    def __init__(self, images_path, x, y, frame_duration, size, rotate=0):
        super().__init__()
        self.rect = pg.Rect(x + (WALL_SIZE - size[0])//2, y + (WALL_SIZE - size[1])//2, size[0], size[1])
        images = load_images_from_folder(images_path)
        Animated.__init__(self, images, size, frame_duration, False, False, rotate)

    def update(self, *args, **kwargs):
        self.animate_new_frame()

class Key(Item):
    def __init__(self, x, y):
        super().__init__("assets/items_and_traps_animations/keys/silver", x, y, 200,
             [WALL_SIZE * 0.8, WALL_SIZE * 0.8])


class Chest(Item):
    def __init__(self, x, y, coins, health_potions):
        Item.__init__(self, "assets/items_and_traps_animations/chest/normal", x, y, 280, (WALL_SIZE * 0.8, WALL_SIZE * 0.8))

        self.open_chest_images = load_images_from_folder("assets/items_and_traps_animations/chest/open")
        self.coins = coins
        self.health_potions = health_potions
        self.opened = False
        self.added_visual = False

    def update(self, *args, **kwargs):
        if self.opened and self.cur_frame == self.last_frame and not self.added_visual:
            visuals.add(NotificationVisual(load_images_from_folder("assets/items_and_traps_animations/coin"), self.rect.move(-WALL_SIZE * 0.1, -60), True, 1600, iterations=3))
            player.coins += random.randint(10, 25)
            self.added_visual = True
        elif not self.added_visual:
            super().update(args, kwargs)

    def open(self):
        if not self.opened:
            self.cur_frame = 0
            self.images = self.open_chest_images
            self.opened = True

class Trap(pg.sprite.Sprite, Animated):
    def __init__(self, images_path, x, y, frame_duration, cooldown, attack_dir, size, rotate=0):
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(x, y, size[0], size[1])
        images = load_images_from_folder(images_path)
        Animated.__init__(self, images, size, frame_duration, False, False, rotate)

        self.attack_dir = attack_dir
        self.attack_cooldown_time = cooldown
        self.last_attack_time = pg.time.get_ticks()
        self.already_hit = False
        self.damage = 0

    def update(self, *args, **kwargs):
        if pg.time.get_ticks() - self.last_attack_time > self.attack_cooldown_time:
            self.animate_new_frame()
            if self.cur_frame == self.last_frame:
                self.last_attack_time = pg.time.get_ticks()
                self.already_hit = False

class FlamethrowerTrap(Trap):
    def __init__(self, x, y, attack_dir):
        if attack_dir[0] == -1:
            x -= 2 * WALL_SIZE
        elif attack_dir[0] == 1:
            x += WALL_SIZE

        if attack_dir[0]:
            images_path = "assets/items_and_traps_animations/flamethrower_sideways"
        else:
            images_path = "assets/items_and_traps_animations/flamethrower_front"

        rotate = 180 if attack_dir[0] == -1 else 0

        width = (abs(attack_dir[0]) + 1) * WALL_SIZE
        height = (abs(attack_dir[1]) + 1) * WALL_SIZE

        size = [width, height]

        x_off = width * 0.1
        y_off = height * 0.1

        size[0] *= 0.8
        size[1] *= 0.8

        super().__init__(images_path, x + x_off, y + y_off, 150, 1000, attack_dir, size, rotate)

    def update(self, *args, **kwargs):
        self.damage = 0 if (self.cur_frame in [0, self.last_frame, self.last_frame-1] or self.already_hit) else 1

        super().update(*args, **kwargs)


class ArrowTrap(Trap):
    def __init__(self, x, y, attack_dir):
        size = ((abs(attack_dir[0]) + 1) * WALL_SIZE, (abs(attack_dir[1]) + 1) * WALL_SIZE)

        if attack_dir[0]:
            images_path = "assets/items_and_traps_animations/arrow_horizontal"
        else:
            images_path = "assets/items_and_traps_animations/arrow_vertical"

        if attack_dir[0] == -1:
            x -= WALL_SIZE

        rotate = 180 if attack_dir[0] == 1 else 0

        Trap.__init__(self, images_path, x, y, 40, 2000, attack_dir, size, rotate)
        self.rect = self.rect.move(14 * attack_dir[0], 0)
        self.arrows = []

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)

        arrow_width = CHARACTER_SIZE * 0.65
        arrow_height = CHARACTER_SIZE * 0.47
        if self.cur_frame == self.last_frame:
            arrow_rect = pg.Rect(self.rect.x + CHARACTER_SIZE * self.attack_dir[0], self.rect.y + CHARACTER_SIZE * self.attack_dir[1], arrow_width, arrow_height)
            new_arrow = pg.sprite.Sprite()
            new_arrow.rect = arrow_rect

            if self.attack_dir[0]:
                image_path = "assets/arrow_horizontal.png"
                new_arrow.rect.y += (CHARACTER_SIZE - arrow_height) // 2
            else:
                image_path = "assets/arrow_vertical.png"

            new_arrow.image = pg.transform.scale(pg.image.load(image_path), (arrow_width, arrow_height))
            new_arrow.image = pg.transform.rotate(new_arrow.image, 180 if self.attack_dir[0] == 1 else 0)

            self.arrows.append(new_arrow)
            self.cur_frame = 0

        for arrow in self.arrows:
            arrow.rect.x += 8 * self.attack_dir[0]
            arrow.rect.y += 8 * self.attack_dir[1]


class SpikeTrap(Trap):
    def __init__(self, x, y):
        size = (WALL_SIZE * 0.8, WALL_SIZE * 0.8)
        images_path = "assets/items_and_traps_animations/peaks"

        Trap.__init__(self, images_path, x + WALL_SIZE * 0.1, y + WALL_SIZE * 0.1, 50, 1500, attack_dir, size)
        self.spikes_up_time = 600
        self.spikes_went_up_time = None
        self.spikes_up_frame_num = 2

    def update(self, *args, **kwargs):
        self.damage = 1 if self.cur_frame == self.spikes_up_frame_num and not self.already_hit else 0

        if self.cur_frame == self.spikes_up_frame_num and not self.spikes_went_up_time:
            self.spikes_went_up_time = pg.time.get_ticks()

        if not (self.spikes_went_up_time and pg.time.get_ticks() - self.spikes_went_up_time < self.spikes_up_time):
            super().update(args, kwargs)
            self.spikes_went_up_time = None


class Enemy(Character):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/skeleton_enemy_1")
        self.attack_dir = None
        self.health = 100
        self.full_health = 100
        self.last_known_player_position = None
        self.roam_position = None
        self.last_roam_time = pg.time.get_ticks()
        self.roam_wait_time = random.randint(1500, 2500)
        self.last_turn_around_animation_time = pg.time.get_ticks()
        self.attack_cooldown = 1500
        self.about_to_attack_time = 0

        self.spotted_time = None
        self.spotted_wait_duration = 500

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

        dx *= self.speed
        dy *= self.speed

        move_x = math.copysign(max(1, abs(dx)), dx)
        move_y = math.copysign(max(1, abs(dy)), dy)

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
            if self.last_known_player_position is None and self.spotted_time is None:
                visuals.add(NotificationVisual(load_images_from_folder("assets/effects/spotted"), self.rect.move(0, -60)))
                self.flip_model_on_move(player_rect.x - self.rect.x)
                self.spotted_time = pg.time.get_ticks()

            if self.spotted_time and pg.time.get_ticks() - self.spotted_time < self.spotted_wait_duration:
                return

            self.spotted_time = None

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
            roam_point = pg.Rect(self.rect)
            roam_point.x = self.roam_position[0]
            roam_point.y = self.roam_position[1]
            roam_point.width = 1
            roam_point.height = 1

            self.in_line_of_sight(roam_point, obstacles, True)
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
            random_point.x += random.randint(50, 150) * [-1, 1][random.randint(0, 1)]
            random_point.y += random.randint(50, 150) * [-1, 1][random.randint(0, 1)]
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


class ActionObject:
    def __init__(self, rect, action_to_perform, max_distance = CHARACTER_SIZE):
        self.rect = rect
        self.action_to_perform = action_to_perform
        self.max_distance = max_distance


    def is_close(self, player):
        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery

        distance = math.sqrt(dx**2 + dy**2)

        return distance < self.max_distance

    def perform_action(self, player):
        if self.is_close(player):
            self.action_to_perform(player)
            return True
        return False


class PlayerUpgradeItem(Item):
    def __init__(self, images_path, x, y, stat, modifier):
        super().__init__(images_path, x, y, 300, (WALL_SIZE * 0.8, WALL_SIZE * 0.8))
        self.stat = stat
        self.modifier = modifier

class MerchantItem(Item, ActionObject):
    def __init__(self, item, price):
        self.item_to_sell = item
        Item.__init__(self, "assets/items_and_traps_animations/mini_chest", item.rect.x, item.rect.y, item.frame_duration, item.rect.size)
        ActionObject.__init__(self, self.rect, self.sell, CHARACTER_SIZE)

        self.images = item.images
        self.price = price
        self.bought = False

    def sell(self, player):
        if player.coins >= self.price and self.price >= 0:
            player.coins -= self.price

            self.bought = True
            player.add_item(self.item_to_sell)



class Merchant(Character):
    def __init__(self, start_x, start_y):
        Character.__init__(self, start_x, start_y, "assets/merchant")

        it1 = MerchantItem(Key(self.rect.x - 2 * WALL_SIZE, start_y + self.rect.height + 20), 5)
        it2 = MerchantItem(Key(self.rect.x, start_y + self.rect.height + 20), 0)
        it3 = MerchantItem(PlayerUpgradeItem("assets/items_and_traps_animations/flag", self.rect.x + 2 * WALL_SIZE, start_y + self.rect.height + 20, "movement_speed", 2), 0)



        self.items_to_sell = [it1, it2, it3]

    def render_items(self, camera, player):
        for item in self.items_to_sell:

            screen.blit(item.image, (item.rect.x + camera.rect.x, item.rect.y + camera.rect.y))

            color = (255, 0, 0) if item.is_close(player) else (255, 255, 255)

            text = font.render(str(item.price) + "$", True, color)
            screen.blit(text, (item.rect.x + camera.rect.x, item.rect.y + camera.rect.y + item.image.get_height() + 10))

    def update(self, *args, **kwargs):
        self.animate_new_frame()

        for i, item in enumerate(self.items_to_sell):
            item.update()

            if item.bought:
                new_item = MerchantItem(Item("assets/items_and_traps_animations/mini_chest", 0, 0, 500, [item.rect.width, item.rect.height]), -1)
                new_item.rect = item.rect
                self.items_to_sell[i] = new_item


class Player(Character):
    def __init__(self, start_x, start_y):
        super().__init__(start_x, start_y, "assets/player_character")
        self.dest_x = self.rect.x
        self.dest_y = self.rect.y
        self.coins = 0
        self.health = 10
        self.full_health = 12
        self.speed = 5
        self.dashing = False
        self.last_dash_time = pg.time.get_ticks()
        self.dash_cooldown = 200
        self.dash_animation_images = load_images_from_folder("assets/effects/dash")
        self.move_animation_images = load_images_from_folder("assets/effects/step")
        self.last_move_animation = pg.time.get_ticks()
        self.move_direction = [1, 0]
        self.current_dash_length = 0
        self.goal_dash_length = 100

        self.normal_images = load_images_from_folder("assets/player_character")
        self.hurt_images = load_images_from_folder("assets/player_character_hurt")
        self.harm_animation_duration = 200
        self.harm_animation_start_time = pg.time.get_ticks() - self.harm_animation_duration * 2
        self.max_flash_count = 5
        self.flash_count = self.max_flash_count

        self.number_of_keys = 0

    def update(self, *args, **kwargs):
        self.animate_new_frame()
        self.update_dash()

        if self.flash_count < self.max_flash_count:
            diff = pg.time.get_ticks() - self.harm_animation_start_time

            if self.flash_count % 2 == 0 and self.images != self.hurt_images and diff < self.harm_animation_duration:
                self.images = self.hurt_images
                self.animate()
            elif diff > self.harm_animation_duration:
                self.images = self.normal_images
                self.animate()
                self.flash_count += 1
                self.harm_animation_start_time = pg.time.get_ticks()

    def take_damage(self, damage):
        self.health -= damage
        self.harm_animation_start_time = pg.time.get_ticks()
        self.flash_count = 0

    def update_dash(self):
        if self.dashing:
            self.move_player(self.move_direction[0], self.move_direction[1], True)

            if self.current_dash_length >= self.goal_dash_length:
                self.dashing = False
                self.current_dash_length = 0

    def move_player(self, dx, dy, ignore_dash_check=False):
        if self.dashing and not ignore_dash_check:
            return

        distance = math.sqrt(dx**2 + dy**2)
        if distance != 0:
            dx /= distance
            dy /= distance

        if self.dashing:
            t = min(1, int(self.current_dash_length / self.goal_dash_length))
            easing_factor = t * (2 - t)
            dx *= self.speed * 2 * (1 + easing_factor)
            dy *= self.speed * 2 * (1 + easing_factor)
        else:
            dx *= self.speed
            dy *= self.speed

        self.current_dash_length += distance * self.speed

        moved = True

        new_x = self.rect.x + dx
        new_y = self.rect.y + dy

        self.move_direction = (0 if dx == 0 else math.copysign(1, dx), 0 if dy == 0 else math.copysign(1, dy))

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

            is_collision_along_x = any(obj.rect.colliderect(new_x_rect) and obj != self for obj in walls)
            is_collision_along_y = any(obj.rect.colliderect(new_y_rect) and obj != self for obj in walls)

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
            visuals.add(Visual(self.move_animation_images, self.rect.move(-25 * self.move_direction[0], 10 - 40 * self.move_direction[1]).inflate(-35, -35), pg.time.get_ticks(), 250))
            self.last_move_animation = pg.time.get_ticks()

    def dash(self):
        if pg.time.get_ticks() - self.last_dash_time < self.dash_cooldown:
            return

        self.current_dash_length = 0

        self.last_dash_time = pg.time.get_ticks()
        self.dashing = True

        self.flip_model_on_move(dx)

        dash_rotation = 90 if dy < 0 else -90 if dy > 0 else 0
        visuals.add(Visual(self.dash_animation_images, self.rect.copy(), pg.time.get_ticks(), 200, not(self.flipped_x), rotate=dash_rotation))

    def add_item(self, item):

        if isinstance(item, Key):
            self.number_of_keys += 1

        if isinstance(item, PlayerUpgradeItem):
            if item.stat == "movement_speed":
                self.speed *= item.modifier


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
font = pg.font.Font("assets/retro_font.ttf", 22)


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

characters = pg.sprite.Group()
traps = pg.sprite.Group()
items = pg.sprite.Group()

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

visuals = pg.sprite.Group()
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
        player.move_player(dx, -dy)

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
                obj.render_items(camera, player)

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
    traps.update()
    items.update()
    characters.update(player.rect, walls)

    pg.display.flip()
    clock.tick(60)

pg.quit()
