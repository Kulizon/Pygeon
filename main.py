import math

import pygame as pg
import random
import csv
import os



pg.init()

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)

screen = pg.display.set_mode((WIDTH, HEIGHT))
clock = pg.time.Clock()

CHARACTER_SIZE = 50
WALL_SIZE = CHARACTER_SIZE

class Animated():
    def __init__(self, images, size, frame_duration, flipped_x=False, flipped_y=False, rotation=0):
        super().__init__()
        self.images = images
        self.image = pg.transform.scale(images[0], size)
        self.frame_duration = frame_duration
        self.last_frame_time = pg.time.get_ticks()
        self.cur_frame = 0
        self.size = size

        self.flipped_x = flipped_x
        self.flipped_y = flipped_y
        self.rotation = rotation

    def animate(self):
        self.last_frame_time = pg.time.get_ticks()
        self.cur_frame = (self.cur_frame + 1) % len(self.images)
        self.image = pg.transform.scale(self.images[self.cur_frame], self.size)
        self.image = pg.transform.flip(self.image, self.flipped_x, self.flipped_y)
        self.image = pg.transform.rotate(self.image, self.rotation)

    def animate_new_frame(self):
        if pg.time.get_ticks() - self.last_frame_time > self.frame_duration:
            self.animate()

class Visual(pg.sprite.Sprite, Animated):
    def __init__(self, images, rect, start_time, duration, flipped_x=False, flipped_y=False, rotation=0):
        pg.sprite.Sprite.__init__(self)
        Animated.__init__(self, images, (rect.width, rect.height), int(duration/len(images)), flipped_x, flipped_y, rotation)

        self.start_time = start_time
        self.duration = duration
        self.image = images[0]
        self.rect = rect

    def update(self, *args, **kwargs):
        self.animate_new_frame()

        if pg.time.get_ticks() - self.start_time >= self.duration:
            # remove yourself from Group
            self.kill()


class Wall(pg.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = pg.transform.scale(image, (WALL_SIZE, WALL_SIZE))
        self.rect = self.image.get_rect(topleft=(x, y))

class Character(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pg.Surface((CHARACTER_SIZE, CHARACTER_SIZE))
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.attacks = []

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

class Player(Character, Animated):
    def __init__(self):
        Character.__init__(self, 400, 500)

        images = load_images_from_folder("player_character")
        Animated.__init__(self, images, (WALL_SIZE, WALL_SIZE), 400)

        self.last_attack_time = pg.time.get_ticks()
        self.attack_cooldown = 0

        self.last_move_time = pg.time.get_ticks()
        self.move_cooldown = 5

        self.dest_x = self.rect.x
        self.dest_y = self.rect.y

        self.moving = False

        self.dash_animation_images = load_images_from_folder("effects/dash")

    def update(self, *args, **kwargs):
        self.animate_new_frame()

        if not self.moving and (self.rect.x % CHARACTER_SIZE != 0 or self.rect.y % CHARACTER_SIZE != 0):
            # snap to closest tile
            self.rect.x -= CHARACTER_SIZE - (self.rect.x % CHARACTER_SIZE)
            self.rect.y -= CHARACTER_SIZE - (self.rect.y % CHARACTER_SIZE)

        if self.rect.x != self.dest_x:
            move = min(int(CHARACTER_SIZE / 3), abs(self.rect.x - self.dest_x))
            self.rect.x += math.copysign(move, self.dest_x - self.rect.x)
        if self.rect.y != self.dest_y:
            move = min(int(CHARACTER_SIZE / 3), abs(self.rect.y - self.dest_y))
            self.rect.y += math.copysign(move, self.dest_y - self.rect.y)

        if self.rect.x != self.dest_x or self.rect.y != self.dest_y:
            self.last_move_time = pg.time.get_ticks()
        else:
            self.moving = False


    def move(self, dx, dy, camera):
        if self.moving or pg.time.get_ticks() - self.last_move_time < self.move_cooldown:
            return

        new_x = self.rect.x + dx
        new_y = self.rect.y + dy

        new_rect = pg.Rect(new_x, new_y, CHARACTER_SIZE, CHARACTER_SIZE)

        if not any(char.rect.colliderect(new_rect) for char in characters) \
                and not any(wall.rect.colliderect(new_rect) for wall in walls):
            # self.rect.x = new_x
            # self.rect.y = new_y
            self.last_move_time = pg.time.get_ticks()
            self.dest_x = new_x
            self.dest_y = new_y
            self.moving = True

            if dx < 0:
                self.flipped_x = True
                self.animate()
            elif dx > 0:
                self.flipped_x = False
                self.animate()

            dash_rotation = 90 if dy < 0 else -90 if dy > 0 else 0
            visuals.add(Visual(self.dash_animation_images, self.rect.copy(), pg.time.get_ticks(), 200, not(self.flipped_x), rotation=dash_rotation))
        else:
            print("Collision cannot move ")

    def slash_attack(self, direction):

        if pg.time.get_ticks() - self.last_attack_time < self.attack_cooldown:
            return

        self.last_attack_time = pg.time.get_ticks()
        self.attack_cooldown = 700

        if direction == pg.K_UP:
            dim = (CHARACTER_SIZE * 3, CHARACTER_SIZE)
            dest = (self.rect.x - CHARACTER_SIZE, self.rect.y - CHARACTER_SIZE)
        elif direction == pg.K_DOWN:
            dim = (CHARACTER_SIZE * 3, CHARACTER_SIZE)
            dest = (self.rect.x - CHARACTER_SIZE, self.rect.y + CHARACTER_SIZE)
        elif direction == pg.K_LEFT:
            dim = (CHARACTER_SIZE, CHARACTER_SIZE * 3)
            dest = (self.rect.x - CHARACTER_SIZE, self.rect.y - CHARACTER_SIZE)
        elif direction == pg.K_RIGHT:
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
            'flipped_x': direction == pg.K_LEFT,
            'flipped_y': direction == pg.K_UP
        }

        self.attacks.append(attack)


class Camera:
    def __init__(self, width, height):
        self.rect = pg.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def update(self, target):
        x = -target.rect.x + WIDTH // 2
        y = -target.rect.y + HEIGHT // 2

        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - WIDTH), x)
        y = max(-(self.height - HEIGHT), y)

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
            tile = image.subsurface((x, y, tile_width, tile_height))
            tiles.append(tile)

    return tiles



