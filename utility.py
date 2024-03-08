import pygame as pg
from shared import WALL_SIZE, CHARACTER_SIZE
import csv
import os

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
