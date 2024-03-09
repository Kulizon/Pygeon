from shared import WALL_SIZE
from utility import Animated, load_images_from_folder
import pygame as pg

class Map():
    def __init__(self):
        rooms = [i + 1 for i in range(10)]
        self.room_map = connect_rooms(rooms)
        self.mini_map = trim_matrix(self.room_map)
        self.discovered_mini_map = deepcopy(self.mini_map)
        for y, row in enumerate(self.discovered_mini_map):
            for x, el in enumerate(row):
                if el != 1:
                    self.discovered_mini_map[y][x] = 0

        w, h = generate_map(self.room_map)

        self.width_px = w
        self.height_px = h

        self.current_mini_map_cell = 0

    def update(self, player):
        new_cell = self.room_map[int(player.rect.y // WALL_SIZE // 16)][int(player.rect.x // WALL_SIZE // 16)]
        if self.current_mini_map_cell != new_cell:
            for y, row in enumerate(self.mini_map):
                for x, el in enumerate(row):
                    if el == new_cell:
                        self.discovered_mini_map[y][x] = new_cell

        self.current_mini_map_cell = self.room_map[int(player.rect.y // WALL_SIZE // 16)][
            int(player.rect.x // WALL_SIZE // 16)]
        return

class MapTile(pg.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = pg.transform.scale(image, (WALL_SIZE, WALL_SIZE))
        self.col = x
        self.row = y
        self.rect = self.image.get_rect(topleft=(x * WALL_SIZE, y * WALL_SIZE))


class AnimatedMapTile(MapTile, Animated):
    def __init__(self, images_path, x, y, frame_duration, flip_x=False, flip_y=False, rotate=0, size=None):
        images = load_images_from_folder(images_path)

        MapTile.__init__(self, images[0], x, y)
        if size:
            self.rect.size = size
        Animated.__init__(self, images, self.rect.size, frame_duration, flip_x, flip_y, rotate)

    def update(self):
        self.animate_new_frame()
