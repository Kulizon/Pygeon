import pygame as pg

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
pg.init()
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


CHARACTER_SIZE = 55
WALL_SIZE = 55

characters = pg.sprite.Group()
traps = pg.sprite.Group()
items = pg.sprite.Group()
visuals = pg.sprite.Group()
walls = pg.sprite.Group()
ground = pg.sprite.Group()
decorations = pg.sprite.Group()

font = pg.font.Font("assets/retro_font.ttf", 22)

class Camera:
    def __init__(self, width, height):
        self.rect = pg.Rect(0, 0, width, height)

        self.width = width
        self.height = height
        self.initial_width = width
        self.initial_height = height

    def update(self, target):
        x = -target.rect.x + (SCREEN_WIDTH // 2)
        y = -target.rect.y + (SCREEN_HEIGHT // 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - SCREEN_WIDTH), x)
        y = max(-(self.height - SCREEN_HEIGHT), y)

        self.rect = pg.Rect(x, y, self.width, self.height)

