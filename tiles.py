from shared import WALL_SIZE
from utility import Animated, load_images_from_folder
import pygame as pg

class MapTile(pg.sprite.Sprite):
    def __init__(self, image, x, y, size=WALL_SIZE):
        super().__init__()
        self.image = pg.transform.scale(image, (size, size))
        self.col = x
        self.row = y
        self.rect = self.image.get_rect(topleft=(x * size, y * size))


class AnimatedMapTile(MapTile, Animated):
    def __init__(self, images_path, x, y, frame_duration, flip_x=False, flip_y=False, rotate=0, size=None):
        images = load_images_from_folder(images_path)

        MapTile.__init__(self, images[0], x, y)
        if size:
            self.rect.size = size
        Animated.__init__(self, images, self.rect.size, frame_duration, flip_x, flip_y, rotate)

    def update(self):
        self.animate_new_frame()