walls = pg.sprite.Group()
ground = pg.sprite.Group()

tiles_images = load_tileset("tileset.png", 16, 16)
tile_map = convert_csv_to_2d_list(csv_file="map.csv")
for row in range(len(tile_map)):
    for col in range(len(tile_map[row])):
        id = tile_map[row][col]
        if id in [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 41, 42, 43, 44, 45, 50, 51, 52, 53, 54, 55]:
            walls.add(Wall(tiles_images[id], col * WALL_SIZE, row * WALL_SIZE))
        else:
            ground.add(Wall(tiles_images[id], col * WALL_SIZE, row * WALL_SIZE))

player = Player()
ch1 = Character(800, 800)

characters = pg.sprite.Group()
characters.add(player, ch1)

camera = Camera(len(tile_map[0]) * WALL_SIZE, len(tile_map) * WALL_SIZE)

visuals = pg.sprite.Group()


running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            keys = pg.key.get_pressed()
            move_val = CHARACTER_SIZE
            dx, dy = 0, 0

            if keys[pg.K_UP] or keys[pg.K_DOWN] or keys[pg.K_RIGHT] or keys[pg.K_LEFT]:
                player.slash_attack(event.key)

            if keys[pg.K_w] or keys[pg.K_a] or keys[pg.K_d] or keys[pg.K_s]:
                if keys[pg.K_w]:
                    dy -= move_val
                elif keys[pg.K_s]:
                    dy += move_val
                elif keys[pg.K_d]:
                    dx += move_val
                elif keys[pg.K_a]:
                    dx -= move_val
                player.move(dx, dy, camera)


    camera.update(player)

    screen.fill(WHITE)
    for tile in ground:
        screen.blit(tile.image, (tile.rect.x + camera.rect.x, tile.rect.y + camera.rect.y))
    for wall in walls:
        screen.blit(wall.image, (wall.rect.x + camera.rect.x, wall.rect.y + camera.rect.y))
    for char in characters:
        screen.blit(char.image, (char.rect.x + camera.rect.x, char.rect.y + camera.rect.y))


    for char in characters:
        for attack in char.attacks:
            dest = attack['dest']
            effect = pg.Surface(attack['dim'])

            attackRect = effect.get_rect()
            attackRect.x = dest[0]
            attackRect.y = dest[1]

            for testedChar in characters:
                if attackRect.colliderect(testedChar) and testedChar != char:
                    print('hit')

            char.attacks.remove(attack)

            images = load_tileset("effects/slash_attack.png", 40, 54)
            attackVisual = Visual(images, attackRect, attack['start_time'], attack['duration'], attack['flipped_x'], attack['flipped_y'])

            visuals.add(attackVisual)

    for visual in visuals:
        screen.blit(visual.image, (visual.rect.x + camera.rect.x, visual.rect.y + camera.rect.y))
    visuals.update()




    characters.update()

    pg.display.flip()
    clock.tick(60)

pg.quit()
