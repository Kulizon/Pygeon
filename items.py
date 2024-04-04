import random
from copy import deepcopy

import pygame as pg

from tiles import MapTile
from shared import WALL_SIZE, visuals, font, screen, SCREEN_WIDTH
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
        self.default_size = WALL_SIZE * 0.8
        Item.__init__(self, load_images_from_folder("assets/items_and_traps_animations/chest/normal"), x, y, 280, (self.default_size, self.default_size))

        self.open_chest_images = load_images_from_folder("assets/items_and_traps_animations/chest/open")
        self.coins = coins
        self.health_potions = health_potions
        self.opened = False
        self.added_visual = False

        self.last_flash_time = 0
        self.flash_count = 0
        self.max_flash_count = 14

    def update(self, player, *args, **kwargs):
        if not self.added_visual or self.flash_count < self.max_flash_count:
            super().update(args, kwargs)

        if not self.opened:
            return

        if self.flash_count < self.max_flash_count and pg.time.get_ticks() - self.last_flash_time > 140:
            self.animate()
            self.flash_count += 1
            self.last_flash_time = pg.time.get_ticks()

        if self.cur_frame == self.last_frame and not self.added_visual:
            visuals.add(NotificationVisual(load_images_from_folder("assets/items_and_traps_animations/coin"), self.rect.move(-WALL_SIZE * 0.1, -60), True, 1600, iterations=3))
            player.coins += random.randint(10, 25)
            self.added_visual = True


    def open(self):
        if not self.opened:
            self.cur_frame = 0
            self.images = self.open_chest_images
            self.opened = True
            self.last_flash_time = pg.time.get_ticks()


class Trapdoor(MapTile, ActionObject):
    def __init__(self, x, y, is_dungeon_exit=False):
        from map_generation import dungeon_tile_images
        MapTile.__init__(self, dungeon_tile_images[39] if is_dungeon_exit else dungeon_tile_images[38], x, y)
        ActionObject.__init__(self, self.rect, self.trapdoor_action)

        self.open_trapdoor_image = dungeon_tile_images[39]
        self.opened = False
        self.is_dungeon_exit = is_dungeon_exit

    def trapdoor_action(self, player, action_objects):
        if self.is_dungeon_exit:
            player.is_in_out_of_dungeon = True
            print(123)
        else:
            if self.opened:
                player.is_next_level = True
            elif player.number_of_keys > 0:
                self.opened = True
                player.number_of_keys -= 1

    def update(self, player):
        word = None
        if self.opened:
            self.image = pg.transform.scale(self.open_trapdoor_image, (WALL_SIZE, WALL_SIZE))

            if self.is_close(player):
                word = "Go deeper!"
        elif self.is_close(player):
                word = "Open trapdoor!" if not self.is_dungeon_exit else "Exit dungeon!"

        if word is not None:
            text = font.render(word, True, (255, 255, 255))
            screen.blit(text, (SCREEN_WIDTH - text.get_width() - 15, 170))

class DungeonDoor(MapTile, ActionObject):
    def __init__(self, x, y, size):
        from map_generation import overworld_tile_images
        MapTile.__init__(self, overworld_tile_images[147], x, y, size)
        ActionObject.__init__(self, self.rect, self.trapdoor_action)
        self.last_notification_added_time = -10000

    def trapdoor_action(self, player, action_objects):
        player.is_in_out_of_dungeon = True

    def update(self, player, *args, **kwargs):
        if self.is_close(player):
            word = "Start dungeoning!1!"
            text = font.render(word, True, (255, 255, 255))

            screen.blit(text, (20, 10))

        if pg.time.get_ticks() - self.last_notification_added_time > 10000:
            visuals.add(NotificationVisual(load_images_from_folder("assets/effects/spotted"), self.rect.move(0, -80), duration=10000, iterations=20))
            self.last_notification_added_time = pg.time.get_ticks()


