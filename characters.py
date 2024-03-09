import math
import random

import pygame as pg

from items import Item, Key
from shared import WALL_SIZE, CHARACTER_SIZE, characters, visuals, font
from utility import Animated, load_images_from_folder, Visual, NotificationVisual, ActionObject


class Character(pg.sprite.Sprite, Animated):
    def __init__(self, x, y, images_path):
        super().__init__()
        self.health = 0
        self.full_health = 0
        images = load_images_from_folder(images_path)

        size_multiplier = 0.96

        Animated.__init__(self, images, (CHARACTER_SIZE * size_multiplier, CHARACTER_SIZE * size_multiplier), 400)
        self.last_attack_time = pg.time.get_ticks()
        self.attack_cooldown = 0
        self.rect = self.image.get_rect(topleft=(x + (CHARACTER_SIZE * size_multiplier) // 2, y + (CHARACTER_SIZE * size_multiplier) // 2))

        self.attacks = []
        self.speed = 1

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

    def update(self, obstacles, *args, **kwargs):
        self.animate_new_frame()
        self.update_dash(obstacles)

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

    def update_dash(self, obstacles):
        if self.dashing:
            self.move_player(self.move_direction[0], self.move_direction[1], obstacles, True)

            if self.current_dash_length >= self.goal_dash_length:
                self.dashing = False
                self.current_dash_length = 0

    def move_player(self, dx, dy, obstacles, ignore_dash_check=False):
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

        is_collision = False
        for obj in obstacles:
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

            is_collision_along_x = any(obj.rect.colliderect(new_x_rect) and obj != self for obj in obstacles)
            is_collision_along_y = any(obj.rect.colliderect(new_y_rect) and obj != self for obj in obstacles)

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

        self.flip_model_on_move(self.move_direction[0])

        dash_rotation = 90 if self.move_direction[1] < 0 else -90 if self.move_direction[1] > 0 else 0
        visuals.add(Visual(self.dash_animation_images, self.rect.copy(), pg.time.get_ticks(), 200, not(self.flipped_x), rotate=dash_rotation))

    def add_item(self, item):

        if isinstance(item, Key):
            self.number_of_keys += 1

        if isinstance(item, PlayerUpgradeItem):
            if item.stat == "movement_speed":
                self.speed *= item.modifier



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

    def change_position(self, move_x, move_y, obstacles):
        if not self.is_colliding_with_walls(move_x, move_y, obstacles):
            self.rect.x += move_x
            self.rect.y += move_y
            return True
        else:
            # fix bug where enemy gets stuck in a wall
            if not self.is_colliding_with_walls(math.copysign(max(1, abs(move_x)), move_x), 0, obstacles):
                self.rect.x += move_x
                return True
            elif not self.is_colliding_with_walls(0, math.copysign(max(1, abs(move_y)), move_y), obstacles):
                self.rect.y += move_y
                return True

        return False

    def move_in_direction(self, goal_position, obstacles):
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

        moved = self.change_position(move_x, move_y, obstacles)

        if distance <= 2 or not moved:
            self.last_known_player_position = None
            self.roam_position = None
            self.last_roam_time = pg.time.get_ticks()
            self.last_turn_around_animation_time = pg.time.get_ticks()
            self.roam_wait_time = random.randint(1500, 2500)

    def update(self, obstacles, player_rect, *args, **kwargs):
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

            self.move_in_direction((player_rect.x, player_rect.y), obstacles)
            self.last_known_player_position = (player_rect.x, player_rect.y)

            distance_to_player = (self.rect.x - player_rect.x) ** 2 + (self.rect.y - player_rect.y) ** 2
            if distance_to_player < 9000 and pg.time.get_ticks() - self.last_attack_time > self.attack_cooldown:

                if abs(self.rect.x - player_rect.x) > abs((self.rect.y - player_rect.y)):
                    self.attack_dir = [math.copysign(1, player_rect.x - self.rect.x), 0]
                else:
                    self.attack_dir = [0, math.copysign(1, self.rect.y - player_rect.y)]

                self.about_to_attack_time = pg.time.get_ticks()

        elif self.last_known_player_position:
            self.move_in_direction(self.last_known_player_position, obstacles)
        elif self.roam_position:
            roam_point = pg.Rect(self.rect)
            roam_point.x = self.roam_position[0]
            roam_point.y = self.roam_position[1]
            roam_point.width = 1
            roam_point.height = 1

            self.in_line_of_sight(roam_point, obstacles, True)
            self.move_in_direction(self.roam_position, obstacles)
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

    def is_colliding_with_walls(self, dx, dy, obstacles):
        new_rect = self.rect.move(dx, dy)
        for wall in obstacles:
            if wall.rect.colliderect(new_rect):
                return True
        return False

    def in_line_of_sight(self, position_rect, obstacles, ignore_view_distance=False, camera=None, screen=None):
        # draw the vision ray
        if camera and screen:
            vision_start = self.rect.centerx + camera.rect.x, self.rect.centery + camera.rect.y
            pos = position_rect.centerx + camera.rect.x, position_rect.centery + camera.rect.y

            pg.draw.line(screen, (255, 255, 0), vision_start, pos, 2)

        if not ignore_view_distance and math.dist((self.rect.centerx, self.rect.centery), (position_rect.centerx, position_rect.centery)) > 250:
            return False

        for obstacle in obstacles:
            if obstacle.rect.clipline((self.rect.center, position_rect.center)):
                return False
        return True






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

    def render_items(self, camera, player, screen):
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


