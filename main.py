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


def compare_rect(rect1, rect2):
    return (rect1.x != rect2.x or
            rect1.y != rect2.y or
            rect1.width != rect2.width or
            rect1.height != rect2.height)

def collide(rect1, rect2):
    return rect1.colliderect(rect2)

def collide_x(rect1, rect2):
    if rect1.colliderect(rect2):
        if rect1.x + rect1.width <= rect2.x:
            return True
    return False


def collide_y(rect1, rect2):
    if rect1.colliderect(rect2):
        if rect1.y - rect1.height <= rect2.y:
            return True
    return False


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

class Character(pg.sprite.Sprite, Animated):
    def __init__(self, x, y, images_path):
        super().__init__()

        images = load_images_from_folder(images_path)
        Animated.__init__(self, images, (WALL_SIZE, WALL_SIZE), 400)

        self.last_attack_time = pg.time.get_ticks()
        self.attack_cooldown = 0
        self.rect = self.image.get_rect(topleft=(x, y))
        self.attacks = []



class Enemy(Character):
    def __init__(self, x, y):
        super().__init__(x, y, "skeleton_enemy_1")
        self.speed = 1
        self.last_known_player_position = None

    def change_position(self, move_x, move_y):
        if not self.is_colliding_with_walls(move_x, move_y):
            self.rect.x += move_x
            self.rect.y += move_y
            return True
        else:
            if not self.is_colliding_with_walls(move_x, 0):
                self.rect.x += move_x
                return True
            elif not self.is_colliding_with_walls(0, move_y):
                self.rect.y += move_y
                return True

        return False

    def update(self, player_rect, obstacles, *args, **kwargs):
        dx = player_rect.x - self.rect.x
        dy = player_rect.y - self.rect.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance != 0:
            dx /= distance
            dy /= distance

        move_x = math.copysign(max(1, abs(dx * self.speed)), dx)
        move_y = math.copysign(max(1, abs(dy * self.speed)), dy)

        print(self.in_line_of_sight(player_rect, obstacles))
        print(self.last_known_player_position)
        print()

        if self.in_line_of_sight(player_rect, obstacles):
            self.last_known_player_position = (player_rect.x, player_rect.y)
            self.change_position(move_x, move_y)
        else:
            if self.last_known_player_position:
                last_player_x, last_player_y = self.last_known_player_position
                dx = last_player_x - self.rect.x
                dy = last_player_y - self.rect.y
                distance = math.sqrt(dx ** 2 + dy ** 2)

                if distance != 0:
                    dx /= distance
                    dy /= distance

                move_x = math.copysign(max(1, abs(dx * self.speed)), dx)
                move_y = math.copysign(max(1, abs(dy * self.speed)), dy)


                if abs(last_player_x - self.rect.x) <= 1 or abs(last_player_y - self.rect.y) <= 1:
                    self.last_known_player_position = None

                changed = self.change_position(move_x, move_y)
                print(changed)
                if not changed:
                    self.last_known_player_position = None



        self.animate_new_frame()

    def is_colliding_with_walls(self, dx, dy):
        new_rect = self.rect.move(dx, dy)
        for wall in walls:
            if wall.rect.colliderect(new_rect):
                return True
        return False

    def in_line_of_sight(self, player_rect, obstacles):
        vision_ray = pg.Rect(self.rect.center, (1, 1))  # Initialize with a small size

        # Adjust width and height of vision_ray based on player and enemy positions
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        vision_ray.width = abs(dx)
        vision_ray.height = abs(dy)

        # Adjust vision_ray's left and top based on relative positions
        if dx < 0:
            vision_ray.left = player_rect.centerx
        if dy < 0:
            vision_ray.top = player_rect.centery

        if dx == 0:
            vision_ray.width = 1
        if dy == 0:
            vision_ray.height = 1

        for obstacle in obstacles:
            if vision_ray.colliderect(obstacle.rect):
                return False
        return True



