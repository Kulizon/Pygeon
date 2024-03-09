import random
import pygame as pg

from shared import WALL_SIZE, visuals, walls, characters, decorations, traps, items
from utility import load_images_from_folder, NotificationVisual, Animated, ActionObject


class Item(pg.sprite.Sprite, Animated):
    def __init__(self, images, x, y, frame_duration, size, rotate=0):
        super().__init__()
        self.rect = pg.Rect(x + (WALL_SIZE - size[0])//2, y + (WALL_SIZE - size[1])//2, size[0], size[1])
        Animated.__init__(self, images, size, frame_duration, False, False, rotate)
        self.pickable = False

    def update(self, *args, **kwargs):
        self.animate_new_frame()

class Key(Item):
    def __init__(self, x, y):
        super().__init__(load_images_from_folder("assets/items_and_traps_animations/keys/silver"), x, y, 200,
             [WALL_SIZE * 0.8, WALL_SIZE * 0.8])
        self.pickable = True


class Chest(Item):
    def __init__(self, x, y, coins, health_potions):
        Item.__init__(self, load_images_from_folder("assets/items_and_traps_animations/chest/normal"), x, y, 280, (WALL_SIZE * 0.8, WALL_SIZE * 0.8))

        self.open_chest_images = load_images_from_folder("assets/items_and_traps_animations/chest/open")
        self.coins = coins
        self.health_potions = health_potions
        self.opened = False
        self.added_visual = False

    def update(self, player, *args, **kwargs):
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



class Trapdoor(Item, ActionObject):
    def __init__(self, x, y):
        Item.__init__(self, load_images_from_folder("assets/items_and_traps_animations/chest/open"), x, y, 280,
                      (WALL_SIZE * 0.8, WALL_SIZE * 0.8))
        ActionObject.__init__(self, self.rect, self.trapdoor_action)

        self.open_trapdoor_images = load_images_from_folder("assets/items_and_traps_animations/chest/normal")
        self.opened = False

    def trapdoor_action(self, player):
        if self.opened:
            from main import generate_new_level
            generate_new_level()
        elif player.number_of_keys > 0:
            print("opened")
            self.opened = True
            player.number_of_keys -= 1

    def update(self, *args, **kwargs):
        if self.opened:
            self.images = self.open_trapdoor_images


