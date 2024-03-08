import math

import pygame as pg
from shared import WALL_SIZE, CHARACTER_SIZE, characters, visuals
from utility import Animated, load_images_from_folder, Visual

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

        print(obstacles)

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

