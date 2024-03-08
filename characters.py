import pygame as pg
from constans import WALL_SIZE, CHARACTER_SIZE
from utility import Animated, load_images_from_folder

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
