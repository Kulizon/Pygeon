import random
import pygame as pg

from shared import WALL_SIZE, visuals, CHARACTER_SIZE
from utility import load_images_from_folder, NotificationVisual, Animated

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

        super().__init__(images_path, x + x_off, y + y_off, 150, 700 + random.random() * 500, attack_dir, size, rotate)

    def update(self, *args, **kwargs):
        self.damage = 0 if (self.cur_frame in [0, self.last_frame, self.last_frame-1] or self.already_hit) else 1

        super().update(*args, **kwargs)


class ArrowTrap(Trap):
    def __init__(self, x, y, attack_dir):
        self.size_modifier = 0.7
        size = [(abs(attack_dir[0]) + 1) * WALL_SIZE * self.size_modifier, (abs(attack_dir[1]) + 1) * WALL_SIZE * self.size_modifier]

        if attack_dir[0]:
            images_path = "assets/items_and_traps_animations/arrow_horizontal"
        else:
            images_path = "assets/items_and_traps_animations/arrow_vertical"

        if attack_dir[0] == -1:
            x -= WALL_SIZE * self.size_modifier + 5

        x += (WALL_SIZE * (1-self.size_modifier))//1.5
        y += (WALL_SIZE * (1-self.size_modifier))//2

        rotate = 180 if attack_dir[0] == 1 else 0

        Trap.__init__(self, images_path, x, y, 30, 1700 + random.random() * 500, attack_dir, size, rotate)
        self.rect = self.rect.move(14 * attack_dir[0], 0)
        self.arrows = []

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)

        arrow_width = CHARACTER_SIZE * 0.65 * self.size_modifier
        arrow_height = CHARACTER_SIZE * 0.47 * self.size_modifier

        if self.attack_dir[1]:
            arrow_width, arrow_height = arrow_height, arrow_width

        if self.cur_frame == self.last_frame:
            arrow_rect = pg.Rect(self.rect.x + CHARACTER_SIZE * self.attack_dir[0] - (CHARACTER_SIZE * 0.65 * (1 - self.size_modifier) // 2),self.rect.y + CHARACTER_SIZE * self.attack_dir[1] - (CHARACTER_SIZE * 0.47 * (1 - self.size_modifier)), arrow_width, arrow_height)

            new_arrow = pg.sprite.Sprite()
            new_arrow.rect = arrow_rect

            if self.attack_dir[0]:
                image_path = "assets/arrow_horizontal.png"
                new_arrow.rect.y += (CHARACTER_SIZE - arrow_height) // 2
            else:
                image_path = "assets/arrow_vertical.png"
                new_arrow.rect.x += (CHARACTER_SIZE - arrow_width) // 2

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

        Trap.__init__(self, images_path, x + WALL_SIZE * 0.1, y + WALL_SIZE * 0.1, 50, 1000 + random.random() * 500, [0, 0], size)
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
