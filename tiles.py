from shared import WALL_SIZE, walls, decorations, font_s, screen, font
from utility import Animated, load_images_from_folder, ActionObject
import pygame as pg


table_ids = [204, 205, 206, 252, 253, 254, 300, 301, 302, 348, 349, 350, 396, 397, 398, 444, 445, 446, 359, 215, 263, 455] # todo: add coffe, etc
plant1_ids = [448, 496]
plant2_ids = [545, 593]
plant3_ids = [641, 689]
fireplace_ids = [267, 268, 269, 219, 220, 221, 172, 270, 159]
fireplace_stool_ids = [159]
counter_table_ids = [696, 744, 745, 697]
stool_ids = [344, 345, ]
windows_ids = [11, 12, 59, 60, 108, 109, 156, 157]
shelf1_ids = [357, 358, 405, 406]
shelf2_ids = [453, 454, 501, 502]
shelf3_ids = [488, 489, 536, 537]
luxury_chair_ids = [588, 589, 636, 637]
luxury_table_ids = [202, 203, 250, 251, 503] # todo: add purple wine, etc
kitchen_decorations_ids = [498, 737, 643]
doormat_ids = [100, 101]

furniture_groups = [table_ids, plant1_ids, plant2_ids, plant3_ids, fireplace_ids,
                    counter_table_ids, stool_ids, windows_ids, shelf1_ids, shelf2_ids, shelf3_ids,
                    luxury_chair_ids, luxury_table_ids, doormat_ids, kitchen_decorations_ids]

class MapTile(pg.sprite.Sprite):
    def __init__(self, image, x, y, size=WALL_SIZE):
        super().__init__()
        self.image = pg.transform.scale(image, (size, size))
        self.col = x
        self.row = y
        self.rect = self.image.get_rect(topleft=(x * size, y * size))
        
    def update(self, player, *args, **kwargs):
        super().update(args, kwargs)

class AnimatedMapTile(MapTile, Animated):
    def __init__(self, images_path, x, y, frame_duration, flip_x=False, flip_y=False, rotate=0, size=None):
        images = load_images_from_folder(images_path)

        MapTile.__init__(self, images[0], x, y)
        if size:
            self.rect.size = size
        Animated.__init__(self, images, self.rect.size, frame_duration, flip_x, flip_y, rotate)

    def update(self, player, *args, **kwargs):
        self.animate_new_frame()


class FurnitureToBuyTile(MapTile, ActionObject):
    def __init__(self, image, x, y, price, tile_id, size=WALL_SIZE):
        MapTile.__init__(self, image, x, y, size)
        ActionObject.__init__(self, self.rect, self.buy, 80) #todo maybe change parameters
        self.default_image = self.image.copy()

        self.barely_visible_image = self.image.copy()
        self.barely_visible_image.fill((255, 255, 255, 100), None, pg.BLEND_RGBA_MULT)

        # set to invisible first
        self.invisible_image = self.image.copy()
        self.invisible_image.fill((255, 255, 255, 0), None, pg.BLEND_RGBA_MULT)
        self.image = self.invisible_image

        self.price = price
        self.bought = False
        self.visible = True
        self.tile_id = tile_id

    def traverse_correct_group(self, function_to_call, player, action_objects):
        furniture_piece_group_ids = []
        for group in furniture_groups:
            if self.tile_id in group:
                furniture_piece_group_ids = group

        for furniture in list(walls) + list(decorations):
            if isinstance(furniture, FurnitureToBuyTile):
                if furniture.tile_id in furniture_piece_group_ids:
                    function_to_call(furniture, player, action_objects)

    def update(self, player, *args, **kwargs):
        if self.bought:
            return

        if not self.is_close(player) and not self.visible and not self.bought:
            self.image = self.invisible_image
            self.visible = False
        elif not self.is_close(player):
            self.visible = False
        else:
            # set visibility to low if close
            self.traverse_correct_group(
                lambda furniture, player, action_objects: self.update_furniture_visibility(furniture), player,[])

            word = "Buy for " + str(self.price)+ "$"
            text = font.render(word, True, (255, 255, 255))

            screen.blit(text, (20, 10))

    def update_furniture_visibility(self, furniture):
        furniture.image = furniture.barely_visible_image
        furniture.visible = True

    def buy(self, player, action_objects=None, buy_only_self=False):
        if player.coins >= self.price and not buy_only_self:
            player.coins -= self.price

        if player.coins >= self.price:
            self.image = self.default_image

            if not buy_only_self:
                self.traverse_correct_group(lambda furniture, player, action_objects: furniture.buy(player, action_objects, True), player,
                                        action_objects)
            if self in action_objects:
                action_objects.remove(self)

            self.bought = True




