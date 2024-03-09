import math

import pygame as pg
from shared import WALL_SIZE, CHARACTER_SIZE, screen, SCREEN_WIDTH, SCREEN_HEIGHT
import csv
import os

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

class Animated():
    def __init__(self, images, size, frame_duration, flipped_x=False, flipped_y=False, rotate=0):
        self.images = images
        self.image = pg.transform.scale(images[0], size)
        self.frame_duration = frame_duration
        self.last_frame_time = pg.time.get_ticks()
        self.cur_frame = 0
        self.last_frame = len(images) - 1
        self.size = size

        self.flipped_x = flipped_x
        self.flipped_y = flipped_y
        self.rotate = rotate

        self.adjust_image()

    def adjust_image(self):
        self.image = pg.transform.scale(self.images[self.cur_frame], self.size)
        self.image = pg.transform.flip(self.image, self.flipped_x, self.flipped_y)
        self.image = pg.transform.rotate(self.image, self.rotate)

    def animate(self):
        self.last_frame_time = pg.time.get_ticks()
        self.cur_frame = (self.cur_frame + 1) % len(self.images)
        self.adjust_image()

    def animate_new_frame(self):
        if pg.time.get_ticks() - self.last_frame_time > self.frame_duration:
            self.animate()

class Visual(pg.sprite.Sprite, Animated):
    def __init__(self, images, rect, start_time, duration, flipped_x=False, flipped_y=False, rotate=0, iterations=1):
        pg.sprite.Sprite.__init__(self)
        Animated.__init__(self, images, (rect.width, rect.height), int(duration/(len(images)*iterations)), flipped_x, flipped_y, rotate)

        self.start_time = start_time
        self.duration = duration
        self.image = images[0]
        self.adjust_image()
        self.rect = rect

    def update(self, *args, **kwargs):
        self.animate_new_frame()

        if pg.time.get_ticks() - self.start_time > self.duration:
            # remove yourself from Group
            self.kill()


class NotificationVisual(Visual):
    def __init__(self, images, rect, float_in=False, duration=-1, iterations=1):
        ratio = images[0].get_width() / images[0].get_height()

        if images[0].get_width() > images[0].get_height():
            rect.width = WALL_SIZE
            rect.height = WALL_SIZE * ratio
        else:
            rect.height = WALL_SIZE
            rect.width = WALL_SIZE * ratio

        super().__init__(images, rect, pg.time.get_ticks(), duration if duration != -1 else len(images) * 100, iterations=iterations)

        self.float_in = float_in
        self.goal_position_y = rect.y - 20

    def update(self, *args, **kwargs):
        if self.float_in and self.rect.y - self.goal_position_y > 5:
            self.rect.y -= 3

        super().update(self, args, kwargs)




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


class Collider():
    def __init__(self, offset, collision_size):
        self.offset = offset
        self.collision_size = collision_size
        self.collision_rect = (0, 0, collision_size[0], collision_size[1])

    def update(self, rect, camera=None):
        self.collision_rect = pg.Rect(rect.x + self.offset[0], rect.y + self.offset[1], self.collision_size[0], self.collision_size[1])
        if camera:
            pg.draw.rect(screen, (255, 255, 0), self.collision_rect.move(camera.rect.x, camera.rect.y))



