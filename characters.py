import math
import random

import pygame as pg

from items import Item, Key
from shared import WALL_SIZE, CHARACTER_SIZE, visuals, font, screen, walls, font_s
from utility import Animated, load_images_from_folder, Visual, NotificationVisual, ActionObject, Collider, load_tileset

player_images = load_tileset("assets/player_character/player.png", 32, 32)
player_upgrades_images = load_tileset("assets/food.png", 16, 16)[0:35]

class Character(pg.sprite.Sprite, Animated):
    def __init__(self, x, y, images, size):
        super().__init__()
        self.health = 0
        self.full_health = 0
        self.default_size = size

        Animated.__init__(self, images, (self.default_size, self.default_size), 200)
        self.last_attack_time = pg.time.get_ticks()
        self.attack_size = self.default_size
        self.attack_cooldown = 0
        self.rect = self.image.get_rect(topleft=(x + CHARACTER_SIZE // 2, y + CHARACTER_SIZE // 2))

        self.attacks = []
        self.speed = 1
        self.move_direction = [1, 0]

        self.movement_collider = None
        self.damage_collider = None

        self.mode = "idle"
        self.death_frame_duration = 135
        self.normal_frame_duration = self.frame_duration
        self.attack_frame_duration = 80

        self.idle_images = [[player_images[200]], [player_images[210]], [player_images[220]], [player_images[230]]]
        self.walking_images = [player_images[10:18], player_images[20:28], player_images[30:38], player_images[40:48]]
        self.dashing_images = [player_images[110:118], player_images[110]]
        self.attack_images = [player_images[160:166], player_images[170:176], player_images[180:186], player_images[190:196]]
        self.death_images = [player_images[150:158]]

        self.velocity_x = 0
        self.velocity_y = 0
        self.default_acceleration = 0.2
        self.acceleration = self.default_acceleration
        self.default_friction = 0.8
        self.friction = self.default_friction
        self.took_damage = False

    def take_damage(self, damage, enemy=None):
        self.health -= damage

        if enemy is None:
            return

        enemy_direction = [enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery]

        length = max(abs(enemy_direction[0]), abs(enemy_direction[1]))
        if length != 0:
            enemy_direction = [enemy_direction[0] / length, enemy_direction[1] / length]

        pushback_distance = 30
        self.move_direction = [-enemy_direction[0], -enemy_direction[1]]

        dx = self.move_direction[0] * pushback_distance
        dy = self.move_direction[1] * pushback_distance

        self.friction = 0.30
        self.acceleration = 0.1
        self.velocity_x = 0
        self.velocity_y = 0
        self.took_damage = True
        self.move_if_possible(dx, dy)

    def get_direction_index(self, direction):
        if direction[0] == 1:
            return 0
        elif direction[0] == -1:
            return 2
        elif direction[1] == -1:
            return 1
        elif direction[1] == 1:
            return 3
        else:
            return 0

    def flip_model_on_move(self, dx):
        if dx < 0 and not self.flipped_x:
            self.flipped_x = True
            self.animate()
        elif dx > 0 and self.flipped_x:
            self.flipped_x = False
            self.animate()

    def slash_attack(self, direction, scale):
        if pg.time.get_ticks() - self.last_attack_time < self.attack_cooldown:
            return

        self.last_attack_time = pg.time.get_ticks()

        size = self.attack_size
        if direction[1] == 1:
            dim = (size * 3, size)
            dest = (self.damage_collider.collision_rect.centerx - dim[0]//4, self.damage_collider.collision_rect.centery - self.damage_collider.collision_size[1] - dim[1]//2)
        elif direction[1] == -1:
            dim = (size * 3, size)
            dest = (self.damage_collider.collision_rect.centerx - dim[0]//4, self.damage_collider.collision_rect.centery + self.damage_collider.collision_size[1])
        elif direction[0] == -1:
            dim = (size, size * 3)
            dest = (self.damage_collider.collision_rect.centerx - self.damage_collider.collision_size[0] - dim[0]//2, self.damage_collider.collision_rect.centery - dim[1]//4)
        elif direction[0] == 1:
            dim = (size, size * 3)
            dest = (self.damage_collider.collision_rect.centerx + self.damage_collider.collision_size[0], self.damage_collider.collision_rect.centery - dim[1]//4)
        else:
            return

        dest = tuple(int(dest[i] + dim[i] * (1-scale)/2) for i in range(len(dest)))
        dim = tuple(int(x * scale) for x in dim)

        attack = {
            'dim': dim,
            'dest': dest,
            'start_time': pg.time.get_ticks(),
            'duration': 150,
            'flipped_x': direction[0] == -1 or direction[1] == -1,
            'flipped_y': (direction[0] == 0 and direction[1] != -1),
            "damage": 34
        }

        self.attacks.append(attack)

    def update(self, camera, *args, **kwargs):
        self.animate_new_frame()
        self.movement_collider.update(self.rect, camera)
        self.damage_collider.update(self.rect, camera)

    def change_images(self, images):
        self.images = images
        self.cur_frame = 0
        self.last_frame = len(images)-1
        self.animate()

    def is_dashing(self):
        return False

    def update_move_values(self, dx, dy):
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance != 0:
            dx /= distance
            dy /= distance
        if self.is_dashing():
            dx *= self.speed * 1.8
            dy *= self.speed * 1.8
        else:
            dx *= self.speed
            dy *= self.speed

        return dx, dy

    def change_walking_images(self, dx, dy):
        new_move_direction = (0 if dx == 0 else math.copysign(1, dx), 0 if dy == 0 else math.copysign(1, dy))

        if new_move_direction[0] == 0 and new_move_direction[1] == 0:
            return

        if self.mode == "idle" or (new_move_direction[0] != self.move_direction[0] or new_move_direction[1] != self.move_direction[1]):
            self.move_direction = new_move_direction
            if self.mode != "attacking":
                self.change_images(self.walking_images[self.get_direction_index(self.move_direction)])
                self.mode = "walking"
        self.move_direction = new_move_direction

    def change_idle_images(self, dx, dy):
        if dx == 0 and dy == 0:
            if self.mode == "attacking" or self.mode == "idle":
                return

            i = self.get_direction_index(self.move_direction)

            print(i, self.mode)

            self.change_images(self.idle_images[2 if i == 1 else 1 if i == 2 else i])
            self.mode = "idle"

    def move_if_possible(self, dx, dy):
        self.movement_collider.update(self.rect)

        if dx < 0:
            self.velocity_x += dx
        elif dx > 0:
            self.velocity_x += dx
        if dy < 0:
            self.velocity_y += dy
        elif dy > 0:
            self.velocity_y += dy

        self.velocity_x *= (1 - self.friction)
        self.velocity_y *= (1 - self.friction)

        # if isinstance(self, Player):
        #     print("if possible move")
        #     print(dx, dy, self.velocity_x, self.velocity_y)

        min_velocity = 0.1
        if abs(self.velocity_y) < min_velocity:
            self.velocity_y = 0
        if abs(self.velocity_x) < min_velocity:
            self.velocity_x = 0

        if self.took_damage and abs(self.velocity_y) + abs(self.velocity_x) < 2:
            self.took_damage = False
            self.friction = self.default_friction
            self.acceleration = self.default_acceleration

        self.velocity_x = abs(self.velocity_x) * (-1 if self.velocity_x < 0 else 1)
        self.velocity_y = abs(self.velocity_y) * (-1 if self.velocity_y < 0 else 1)

        dx = self.velocity_x
        dy = self.velocity_y

        dx = math.copysign(math.ceil(abs(dx)), dx)
        dy = math.copysign(math.ceil(abs(dy)), dy)
        new_rect = self.movement_collider.collision_rect.move(dx, dy)

        if dx == 0 and dy == 0:
            self.friction = self.default_friction
            return False

        is_collision, is_collision_along_x, is_collision_along_y = False, False, False
        for obj in walls:
            if obj.rect.colliderect(new_rect) and obj != self:
                is_collision = True
                break
        if not is_collision:
            self.rect.x += dx
            self.rect.y += dy
        else:
            # if collision occurred, try moving along each axis individually
            new_x_rect = self.movement_collider.collision_rect.move(dx, 0)
            new_y_rect = self.movement_collider.collision_rect.move(0, dy)

            is_collision_along_x = any(obj.rect.colliderect(new_x_rect) and obj != self for obj in walls)
            is_collision_along_y = any(obj.rect.colliderect(new_y_rect) and obj != self for obj in walls)

            if not is_collision_along_x:
                self.rect.x += dx
            elif not is_collision_along_y:
                self.rect.y += dy

        return not (is_collision and (is_collision_along_x or dx == 0) and (is_collision_along_y or dy == 0))


class Player(Character):
    def __init__(self, start_x, start_y):
        Character.__init__(self, start_x, start_y, player_images[0:4], CHARACTER_SIZE * 1.6)
        self.full_health = 12
        self.speed = 20

        self.last_dash_time = pg.time.get_ticks()
        self.dash_cooldown = 200
        self.dash_frame_duration = 80

        self.dash_animation_images = load_images_from_folder("assets/effects/dash")
        self.move_animation_images = load_images_from_folder("assets/effects/step")
        self.last_move_animation = pg.time.get_ticks()

        self.harm_animation_duration = 150
        self.harm_animation_start_time = pg.time.get_ticks()
        self.max_flash_count = 11
        self.flash_count = self.max_flash_count

        self.number_of_keys = 10
        self.coins = 1595
        self.health = 4
        self.is_next_level = False

        off_x = 40
        off_y = 40
        self.movement_collider = Collider((off_x // 2, self.rect.height - off_y), (self.rect.width - off_x, off_y // 2))
        self.damage_collider = Collider((self.rect.width // 4, self.rect.height // 4),
                                        (self.rect.width // 2, self.rect.height // 2), (255, 0, 0))

    def is_dashing(self):
        return self.mode == "dashing"

    def stop_attacking(self):
        self.frame_duration = self.normal_frame_duration
        print(self.frame_duration)
        self.change_images(self.idle_images[self.get_direction_index(self.move_direction)])
        self.mode = "idle"

    def update(self, camera, *args, **kwargs):
        if self.mode == "dead" and self.cur_frame == self.last_frame:
            return

        super().update(camera)

        if self.health <= 0 and self.mode != "dead":
            self.change_images(self.death_images[0])
            self.mode = "dead"
            self.frame_duration = self.death_frame_duration
            return

        self.update_dash()

        print(self.mode)

        if self.mode == "attacking" and self.cur_frame == self.last_frame:
            self.stop_attacking()

        if self.flash_count < self.max_flash_count:
            diff = pg.time.get_ticks() - self.harm_animation_start_time

            if self.flash_count % 2 == 0 and diff < self.harm_animation_duration:
                self.image = pg.transform.scale(self.image, (0, 0))

            elif diff > self.harm_animation_duration:
                self.image = pg.transform.scale(self.image, (self.default_size, self.default_size))
                self.flash_count += 1
                self.harm_animation_start_time = pg.time.get_ticks()

    def take_damage(self, damage, enemy=None):
        if self.mode == "dead" or self.mode == "dashing":
            return False

        super().take_damage(damage, enemy)

        if self.health > 0:
            self.harm_animation_start_time = pg.time.get_ticks()
            self.flash_count = 0

        return True

    def slash_attack(self, direction, scale):
        if self.is_dashing():
            return

        super().slash_attack(direction, scale)
        self.mode = "attacking"
        self.frame_duration = self.attack_frame_duration
        i = self.get_direction_index(direction)
        self.change_images(self.attack_images[1 if i == 3 else 3 if i == 1 else i])

    def stop_dash(self):
        self.change_images(self.walking_images[self.get_direction_index(self.move_direction)])
        self.mode = "idle"
        self.flip_model_on_move(1 if self.flipped_x else 0)
        self.last_dash_time = pg.time.get_ticks()
        self.frame_duration = self.normal_frame_duration

    def update_dash(self):
        if self.is_dashing():
            self.move_player(self.move_direction[0], self.move_direction[1], True)

            if self.cur_frame == self.last_frame:
                self.stop_dash()

    def add_walking_effect(self):
        if pg.time.get_ticks() - self.last_move_animation > 220:
            visuals.add(Visual(self.move_animation_images,
                               self.rect.move(-25 * self.move_direction[0], 10 - 40 * self.move_direction[1]).inflate(
                                   -70, -70), pg.time.get_ticks(), 250))
            self.last_move_animation = pg.time.get_ticks()

    def move_player(self, dx, dy, ignore_dash_check=False):
        if (self.mode == "dead") or (self.is_dashing() and not ignore_dash_check) or \
                (self.mode == "idle" and dx == 0 and dy == 0):
            return

        # fix insane acceleration
        if self.took_damage:
            dx = 0
            dy = 0

        self.change_idle_images(dx, dy)
        dx, dy = self.update_move_values(dx, dy)

        self.change_walking_images(dx, dy)
        moved = self.move_if_possible(dx, dy)

        if moved:
            self.add_walking_effect()

    def dash(self):
        if pg.time.get_ticks() - self.last_dash_time < self.dash_cooldown:
            return

        self.last_dash_time = pg.time.get_ticks()
        self.mode = "dashing"
        self.frame_duration = self.dash_frame_duration

        self.flip_model_on_move(self.move_direction[0])
        self.change_images(self.dashing_images[0])

        dash_rotation = 90 if self.move_direction[1] < 0 else -90 if self.move_direction[1] > 0 else 0
        visuals.add(Visual(self.dash_animation_images, self.damage_collider.collision_rect.copy(), pg.time.get_ticks(), 200, not self.flipped_x, rotate=dash_rotation))

    def add_item(self, item):
        if isinstance(item, Key):
            self.number_of_keys += 1

        if isinstance(item, PlayerUpgradeItem):
            if item.stat == "movement_speed":
                self.speed *= item.modifier
            elif item.stat == "attack_speed":
                self.attack_cooldown *= item.modifier
            elif item.stat == "dash_length":
                self.dash_frame_duration *= item.modifier
            elif item.stat == "dash_regeneration_speed":
                self.dash_cooldown *= item.modifier
            elif item.stat == "attack_size":
                self.attack_size *= item.modifier


class Enemy(Character):
    def __init__(self, x, y):
        Character.__init__(self, x, y, load_images_from_folder("assets/skeleton_enemy_1"), CHARACTER_SIZE * 0.96)
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

        off_x = 10
        off_y = 20
        self.movement_collider = Collider((off_x//2, self.rect.height - off_y), (self.rect.width - off_x, off_y))
        self.damage_collider = Collider((1, 1), (self.rect.width, self.rect.height), (255, 0, 0))

        self.spotted_time = None
        self.spotted_wait_duration = 500

    def change_position(self, move_x, move_y, obstacles):
        if not self.is_colliding_with_walls(move_x, move_y, obstacles):
            self.rect.x += move_x
            self.rect.y += move_y
            return True
        else:
            # fix bug where enemy gets stuck in a wall
            if not self.is_colliding_with_walls(move_x, 0, obstacles):
                self.rect.x += move_x
                return True
            elif not self.is_colliding_with_walls(0, move_y, obstacles):
                self.rect.y += move_y
                return True
        return False

    def move_enemy(self, goal_position):
        pos_x, pos_y = goal_position
        dx = pos_x - self.rect.x
        dy = pos_y - self.rect.y

        dx, dy = self.update_move_values(dx, dy)
        self.flip_model_on_move(dx)

        moved = self.move_if_possible(dx, dy)

        if not moved or (dx and dy == 0):
            self.last_known_player_position = None
            self.roam_position = None
            self.last_roam_time = pg.time.get_ticks()
            self.last_turn_around_animation_time = pg.time.get_ticks()
            self.roam_wait_time = random.randint(1500, 2500)

    def launch_attack(self):
        if self.attack_dir and pg.time.get_ticks() - self.about_to_attack_time > 180:
            self.slash_attack(self.attack_dir, 0.8)
            self.attack_dir = None
            self.about_to_attack_time = 0

    def prepare_attack(self, player_rect):
        if pg.time.get_ticks() - self.last_attack_time > self.attack_cooldown:
            if abs(self.rect.x - player_rect.x) > abs((self.rect.y - player_rect.y)):
                self.attack_dir = [math.copysign(1, player_rect.x - self.rect.x), 0]
            else:
                self.attack_dir = [0, math.copysign(1, self.rect.y - player_rect.y)]
            self.about_to_attack_time = pg.time.get_ticks()

    def roam_to(self, camera):
        self.in_line_of_sight(pg.Rect(self.roam_position[0], self.roam_position[1], 1, 1), walls, True, camera)
        self.move_enemy(self.roam_position)

    def choose_where_to_roam(self, camera):
        random_point = pg.Rect(self.rect.move(random.randint(50, 150) * [-1, 1][random.randint(0, 1)],
                                              random.randint(50, 150) * [-1, 1][random.randint(0, 1)]))
        random_point.width = 1
        random_point.height = 1

        if self.in_line_of_sight(random_point, walls, True, camera):
            self.roam_position = (random_point.x, random_point.y)

    def handle_spotting(self, player_rect):
        if self.last_known_player_position is None and self.spotted_time is None:
            visuals.add(NotificationVisual(load_images_from_folder("assets/effects/spotted"), self.rect.move(0, -60)))
            self.flip_model_on_move(player_rect.x - self.rect.x)
            self.spotted_time = pg.time.get_ticks()

        self.last_known_player_position = (player_rect.x, player_rect.y)
        if self.spotted_time and pg.time.get_ticks() - self.spotted_time < self.spotted_wait_duration:
            return

        self.spotted_time = None
        distance_to_player = (self.rect.x - player_rect.x) ** 2 + (self.rect.y - player_rect.y) ** 2

        if distance_to_player > 12000:
            self.move_enemy((player_rect.x, player_rect.y))
        else:
            self.prepare_attack(player_rect)


    def update(self, camera, player_rect, *args, **kwargs):
        super().update(camera)
        # handle knockback
        if self.took_damage and (self.velocity_x > 0.05 or self.velocity_y > 0.05):
            self.move_enemy([0, 0])

        if self.about_to_attack_time != 0:
            self.launch_attack()
        elif self.in_line_of_sight(player_rect, walls, False, camera):
            self.handle_spotting(player_rect)
        elif self.last_known_player_position:
            self.move_enemy(self.last_known_player_position)
        elif self.roam_position:
            self.roam_to(camera)
        else:
            # todo: refactor like hurt animation
            wait_dt = pg.time.get_ticks() - self.last_roam_time
            animation_dt = pg.time.get_ticks() - self.last_turn_around_animation_time

            if wait_dt < self.roam_wait_time - 50:
                if animation_dt < self.roam_wait_time/2:
                    self.flipped_x = not self.flipped_x
                    self.last_turn_around_animation_time = pg.time.get_ticks()
            else:
                # chose random point, check if in line of sight
                self.choose_where_to_roam(camera)

        self.animate_new_frame()

    def is_colliding_with_walls(self, dx, dy, obstacles):
        self.movement_collider.update(self.rect)
        new_rect = self.movement_collider.collision_rect.move(dx, dy)
        for wall in obstacles:
            if wall.rect.colliderect(new_rect):
                return True
        return False

    def in_line_of_sight(self, position_rect, obstacles, ignore_view_distance=False, camera=None):
        # draw the vision ray
        if camera:
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
    def __init__(self, images, x, y, stat, modifier):
        Item.__init__(self, images, x, y, 300, (WALL_SIZE * 0.7, WALL_SIZE * 0.7))
        self.rect.x = x
        self.rect.y = y
        self.stat = stat
        self.modifier = modifier


class MerchantItem(Item, ActionObject):
    def __init__(self, item, price, description=None):
        Item.__init__(self, [pg.image.load("assets/x.png")], item.rect.x, item.rect.y, item.frame_duration, item.rect.size)
        ActionObject.__init__(self, self.rect, self.sell, CHARACTER_SIZE)
        self.item_to_sell = item

        self.images = item.images
        self.animate()
        self.price = price
        self.bought = False
        self.description = description

    def sell(self, player):
        if player.coins >= self.price >= 0:
            player.coins -= self.price

            self.bought = True
            player.add_item(self.item_to_sell)

    def render(self, camera, player):
        screen.blit(self.image, (self.rect.x + camera.rect.x, self.rect.y + camera.rect.y))

        color = (255, 0, 0) if self.is_close(player) else (255, 255, 255)

        text = font.render(str(self.price) + "$", True, color)
        screen.blit(text, (self.rect.x + camera.rect.x, self.rect.y + camera.rect.y + self.image.get_height() + 10))


        if self.description and self.is_close(player):
            words = self.description.split(" ")
            longest_word = max(self.description.split(), key=len)

            box_width = font_s.render(longest_word, True, (0,0,0)).get_width()

            off_x = 20
            off_y = 20
            pg.draw.rect(screen, (0, 0, 0), (
                self.rect.centerx + camera.rect.x - box_width//2 - off_x//2, self.rect.y + camera.rect.y - len(words) * font_s.get_height() - off_y//2 - 20,
                box_width + off_x, len(words) * font_s.get_height() + off_y))

            for i, word in enumerate(words):
                description_text = font_s.render(word, True, (255, 255, 255))

                screen.blit(description_text, (self.rect.centerx + camera.rect.x - description_text.get_width()//2,
                                               self.rect.y + camera.rect.y - (len(words) - i) * description_text.get_height() - 20))


class Merchant(Character):
    def __init__(self, start_x, start_y):
        Character.__init__(self, start_x, start_y, load_images_from_folder("assets/merchant"), CHARACTER_SIZE * 0.96)

        it1 = self.create_random_player_upgrade(self.rect.x - 2 * WALL_SIZE, start_y + self.rect.height + 40)
        it2 = self.create_random_player_upgrade(self.rect.x, start_y + self.rect.height + 40)
        it3 = self.create_random_player_upgrade(self.rect.x + 2 * WALL_SIZE, start_y + self.rect.height + 40)

        self.items_to_sell = [it1, it2, it3]

        off_x = 10
        off_y = 20
        self.movement_collider = Collider((off_x//2, self.rect.height - off_y), (self.rect.width - off_x, off_y))
        self.damage_collider = Collider((1, 1), (self.rect.width, self.rect.height), (255, 0, 0))

    def create_random_player_upgrade(self, pos_x, pos_y):
        image = [player_upgrades_images[random.randint(0, len(player_upgrades_images)-1)]]

        stats = {
            "movement_speed": [1.05, 1.1],
            "attack_speed": [0.92, 0.96],
            "dash_regeneration_speed": [0.92, 0.96],
            "dash_length": [1.05, 1.15],
            "attack_size": [1.05, 1.2],
        }

        stat = random.choice(list(stats.keys()))
        modifier_range = stats[stat]
        modifier_range = list(map(lambda x: x * 1, modifier_range))
        modifier = random.uniform(modifier_range[0], modifier_range[1])

        price = random.randint(0, 20) + 10
        description = "Increase " + " ".join(stat.split("_"))

        return MerchantItem(PlayerUpgradeItem(image, pos_x, pos_y, stat, modifier), price, description=description)

    def render_items(self, camera, player):
        for item in self.items_to_sell:
            item.render(camera, player)

    def update(self, camera, *args, **kwargs):
        super().update(camera)

        for i, item in enumerate(self.items_to_sell):
            item.update()

            if item.bought:
                new_item = MerchantItem(Item([pg.image.load("assets/x.png")], 0, 0, 500, [item.rect.width, item.rect.height]), -1)
                new_item.rect = item.rect
                self.items_to_sell[i] = new_item


