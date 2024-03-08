import pygame as pg
pg.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
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