class Player(Character):
    def __init__(self):
        super().__init__(400, 400, "player_character")
        self.dest_x = self.rect.x
        self.dest_y = self.rect.y

        self.dashing = False
        self.last_dash_time = pg.time.get_ticks()
        self.dash_cooldown = 500
        self.dash_animation_images = load_images_from_folder("effects/dash")

        self.direction = [0, 0]

    def update(self, *args, **kwargs):
        self.animate_new_frame()
        self.update_dash()


    def update_dash(self):
        if self.dashing:
            if self.rect.x != self.dest_x or self.rect.y != self.dest_y:
                move_x = min(15, abs(self.rect.x - self.dest_x))
                move_y = min(15, abs(self.rect.y - self.dest_y))
                self.move(math.copysign(move_x, self.direction[0]), math.copysign(move_y, self.direction[1]), True)

            if self.rect.x == self.dest_x and self.rect.y == self.dest_y:
                self.dashing = False

    import pygame as pg
    import math

    import pygame as pg
    import math

    def move(self, dx, dy, ignore_dash_check=False):
        if self.dashing and not ignore_dash_check:
            return

        new_x = self.rect.x + dx
        new_y = self.rect.y + dy

        full_move_rect = pg.Rect(new_x, new_y, CHARACTER_SIZE, CHARACTER_SIZE)
        objs = [characters, walls]

        new_rect = full_move_rect
        collision_function = collide

        is_collision = False
        for group in objs:
            for obj in group:
                if collision_function(obj.rect, new_rect) and obj != self:
                    is_collision = True
                    break
            if is_collision:
                break

        if not is_collision:
            self.rect = new_rect
            if dx != 0:
                self.flip_model_on_move(dx)
        else:
            # If collision occurred, try moving along each axis individually
            new_x_rect = pg.Rect(new_x, self.rect.y, CHARACTER_SIZE, CHARACTER_SIZE)
            new_y_rect = pg.Rect(self.rect.x, new_y, CHARACTER_SIZE, CHARACTER_SIZE)

            is_collision_along_x = any(collide(obj.rect, new_x_rect) and obj != self for group in objs for obj in group)
            is_collision_along_y = any(collide(obj.rect, new_y_rect) and obj != self for group in objs for obj in group)

            if not is_collision_along_x:
                self.rect.x = new_x
                self.flip_model_on_move(dx)
            elif not is_collision_along_y:
                self.rect.y = new_y
            else:
                # both axes have collisions, cannot move
                self.dashing = False
                self.last_dash_time = pg.time.get_ticks()
                print("Collision, cannot move")

    def dash(self):
        if pg.time.get_ticks() - self.last_dash_time < self.dash_cooldown:
            return

        print(self.direction)

        dx = 100 * self.direction[0]
        dy = 100 * self.direction[1]

        new_x = self.rect.x + dx
        new_y = self.rect.y + dy

        self.last_dash_time = pg.time.get_ticks()
        self.dest_x = new_x
        self.dest_y = new_y
        self.dashing = True

        self.flip_model_on_move(dx)

        dash_rotation = 90 if dy < 0 else -90 if dy > 0 else 0
        visuals.add(Visual(self.dash_animation_images, self.rect.copy(), pg.time.get_ticks(), 200, not(self.flipped_x), rotation=dash_rotation))

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
ch1 = Enemy(800, 800)

characters = pg.sprite.Group()
characters.add(player, ch1)

camera = Camera(len(tile_map[0]) * WALL_SIZE, len(tile_map) * WALL_SIZE)

visuals = pg.sprite.Group()


running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        keys = pg.key.get_pressed()
        if event.type == pg.KEYDOWN:
            dx, dy = 0, 0

            if keys[pg.K_UP] or keys[pg.K_DOWN] or keys[pg.K_RIGHT] or keys[pg.K_LEFT]:
                player.slash_attack(event.key)

            if keys[pg.K_SPACE]:
                player.dash()

    keys = pg.key.get_pressed()

    move_val = 5

    dx = move_val if keys[pg.K_d] else -move_val if keys[pg.K_a] else 0
    dy = move_val if keys[pg.K_w] else -move_val if keys[pg.K_s] else 0

    if dx != 0 or dy != 0:
        player.move(dx, -dy)

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

            images = load_images_from_folder("effects/slash_attack")
            attackVisual = Visual(images, attackRect, attack['start_time'], attack['duration'], attack['flipped_x'], attack['flipped_y'])

            visuals.add(attackVisual)

    for visual in visuals:
        screen.blit(visual.image, (visual.rect.x + camera.rect.x, visual.rect.y + camera.rect.y))
    visuals.update()

    characters.update(player.rect, walls)

    pg.display.flip()
    clock.tick(60)

pg.quit()
