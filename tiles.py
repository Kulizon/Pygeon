from shared import WALL_SIZE, walls
from utility import Animated, load_images_from_folder, ActionObject
import pygame as pg


table_ids = [] # todo: add coffe, etc
plant1_ids = []
plant2_ids = []
plant3_ids = []
fireplace_ids = []
counter_table_ids = []
stool_ids = []
windows_ids = [11, 12, 59, 60, 108, 109, 156, 167]
shelf1_ids = []
shelf2_ids = []
luxury_chair_ids = []
luxury_table_ids = [] # todo: add purple wine, etc
doormat_ids = []

groups = [table_ids, plant1_ids, plant2_ids, plant3_ids, fireplace_ids,
          counter_table_ids, stool_ids, windows_ids, shelf1_ids, shelf2_ids, luxury_chair_ids, luxury_table_ids, doormat_ids]

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


class FurnitureToBuyTile(MapTile, ActionObject):
    def __init__(self, image, x, y, price, tile_id, size=WALL_SIZE):
        MapTile.__init__(self, image, x, y, size)
        ActionObject.__init__(self, self.rect, self.buy, 50) #todo maybe change parameters
        self.default_image = self.image.copy()

        # set visibility to low first
        self.image.fill((255, 255, 255, 100), None, pg.BLEND_RGBA_MULT)

        self.price = price
        self.bought = False
        self.tile_id = tile_id

    def buy(self, player, buy_only_self=False):
        if player.coins >= self.price:
            player.coins -= self.price

        print(self.tile_id, windows_ids)

        self.image = self.default_image
        # todo: iterate every object in ground and walls,
        # change also objects that pair with the current one
        # by ids

        furniture_piece_group_ids = []
        for group in groups:
            if self.tile_id in group:
                furniture_piece_group_ids = group

        if not buy_only_self:
            for furniture in walls:
                if isinstance(furniture, FurnitureToBuyTile):
                    if furniture.tile_id in furniture_piece_group_ids:
                        furniture.buy(player, True)

        self.bought = True




